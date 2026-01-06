#!/bin/bash
# Script de inicio rápido para ethic-obs-v2
# Autor: Sistema Ético de Observabilidad
# Uso: chmod +x start.sh && ./start.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones
print_header() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   🚀 SISTEMA ÉTICO DE OBSERVABILIDAD (ethic-obs-v2)        ║"
    echo "║   EU AI Act + UNESCO Principles 2026                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_docker() {
    print_header
    echo ""
    echo "[1/5] Verificando Docker..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        echo "    Descarga desde: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    print_success "Docker detectado"
    echo ""
}

check_docker_compose() {
    echo "[2/5] Verificando Docker Compose..."

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado"
        exit 1
    fi
    print_success "Docker Compose detectado"
    echo ""
}

show_menu() {
    echo "[3/5] Opciones disponibles:"
    echo ""
    echo "  1) ▶️  Iniciar sistema completo (Ollama + 3 Agentes)"
    echo "  2) 🛑  Detener sistema"
    echo "  3) 🔄  Reiniciar sistema"
    echo "  4) 📊  Ver logs en tiempo real"
    echo "  5) ✔️  Verificar estado"
    echo "  6) 🧹  Limpiar todo (eliminar contenedores)"
    echo "  7) ❌  Salir"
    echo ""
}

start_system() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   ▶️  INICIANDO SISTEMA...                                  ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo "Iniciando contenedores..."
    docker-compose up -d

    if [ $? -ne 0 ]; then
        print_error "Error al iniciar sistema"
        exit 1
    fi

    echo ""
    print_success "Contenedores iniciados"
    echo ""
    echo "⏳ Esperando a que Ollama esté listo (puede tomar 20-30 segundos)..."
    echo "   Comprobando salud del servicio..."
    echo ""

    # Health check
    max_retries=30
    retry=0

    while [ $retry -lt $max_retries ]; do
        if docker-compose exec -T ollama ollama list &> /dev/null; then
            echo ""
            print_success "Ollama está listo"
            system_ready
            return
        fi

        sleep 1
        retry=$((retry + 1))
        echo -ne "\r   Intento $retry/$max_retries..."
    done

    print_warning "Ollama tarda más de lo esperado. Verificando logs..."
    docker-compose logs ollama
    echo ""
    print_info "El sistema puede seguir iniciándose en background"
    echo "   Ejecuta 'docker-compose logs -f ollama' para ver progreso"
    system_ready
}

system_ready() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   ✓ SISTEMA OPERATIVO                                      ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo "📡 Agentes disponibles:"
    echo "   - BiasAgent (Sesgos)       : http://localhost:8003/mcp"
    echo "   - AIActAgent (EU AI Act)   : http://localhost:8004/mcp"
    echo "   - UNESCOAgent (Principios) : http://localhost:8005/mcp"
    echo ""
    echo "🧪 Prueba rápida con cURL:"
    echo '   curl -X POST http://localhost:8003/mcp \'
    echo '     -H "Content-Type: application/json" \'
    echo '     -d '"'"'{ "jsonrpc": "2.0", "id": 1, "method": "detect_bias", "params": {"text": "test"} }'"'"
    echo ""
    echo "📚 Más información:"
    echo "   - Ver logs: ejecuta este script y elige opción 4"
    echo "   - Ver documentación: abre docs/EJECUCION.md"
    echo ""
    read -p "Presiona Enter para continuar..."
}

stop_system() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   🛑  DETENIENDO SISTEMA...                                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    docker-compose stop
    echo ""
    print_success "Sistema detenido"
    echo "    Para reiniciar: ejecuta este script y elige opción 1"
    echo ""
    read -p "Presiona Enter para continuar..."
}

restart_system() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   🔄  REINICIANDO SISTEMA...                                ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    docker-compose restart
    echo ""
    print_success "Sistema reiniciado"
    echo "⏳ Esperando estabilización..."
    sleep 10
    echo ""
    print_success "Listo"
    echo ""
    read -p "Presiona Enter para continuar..."
}

show_logs() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   📊  LOGS EN TIEMPO REAL                                   ║"
    echo "║   (Presiona Ctrl+C para salir)                             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    docker-compose logs -f
}

show_status() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   ✔️  ESTADO DEL SISTEMA                                    ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    docker-compose ps
    echo ""
    echo "📊 Uso de recursos:"
    docker stats --no-stream
    echo ""
    read -p "Presiona Enter para continuar..."
}

clean_system() {
    clear
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   🧹  LIMPIAR SISTEMA                                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    print_warning "Esto eliminará todos los contenedores"
    echo "   Los datos de Ollama se conservarán"
    echo ""
    read -p "¿Confirmar? (s/n): " confirm

    if [ "$confirm" != "s" ]; then
        echo "Operación cancelada"
        read -p "Presiona Enter para continuar..."
        return
    fi

    echo ""
    echo "Eliminando contenedores..."
    docker-compose down
    print_success "Hecho"
    echo ""
    read -p "Presiona Enter para continuar..."
}

# Main menu loop
main_menu() {
    while true; do
        print_header
        show_menu

        read -p "Elige opción (1-7): " choice

        case $choice in
            1) start_system ;;
            2) stop_system ;;
            3) restart_system ;;
            4) show_logs ;;
            5) show_status ;;
            6) clean_system ;;
            7)
                clear
                echo ""
                print_success "Adiós"
                echo ""
                exit 0
                ;;
            *)
                print_error "Opción no válida"
                sleep 2
                ;;
        esac
    done
}

# Ejecución principal
check_docker
check_docker_compose
main_menu
