import os

import tomli
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from openai import OpenAI

# Carga configuraciones
load_dotenv()
with open("rules.toml", "rb") as f:
    RULES = tomli.load(f)
    EU_RULES = [r for r in RULES["eu_ai_act"] if r["enabled"]]  # Filtra reglas EU

app = FastAPI(title="EU AI Act Agent")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1", api_key=os.getenv("OPENROUTER_API_KEY")
)


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    data = await request.json()
    method = data.get("method")
    params = data.get("params", {})

    if method == "health":
        return {
            "jsonrpc": "2.0",
            "result": {
                "status": "healthy",
                "llm": os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo"),
            },
        }

    elif method == "detect_risk":
        text = params.get("text", "")
        rule_id = params.get("rule", "risk_management")  # Default: Art. 9
        rule = next((r for r in EU_RULES if r["id"] == rule_id), None)

        if not rule:
            raise HTTPException(
                status_code=400, detail=f"Regla {rule_id} no encontrada"
            )

        response = client.chat.completions.create(
            model=os.getenv("OPENROUTER_MODEL"),
            messages=[
                {
                    "role": "user",
                    "content": f"{rule['check_prompt']}\nTexto: \"{text}\"\nRespuesta en JSON: {{'score': float, 'reason': str}}",
                }
            ],
            temperature=0.3,
        )
        result = eval(response.choices[0].message.content)
        return {
            "jsonrpc": "2.0",
            "result": {
                "risk_detected": result["score"] > rule["threshold"],
                "rule": rule["id"],
                "reason": result["reason"],
            },
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
