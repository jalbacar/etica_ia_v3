@echo off
REM Script de inicio rápido para ethic-obs-v2
REM Autor: Sistema Ético de Observabilidad
REM Uso: start.bat

setlocal enabledelayedexpansion

cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   🚀 SISTEMA ÉTICO DE OBSERVABILIDAD (ethic-obs-v2)        ║
echo ║   EU AI Act + UNESCO Principles 2026                       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar Docker
echo [1/5] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Docker no está instalado o no está en PATH
    echo    Descarga desde: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✓ Docker detectado
echo.

REM Verificar Docker Compose
echo [2/5] Verificando Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Docker Compose no está instalado
    echo    Debe venir incluido con Docker Desktop
    pause
    exit /b 1
)
echo ✓ Docker Compose detectado
echo.

REM Mostrar opciones
echo [3/5] Opciones disponibles:
echo.
echo   1) ▶️  Iniciar sistema completo (Ollama + 3 Agentes)
echo   2) 🛑  Detener sistema
echo   3) 🔄  Reiniciar sistema
echo   4) 📊  Ver logs en tiempo real
echo   5) ✔️  Verificar estado
echo   6) 🧹  Limpiar todo (eliminar contenedores)
echo   7) ❌  Salir
echo.

set /p choice="Elige opción (1-7): "

if "%choice%"=="1" goto start_system
if "%choice%"=="2" goto stop_system
if "%choice%"=="3" goto restart_system
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto status
if "%choice%"=="6" goto clean
if "%choice%"=="7" goto exit_script

echo ❌ Opción no válida
pause
exit /b 1

:start_system
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   ▶️  INICIANDO SISTEMA...                                  ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo Iniciando contenedores...
docker-compose up -d

if errorlevel 1 (
    echo ❌ Error al iniciar sistema
    pause
    exit /b 1
)

echo.
echo ✓ Contenedores iniciados
echo.
echo ⏳ Esperando a que Ollama esté listo (puede tomar 20-30 segundos)...
echo    Comprobando salud del servicio...

setlocal enabledelayedexpansion
set "max_retries=30"
set "retry=0"

:health_check
set /a retry=retry+1
timeout /t 1 /nobreak >nul

docker-compose exec -T ollama ollama list >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ✓ Ollama está listo
    goto system_ready
)

if !retry! lss !max_retries! (
    goto health_check
)

echo ⚠️  Ollama tarda más de lo esperado. Verificando logs...
docker-compose logs ollama
echo.
echo 💡 El sistema puede seguir iniciándose en background
echo    Ejecuta "docker-compose logs -f ollama" para ver progreso

:system_ready
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   ✓ SISTEMA OPERATIVO                                      ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 📡 Agentes disponibles:
echo    - BiasAgent (Sesgos)       : http://localhost:8003/mcp
echo    - AIActAgent (EU AI Act)   : http://localhost:8004/mcp
echo    - UNESCOAgent (Principios) : http://localhost:8005/mcp
echo.
echo 🧪 Prueba rápida con cURL:
echo    curl -X POST http://localhost:8003/mcp ^
echo      -H "Content-Type: application/json" ^
echo      -d "{ \"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"detect_bias\", \"params\": {\"text\": \"test\"} }"
echo.
echo 📚 Más información:
echo    - Ver logs: ejecuta este script y elige opción 4
echo    - Ver documentación: abre docs/EJECUCION.md
echo.
pause
goto menu

:stop_system
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   🛑  DETENIENDO SISTEMA...                                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
docker-compose stop
echo.
echo ✓ Sistema detenido
echo    Para reiniciar: ejecuta este script y elige opción 1
echo.
pause
goto menu

:restart_system
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   🔄  REINICIANDO SISTEMA...                                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
docker-compose restart
echo.
echo ✓ Sistema reiniciado
timeout /t 5 /nobreak
echo ⏳ Esperando estabilización...
timeout /t 10 /nobreak
echo.
echo ✓ Listo
echo.
pause
goto menu

:logs
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   📊  LOGS EN TIEMPO REAL                                   ║
echo ║   (Presiona Ctrl+C para salir)                             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
docker-compose logs -f
goto menu

:status
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   ✔️  ESTADO DEL SISTEMA                                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
docker-compose ps
echo.
echo 📊 Uso de recursos:
docker stats --no-stream
echo.
pause
goto menu

:clean
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   🧹  LIMPIAR SISTEMA                                       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo ⚠️  ADVERTENCIA: Esto eliminará todos los contenedores
echo    Los datos de Ollama se conservarán
echo.
set /p confirm="¿Confirmar? (s/n): "
if /i not "%confirm%"=="s" (
    echo Operación cancelada
    pause
    goto menu
)

echo.
echo Eliminando contenedores...
docker-compose down
echo ✓ Hecho
echo.
pause
goto menu

:exit_script
cls
echo.
echo ✓ Adiós
echo.
exit /b 0

:menu
cls
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   🚀 SISTEMA ÉTICO DE OBSERVABILIDAD (ethic-obs-v2)        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo   1) ▶️  Iniciar sistema
echo   2) 🛑  Detener sistema
echo   3) 🔄  Reiniciar sistema
echo   4) 📊  Ver logs
echo   5) ✔️  Ver estado
echo   6) 🧹  Limpiar
echo   7) ❌  Salir
echo.
set /p choice="Elige opción (1-7): "

if "%choice%"=="1" goto start_system
if "%choice%"=="2" goto stop_system
if "%choice%"=="3" goto restart_system
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto status
if "%choice%"=="6" goto clean
if "%choice%"=="7" goto exit_script

goto menu

endlocal
