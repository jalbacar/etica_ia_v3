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
mcp = FastMCP("BiasAgent")

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
def detect_bias(text: str) -> dict:
    """Detecta sesgos discriminatorios según UNESCO Fairness + EU AI Act.
    Retorna un score entre 0 y 1, donde valores > 0.7 indican riesgo de discriminación.
    Principio 6 de UNESCO: Equidad y no discriminación.
    """
    if not text or len(text.strip()) == 0:
        return {
            "agent": "bias",
            "ethical": True,
            "score": 0.0,
            "principle": "UNESCO Principle 6: Fairness & Non-Discrimination",
            "reason": "✓ Texto vacío",
        }

    if llm is None:
        logger.error("LLM no está disponible")
        return {
            "agent": "bias",
            "ethical": False,
            "score": 0.5,
            "error": "LLM service not available",
            "status": "offline",
        }

    try:
        prompt = f"""Sesgo discriminatorio (género/raza/edad/origen) - score 0-1:
{text}
Responde SOLO con un número decimal entre 0 y 1 (ej: 0.85)."""

        logger.debug(f"Invocando LLM con prompt completo: {prompt}")
        logger.info(f"Texto recibido para evaluación: {text}")

        # Invocación del modelo - OllamaLLM retorna objeto con .content
        result = llm.invoke(prompt)

        logger.debug(f"Resultado completo del LLM: {result}")
        logger.info(f"Respuesta del LLM recibida: {result}")

        # Extraer score de manera robusta
        logger.debug("Iniciando extracción de score del resultado del LLM")
        logger.info(f"Resultado bruto antes de parsear: {result}")
        score = parse_score(result)

        logger.info(
            f"Detección de sesgo completada: score={score}, ethical={score < 0.7}"
        )
        logger.info(f"Detalles del análisis: score={score}, texto='{text}'")

        return {
            "agent": "bias",
            "ethical": score < 0.7,
            "score": round(score, 2),
            "principle": "UNESCO Principle 6: Fairness & Non-Discrimination",
            "reason": (
                "⚠️ Alto riesgo de discriminación detected"
                if score > 0.7
                else "✓ Cumple con principios éticos de equidad"
            ),
        }
    except ValueError as e:
        logger.error(
            f"Error al convertir score a float: {e}. Resultado recibido: {result}"
        )
        return {
            "agent": "bias",
            "ethical": False,
            "score": 0.5,
            "error": f"Invalid score format: {e}",
        }
    except Exception as e:
        logger.error(f"Error en detect_bias: {e}", exc_info=True)
        return {
            "agent": "bias",
            "ethical": False,
            "score": 0.5,
            "error": str(e),
        }


@mcp.tool()
def bias_supervisor(text: str) -> dict:
    """Endpoint principal del agente para supervisión de sesgos.
    Usa `detect_bias` como lógica subyacente.
    Compatible con EU AI Act Art. 9 (Risk Management) y UNESCO Principle 6.
    """
    return detect_bias(text)


@mcp.tool()
def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy" if llm is not None else "degraded",
        "service": "BiasAgent",
        "version": "1.0.0",
        "llm_available": llm is not None,
        "llm_model": "llama3.2:latest",
    }


# Crear la app FastAPI que envuelve FastMCP
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Iniciando BiasAgent con FastMCP 2.0.0")
    logger.info("=" * 60)
    yield
    logger.info("BiasAgent terminando")


app = FastAPI(title="BiasAgent MCP", lifespan=lifespan)


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
        if method == "detect_bias":
            result = detect_bias(params.get("text", ""))
        elif method == "bias_supervisor":
            result = bias_supervisor(params.get("text", ""))
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
        "service": "BiasAgent",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando servidor Uvicorn en 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
