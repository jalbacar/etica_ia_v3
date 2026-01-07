# Ethical Guard - Python Decorator

Paquete oficial de Ethical Guard para la validación automática de inputs y outputs en sistemas de IA.

## Instalación

Puedes instalar este paquete directamente desde el repositorio o desde un archivo local.

### Instalación local (para pruebas)
```bash
cd client_python
pip install -e .
```

### Instalación vía Git (ejemplo)
```bash
pip install git+https://github.com/yourorg/ethic-obs-v2.git#subdirectory=client_python
```

## Uso Rápido

```python
from ethical_guard import ethical_guard, EthicalGuardException

@ethical_guard(
    context={"domain": "hr"},
    block_threshold=0.65,
    generate_report=True
)
async def mi_funcion_ia(input_texto):
    # Tu lógica aquí
    return "Resultado de la IA"

# Uso del orquestador
try:
    resultado = await mi_funcion_ia("Hola mundo")
except EthicalGuardException as e:
    print(f"Bloqueado: {e.decision} con score {e.risk_score}")
```

## Configuración

El paquete busca por defecto el orquestador en `http://localhost:8000`. Puedes cambiarlo mediante variables de entorno:

```bash
export ORCHESTRATOR_URL=https://tu-orquestador.com
```

O pasándolo directamente al decorador:

```python
@ethical_guard(orchestrator_url="http://mi-servidor:8000")
```

## Características

- ✅ **Validación Dual**: Verifica tanto lo que envías (input) como lo que generas (output).
- ✅ **Router Inteligente**: Selección automática de agentes basada en contexto (ahorro de tokens).
- ✅ **Reportes Automáticos**: Generación de informes éticos en Markdown si se solicita.
- ✅ **Thresholds Personalizables**: Controla qué tan estricto es el sistema.
- ✅ **Soporte Async/Sync**: Compatible con funciones asíncronas y síncronas.

## Documentación Completa

Para más detalles sobre agentes, reglas y arquitectura, visita:
[docs/ETHICAL_REPORTER.md](../docs/ETHICAL_REPORTER.md)
[docs/AGENT_ROUTER.md](../docs/AGENT_ROUTER.md)
