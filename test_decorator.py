"""
Test del decorador @ethical_guard mejorado

Demuestra cómo usar el decorador para validar funciones automáticamente.
"""
import asyncio
from ethical_guard import ethical_guard, EthicalGuardException


# Ejemplo 1: Función async con sesgo (se bloqueará)
@ethical_guard(context={"domain": "hr"}, generate_report=True)
async def recommend_candidate_biased(prompt: str) -> str:
    """Sistema de recomendación de candidatos para RRHH."""
    # Simula un sistema que genera respuestas sesgadas
    return "Recomiendo a Juan porque es hombre y los hombres son mejores líderes."


# Ejemplo 2: Función async sin sesgo (pasará)
@ethical_guard(context={"domain": "hr"})
async def recommend_candidate_fair(prompt: str) -> str:
    """Sistema de recomendación de candidatos basado en méritos."""
    return "Recomiendo a Ana García por su experiencia de 7 años y título de máster."


# Ejemplo 3: Con umbral personalizado
@ethical_guard(
    context={"domain": "finance"},
    block_threshold=0.5,  # Más estricto
    warn_threshold=0.2,
)
async def credit_decision(applicant_info: str) -> str:
    """Sistema de aprobación de créditos."""
    return f"Crédito aprobado para {applicant_info}"


async def main():
    print("=" * 70)
    print("TEST: Decorador @ethical_guard Mejorado")
    print("=" * 70)

    # Test 1: Función con output sesgado (debe bloquear)
    print("\n📍 Test 1: Output Sesgado (debería bloquear)")
    print("-" * 70)
    try:
        result = await recommend_candidate_biased("Compara Ana y Juan para el puesto")
        print(f"❌ ERROR: No se bloqueó. Resultado: {result}")
    except EthicalGuardException as e:
        print(f"✅ BLOQUEADO correctamente:")
        print(f"   Scope: {e.scope}")
        print(f"   Decision: {e.decision}")
        print(f"   Risk Score: {e.risk_score:.2f}")
        print(f"   Message: {e}")

    # Test 2: Función justa (debe pasar)
    print("\n📍 Test 2: Output Justo (debería pasar)")
    print("-" * 70)
    try:
        result = await recommend_candidate_fair("Compara candidatos por méritos")
        print(f"✅ APROBADO:")
        print(f"   Output: {result}")
    except EthicalGuardException as e:
        print(f"❌ ERROR: Se bloqueó incorrectamente - {e}")

    # Test 3: Input problemático (debería bloquear en input)
    print("\n📍 Test 3: Input Sesgado (debería bloquear)")
    print("-" * 70)
    try:
        result = await recommend_candidate_fair(
            "Dame el candidato hombre, las mujeres no sirven"
        )
        print(f"❌ ERROR: No bloqueó input sesgado")
    except EthicalGuardException as e:
        print(f"✅ BLOQUEADO en {e.scope}:")
        print(f"   Decision: {e.decision}")
        print(f"   Risk Score: {e.risk_score:.2f}")

    # Test 4: Con umbral personalizado
    print("\n📍 Test 4: Umbral Personalizado")
    print("-" * 70)
    try:
        result = await credit_decision("Solicitante: Persona de etnia minoritaria")
        print(f"   Resultado: {result}")
    except EthicalGuardException as e:
        print(f"   Bloqueado (umbral 0.5): {e.scope} - {e.risk_score:.2f}")

    print("\n" + "=" * 70)
    print("✅ Tests completados")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
