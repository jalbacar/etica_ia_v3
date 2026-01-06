#!/bin/bash
# Script para reiniciar limpiamente ethic-obs-v2
# Elimina contenedores viejos, reconstruye imágenes y reinicia

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   🔄 REINICIO LIMPIO - ethic-obs-v2                        ║"
    echo "║   Reconstruyendo todo desde cero                           ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}▶️  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

main() {
    print_header

    # Paso 1: Detener contenedores
    print_step "Paso 1: Deteniendo contenedores activos"
    if docker-compose ps | grep -q "Up\|Restarting"; then
        docker-compose stop 2>/dev/null || true
        print_success "Contenedores detenidos"
    else
        print_warning "No hay contenedores activos"
    fi

    # Paso 2: Eliminar contenedores
    print_step "Paso 2: Eliminando contenedores"
    docker-compose rm -f 2>/dev/null || true
    print_success "Contenedores eliminados"

    # Paso 3: Limpiar imágenes viejas (opcional)
    print_step "Paso 3: Limpiando imágenes de construcción anteriores"
    docker image prune -f --filter "label!=keep" 2>/dev/null || true
    print_success "Imágenes limpias"

    # Paso 4: Reconstruir imágenes
    print_step "Paso 4: Reconstruyendo imágenes de agentes"
    docker-compose build --no-cache
    print_success "Imágenes reconstruidas"

    # Paso 5: Iniciar sistema
    print_step "Paso 5: Iniciando sistema"
    docker-compose up -d
    print_success "Sistema iniciado"

    # Paso 6: Esperar a que Ollama esté listo
    print_step "Paso 6: Esperando que Ollama esté listo"
    max_retries=60
    retry=0

    while [ $retry -lt $max_retries ]; do
        if docker-compose exec -T ollama ollama list &> /dev/null; then
            echo ""
            print_success "✓ Ollama está listo"
            break
        fi

        sleep 1
        retry=$((retry + 1))
        echo -ne "\r   Intento $retry/$max_retries..."
    done

    if [ $retry -ge $max_retries ]; then
        print_warning "Ollama tardó más de lo esperado"
        echo "   Continuando de todas formas..."
    fi

    # Paso 7: Verificar estado
    print_step "Paso 7: Verificando estado del sistema"
    echo ""
    docker-compose ps
    echo ""

    # Paso 8: Verificar conectividad
    print_step "Paso 8: Verificando conectividad"

    # Health check BiasAgent
    echo "Probando BiasAgent..."
    if curl -s http://localhost:8003/info &> /dev/null || curl -s -X GET http://localhost:8003/ &> /dev/null; then
        print_success "BiasAgent responde"
    else
        print_warning "BiasAgent aún no responde (esperado si acaba de iniciar)"
    fi

    # Health check Ollama
    echo "Probando Ollama..."
    if curl -s http://localhost:11434 &> /dev/null; then
        print_success "Ollama responde"
    else
        print_warning "Ollama aún no responde"
    fi

    # Paso 9: Mostrar instrucciones finales
    print_step "Paso 9: Instrucciones finales"
    echo ""
    echo "✓ Sistema reiniciado completamente"
    echo ""
    echo "Próximos pasos:"
    echo ""
    echo "1. Ver logs en tiempo real:"
    echo "   docker-compose logs -f"
    echo ""
    echo "2. Probar BiasAgent:"
    echo "   curl -X POST http://localhost:8003/mcp \\"
    echo '     -H "Content-Type: application/json" \'
    echo '     -d '"'"'{"jsonrpc":"2.0","id":1,"method":"health","params":{}}'"'"
    echo ""
    echo "3. Ejecutar diagnóstico:"
    echo "   ./diagnostico.sh"
    echo ""
    echo "4. Ver estado:"
    echo "   docker-compose ps"
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ REINICIO COMPLETADO EXITOSAMENTE                      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

main
