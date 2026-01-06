import json
import os
from typing import Annotated, Dict, List, Literal, TypedDict, Union

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

load_dotenv()

# Evita UnicodeEncodeError en headers HTTP: forzamos locales ASCII dentro del contenedor
# (httpx normaliza headers como ASCII por defecto).
os.environ.setdefault("LC_ALL", "C")
os.environ.setdefault("LANG", "C")

# Flag de test: si está activo, NO llama al LLM y permite probar el flujo end-to-end
# (agentes + scoring determinista) sin depender de OpenRouter.
SKIP_LLM_SUMMARY = os.getenv("SKIP_LLM_SUMMARY", "false").strip().lower() in (
    "1",
    "true",
    "yes",
    "y",
    "on",
)

# --- Definición del Estado ---


class AgentResponse(TypedDict):
    """Estructura para almacenar la respuesta individual de cada agente."""

    agent_id: str
    status: str
    result: Dict
    error: Union[str, None]


class NormalizedEvaluation(TypedDict):
    """
    Evaluación normalizada por regla/framework para que el output "huela" a rules.toml
    sin hacer el sistema complejo.
    """

    framework: Literal["bias", "unesco", "eu_ai_act"]
    rule_id: str
    rule_name: Union[str, None]
    score: Union[float, None]  # 0..1 si existe
    threshold: Union[float, None]  # 0..1 si existe
    triggered: Union[bool, None]
    reason: Union[str, None]
    source_agent: str
    scope: Literal["input", "output"]


class AuditResult(TypedDict):
    scope: Literal["input", "output"]
    analysis_text: str
    agent_findings: List[AgentResponse]
    evaluations: List[NormalizedEvaluation]
    risk_score: float
    risk_inputs: Dict
    decision: Literal["allow", "warn", "block"]


class OrchestratorDecision(TypedDict):
    decision: Literal["allow", "warn", "block"]
    risk_score: float
    summary: str
    key_findings: List[str]
    recommendations: List[str]
    risk_inputs: Dict


def compute_risk_score(agent_responses: List[AgentResponse]) -> Dict[str, object]:
    """
    Computa un risk_score determinista (0.0-1.0) a partir de los outputs de los agentes y devuelve
    además detalles de depuración (risk_inputs).

    Heurística (sencilla pero funcional):
    - Si un agente aporta un score numérico (0..1), se usa como señal principal.
    - Si no hay score, se usan banderas booleanas (bias_detected / violation_detected / risk_detected).
    - Si un agente falla (status=error) añade 0.15 por incertidumbre (cap en 1.0)
    - risk_score final = max(señales) + incertidumbre, cap a 1.0
    """

    def _as_float_0_1(value) -> Union[float, None]:
        if value is None:
            return None
        try:
            f = float(value)
        except (TypeError, ValueError):
            return None
        if f < 0.0 or f > 1.0:
            return None
        return f

    uncertainty = 0.0
    per_agent_signal: Dict[str, float] = {}
    signal_scores: List[float] = []

    for r in agent_responses:
        agent_id = r.get("agent_id") or "unknown"
        status = r.get("status")

        if status != "success":
            uncertainty += 0.15
            per_agent_signal[agent_id] = 0.0
            continue

        result = r.get("result", {}) or {}

        # Preferimos score numérico si existe
        numeric_score = _as_float_0_1(result.get("score"))
        if numeric_score is None and isinstance(result.get("result"), dict):
            # por si algún agente anida "result": {"score": ...}
            numeric_score = _as_float_0_1(result["result"].get("score"))

        if numeric_score is not None:
            per_agent_signal[agent_id] = float(numeric_score)
            signal_scores.append(float(numeric_score))
            continue

        # Fallback a heurística booleana por agente
        if agent_id == "bias":
            s = 0.6 if bool(result.get("bias_detected")) else 0.0
        elif agent_id == "unesco":
            s = 0.7 if bool(result.get("violation_detected")) else 0.0
        elif agent_id == "eu_ai_act":
            s = 0.7 if bool(result.get("risk_detected")) else 0.0
        else:
            s = 0.0

        per_agent_signal[agent_id] = float(s)
        signal_scores.append(float(s))

    base_signal = max(signal_scores) if signal_scores else 0.0
    final_risk_score = min(1.0, max(0.0, float(base_signal + uncertainty)))

    return {
        "risk_score": final_risk_score,
        "risk_inputs": {
            "base_signal": float(base_signal),
            "uncertainty": float(uncertainty),
            "final_risk_score": float(final_risk_score),
            "per_agent_signal": per_agent_signal,
        },
    }


