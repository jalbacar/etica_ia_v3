# 🚀 Guía de Ejecución del Sistema Ético Observabilidad (ethic-obs-v2)

## 📋 Contenido
1. [Requisitos Previos](#requisitos-previos)
2. [Ejecución Rápida](#ejecución-rápida)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Endpoints y Uso](#endpoints-y-uso)
5. [Monitoreo y Logs](#monitoreo-y-logs)
6. [Solución de Problemas](#solución-de-problemas)

---

## 🔧 Requisitos Previos

### Instalaciones Necesarias
- **Docker**: v20.10+
- **Docker Compose**: v2.0+
- **Git** (opcional, para clonar)
- **cURL** o **Postman** (para probar endpoints)

### Verificar Instalación
```bash
docker --version
docker-compose --version
```

### Espacio Requerido
- **Disco**: ~5GB (Ollama + modelos)
- **RAM**: Mínimo 4GB disponibles (recomendado 8GB+)
- **CPU**: 2+ núcleos

---

## ⚡ Ejecución Rápida

### Paso 1: Posicionarse en el Directorio
```bash
cd F:/PROPIO/Obs/ethic-obs-v2
```

### Paso 2: Iniciar el Sistema Completo
```bash
docker-compose up -d
```

**¿Qué hace esto?**
- Descarga imagen de Ollama (si no existe)
- Construye 3 imágenes de agentes (bias, ai-act, unesco)
- Inicia 4 contenedores (Ollama + 3 agentes)
- Expone puertos locales 8003, 8004, 8005

### Paso 3: Esperar a que Ollama esté Listo
```bash
docker-compose logs -f ollama
```

Espera hasta ver:
```
Started Llama Server
```

**Presiona Ctrl+C** para salir de los logs.

### Paso 4: Verificar que Todo Está Corriendo
```bash
docker-compose ps
```

Deberías ver:
```
NAME                    STATUS
ethic-obs-v2-ollama-1           Up (healthy)
ethic-obs-v2-bias-agent-1       Up
ethic-obs-v2-ai-act-agent-1     Up
ethic-obs-v2-unesco-agent-1     Up
```

### Paso 5: Probar Endpoints

#### Opción A: Usar cURL (Windows PowerShell)
```powershell
$body = @{
    jsonrpc = "2.0"
    id = 1
    method = "detect_bias"
    params = @{ text = "Las mujeres no son buenas en programación" }
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8003/mcp" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

#### Opción B: Usar cURL (Bash/CMD)
```bash
curl -X POST http://localhost:8003/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "detect_bias",
    "params": {"text": "Las mujeres no son buenas en programación"}
  }'
```

#### Opción C: Usar Postman
1. Abre Postman
2. Crear POST request a: `http://localhost:8003/mcp`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "detect_bias",
  "params": {"text": "Las mujeres no son buenas en programación"}
}
```
5. Click "Send"

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    Cliente (JS/Python)                      │
└────────────┬────────────┬────────────┬─────────────────────┘
             │            │            │
       ┌─────▼──┐  ┌──────▼────┐  ┌────▼────────┐
       │ Port   │  │  Port     │  │  Port      │
       │ 8003   │  │  8004     │  │  8005      │
       └─────┬──┘  └──────┬────┘  └────┬───────┘
             │            │            │
       ┌─────▼──────┐  ┌──▼──────┐  ┌──▼─────────┐
       │ BiasAgent  │  │AIActAgent│  │UNESCOAgent │
       │ (FastMCP)  │  │(FastMCP) │  │ (FastMCP)  │
       └─────┬──────┘  └──┬──────┘  └──┬────────┘
             │            │            │
             └────────────┼────────────┘
                          │
                    ┌─────▼────────┐
                    │ Ollama LLM   │
                    │ llama3.2     │
                    │ (Port 11434) │
                    └──────────────┘
```

### Componentes

| Componente | Puerto | Rol | Framework |
|-----------|--------|-----|-----------|
| **Ollama** | 11434 | Servicio LLM local | Ollama |
| **BiasAgent** | 8003 | Detecta sesgos (UNESCO Principle 6) | FastMCP 2.0 |
| **AIActAgent** | 8004 | Valida EU AI Act (Art. 9, 13, 14) | FastMCP 2.0 |
| **UNESCOAgent** | 8005 | Evalúa principios UNESCO (1, 4, 6) | FastMCP 2.0 |

---

## 📡 Endpoints y Uso

### 1️⃣ BiasAgent (Puerto 8003)

**Endpoint**: `http://localhost:8003/mcp`

**Métodos disponibles**:
- `detect_bias`: Detecta sesgos discriminatorios
- `bias_supervisor`: Supervisor principal de sesgos

**Ejemplo - Detectar Sesgo**:
```bash
curl -X POST http://localhost:8003/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "detect_bias",
    "params": {"text": "Todos los ancianos son lentos"}
  }'
```

**Respuesta**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "agent": "bias",
    "ethical": false,
    "score": 0.85,
    "principle": "UNESCO Principle 6: Fairness & Non-Discrimination",
    "reason": "⚠️ Alto riesgo de discriminación detected"
  }
}
```

### 2️⃣ AIActAgent (Puerto 8004)

**Endpoint**: `http://localhost:8004/mcp`

**Métodos disponibles**:
- `ai_act_risk_management`: Evalúa riesgos (Art. 9)
- `ai_act_transparency`: Evalúa transparencia (Art. 13)
- `ai_act_suite`: Evaluación completa

**Ejemplo - Evaluar Riesgo AI Act**:
```bash
curl -X POST http://localhost:8004/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "ai_act_risk_management",
    "params": {"text": "Sistema de aprobación de créditos sin auditoría"}
  }'
```

