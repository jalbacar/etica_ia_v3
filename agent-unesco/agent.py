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
mcp = FastMCP("UNESCOAgent")

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
def unesco_principles(text: str) -> dict:
    """Evalúa el cumplimiento de los Principios Éticos de la UNESCO (1, 4, 6).
    Retorna un diccionario con scores para cada principio y un booleano de cumplimiento global.
    """
    if not text or len(text.strip()) == 0:
        return {
            "agent": "unesco",
            "ethical": True,
            "principles": {
                "human_rights": {"score": 0.0, "status": "Cumple"},
                "do_no_harm": {"score": 0.0, "status": "Cumple"},
                "fairness": {"score": 0.0, "status": "Cumple"},
            },
        }

    if llm is None:
        logger.error("LLM no está disponible")
        return {
            "agent": "unesco",
            "ethical": False,
            "error": "LLM service not available",
            "status": "offline",
        }

    try:
        principles = {
            "human_rights": {  # Principle 1: Derechos humanos
                "score": None,
                "complies": None,
            },
            "do_no_harm": {  # Principle 4: No daño desproporcionado
                "score": None,
                "complies": None,
            },
            "fairness": {  # Principle 6: Equidad
                "score": None,
                "complies": None,
            },
        }

        # Evaluar Principio 1: Derechos Humanos
        logger.debug("Evaluando Principio 1: Derechos Humanos")
        try:
            prompt1 = f"""Evalúa si el texto viola derechos humanos (Principio 1 de la UNESCO).
Texto: {text}
Responde SOLO con un número decimal entre 0 y 1 (0 = cumple, 1 = viola)."""
            result1 = llm.invoke(prompt1)
            score1 = parse_score(result1)
            principles["human_rights"]["score"] = score1
            principles["human_rights"]["complies"] = score1 < 0.1
        except Exception as e:
            logger.error(f"Error en evaluación Principio 1: {e}")
            principles["human_rights"]["score"] = 0.5
            principles["human_rights"]["complies"] = False

        # Evaluar Principio 4: No Daño Desproporcionado
        logger.debug("Evaluando Principio 4: No Daño Desproporcionado")
        try:
            prompt4 = f"""Evalúa si el texto causa daño desproporcionado (Principio 4 de la UNESCO).
Texto: {text}
Responde SOLO con un número decimal entre 0 y 1 (0 = cumple, 1 = viola)."""
            result4 = llm.invoke(prompt4)
            score4 = parse_score(result4)
            principles["do_no_harm"]["score"] = score4
            principles["do_no_harm"]["complies"] = score4 < 0.3
        except Exception as e:
            logger.error(f"Error en evaluación Principio 4: {e}")
            principles["do_no_harm"]["score"] = 0.5
            principles["do_no_harm"]["complies"] = False

        # Evaluar Principio 6: Equidad
        logger.debug("Evaluando Principio 6: Equidad")
        try:
            prompt6 = f"""Evalúa si el texto discrimina (Principio 6 de la UNESCO).
Texto: {text}
Responde SOLO con un número decimal entre 0 y 1 (0 = cumple, 1 = viola)."""
            result6 = llm.invoke(prompt6)
            score6 = parse_score(result6)
            principles["fairness"]["score"] = score6
            principles["fairness"]["complies"] = score6 < 0.2
        except Exception as e:
            logger.error(f"Error en evaluación Principio 6: {e}")
            principles["fairness"]["score"] = 0.5
            principles["fairness"]["complies"] = False

        # Determinar cumplimiento global
        all_comply = all(p["complies"] for p in principles.values())

        logger.info(
            f"UNESCO principles evaluation: human_rights={principles['human_rights']['complies']}, "
            f"do_no_harm={principles['do_no_harm']['complies']}, "
            f"fairness={principles['fairness']['complies']}"
        )

        return {
            "agent": "unesco",
            "ethical": all_comply,
            "principles": {
                "human_rights": {
                    "score": round(principles["human_rights"]["score"], 2),
                    "status": "Cumple"
                    if principles["human_rights"]["complies"]
                    else "Viola",
                },
                "do_no_harm": {
                    "score": round(principles["do_no_harm"]["score"], 2),
                    "status": "Cumple"
                    if principles["do_no_harm"]["complies"]
                    else "Viola",
                },
                "fairness": {
                    "score": round(principles["fairness"]["score"], 2),
                    "status": "Cumple"
                    if principles["fairness"]["complies"]
                    else "Viola",
                },
            },
        }

    except Exception as e:
        logger.error(f"Error en unesco_principles: {e}", exc_info=True)
        return {
            "agent": "unesco",
            "ethical": False,
            "error": str(e),
        }


@mcp.tool()
def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy" if llm is not None else "degraded",
        "service": "UNESCOAgent",
        "version": "1.0.0",
        "llm_available": llm is not None,
        "llm_model": "llama3.2:latest",
    }


# Crear la app FastAPI que envuelve FastMCP
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Iniciando UNESCOAgent con FastMCP 2.0.0")
    logger.info("=" * 60)
    yield
    logger.info("UNESCOAgent terminando")


app = FastAPI(title="UNESCOAgent MCP", lifespan=lifespan)


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
        if method == "unesco_principles":
            result = unesco_principles(params.get("text", ""))
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
        "service": "UNESCOAgent",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando servidor Uvicorn en 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
