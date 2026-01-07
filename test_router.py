"""
Test del Smart Agent Router
Compara el resultado con router automático vs agentes explícitos
"""
import asyncio
import json
from client_python.ethical_subject import (
    Candidate,
    HiringScorer,
    EthicalPacketBuilder,
    OrchestratorClient,
)


async def test_router():
    print("=" * 70)
    print("TEST: Smart Agent Router")
    print("=" * 70)

    # Caso de uso: sistema de contratación con sesgo
    candidates = [
        Candidate(
            name="Ana",
            years_experience=6,
            education_level="master",
            gender="mujer",
            age=32,
        ),
        Candidate(
            name="Juan",
            years_experience=5,
            education_level="bachelor",
            gender="hombre",
            age=31,
        ),
    ]

    # Scoring con sesgo (usa género)
    scorer = HiringScorer(use_sensitive_features=True)
    decision = scorer.decide(candidates)

    builder = EthicalPacketBuilder(company_name="ACME Corp")
    system_prompt = builder.build_system_prompt()
    user_input = builder.build_user_input("Engineering Manager", candidates)
    assistant_output = builder.build_assistant_output(decision)

    client = OrchestratorClient(base_url="http://localhost:8000")

    # Test 1: Router automático (agents=[])
    print("\n📍 TEST 1: Router Automático (agents=[])")
    print("-" * 70)
    result_auto = await client.analyze(
        system_prompt=system_prompt,
        user_input=user_input,
        assistant_output=assistant_output,
        context={"domain": "hr", "scenario": "hiring_demo"},
        agents=[],  # ← Router selecciona automáticamente
    )
    
    auto_agents = list(result_auto["decision"]["risk_inputs"]["per_agent_signal"].keys())
    auto_score = result_auto["decision"]["risk_score"]
    
    print(f"✓ Agentes seleccionados: {auto_agents}")
    print(f"✓ Risk score: {auto_score}")
    print(f"✓ Decision: {result_auto['decision']['decision']}")

    # Test 2: Agentes explícitos (todos)
    print("\n📍 TEST 2: Agentes Explícitos (todos)")
    print("-" * 70)
    result_explicit = await client.analyze(
        system_prompt=system_prompt,
        user_input=user_input,
        assistant_output=assistant_output,
        context={"domain": "hr", "scenario": "hiring_demo"},
        agents=["bias", "unesco", "eu_ai_act"],  # ← Todos los agentes
    )
    
    explicit_agents = list(result_explicit["decision"]["risk_inputs"]["per_agent_signal"].keys())
    explicit_score = result_explicit["decision"]["risk_score"]
    
    print(f"✓ Agentes usados: {explicit_agents}")
    print(f"✓ Risk score: {explicit_score}")
    print(f"✓ Decision: {result_explicit['decision']['decision']}")

    # Comparación
    print("\n📊 COMPARACIÓN")
    print("=" * 70)
    print(f"{'Métrica':<30} | {'Router Auto':<20} | {'Explícito':<20}")
    print("-" * 70)
    print(f"{'Agentes invocados':<30} | {len(auto_agents):<20} | {len(explicit_agents):<20}")
    print(f"{'Risk Score':<30} | {auto_score:<20.2f} | {explicit_score:<20.2f}")
    print(f"{'Ahorro estimado tokens':<30} | {((len(explicit_agents) - len(auto_agents)) / len(explicit_agents) * 100):.0f}%{'':<16} | {'0%':<20}")
    
    print("\n✅ El router funcionó correctamente" if len(auto_agents) < len(explicit_agents) else "\n⚠️ El router no seleccionó menos agentes")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_router())