### 3️⃣ UNESCOAgent (Puerto 8005)

**Endpoint**: `http://localhost:8005/mcp`

**Métodos disponibles**:
- `unesco_principles`: Evalúa principios UNESCO (1, 4, 6)

**Ejemplo - Evaluar Principios UNESCO**:
```bash
curl -X POST http://localhost:8005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "unesco_principles",
    "params": {"text": "Sistema que prioriza derechos humanos y equidad"}
  }'
```

---

## 🔍 Monitoreo y Logs

### Ver Logs en Tiempo Real
```bash
# Todos los servicios
docker-compose logs -f

# Solo Ollama
docker-compose logs -f ollama

# Solo BiasAgent
docker-compose logs -f bias-agent

# Solo AIActAgent
docker-compose logs -f ai-act-agent

# Solo UNESCOAgent
docker-compose logs -f unesco-agent
```

### Ver Estado de Contenedores
```bash
docker-compose ps
```

### Ejecutar Comando dentro de Contenedor
```bash
# Entrar a bash del bias-agent
docker-compose exec bias-agent bash

# Listar modelos en Ollama
docker-compose exec ollama ollama list

# Ver recursos usados
docker stats
```

### Detener Sistema
```bash
# Detener sin eliminar
docker-compose stop

# Detener y eliminar contenedores
docker-compose down

# Detener, eliminar y limpiar volúmenes (data Ollama)
docker-compose down -v
```

---

## 🐍 Cliente Python

### Instalación
```bash
cd client_python
pip install aiohttp
```

### Uso del Decorador Ético
```python
from decorator import ethical_guard

@ethical_guard()
async def generate_response(prompt):
    # Tu lógica de IA
    return f"Respuesta a: {prompt}"

# Validar entrada y salida automáticamente
result = await generate_response("Tu texto aquí")
```

**¿Qué hace?**
- Valida el prompt contra los 3 agentes
- Si falla, lanza `ValueError: 🛑 Ethical block`
- Valida la salida generada
- Si falla, lanza `ValueError: 🛑 Output block`

---

## 🌐 Cliente JavaScript

### Instalación
```bash
cd client-js
npm install
```

### Uso Básico
```javascript
import EthicalLego from './index.mjs';

// Verificar si un texto es ético
const { ethical, results } = await EthicalLego.checkAll(
  "Tu texto a validar"
);

if (ethical) {
  console.log("✓ Texto ético");
} else {
  console.log("✗ Texto contiene problemas éticos");
  console.log(results);
}
```

### Ejecutar Tests
```bash
node test.mjs
```

---

## 🚨 Solución de Problemas

### Problema: Puertos Ocupados
```bash
# Buscar qué usa puerto 8003
netstat -ano | findstr :8003

# Matar proceso (Windows)
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8003 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Problema: Ollama No Inicia
```bash
# Verificar logs
docker-compose logs ollama

# Reconstruir imagen
docker-compose down
docker-compose up --build ollama
```

### Problema: Agentes No Responden
```bash
# Verificar conectividad a Ollama
docker-compose exec bias-agent curl http://ollama:11434

# Reiniciar agentes
docker-compose restart bias-agent ai-act-agent unesco-agent
```

### Problema: Respuestas Lentas
- **Esperado**: Primera invocación tarda ~10-30s (carga del modelo)
- **Solución**: Ollama cachea el modelo en memoria para invocaciones posteriores
- **Verificar**: `docker stats` para ver uso de RAM

### Problema: "Connection refused"
```bash
# Asegúrate que está en ejecución
docker-compose ps

# Inicia si está detenido
docker-compose up -d

# Espera a que Ollama esté healthy
docker-compose logs ollama | tail -20
```

### Problema: Modelo llama3.2 No Descarga
```bash
# Descargar manualmente
docker-compose exec ollama ollama pull llama3.2:latest

# Verificar descarga
docker-compose exec ollama ollama list
```

---

## 📊 Flujo Completo de Ejemplo

### 1. Iniciar Sistema
```bash
docker-compose up -d
sleep 10  # Esperar a que Ollama esté listo
```

### 2. Validar Texto Problemático
```bash
curl -X POST http://localhost:8003/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "detect_bias",
    "params": {"text": "Los hombres son superiores"}
  }'
```

**Resultado esperado**:
```json
{
  "result": {
    "ethical": false,
    "score": 0.95,
    "reason": "⚠️ Alto riesgo de discriminación detected"
  }
}
```

### 3. Validar Texto Aceptable
```bash
curl -X POST http://localhost:8003/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "detect_bias",
    "params": {"text": "Las personas tienen derecho a oportunidades iguales"}
  }'
```

**Resultado esperado**:
```json
{
  "result": {
    "ethical": true,
    "score": 0.15,
    "reason": "✓ Cumple con principios éticos de equidad"
  }
}
```

### 4. Detener Sistema
```bash
docker-compose down
```

---

## 📚 Referencias

- **EU AI Act**: https://digital-strategy.ec.europa.eu/en/policies/ai-act
- **UNESCO AI Ethics**: https://en.unesco.org/artificial-intelligence
- **FastMCP**: https://github.com/jlouis/fastmcp
- **Ollama**: https://ollama.ai
- **LangChain**: https://langchain.com

---

## 🎯 Próximos Pasos

1. **Integrar en tu aplicación**: Usa los clients (Python/JS)
2. **Personalizar reglas**: Edita `rules.toml`
3. **Ajustar umbrales**: Modifica scores en agentes
4. **Monitoreo en producción**: Usa ELK Stack, Datadog, etc.
