# 🧠 Smart Agent Router - Documentación

## Descripción

El **Smart Agent Router** es un componente del orquestador que selecciona automáticamente qué agentes éticos invocar basándose en el contenido y contexto, optimizando costes de tokens.

---

## ¿Cómo funciona?

### Modo Manual (comportamiento original)
```json
POST /analyze
{
  "system_prompt": "...",
  "user_input": "...",
  "agents": ["bias", "unesco"]  ← Tú eliges los agentes
}
```
✅ El orquestador usa solo los agentes especificados.

### Modo Automático (nuevo)
```json
POST /analyze
{
  "system_prompt": "...",
  "user_input": "...",
  "agents": []  ← Lista vacía = router activa
}
```
✅ El router analiza el contenido y selecciona automáticamente los agentes apropiados.

---

## Estrategias de Routing

### 1. Determinista (Actual - 0 tokens)

El router usa 3 capas de detección:

#### a) Domain Mapping
Si el contexto incluye un dominio conocido:
```json
{"context": {"domain": "hr"}}  →  ["bias", "eu_ai_act"]
```

**Dominios soportados**:
- `hr`, `rrhh`, `hiring` → bias + eu_ai_act
- `finance`, `finanzas`, `credit` → eu_ai_act + bias
- `healthcare`, `salud` → unesco + eu_ai_act + bias
- `education`, `educacion` → unesco + bias
- `legal`, `law` → eu_ai_act + unesco
- `security`, `seguridad` → eu_ai_act + unesco

#### b) Pattern Matching (Regex)

**Patrones de Bias**:
- Género: `hombre`, `mujer`, `género`, `masculino`, `femenino`
- Edad: `edad`, `joven`, `viejo`, `anciano`
- Raza: `raza`, `etnia`, `color`, `negro`, `blanco`, `asiático`
- Discapacidad: `discapacidad`, `ciego`, `sordo`
- Religión: `religión`, `musulmán`, `cristiano`, `judío`
- Orientación sexual: `gay`, `lesbiana`, `homosexual`
- Comparaciones sesgadas: "mejor/peor por ser..."

**Patrones EU AI Act**:
- Riesgo: `riesgo`, `alto riesgo`, `risk management`
- Sistemas: `crédito`, `contratación`, `hiring`, `loan`, `scoring`
- Biométricos: `biométrico`, `facial`, `reconocimiento`
- Decisiones automáticas: `decisión automática`, `automated decision`
- Artículos específicos: `Art. 9`, `Art. 13`, `Art. 14`

**Patrones UNESCO**:
- Derechos: `derechos humanos`, `human rights`, `dignidad`
- Daño: `daño`, `harm`, `perjuicio`
- Discriminación: `discriminación`, `no discriminación`
- Equidad: `equidad`, `fairness`, `justicia social`

#### c) Fallback
Si no detecta ningún patrón específico → **todos los agentes** (seguridad)

### 2. LLM-based (Futuro - ~50-100 tokens)

**Estado**: Preparado pero desactivado por defecto.

Para activar en el futuro:
```bash
# En .env o docker-compose.yml
USE_LLM_ROUTER=true
```

Usará OpenRouter para clasificación más precisa en casos edge.

---

## Ejemplos de Uso

### Ejemplo 1: Caso de RRHH con sesgo

**Request**:
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "system_prompt": "Asistente de RRHH",
    "user_input": "Juan es mejor porque es hombre",
    "context": {"domain": "hr"},
    "agents": []
  }'
```

**Router detecta**:
- Domain `hr` → `["bias", "eu_ai_act"]`
- Patrón "hombre" → agrega `bias` (ya estaba)

**Resultado**: Invoca `["bias", "eu_ai_act"]` (2 agentes)

**Ahorro**: 33% menos tokens que invocar los 3 agentes.

---

### Ejemplo 2: Caso financiero

**Request**:
```json
{
  "user_input": "Sistema automático de aprobación de créditos",
  "context": {"domain": "finance"},
  "agents": []
}
```

**Router detecta**:
- Domain `finance` → `["eu_ai_act", "bias"]`
- Patrón "créditos" → agrega `eu_ai_act` (ya estaba)

**Resultado**: `["eu_ai_act", "bias"]`

---

### Ejemplo 3: Sin dominio claro

**Request**:
```json
{
  "user_input": "Sistema de IA general",
  "agents": []
}
```

**Router detecta**: Ningún patrón específico

**Resultado (fallback)**: `["bias", "unesco", "eu_ai_act"]` (todos)

---

## Metadata en la Respuesta

El orquestador incluye información del routing:

```json
{
  "decision": {
    "risk_inputs": {
      "routing_mode": "auto",
      "selected_agents": ["bias", "eu_ai_act"],
      "per_agent_signal": {
        "bias": 0.6,
        "eu_ai_act": 0.0
      }
    }
  }
}
```

| Campo | Descripción |
|-------|-------------|
| `routing_mode` | `"auto"` (router) o `"explicit"` (manual) |
| `selected_agents` | Lista de agentes que se invocaron |
| `per_agent_signal` | Señales de cada agente invocado |

---

## Logs

Cuando se usa routing automático:
```bash
docker compose logs -f orchestrator
```

Verás:
```
[AgentRouter] Auto-selected agents: ['bias', 'eu_ai_act']
```

---

## Configuración

### Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `USE_LLM_ROUTER` | `false` | Activa routing LLM (futuro) |

---

## Beneficios

### 1. Reducción de Costes
- **Hasta 66% menos tokens** en casos específicos (1 agente vs 3)
- Promedio estimado: **~30-40% de ahorro**

### 2. Menor Latencia
- Menos llamadas LLM = respuesta más rápida

### 3. Autoajustable
- Añadir nuevos dominios es trivial (solo actualizar `DOMAIN_MAPPING`)
- Añadir patrones nuevos es simple (regex)

---

## Testing

### Test Manual
```bash
# Router auto
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "RRHH", "user_input": "Juan es mejor porque es hombre", "context": {"domain": "hr"}, "agents": []}'

# Explícito (comparación)
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "RRHH", "user_input": "Juan es mejor porque es hombre", "context": {"domain": "hr"}, "agents": ["bias", "unesco", "eu_ai_act"]}'
```

### Test con Cliente Python
```bash
python test_router_simple.py
```

---

## Evolución Futura

1. **Entrenamiento**: Recopilar datos de routing para mejorar patrones
2. **LLM Router**: Activar clasificación LLM para casos complejos
3. **Reglas por dominio**: Personalizar patrones según cliente
4. **Métricas**: Dashboard de ahorro de tokens

---

## Arquitectura Técnica

```python
class AgentRouter:
    # Patrones regex
    BIAS_PATTERNS = [...]
    EU_AI_ACT_PATTERNS = [...]
    UNESCO_PATTERNS = [...]
    
    # Mapeo de dominios
    DOMAIN_MAPPING = {...}
    
    @classmethod
    def route(cls, text: str, context: Dict) -> List[str]:
        # 1. Domain mapping
        # 2. Pattern matching
        # 3. Fallback a todos
```

**Ubicación**: `agent-orchestrator/orchestrator.py` (líneas 40-195)