def decision_from_risk_score(risk_score: float) -> Literal["allow", "warn", "block"]:
    """
    Mapea determinísticamente el score a una decisión.
    Ajustable según tus políticas.
    """
    if risk_score >= 0.75:
        return "block"
    if risk_score >= 0.35:
        return "warn"
    return "allow"


class GraphState(TypedDict):
    """
    El estado del grafo que se propaga entre nodos.
    """

    # Entradas originales (trazabilidad)
    system_prompt: str
    user_input: str
    assistant_output: Union[str, None]

    # Texto/paquete completo a evaluar por los agentes (actual)
    analysis_text: str

    # Textos separados para auditoría input/output
    input_analysis_text: str
    output_analysis_text: Union[str, None]

    # Respuestas acumuladas de los agentes especialistas (sobre analysis_text)
    # Se usa Annotated con una función de reducción para acumular en la lista
    agent_responses: Annotated[List[AgentResponse], lambda x, y: x + y]

    # Veredicto final estructurado generado por el orquestador
    final_report: OrchestratorDecision

    # Metadatos o flags de control
    metadata: Dict


# --- Esquemas de Entrada/Salida para la API ---


class AnalysisRequest(BaseModel):
    system_prompt: str = Field(..., description="System prompt usado por la empresa")
    user_input: str = Field(..., description="Input del usuario final")
    assistant_output: Union[str, None] = Field(
        default=None,
        description="Salida del asistente (si ya existe). Si no existe, se evalúa solo el paquete system+user.",
    )
    context: Dict = Field(default_factory=dict)
    agents: List[Literal["bias", "unesco", "eu_ai_act"]] = Field(
        default_factory=lambda: ["bias", "unesco", "eu_ai_act"]
    )


class AnalysisResponse(BaseModel):
    system_prompt: str
    user_input: str
    assistant_output: Union[str, None]

    # Auditorías separadas (lo que pedías: input y output desde reglas/riesgos)
    input_audit: AuditResult
    output_audit: Union[AuditResult, None]

    # Para trazabilidad: el paquete completo que se pasó a los agentes
    analysis_text: str

    # Raw findings (compatibilidad / debugging)
    findings: List[AgentResponse]

    # Decisión final consolidada (con risk_inputs siempre)
    decision: OrchestratorDecision


# --- Configuración de URLs de Agentes ---

BIAS_AGENT_URL = os.getenv("BIAS_AGENT_URL", "http://bias-agent:8000/mcp")
EU_AGENT_URL = os.getenv("EU_AGENT_URL", "http://eu-ai-act-agent:8000/mcp")
UNESCO_AGENT_URL = os.getenv("UNESCO_AGENT_URL", "http://unesco-agent:8000/mcp")


def build_analysis_text(
    system_prompt: str, user_input: str, assistant_output: Union[str, None]
) -> str:
    """
    Construye el 'paquete completo' a evaluar.
    Requisito: siempre paquete completo, y si existe assistant_output, se incluye.
    """
    parts = [
        "=== SYSTEM PROMPT ===",
        system_prompt,
        "",
        "=== USER INPUT ===",
        user_input,
    ]
    if assistant_output is not None:
        parts += [
            "",
            "=== ASSISTANT OUTPUT ===",
            assistant_output,
        ]
    return "\n".join(parts)


def build_input_text(system_prompt: str, user_input: str) -> str:
    return "\n".join(
        [
            "=== SYSTEM PROMPT ===",
            system_prompt,
            "",
            "=== USER INPUT ===",
            user_input,
        ]
    )


def build_output_text(assistant_output: Union[str, None]) -> Union[str, None]:
    if assistant_output is None:
        return None
    return "\n".join(
        [
            "=== ASSISTANT OUTPUT ===",
            assistant_output,
        ]
    )


