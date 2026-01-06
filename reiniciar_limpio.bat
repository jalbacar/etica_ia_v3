@echo off
REM Script para reiniciar limpiamente ethic-obs-v2 en Windows
REM Elimina contenedores viejos, reconstruye imágenes y reinicia

setlocal enabledelayedexpansion

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   🔄 REINICIO LIMPIO - ethic-obs-v2                        ║
echo ║   Reconstruyendo todo desde cero                           ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Docker no está instalado
    pause
    exit /b 1
)

REM Paso 1: Detener contenedores
echo [1/8] Deteniendo contenedores activos...
docker-compose ps >nul 2>&1
if errorlevel 0 (
    docker-compose stop >nul 2>&1
    echo ✓ Contenedores detenidos
) else (
    echo ⚠️  No hay contenedores activos
)
echo.

REM Paso 2: Eliminar contenedores
echo [2/8] Eliminando contenedores...
docker-compose rm -f >nul 2>&1
echo ✓ Contenedores eliminados
echo.

REM Paso 3: Limpiar imágenes
echo [3/8] Limpiando imágenes viejas...
docker image prune -f >nul 2>&1
echo ✓ Imágenes limpias
echo.

REM Paso 4: Reconstruir imágenes
echo [4/8] Reconstruyendo imágenes de agentes (esto puede tomar 1-2 minutos)...
docker-compose build --no-cache
if errorlevel 1 (
    echo ❌ Error al reconstruir imágenes
    pause
    exit /b 1
)
echo ✓ Imágenes reconstruidas
echo.

REM Paso 5: Iniciar sistema
echo [5/8] Iniciando sistema...
docker-compose up -d
if errorlevel 1 (
    echo ❌ Error al iniciar sistema
    pause
    exit /b 1
)
echo ✓ Sistema iniciado
echo.

REM Paso 6: Esperar a Ollama
echo [6/8] Esperando que Ollama esté listo (puede tomar 30 segundos)...
set "max_retries=60"
set "retry=0"

:health_check
set /a retry=retry+1
timeout /t 1 /nobreak >nul
docker-compose exec -T ollama ollama list >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ✓ Ollama está listo
    goto ollama_ready
)

if !retry! lss !max_retries! (
    goto health_check
)

echo ⚠️  Ollama tardó más de lo esperado. Continuando...

:ollama_ready
echo.

REM Paso 7: Verificar estado
echo [7/8] Verificando estado del sistema...
echo.
docker-compose ps
echo.

REM Paso 8: Mostrar instrucciones
echo [8/8] Instrucciones finales...
echo.
echo ✓ Sistema reiniciado completamente
echo.
echo Próximos pasos:
echo.
echo 1. Ver logs en tiempo real:
echo    docker-compose logs -f
echo.
echo 2. Probar BiasAgent:
echo    curl -X POST http://localhost:8003/mcp -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"health\",\"params\":{}}"
echo.
echo 3. Ejecutar tests:
echo    test_quick.sh
echo.
echo 4. Ver estado:
echo    docker-compose ps
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   ✅ REINICIO COMPLETADO EXITOSAMENTE                      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
pause
