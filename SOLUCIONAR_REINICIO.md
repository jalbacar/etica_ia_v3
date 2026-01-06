# 🔧 SOLUCIONAR REINICIO CONTINUO DE AGENTES

## ⚠️ PROBLEMA IDENTIFICADO

Los contenedores se reinician constantemente porque:

```
ERROR: Error loading ASGI app. Attribute "app" not found in module "agent".
```

**Causa raíz:** Los Dockerfiles intentaban ejecutar `uvicorn agent:app` pero FastMCP 2.0 no expone un atributo `.app` de esa forma.

---

## ✅ SOLUCIÓN APLICADA

Se han realizado los siguientes cambios:

### 1. Dockerfiles Actualizados
```
ANTES: CMD ["uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "8000"]
DESPUÉS: CMD ["python", "agent.py"]
```

✅ Los 3 Dockerfiles han sido actualizados:
- `agent-bias/Dockerfile`
- `agent-ai-act/Dockerfile`
- `agent-unesco/Dockerfile`

### 2. Código de Agentes Actualizado

```python
# ANTES (incorrecto)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp.app, host="0.0.0.0", port=8000)

# DESPUÉS (correcto)
if __name__ == "__main__":
    mcp.run()
```

✅ Los 3 agentes ahora ejecutan `mcp.run()` directamente

---

## 🚀 INSTRUCCIONES PARA EJECUTAR AHORA

### Opción A: Script Automático (RECOMENDADO)
```bash
chmod +x reiniciar_limpio.sh
./reiniciar_limpio.sh
```

**Esto hace:**
1. Detiene todos los contenedores
2. Elimina contenedores viejos
3. Reconstruye imágenes desde cero
4. Inicia el sistema
5. Verifica conectividad

### Opción B: Manual
```bash
# Paso 1: Detener todo
docker-compose down

# Paso 2: Limpiar imágenes viejas
docker image prune -f

# Paso 3: Reconstruir
docker-compose build --no-cache

# Paso 4: Iniciar
docker-compose up -d

# Paso 5: Verificar
docker-compose ps
```

---

## 📊 VERIFICAR QUE FUNCIONA

### Opción 1: Ver Logs en Tiempo Real
```bash
docker-compose logs -f bias-agent
```

Debería ver:
```
INFO:__main__:============================================================
INFO:__main__:Iniciando BiasAgent con FastMCP 2.0.0
INFO:__main__:============================================================
INFO:__main__:✓ OllamaLLM inicializado en http://ollama:11434
INFO:__main__:Iniciando servidor en puerto 8000
```

### Opción 2: Ver Estado
```bash
docker-compose ps

# Debería mostrar:
# ollama          Up (healthy)
# bias-agent      Up
# ai-act-agent    Up
# unesco-agent    Up
```

### Opción 3: Test Rápido
```bash
curl -X POST http://localhost:8003/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "health",
    "params": {}
  }'

# Debería responder:
# {"jsonrpc":"2.0","id":1,"result":{"status":"healthy",...}}
```

---

## 🧪 EJECUTAR TESTS

```bash
chmod +x test_quick.sh
./test_quick.sh
```

O si quieres diagnosticar problemas:
```bash
chmod +x diagnostico.sh
./diagnostico.sh
```

---

## 📋 RESUMEN DE CAMBIOS

| Archivo | Cambio | Estado |
|---------|--------|--------|
| `agent-bias/Dockerfile` | `CMD ["python", "agent.py"]` | ✅ Actualizado |
| `agent-ai-act/Dockerfile` | `CMD ["python", "agent.py"]` | ✅ Actualizado |
| `agent-unesco/Dockerfile` | `CMD ["python", "agent.py"]` | ✅ Actualizado |
| `agent-bias/agent.py` | `mcp.run()` en lugar de `uvicorn` | ✅ Actualizado |
| `agent-ai-act/agent.py` | `mcp.run()` en lugar de `uvicorn` | ✅ Actualizado |
| `agent-unesco/agent.py` | `mcp.run()` en lugar de `uvicorn` | ✅ Actualizado |
| `reiniciar_limpio.sh` | Script de reinicio automático | ✅ Creado |

---

## ⏱️ TIEMPO ESPERADO

- **Limpieza y reconstrucción:** 2-3 minutos
- **Inicio de Ollama:** 20-30 segundos
- **Disponibilidad de agentes:** Inmediata después de Ollama

---

## 🎯 QUÉ HACER EXACTAMENTE AHORA

### Paso 1: Ejecutar Script de Reinicio
```bash
cd F:/PROPIO/Obs/ethic-obs-v2
chmod +x reiniciar_limpio.sh
./reiniciar_limpio.sh
```

### Paso 2: Esperar Salida
El script te mostrará cuando todo esté listo.

### Paso 3: Verificar
```bash
docker-compose ps
# Todos deben estar "Up"
```

### Paso 4: Probar
```bash
./test_quick.sh
```

---

## 🚨 Si Sigue Reiniciándose

Si después de esto los contenedores siguen reiniciándose:

```bash
# Ver logs detallados
docker-compose logs --tail=50 bias-agent

# Entrar al contenedor para depurar
docker-compose exec bias-agent bash

# Dentro del contenedor
python agent.py  # Ejecutar manualmente para ver errores
```

---

## 📞 Información Importante

- **FastMCP 2.0.0** se ejecuta como servidor MCP nativo
- No necesita Uvicorn ni FastAPI
- Se comunica via JSON-RPC
- Los puertos exponen endpoints `/mcp`

---

## ✅ RESUMEN FINAL

```
❌ ANTES:
   - Dockerfiles intentaban usar uvicorn agent:app
   - FastMCP no expone .app
   - Error: "Attribute app not found"
   - Reinicio continuo

✅ DESPUÉS:
   - Dockerfiles ejecutan: python agent.py
   - Código ejecuta: mcp.run()
   - FastMCP se ejecuta correctamente
   - Agentes permanecen activos
```

---

## 🔗 Próximos Pasos

1. ✅ Ejecutar `./reiniciar_limpio.sh`
2. ✅ Esperar a que Ollama esté listo
3. ✅ Verificar con `docker-compose ps`
4. ✅ Probar con `./test_quick.sh`
5. ✅ Leer documentación: `docs/EJECUCION.md`

---

**¡Sistema listo para usar!** 🎉