def normalize_evaluations(
    scope: Literal["input", "output"],
    agent_responses: List[AgentResponse],
    used_rules: Dict[str, Dict[str, Union[str, None]]],
) -> List[NormalizedEvaluation]:
    """
    Normaliza a un formato "por regla" sin complicarlo.

    - used_rules: info mínima sobre qué regla invocó el orquestador por agente
      (p.ej. {"unesco": {"rule_id": "human_rights", "rule_name": None}, ...})
    """
    out: List[NormalizedEvaluation] = []

    for r in agent_responses:
        agent_id = r.get("agent_id")
        status = r.get("status")
        result = r.get("result", {}) or {}
        error = r.get("error")

        if agent_id not in ("bias", "unesco", "eu_ai_act"):
            continue

        rule_id = (used_rules.get(agent_id, {}) or {}).get("rule_id") or (
            result.get("rule") or result.get("rule_id") or "unknown"
        )
        rule_name = (used_rules.get(agent_id, {}) or {}).get("rule_name") or result.get(
            "rule_name"
        )

        score = None
        threshold = None
        triggered = None

        # Intentamos capturar score/threshold/triggered si existen en el result del agente
        if isinstance(result, dict):
            if "score" in result:
                try:
                    score = float(result.get("score"))
                except Exception:
                    score = None
            if "threshold" in result:
                try:
                    threshold = float(result.get("threshold"))
                except Exception:
                    threshold = None

            if agent_id == "bias":
                if "bias_detected" in result:
                    triggered = bool(result.get("bias_detected"))
            elif agent_id == "unesco":
                if "violation_detected" in result:
                    triggered = bool(result.get("violation_detected"))
            elif agent_id == "eu_ai_act":
                if "risk_detected" in result:
                    triggered = bool(result.get("risk_detected"))

        reason = None
        if isinstance(result, dict):
            # distintos agentes usan "reason"
            if "reason" in result:
                reason = result.get("reason")
        if not reason and error:
            reason = error

        out.append(
            {
                "framework": agent_id,
                "rule_id": str(rule_id),
                "rule_name": rule_name if rule_name is None else str(rule_name),
                "score": score,
                "threshold": threshold,
                "triggered": triggered if status == "success" else None,
                "reason": None if reason is None else str(reason),
                "source_agent": agent_id,
                "scope": scope,
            }
        )

    return out


# --- Nodos de Trabajo (Worker Nodes) ---


async def call_bias_agent(state: GraphState) -> Dict:
    """Llama al microservicio de detección de sesgos."""
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "detect_bias",
                "params": {"text": state["analysis_text"]},
                "id": 1,
            }
            response = await client.post(BIAS_AGENT_URL, json=payload, timeout=30.0)
            result = response.json().get("result", {})
            # Enriquecemos mínimamente con rule_id para reflejar rules.toml (sin complicarlo)
            if isinstance(result, dict) and "rule_id" not in result:
                result["rule_id"] = "fairness_non_discrimination"
                result["rule_name"] = "Fairness / Non-discrimination"
            return {
                "agent_responses": [
                    {
                        "agent_id": "bias",
                        "status": "success",
                        "result": result,
                        "error": None,
                    }
                ]
            }
        except Exception as e:
            return {
                "agent_responses": [
                    {
                        "agent_id": "bias",
                        "status": "error",
                        "result": {},
                        "error": str(e),
                    }
                ]
            }


async def call_eu_agent(state: GraphState) -> Dict:
    """Llama al microservicio de EU AI Act."""
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "detect_risk",
                "params": {"text": state["analysis_text"], "rule": "risk_management"},
                "id": 1,
            }
            response = await client.post(EU_AGENT_URL, json=payload, timeout=30.0)
            result = response.json().get("result", {})
            # Aseguramos que el result refleje claramente la rule evaluada (rules.toml)
            if isinstance(result, dict) and "rule_id" not in result:
                result["rule_id"] = result.get("rule", "risk_management")
            return {
                "agent_responses": [
                    {
                        "agent_id": "eu_ai_act",
                        "status": "success",
                        "result": result,
                        "error": None,
                    }
                ]
            }
        except Exception as e:
            return {
                "agent_responses": [
                    {
                        "agent_id": "eu_ai_act",
                        "status": "error",
                        "result": {},
                        "error": str(e),
                    }
                ]
            }


async def call_unesco_agent(state: GraphState) -> Dict:
    """Llama al microservicio de UNESCO."""
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "detect_ethical_risk",
                "params": {"text": state["analysis_text"], "rule_id": "human_rights"},
                "id": 1,
            }
            response = await client.post(UNESCO_AGENT_URL, json=payload, timeout=30.0)
            result = response.json().get("result", {})
            # Aseguramos que el result refleje claramente la rule evaluada (rules.toml)
            if isinstance(result, dict) and "rule_id" not in result:
                result["rule_id"] = result.get("rule", "human_rights")
            return {
                "agent_responses": [
                    {
                        "agent_id": "unesco",
                        "status": "success",
                        "result": result,
                        "error": None,
                    }
                ]
            }
        except Exception as e:
            return {
                "agent_responses": [
                    {
                        "agent_id": "unesco",
                        "status": "error",
                        "result": {},
                        "error": str(e),
                    }
                ]
            }


