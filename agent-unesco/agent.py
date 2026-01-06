import os

import tomli
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from openai import OpenAI

# Carga configuraciones
load_dotenv()
with open("rules.toml", "rb") as f:
    RULES = tomli.load(f)
    UNESCO_RULES = [r for r in RULES["unesco"] if r["enabled"]]  # Filtra reglas UNESCO

app = FastAPI(title="UNESCO Ethical Agent")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
)


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    data = await request.json()
    method = data.get("method")
    params = data.get("params", {})

    if method == "health":
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "result": {
                    "status": "healthy",
                    "service": "UNESCO Agent",
                    "llm_model": os.getenv("OPENROUTER_MODEL"),
                },
            }
        )

    elif method == "detect_ethical_risk":
        text = params.get("text", "")
        rule_id = params.get("rule_id", "human_rights")  # Default: Principle 1
        rule = next((r for r in UNESCO_RULES if r["id"] == rule_id), None)

        if not rule:
            raise HTTPException(
                status_code=400, detail=f"UNESCO rule {rule_id} not found"
            )

        # Llamada a OpenRouter con prompt específico de UNESCO
        response = client.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL"),
            messages=[
                {
                    "role": "user",
                    "content": f"""Evalúa este texto según {rule["name"]} (UNESCO).
                Texto: "{text}"
                Respuesta en JSON: {{"score": float, "reason": str}}""",
                }
            ],
            temperature=0.3,
        )
        result = eval(response.choices[0].message.content)
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "result": {
                    "violation_detected": result["score"] > rule["threshold"],
                    "score": result["score"],
                    "reason": result["reason"],
                    "rule": rule_id,
                },
            }
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
