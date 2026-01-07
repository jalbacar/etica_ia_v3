"""
Decorador ético para funciones Python.

Valida automáticamente inputs y outputs usando el orquestador ético.
Usa el router automático para optimizar costes de tokens.

Ejemplo:
    from client_python.decorator import ethical_guard

    @ethical_guard()
    async def generate_recommendation(user_input: str) -> str:
        '''Sistema de recomendación de candidatos.'''
        # Tu lógica aquí
        return "Recomiendo a Juan porque es hombre"  # ← Esto se bloqueará
"""

import asyncio
import inspect
import os
from functools import wraps
from typing import Callable, Optional

import httpx


class EthicalGuardException(ValueError):
    """Exception lanzada cuando una validación ética falla."""

    def __init__(
        self,
        message: str,
        decision: str,
        risk_score: float,
        scope: str,
        analysis_result: dict = None,
    ):
        super().__init__(message)
        self.decision = decision
        self.risk_score = risk_score
        self.scope = scope  # "input" o "output"
        self.analysis_result = analysis_result


def ethical_guard(
    orchestrator_url: Optional[str] = None,
    block_threshold: float = 0.65,  # Bajado de 0.75 a 0.65 para mayor sensibilidad
    warn_threshold: float = 0.35,
    context: Optional[dict] = None,
    agents: Optional[list] = None,
    generate_report: bool = False,
    report_path: Optional[str] = None,
):
    """
    Decorador que valida inputs y outputs de funciones con el orquestador ético.

    Args:
        orchestrator_url: URL del orquestador (default: env ORCHESTRATOR_URL o http://localhost:8000)
        block_threshold: Score mínimo para bloquear (default: 0.65)
        warn_threshold: Score mínimo para warning (default: 0.35)
        context: Contexto adicional para el orquestador (ej: {"domain": "hr"})
        agents: Lista de agentes a usar (None = router automático)
        generate_report: Si True, genera informe markdown
        report_path: Ruta donde guardar el reporte (default: ethical_report_{timestamp}.md)

    Raises:
        EthicalGuardException: Si el input o output es bloqueado

    Example:
        @ethical_guard(context={"domain": "hr"})
        async def recommend_candidate(prompt: str) -> str:
            '''Recomienda un candidato para un puesto.'''
            return f"Recomiendo a Juan"

        # Si el input o output viola principios éticos, lanza excepción
        try:
            result = await recommend_candidate("Compara Ana y Juan")
        except EthicalGuardException as e:
            print(f"Bloqueado: {e.message} (risk: {e.risk_score})")
    """
    orchestrator_url = orchestrator_url or os.getenv(
        "ORCHESTRATOR_URL", "http://localhost:8000"
    )
    context = context or {}

    def decorator(func: Callable):
        # Determinar si la función es async
        is_async = inspect.iscoroutinefunction(func)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Construir system_prompt desde docstring
            system_prompt = (
                func.__doc__ or f"Función: {func.__name__}"
            ).strip()

            # Primer argumento como user_input
            user_input = str(args[0]) if args else str(kwargs.get("input", ""))

            # 1. VALIDAR INPUT
            async with httpx.AsyncClient(timeout=60.0) as client:
                input_analysis = await client.post(
                    f"{orchestrator_url}/analyze",
                    json={
                        "system_prompt": system_prompt,
                        "user_input": user_input,
                        "context": context,
                        "agents": agents or [],  # Router automático si None
                    },
                )
                input_analysis.raise_for_status()
                input_result = input_analysis.json()

                input_decision = input_result["decision"]["decision"]
                input_risk = input_result["decision"]["risk_score"]

                # Lógica de bloqueo mejorada:
                # 1. Bloquear si decision="block"
                # 2. Bloquear si decision="warn" Y risk >= block_threshold
                should_block = (
                    input_decision == "block"
                    or (input_decision == "warn" and input_risk >= block_threshold)
                )

                if should_block:
                    if generate_report:
                        await _save_report(
                            client, orchestrator_url, input_result, report_path, "input"
                        )

                    raise EthicalGuardException(
                        f"🛑 Input bloqueado por evaluación ética (risk: {input_risk:.2f}, decision: {input_decision})",
                        decision=input_decision,
                        risk_score=input_risk,
                        scope="input",
                        analysis_result=input_result,
                    )

                # Warning si supera warn_threshold pero no bloquea
                if input_risk >= warn_threshold and not should_block:
                    print(
                        f"⚠️  Warning: Input con riesgo medio (score: {input_risk:.2f})"
                    )

                # 2. EJECUTAR FUNCIÓN
                result = await func(*args, **kwargs)

                # 3. VALIDAR OUTPUT
                output_analysis = await client.post(
                    f"{orchestrator_url}/analyze",
                    json={
                        "system_prompt": system_prompt,
                        "user_input": user_input,
                        "assistant_output": str(result),
                        "context": context,
                        "agents": agents or [],
                    },
                )
                output_analysis.raise_for_status()
                output_result = output_analysis.json()

                output_decision = output_result["decision"]["decision"]
                output_risk = output_result["decision"]["risk_score"]

                # Lógica de bloqueo mejorada:
                # 1. Bloquear si decision="block"
                # 2. Bloquear si decision="warn" Y risk >= block_threshold
                should_block = (
                    output_decision == "block"
                    or (output_decision == "warn" and output_risk >= block_threshold)
                )

                if should_block:
                    if generate_report:
                        await _save_report(
                            client, orchestrator_url, output_result, report_path, "output"
                        )

                    raise EthicalGuardException(
                        f"🛑 Output bloqueado por evaluación ética (risk: {output_risk:.2f}, decision: {output_decision})",
                        decision=output_decision,
                        risk_score=output_risk,
                        scope="output",
                        analysis_result=output_result,
                    )

                # Warning si supera warn_threshold pero no bloquea
                if output_risk >= warn_threshold and not should_block:
                    print(
                        f"⚠️  Warning: Output con riesgo medio (score: {output_risk:.2f})"
                    )

                # Generar reporte si está habilitado y todo OK
                if generate_report:
                    await _save_report(
                        client, orchestrator_url, output_result, report_path, "success"
                    )

                return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """Wrapper para funciones síncronas."""
            return asyncio.run(async_wrapper(*args, **kwargs))

        return async_wrapper if is_async else sync_wrapper

    return decorator


async def _save_report(
    client: httpx.AsyncClient,
    orchestrator_url: str,
    analysis_result: dict,
    report_path: Optional[str],
    status: str,
):
    """Helper para guardar reporte markdown."""
    try:
        report_response = await client.post(
            f"{orchestrator_url}/report",
            json={"analysis_result": analysis_result},
        )
        report_response.raise_for_status()
        report_data = report_response.json()

        if report_path is None:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"ethical_report_{status}_{timestamp}.md"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_data["markdown"])

        print(f"📄 Reporte guardado: {report_path}")
    except Exception as e:
        print(f"⚠️  Error guardando reporte: {e}")