async def generate_final_report(state: GraphState) -> Dict:
    """
    Genera SOLO campos narrativos con LLM y calcula determinísticamente decision/risk_score.

    - risk_score: determinista (compute_risk_score)
    - decision: determinista (decision_from_risk_score)
    - summary/key_findings/recommendations: LLM (JSON válido)
    """
    risk_calc = compute_risk_score(state["agent_responses"])
    risk_score = float(risk_calc["risk_score"])
    decision = decision_from_risk_score(risk_score)

    # OpenRouter es compatible con la API de OpenAI, pero sus cabeceras (y/o las del SDK)
    # pueden provocar UnicodeEncodeError dentro de httpx si algún valor no es ASCII.
    #
    # Para evitarlo:
    # - Usamos OPENAI_API_KEY (o fallback a OPENROUTER_API_KEY) como api_key
    # - Añadimos solo headers ASCII y sanitizamos su contenido.
    # - Forzamos también un User-Agent ASCII (algunos stacks lo incluyen automáticamente).
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta API key. Define OPENAI_API_KEY (recomendado) o OPENROUTER_API_KEY."
        )

    http_referer = (
        os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    x_title = (
        os.getenv("OPENROUTER_X_TITLE", "ethic-obs-orchestrator")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    user_agent = (
        os.getenv("OPENROUTER_USER_AGENT", "ethic-obs-orchestrator/1.0")
        .encode("ascii", "ignore")
        .decode("ascii")
    )

    if SKIP_LLM_SUMMARY:
        final_report: OrchestratorDecision = {
            "decision": decision,
            "risk_score": risk_score,
            "summary": "SKIP_LLM_SUMMARY habilitado: narrativa omitida para prueba end-to-end.",
            "key_findings": [],
            "recommendations": [],
            "risk_inputs": risk_calc["risk_inputs"],
        }
        return {"final_report": final_report}

    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo"),
        temperature=0.2,
        default_headers={
            "HTTP-Referer": http_referer,
            "X-Title": x_title,
            "User-Agent": user_agent,
        },
    )

    responses_str = json.dumps(state["agent_responses"], ensure_ascii=False, indent=2)

    system_prompt = (
        "Eres un Orquestador Ético de IA. Recibirás un paquete (system/user/assistant) y hallazgos "
        "de tres agentes (Sesgo, EU AI Act y UNESCO). Tu tarea es redactar SOLO los campos narrativos.\n\n"
        "Devuelve SIEMPRE un JSON válido (sin markdown) con este esquema exacto:\n"
        "{\n"
        '  "summary": "string",\n'
        '  "key_findings": ["string", ...],\n'
        '  "recommendations": ["string", ...]\n'
        "}\n"
        "No incluyas campos extra. No incluyas decision ni risk_score."
    )

    user_prompt = (
        "Paquete completo analizado:\n"
        f"{state['analysis_text']}\n\n"
        "Resultados de los agentes (JSON):\n"
        f"{responses_str}\n\n"
        f"Decisión ya calculada por política interna: {decision}\n"
        f"Risk score ya calculado por política interna: {risk_score}\n\n"
        "Redacta summary, key_findings y recommendations coherentes con esos hallazgos."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    response = await llm.ainvoke(messages)

    narrative = {
        "summary": "",
        "key_findings": [],
        "recommendations": [],
    }
    try:
        parsed = json.loads(response.content)
        if isinstance(parsed, dict):
            narrative["summary"] = str(parsed.get("summary", "") or "")
            narrative["key_findings"] = list(parsed.get("key_findings", []) or [])
            narrative["recommendations"] = list(parsed.get("recommendations", []) or [])
    except Exception:
        narrative = {
            "summary": "No se pudo parsear la narrativa del sintetizador como JSON. Revisa el contenido devuelto por el LLM.",
            "key_findings": [],
            "recommendations": [
                "Ajustar el prompt del sintetizador para forzar JSON válido y reintentar."
            ],
        }

    final_report: OrchestratorDecision = {
        "decision": decision,
        "risk_score": risk_score,
        "summary": narrative["summary"],
        "key_findings": narrative["key_findings"],
        "recommendations": narrative["recommendations"],
        "risk_inputs": risk_calc["risk_inputs"],
    }

    return {"final_report": final_report}


# --- Construcción del Grafo ---


def create_orchestrator_graph(enabled_agents: List[str] | None = None):
    # Inicializamos el grafo con nuestro estado personalizado
    workflow = StateGraph(GraphState)

    # Añadimos los nodos
    workflow.add_node("bias_agent", call_bias_agent)
    workflow.add_node("eu_agent", call_eu_agent)
    workflow.add_node("unesco_agent", call_unesco_agent)
    workflow.add_node("summarizer", generate_final_report)

    # Entradas en paralelo según agents habilitados
    enabled_agents = enabled_agents or ["bias", "unesco", "eu_ai_act"]
    entry_nodes: List[str] = []
    if "bias" in enabled_agents:
        entry_nodes.append("bias_agent")
    if "eu_ai_act" in enabled_agents:
        entry_nodes.append("eu_agent")
    if "unesco" in enabled_agents:
        entry_nodes.append("unesco_agent")

    # LangGraph no admite pasar una lista a set_entry_point(). En su lugar, hacemos fan-out desde START:
    # - si hay agentes habilitados: START -> cada agente
    # - si no hay agentes habilitados: START -> summarizer
    if entry_nodes:
        for node in entry_nodes:
            workflow.add_edge(START, node)
    else:
        workflow.add_edge(START, "summarizer")

    # Todos convergen en el sintetizador (solo desde los que existan)
    if "bias_agent" in entry_nodes:
        workflow.add_edge("bias_agent", "summarizer")
    if "eu_agent" in entry_nodes:
        workflow.add_edge("eu_agent", "summarizer")
    if "unesco_agent" in entry_nodes:
        workflow.add_edge("unesco_agent", "summarizer")

    # El sintetizador es el punto final
    workflow.add_edge("summarizer", END)

    return workflow.compile()


# --- API FastAPI (punto centralizado) ---

app = FastAPI(title="Ethic Orchestrator")


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(payload: AnalysisRequest) -> AnalysisResponse:
    # Textos separados para auditoría input/output
    input_text = build_input_text(payload.system_prompt, payload.user_input)
    output_text = build_output_text(payload.assistant_output)

    # Paquete completo que se pasa a los agentes (como acordamos)
    analysis_text = build_analysis_text(
        system_prompt=payload.system_prompt,
        user_input=payload.user_input,
        assistant_output=payload.assistant_output,
    )

    graph = create_orchestrator_graph(enabled_agents=payload.agents)

    initial_state: GraphState = {
        "system_prompt": payload.system_prompt,
        "user_input": payload.user_input,
        "assistant_output": payload.assistant_output,
        "analysis_text": analysis_text,
        "input_analysis_text": input_text,
        "output_analysis_text": output_text,
        "agent_responses": [],
        "final_report": {
            "decision": "warn",
            "risk_score": 0.5,
            "summary": "",
            "key_findings": [],
            "recommendations": [],
            "risk_inputs": {
                "base_signal": 0.0,
                "uncertainty": 0.0,
                "final_risk_score": 0.0,
                "per_agent_signal": {},
            },
        },
        "metadata": payload.context or {},
    }

    final_state = await graph.ainvoke(initial_state)

    findings = final_state.get("agent_responses", [])
    decision_obj = final_state.get("final_report", {})

    # Used rules (mínimo, para que quede claro qué rule_id se invocó por agente)
    used_rules = {
        "bias": {
            "rule_id": "fairness_non_discrimination",
            "rule_name": "Fairness / Non-discrimination",
        },
        "unesco": {"rule_id": "human_rights", "rule_name": None},
        "eu_ai_act": {"rule_id": "risk_management", "rule_name": None},
    }

    # Normalizamos evaluaciones y las exponemos en auditorías separadas.
    # Nota: los findings vienen del paquete completo (system+user+assistant),
    # pero los presentamos separados para input/output sin duplicar llamadas.
    evaluations_input = normalize_evaluations("input", findings, used_rules)
    evaluations_output = normalize_evaluations("output", findings, used_rules)

    risk_score_val = float(decision_obj.get("risk_score", 0.0) or 0.0)
    risk_inputs_val = decision_obj.get("risk_inputs", {}) or {}

    input_audit: AuditResult = {
        "scope": "input",
        "analysis_text": input_text,
        "agent_findings": findings,
        "evaluations": evaluations_input,
        "risk_score": risk_score_val,
        "risk_inputs": risk_inputs_val,
        "decision": str(decision_obj.get("decision", "warn")),
    }

    output_audit: Union[AuditResult, None]
    if output_text is None:
        output_audit = None
    else:
        output_audit = {
            "scope": "output",
            "analysis_text": output_text,
            "agent_findings": findings,
            "evaluations": evaluations_output,
            "risk_score": risk_score_val,
            "risk_inputs": risk_inputs_val,
            "decision": str(decision_obj.get("decision", "warn")),
        }

    return AnalysisResponse(
        system_prompt=final_state["system_prompt"],
        user_input=final_state["user_input"],
        assistant_output=final_state["assistant_output"],
        input_audit=input_audit,
        output_audit=output_audit,
        analysis_text=final_state["analysis_text"],
        findings=findings,
        decision=decision_obj,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
