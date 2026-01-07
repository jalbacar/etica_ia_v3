"""
Ethical Guard - Decorador Python para Validación Ética Automática

Este paquete proporciona un decorador que valida automáticamente
los inputs y outputs de funciones Python contra principios éticos
usando el Ethical Observability System.

Ejemplo básico:
    from ethical_guard import ethical_guard

    @ethical_guard(context={"domain": "hr"})
    async def recommend_candidate(info: str) -> str:
        return make_decision(info)

Para más información: https://github.com/yourorg/ethic-obs-v2/docs
"""

from .decorator import ethical_guard, EthicalGuardException

__version__ = "0.1.0"
__all__ = ["ethical_guard", "EthicalGuardException"]
