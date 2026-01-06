# 🚀 CÓMO EJECUTAR EL SISTEMA ÉTICO COMPLETO

## Resumen: ethic-obs-v2

Este es un sistema de **observabilidad ética** que valida textos contra:
- **EU AI Act** (Artículos 9, 13, 14)
- **UNESCO Principles** (Principios 1, 4, 6)
- **Sesgos discriminatorios** (género, raza, edad, origen)

---

## ⚡ INICIO RÁPIDO (3 pasos)

### Paso 1: Navega al directorio
```bash
cd F:/PROPIO/Obs/ethic-obs-v2
```

### Paso 2: Inicia el sistema

**Windows:**
```cmd
start.bat
# Selecciona opción 1 en el menú
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
# Selecciona opción 1 en el menú
```

**O directo:**
```bash
docker-compose up -d
```

### Paso 3: Espera a que Ollama esté listo
```bash
docker-compose logs -f ollama
# Verás: "Started Llama Server" cuando esté listo
# Presiona Ctrl+C
```

---

## ✅ Verificar que Funciona

```bash
# Ver estado
docker-compose ps

# Debería mostrar todos en "Up"
# ollama debe estar "Up (healthy)"
```

---

## 🧪 Probar Sistema

### Opción A: Script de Tests (Recomendado)
```bash
chmod +x test_quick.sh
./test_quick.sh
# Menú interactivo con 7 tests
```

### Opción B: cURL Manual
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

**Respuesta esperada:**
```json
{
  "result": {
    "ethical": false,
    "score": 0.85,
    "principle": "UNESCO Principle 6: Fairness & Non-Discrimination",
    "reason": "⚠️ Alto riesgo de discriminación detected"
  }
}
```

---

## 📡 Agentes Disponibles

| Agente | Puerto | Función |
|--------|--------|---------|
| **BiasAgent** | 8003 | Detecta sesgos discriminatorios |
| **AIActAgent** | 8004 | Valida EU AI Act (Art. 9, 13, 14) |
| **UNESCOAgent** | 8005 | Evalúa principios UNESCO (1, 4, 6) |

---

## 🛠️ Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Solo BiasAgent
docker-compose logs -f bias-agent

# Detener sistema
docker-compose stop

# Reiniciar
docker-compose restart

# Eliminar contenedores
docker-compose down

# Ver recursos
docker stats

# Entrar a contenedor
docker-compose exec bias-agent bash
```

---

## 📚 Documentación

- **INICIO_RAPIDO.md** - Guía visual de 3 pasos
- **docs/EJECUCION.md** - Documentación completa (489 líneas)
  - Arquitectura
  - Todos los endpoints
  - Ejemplos Postman/cURL
  - Solución de problemas
  - Clientes Python/JS

---

## 🐍 Usar en Python

```python
from client_python.decorator import ethical_guard

@ethical_guard()
async def mi_llm(prompt):
    # Tu código aquí
    return "respuesta"

# Valida automáticamente entrada y salida
resultado = await mi_llm("texto a validar")
```

---

## 🌐 Usar en JavaScript

```javascript
import EthicalLego from './client-js/index.mjs';

const { ethical, results } = await EthicalLego.checkAll("test");
if (ethical) {
  console.log("✓ Pasó validación");
} else {
  console.log("✗ Violó estándares éticos");
}
```

---

## 🔧 Solución de Problemas

### "Connection refused" en puerto 8003
```bash
docker-compose ps
docker-compose up -d
# Esperar 30 segundos
```

### Ollama no inicia
```bash
docker-compose logs ollama
docker-compose pull ollama
docker-compose up ollama
```

### Puerto ya en uso
```bash
# Windows
netstat -ano | findstr :8003
taskkill /PID <PID> /F

# Linux
lsof -i :8003 | awk '/LISTEN/ {print $2}' | xargs kill -9
```

### Respuestas lentas
- **Normal**: Primera ejecución tarda 10-30s (carga del modelo)
- Después se cachea en memoria (más rápido)

---

## 📊 Estructura del Proyecto

```
ethic-obs-v2/
├── agent-bias/           # Detector de sesgos
├── agent-ai-act/         # Validación EU AI Act
├── agent-unesco/         # Principios UNESCO
├── client_python/        # Cliente Python
├── client-js/            # Cliente JavaScript
├── docs/
│   └── EJECUCION.md      # Guía completa
├── docker-compose.yml    # Configuración
├── rules.toml            # Reglas éticas
├── start.sh              # Script Linux/Mac
├── start.bat             # Script Windows
└── test_quick.sh         # Tests
```

---

## 📈 Flujo de Uso Típico

```
1. Cliente envía texto
   ↓
2. Validar con BiasAgent/AIActAgent/UNESCOAgent
   ↓
3. Si es ético → Procesar con LLM
   ↓
4. Validar salida nuevamente
   ↓
5. Retornar respuesta
```

---

## 🎯 Próximos Pasos

1. ✅ Ejecutar: `./start.sh` o `start.bat`
2. 📚 Leer: `docs/EJECUCION.md`
3. 🧪 Probar: `./test_quick.sh`
4. 🔗 Integrar clientes en tu aplicación
5. ⚙️ Personalizar `rules.toml`
6. 📊 Monitorear en producción

---

## ✅ Sistema Listo

Ejecuta en terminal:

**Windows:**
```cmd
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

¡Disfruta de tu observabilidad ética! 🎉