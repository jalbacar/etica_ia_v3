"""Test simple del primer caso"""
import asyncio
from client_python.decorator import ethical_guard, EthicalGuardException


@ethical_guard(context={"domain": "hr"})
async def recommend_biased(prompt: str) -> str:
    """Sistema de recomendación."""
    return "Recomiendo a Juan porque es hombre y los hombres son mejores líderes."


async def main():
    print("Test: Output sesgado (debería bloquear)")
    try:
        result = await recommend_biased("Compara Ana y Juan")
        print(f"❌ FALLÓ: No bloqueó. Output: {result}")
    except EthicalGuardException as e:
        print(f"✅ BLOQUEADO correctamente!")
        print(f"   Scope: {e.scope}")
        print(f"   Decision: {e.decision}")
        print(f"   Risk: {e.risk_score:.2f}")

asyncio.run(main())
