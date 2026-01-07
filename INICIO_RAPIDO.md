# 🚀 INICIO RÁPIDO - ethic-obs-v2

## Sistema Ético de Observabilidad
**EU AI Act + UNESCO Principles 2026**

Este repositorio expone 2 formas de consumo:

1) **Agentes directos** (JSON-RPC por `/mcp`)  
2) **Orquestador centralizado** (HTTP por `/analyze`) → recomendado para validar **input y output** de forma unificada.

---

## ⚡ 3 Pasos para Ejecutar

### 1️⃣ Abre Terminal/CMD en este directorio
```bash
cd F:/PROPIO/Obs/ethic-obs-v2
```

### 2️⃣ Inicia el Sistema

**Windows:**
```cmd
start.bat
```
Selecciona opción `1` en el menú

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```
Selecciona opción `1` en el menú

**O con Docker Compose directamente:**
```bash
docker compose up -d
```

### 3️⃣ Verifica que los servicios están arriba
```bash
docker compose ps
```

Debería mostrar como mínimo:
- orchestrator (up)
- bias-agent (up)
- eu-ai-act-agent (up)
- unesco-agent (up)

---

## ✅ Endpoint recomendado (Orquestador)

El orquestador recibe el “paquete” de auditoría:

- `system_prompt` (política de la empresa / comportamiento del sistema)
- `user_input` (entrada del usuario)
- `assistant_output` (salida generada por el sistema; opcional)
- `context` (metadatos)
- `agents` (qué agentes correr)

### 🧪 Prueba rápida (cURL) contra el Orquestador
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "Eres un asistente de RRHH.",
    "user_input": "Compara a Ana y Juan para un puesto.",
    "assistant_output": "Juan es mejor por ser hombre.",
    "context": { "domain": "hr" },
    "agents": ["bias", "unesco", "eu_ai_act"]
  }'
```

### Qué devuelve
El response incluye criterios éticos “anclados” a reglas, por ejemplo:

- `input_audit.evaluations[]` (framework + rule_id + triggered/score + reason)
- `output_audit.evaluations[]` (si hay assistant_output)
- `decision` con `risk_score` + `risk_inputs` (siempre)

---

## 🧠 Router Automático de Agentes (Nuevo)

Si **no especificas `agents`** (o envías `[]`), el orquestador selecciona automáticamente los agentes apropiados.

### Ventajas
- ✅ **Ahorro de tokens**: Solo invoca agentes necesarios (hasta 66% menos)
- ✅ **Menor latencia**: Menos llamadas LLM
- ✅ **Automático**: No necesitas saber qué agentes usar

### Ejemplo
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "Asistente de RRHH",
    "user_input": "Juan es mejor porque es hombre",
    "context": { "domain": "hr" },
    "agents": []
  }'
```

**Resultado**: El router detecta `domain: "hr"` + patrones de sesgo → invoca solo `["bias", "eu_ai_act"]`

📚 **Documentación completa**: Ver `docs/AGENT_ROUTER.md`

---

## 📄 Generador de Informes Éticos (Nuevo)

El orquestador incluye un endpoint **`POST /report`** que genera **informes éticos en markdown** desde el JSON técnico.

### Para Qué Sirve
Transforma evaluaciones técnicas en narrativa comprensible para:
- 👔 Ejecutivos
- ⚖️ Equipos de Compliance
- 📋 Auditores
- 👥 RRHH

### Ejemplo de Uso
```bash
# 1. Analizar
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "RRHH", "user_input": "Texto", "agents": []}' \
  > analysis.json

# 2. Generar informe markdown
curl -X POST http://localhost:8000/report \
  -H "Content-Type: application/json" \
  -d "{\"analysis_result\": $(cat analysis.json)}" \
  | jq -r '.markdown' > informe_etico.md
```

### Resultado
```markdown
# 📊 Informe Ético - Evaluación de Sistema IA

## Resumen Ejecutivo
Decisión: ⛔ BLOCK  
Nivel de Riesgo: 0.85 / 1.0

## Hallazgos Principales
... (lenguaje natural, sin JSON)

## Recomendaciones
... (accionables)
```

📚 **Documentación completa**: Ver `docs/ETHICAL_REPORTER.md`

---

## 📡 Agentes (acceso directo)

Cada agente expone `POST /mcp` (JSON-RPC). Esto es útil para depurar, pero el consumo recomendado es vía orquestador.

| Agente | Puerto | URL | Función |
|--------|--------|-----|---------|
| **BiasAgent** | 8003 | http://localhost:8003/mcp | Detecta sesgos |
| **EU AI Act Agent** | 8005 | http://localhost:8005/mcp | EU AI Act compliance |
| **UNESCOAgent** | 8006 | http://localhost:8006/mcp | Principios UNESCO |

Ejemplo directo:
```bash
curl -X POST http://localhost:8003/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "detect_bias",
    "params": {"text": "test"}
  }'
```

---

## 🐍 Cómo probarlo desde Python (demo)

Incluye un ejemplo de “pieza de software” evaluable éticamente (un scoring de contratación) en:
- `client_python/ethical_subject.py`
- `client_python/run_ethical_subject_demo.py`

### 1) Instala dependencias del cliente (local)
```bash
pip install httpx
```

### 2) Ejecuta el demo como módulo (recomendado)
Desde la raíz del repo `ethic-obs-v2/`:
```bash
python -m client_python.run_ethical_subject_demo
```

Variables opcionales:
- `ORCHESTRATOR_BASE_URL` (default `http://localhost:8000`)
- `USE_SENSITIVE_FEATURES` (default `true`)

Ejemplo:
```bash
ORCHESTRATOR_BASE_URL=http://localhost:8000 USE_SENSITIVE_FEATURES=true python -m client_python.run_ethical_subject_demo
```

---

## 🛠️ Comandos Útiles

### Ver Logs
```bash
docker compose logs -f                    # Todos
docker compose logs -f orchestrator       # Solo orquestador
docker compose logs -f bias-agent         # Solo BiasAgent
docker compose logs -f eu-ai-act-agent    # Solo EU AI Act
docker compose logs -f unesco-agent       # Solo UNESCO
```

### Detener Sistema
```bash
docker compose stop
```

### Reiniciar Sistema
```bash
docker compose restart
```

### Limpiar Todo
```bash
docker compose down
```

### Ver Recursos
```bash
docker stats
```

---

## 📚 Documentación Completa

Ver archivo: `docs/EJECUCION.md`

Incluye:
- Arquitectura detallada
- Todos los endpoints
- Ejemplos de uso
- Solución de problemas
- Clientes Python y JavaScript

---

## 🌐 Cliente JavaScript

```javascript
import EthicalLego from './client-js/index.mjs';

const { ethical, results } = await EthicalLego.checkAll("test");
if (ethical) console.log("✓ Ético");
```

---

## ⚠️ Requisitos

- Docker 20.10+
- Docker Compose 2.0+
- RAM: 4GB mínimo (8GB recomendado)

---

## 🆘 Problemas Comunes

### Error 422 (Unprocessable Entity) en /analyze
Suele indicar que falta alguno de estos campos en el body JSON:
- `system_prompt`
- `user_input`

### Orquestador devuelve 500 al generar narrativa
Si estás en modo prueba, el orquestador puede estar configurado para omitir la narrativa del LLM.
Revisa variables de entorno y logs del servicio `orchestrator`.

---

## 🎯 Siguiente Paso

1. ✅ Sistema corriendo → usa `POST /analyze`
2. 📝 Integrar el orquestador en tu app (validación de input/output)
3. ⚙️ Personalizar `rules.toml`
4. 📊 Monitorear en producción