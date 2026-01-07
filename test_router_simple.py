"""Test simple del router"""
import asyncio
import json
from client_python.ethical_subject import OrchestratorClient


async def main():
    client = OrchestratorClient()
    
    print("=" * 60)
    print("TEST 1: Router Auto (agents=[])")
    print("=" * 60)
    
    r1 = await client.analyze(
        system_prompt="Asistente RRHH",
        user_input="Juan es mejor porque es hombre",
        assistant_output=None,
        context={"domain": "hr"},
        agents=[],
    )
    
    agents_auto = list(r1["decision"]["risk_inputs"]["per_agent_signal"].keys())
    print(f"Agentes seleccionados: {agents_auto}")
    print(f"Risk score: {r1['decision']['risk_score']}")
    
    print("\n" + "=" * 60)
    print("TEST 2: Explícito (3 agentes)")
    print("=" * 60)
    
    r2 = await client.analyze(
        system_prompt="Asistente RRHH",
        user_input="Juan es mejor porque es hombre",
        assistant_output=None,
        context={"domain": "hr"},
        agents=["bias", "unesco", "eu_ai_act"],
    )
    
    agents_explicit = list(r2["decision"]["risk_inputs"]["per_agent_signal"].keys())
    print(f"Agentes usados: {agents_explicit}")
    print(f"Risk score: {r2['decision']['risk_score']}")
    
    print("\n" + "=" * 60)
    print(f"AHORRO: {len(agents_auto)} vs {len(agents_explicit)} agentes")
    print(f"Reducción: {((len(agents_explicit) - len(agents_auto)) / len(agents_explicit) * 100):.0f}%")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
