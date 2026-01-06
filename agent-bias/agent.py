import os

import tomli
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse  # ← Añade esta línea
from openai import OpenAI

load_dotenv()

app = FastAPI(title="BiasAgent MCP")

# Configuración OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
)

with open("rules.toml", "rb") as f:
    RULES = tomli.load(f)
    BIAS_RULES = [
        r for r in RULES["unesco"] if r["id"] == "fairness_non_discrimination"
    ]


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    try:
        data = await request.json()
        method = data.get("method")
        params = data.get("params", {})

        if method == "health":
            return JSONResponse(
                {  # ← Usa JSONResponse
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "status": "healthy",
                        "llm": os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo"),
                    },
                }
            )

        elif method == "detect_bias":
            text = params.get("text", "")
            response = client.chat.completions.create(
                model=os.getenv("OPENROUTER_MODEL"),
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analiza si este texto contiene sesgos (responde en JSON):\nTexto: "{text}"\nFormato: {{"bias_detected": bool, "reason": "explicación"}}""",
                    }
                ],
                temperature=0.3,
            )
            # Decodificar respuesta como JSON seguro
            import json

            result = json.loads(response.choices[0].message.content)

            return JSONResponse(
                {  # ← Usa JSONResponse
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": result,
                }
            )

        else:
            raise HTTPException(status_code=400, detail="Método no soportado")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
            headers={
                "Content-Type": "application/json; charset=utf-8"
            },  # ← Fuerza UTF-8
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
