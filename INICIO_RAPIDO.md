# 🚀 INICIO RÁPIDO - ethic-obs-v2

## Sistema Ético de Observabilidad
**EU AI Act + UNESCO Principles 2026**

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
docker-compose up -d
```

### 3️⃣ Espera a que Ollama esté Listo
```bash
docker-compose logs -f ollama
```
Verás: `Started Llama Server` cuando esté listo

**Presiona Ctrl+C para salir**

---

## ✅ Verificar que Funciona

```bash
# Ver estado
docker-compose ps

# Debería mostrar:
# - ollama (healthy)
# - bias-agent (up)
# - ai-act-agent (up)
# - unesco-agent (up)
```

---

## 🧪 Prueba Rápida

### Opción A: Usar Script de Test
```bash
chmod +x test_quick.sh
./test_quick.sh
```

### Opción B: Usar cURL
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

## 📡 Agentes Disponibles

| Agente | Puerto | URL | Función |
|--------|--------|-----|---------|
| **BiasAgent** | 8003 | http://localhost:8003/mcp | Detecta sesgos |
| **AIActAgent** | 8004 | http://localhost:8004/mcp | EU AI Act compliance |
| **UNESCOAgent** | 8005 | http://localhost:8005/mcp | Principios UNESCO |

---

## 🛠️ Comandos Útiles

### Ver Logs
```bash
docker-compose logs -f                    # Todos
docker-compose logs -f bias-agent         # Solo BiasAgent
```

### Detener Sistema
```bash
docker-compose stop
```

### Reiniciar Sistema
```bash
docker-compose restart
```

### Limpiar Todo
```bash
docker-compose down
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

## 🐍 Cliente Python

```python
from decorator import ethical_guard

@ethical_guard()
async def my_function(prompt):
    return f"Response to {prompt}"

# Valida automáticamente entrada y salida
result = await my_function("test")
```

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
- Disco: 5GB para Ollama

---

## 🆘 Problemas Comunes

### Puerto 8003 ya en uso
```bash
# Windows
netstat -ano | findstr :8003
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8003 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

### Ollama no responde
```bash
docker-compose restart ollama
docker-compose logs ollama
```

### Agentes no conectan a Ollama
```bash
docker-compose exec bias-agent curl http://ollama:11434
```

---

## 🎯 Siguiente Paso

1. ✅ Sistema corriendo → Ver `docs/EJECUCION.md`
2. 📝 Integrar clientes en tu app
3. ⚙️ Personalizar `rules.toml`
4. 📊 Monitorear en producción

---

## 📞 Estructura del Proyecto

```
ethic-obs-v2/
├── agent-bias/          # Detector de sesgos
├── agent-ai-act/        # Validación EU AI Act
├── agent-unesco/        # Principios UNESCO
├── client_python/       # Cliente Python
├── client-js/           # Cliente JavaScript
├── docs/
│   └── EJECUCION.md     # Documentación completa
├── docker-compose.yml   # Configuración Docker
├── rules.toml           # Reglas de validación
├── start.sh             # Script Linux/Mac
├── start.bat            # Script Windows
└── test_quick.sh        # Tests rápidos
```

---

**Creado con ❤️ para observabilidad ética**

EU AI Act 2026 + UNESCO Principles