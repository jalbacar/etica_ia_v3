"""
Test del endpoint /report - Generación de informes éticos en markdown
"""
import asyncio
import json
from client_python.ethical_subject import (
    Candidate,
    HiringScorer,
    EthicalPacketBuilder,
    OrchestratorClient,
)


async def test_reporter():
    print("=" * 70)
    print("TEST: Ethical Reporter")
    print("=" * 70)

    # Caso con sesgo para generar un informe interesante
    candidates = [
        Candidate(
            name="Ana García",
            years_experience=7,
            education_level="master",
            gender="mujer",
            age=34,
        ),
        Candidate(
            name="Juan Pérez",
            years_experience=4,
            education_level="bachelor",
            gender="hombre",
            age=29,
        ),
    ]

    # Scoring con sesgo
    scorer = HiringScorer(use_sensitive_features=True)
    decision = scorer.decide(candidates)

    builder = EthicalPacketBuilder(company_name="Tech Corp")
    system_prompt = builder.build_system_prompt()
    user_input = builder.build_user_input("Senior Developer", candidates)
    assistant_output = builder.build_assistant_output(decision)

    client = OrchestratorClient(base_url="http://localhost:8000")

    print("\n📍 Paso 1: Análisis ético")
    print("-" * 70)
    
    # 1. Analizar
    analysis = await client.analyze(
        system_prompt=system_prompt,
        user_input=user_input,
        assistant_output=assistant_output,
        context={"domain": "hr", "company": "Tech Corp"},
        agents=[],  # Router automático
    )
    
    print(f"✓ Análisis completado")
    print(f"  - Decisión: {analysis['decision']['decision']}")
    print(f"  - Risk Score: {analysis['decision']['risk_score']:.2f}")
    print(f"  - Agentes usados: {list(analysis['decision']['risk_inputs']['per_agent_signal'].keys())}")

    print("\n📍 Paso 2: Generación de informe markdown")
    print("-" * 70)
    
    # 2. Generar reporte
    import httpx
    async with httpx.AsyncClient(timeout=60.0) as http_client:
        report_response = await http_client.post(
            "http://localhost:8000/report",
            json={"analysis_result": analysis, "language": "es"}
        )
        report_response.raise_for_status()
        report_data = report_response.json()
    
    markdown = report_data["markdown"]
    word_count = report_data["word_count"]
    
    print(f"✓ Informe generado")
    print(f"  - Palabras: {word_count}")
    print(f"  - Idioma: {report_data['language']}")
    print(f"  - Timestamp: {report_data['generated_at']}")

    # 3. Guardar en archivo
    output_file = "informe_etico_demo.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    print(f"\n✓ Informe guardado en: {output_file}")

    # 4. Mostrar preview
    print("\n" + "=" * 70)
    print("PREVIEW DEL INFORME")
    print("=" * 70)
    lines = markdown.split("\n")
    for line in lines[:30]:  # Primeras 30 líneas
        print(line)
    
    if len(lines) > 30:
        print(f"\n... ({len(lines) - 30} líneas más)")
    
    print("\n" + "=" * 70)
    print(f"✅ Test completado. Revisa el archivo '{output_file}'")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_reporter())
