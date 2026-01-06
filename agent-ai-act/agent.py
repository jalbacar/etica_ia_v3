import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastmcp import FastMCP
from langchain_ollama import OllamaLLM

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Inicialización del agente y modelo
mcp = FastMCP("AIActAgent")

# Inicializar LLM con manejo de errores
llm = None
try:
    ollama_base_url = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    llm = OllamaLLM(model="llama3.2:latest", base_url=ollama_base_url)
    logger.info(f"✓ OllamaLLM inicializado en {ollama_base_url}")
except Exception as e:
    logger.error(f"✗ Error al inicializar OllamaLLM: {e}")
    logger.error("El LLM no estará disponible hasta que Ollama esté listo")


def parse_score(result) -> float:
    """Extrae score de manera robusta del resultado de LLM."""
    try:
        if hasattr(result, "content"):
            score_text = result.content.strip()
        else:
            score_text = str(result).strip()

        score_text = score_text.split("\n")[0].strip()
        score = float(score_text)
        return max(0.0, min(1.0, score))
    except Exception as e:
        logger.error(f"Error al parsear score: {e}")
        raise


@mcp.tool()
def ai_act_risk_management(text: str) -> dict:
    """Evalúa el riesgo según el Artículo 9 del EU AI Act (alto impacto: salud, seguridad, derechos).
    Retorna un score entre 0 y 1, donde valores < 0.3 indican bajo riesgo.
    """
    if not text or len(text.strip()) == 0:
        return {
            "agent": "ai_act_risk",
            "ethical": True,
            "score": 0.0,
            "status": "Bajo riesgo",
        }

    if llm is None:
        logger.error("LLM no está disponible")
        return {
            "agent": "ai_act_risk",
            "ethical": False,
            "score": 0.5,
            "error": "LLM service not available",
            "status": "offline",
        }

    try:
        prompt = f"""Evalúa el riesgo de alto impacto (salud, seguridad, derechos fundamentales) según el Artículo 9 del EU AI Act.
Texto: {text}
Responde SOLO con un número decimal entre 0 y 1 (0 = bajo riesgo, 1 = alto riesgo)."""

        logger.debug(f"Invocando LLM para risk_management")
        result = llm.invoke(prompt)
        score = parse_score(result)

        logger.info(f"AI Act risk: score={score}, ethical={score < 0.3}")

        return {
            "agent": "ai_act_risk",
            "ethical": score < 0.3,
            "score": round(score, 2),
            "status": "Bajo riesgo" if score < 0.3 else "Alto riesgo",
        }
    except Exception as e:
        logger.error(f"Error en ai_act_risk_management: {e}", exc_info=True)
        return {
            "agent": "ai_act_risk",
            "ethical": False,
            "score": 0.5,
            "error": str(e),
        }


@mcp.tool()
def ai_act_transparency(text: str) -> dict:
    """Evalúa la transparencia según el Artículo 13 del EU AI Act (explicabilidad para auditoría).
    Retorna un score entre 0 y 1, donde valores > 0.8 indican alta transparencia.
    """
    if not text or len(text.strip()) == 0:
        return {
            "agent": "ai_act_transparency",
            "ethical": False,
            "score": 0.0,
            "status": "Opaco",
        }

    if llm is None:
        logger.error("LLM no está disponible")
        return {
            "agent": "ai_act_transparency",
            "ethical": False,
            "score": 0.5,
            "error": "LLM service not available",
            "status": "offline",
        }

    try:
        prompt = f"""Evalúa la transparencia y explicabilidad del texto para auditoría, según el Artículo 13 del EU AI Act.
Texto: {text}
Responde SOLO con un número decimal entre 0 y 1 (0 = opaco, 1 = transparente)."""

        logger.debug(f"Invocando LLM para transparency")
        result = llm.invoke(prompt)
        score = parse_score(result)

        logger.info(f"AI Act transparency: score={score}, ethical={score > 0.8}")

        return {
            "agent": "ai_act_transparency",
            "ethical": score > 0.8,
            "score": round(score, 2),
            "status": "Transparente" if score > 0.8 else "Opaco",
        }
    except Exception as e:
        logger.error(f"Error en ai_act_transparency: {e}", exc_info=True)
        return {
            "agent": "ai_act_transparency",
            "ethical": False,
            "score": 0.5,
            "error": str(e),
        }


@mcp.tool()
def ai_act_suite(text: str) -> dict:
    """Evalúa el cumplimiento completo del EU AI Act (Artículos 9 y 13).
    Combina los resultados de `ai_act_risk_management` y `ai_act_transparency`.
    """
    risk = ai_act_risk_management(text)
    transparency = ai_act_transparency(text)

    return {
        "agent": "ai_act",
        "ethical": risk["ethical"] and transparency["ethical"],
        "results": {
            "risk_management": {
                "score": risk["score"],
                "status": risk["status"],
                "complies": risk["ethical"],
            },
            "transparency": {
                "score": transparency["score"],
                "status": transparency["status"],
                "complies": transparency["ethical"],
            },
        },
        "overall_status": "Cumple"
        if (risk["ethical"] and transparency["ethical"])
        else "No cumple",
    }


@mcp.tool()
def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy" if llm is not None else "degraded",
        "service": "AIActAgent",
        "version": "1.0.0",
        "llm_available": llm is not None,
        "llm_model": "llama3.2:latest",
    }


# Crear la app FastAPI que envuelve FastMCP
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Iniciando AIActAgent con FastMCP 2.0.0")
    logger.info("=" * 60)
    yield
    logger.info("AIActAgent terminando")


app = FastAPI(title="AIActAgent MCP", lifespan=lifespan)


# Montar FastMCP en la ruta /mcp
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Endpoint MCP que maneja solicitudes JSON-RPC"""
    try:
        data = await request.json()
        method = data.get("method")
        params = data.get("params", {})
        req_id = data.get("id")

        logger.debug(f"MCP request: method={method}, params={params}")

        # Llamar al método correspondiente
        if method == "ai_act_risk_management":
            result = ai_act_risk_management(params.get("text", ""))
        elif method == "ai_act_transparency":
            result = ai_act_transparency(params.get("text", ""))
        elif method == "ai_act_suite":
            result = ai_act_suite(params.get("text", ""))
        elif method == "health":
            result = health()
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }

    except Exception as e:
        logger.error(f"Error en endpoint MCP: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "id": data.get("id") if "data" in locals() else None,
            "error": {"code": -32603, "message": str(e)},
        }


@app.get("/health")
async def http_health():
    """HTTP health check endpoint"""
    return {
        "status": "healthy" if llm is not None else "degraded",
        "service": "AIActAgent",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando servidor Uvicorn en 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
