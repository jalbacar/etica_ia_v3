#!/bin/bash
# Script de diagnóstico para ethic-obs-v2
# Ayuda a identificar por qué los agentes no se levantan o se reinician

set +e  # No salir en errores

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   🔍 DIAGNÓSTICO - ethic-obs-v2                            ║"
    echo "║   Detectando problemas con agentes                         ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 1. Verificar Docker
check_docker() {
    print_section "1. VERIFICAR DOCKER"

    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        return 1
    fi
    print_success "Docker instalado"

    docker_version=$(docker --version)
    print_info "$docker_version"

    if ! docker ps &> /dev/null; then
        print_error "Docker daemon no está corriendo"
        return 1
    fi
    print_success "Docker daemon corriendo"
    return 0
}

# 2. Verificar Docker Compose
check_docker_compose() {
    print_section "2. VERIFICAR DOCKER COMPOSE"

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado"
        return 1
    fi
    print_success "Docker Compose instalado"

    docker_compose_version=$(docker-compose --version)
    print_info "$docker_compose_version"
    return 0
}

# 3. Verificar estado de contenedores
check_containers() {
    print_section "3. ESTADO DE CONTENEDORES"

    echo "Contenedores en ejecución:"
    docker-compose ps

    echo ""

    # Verificar estado específico de cada agente
    for agent in ollama bias-agent ai-act-agent unesco-agent; do
        container_id=$(docker-compose ps -q $agent 2>/dev/null)

        if [ -z "$container_id" ]; then
            print_warning "Contenedor $agent no encontrado"
            continue
        fi

        status=$(docker ps --filter "id=$container_id" --format "{{.State}}")

        if [ "$status" = "running" ]; then
            print_success "$agent: RUNNING"
        else
            print_error "$agent: $status"
        fi
    done
}

# 4. Verificar logs de errores
check_logs() {
    print_section "4. ÚLTIMOS LOGS (últimas 20 líneas por contenedor)"

    for agent in ollama bias-agent ai-act-agent unesco-agent; do
        echo ""
        echo -e "${YELLOW}=== Logs de $agent ===${NC}"
        docker-compose logs --tail=20 $agent 2>/dev/null || echo "No hay logs disponibles"
    done
}

# 5. Verificar conectividad a Ollama
check_ollama_connectivity() {
    print_section "5. CONECTIVIDAD A OLLAMA"

    # Desde el host
    print_info "Probando conexión a Ollama desde host:"
    if curl -s http://localhost:11434 &> /dev/null; then
        print_success "Ollama accesible en localhost:11434"
    else
        print_warning "Ollama NO accesible en localhost:11434"
    fi

    # Desde los contenedores
    print_info "Probando conectividad desde contenedor bias-agent:"
    docker-compose exec -T bias-agent curl -s http://ollama:11434 &> /dev/null
    if [ $? -eq 0 ]; then
        print_success "Agente puede conectar a Ollama en red interna"
    else
        print_error "Agente NO puede conectar a Ollama"
    fi
}

# 6. Verificar modelo de Ollama
check_ollama_model() {
    print_section "6. MODELO OLLAMA"

    print_info "Listando modelos disponibles:"
    docker-compose exec -T ollama ollama list 2>/dev/null || echo "No se puede listar modelos"
}

# 7. Verificar endpoints
check_endpoints() {
    print_section "7. ENDPOINTS DE AGENTES"

    for port in 8003 8004 8005; do
        agent_name="Unknown"
        [ $port -eq 8003 ] && agent_name="BiasAgent"
        [ $port -eq 8004 ] && agent_name="AIActAgent"
        [ $port -eq 8005 ] && agent_name="UNESCOAgent"

        echo ""
        print_info "Probando $agent_name (puerto $port):"

        if curl -s http://localhost:$port/mcp &> /dev/null; then
            print_success "Endpoint $agent_name accesible"
        else
            print_error "Endpoint $agent_name NO accesible"
        fi
    done
}

# 8. Verificar archivos de configuración
check_configs() {
    print_section "8. ARCHIVOS DE CONFIGURACIÓN"

    echo "Verificando archivos necesarios:"

    for file in docker-compose.yml agent-bias/Dockerfile agent-bias/agent.py agent-bias/requirements.txt; do
        if [ -f "$file" ]; then
            print_success "$file existe"
        else
            print_error "$file NO EXISTE"
        fi
    done
}

# 9. Verificar recursos del sistema
check_resources() {
    print_section "9. RECURSOS DEL SISTEMA"

    print_info "Uso de Docker:"
    docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}\t{{.CPUPerc}}" 2>/dev/null || echo "No se puede obtener estadísticas"

    echo ""
    print_info "Espacio en disco:"
    df -h | grep -E "^/dev|Filesystem"
}

# 10. Verificar conectividad de red Docker
check_docker_network() {
    print_section "10. RED DOCKER"

    print_info "Redes Docker:"
    docker network ls | grep -i ethic || docker network ls | head -5

    echo ""
    print_info "Inspeccionando red ethic-obs-v2_default:"
    docker network inspect ethic-obs-v2_default 2>/dev/null | grep -E "Name|Containers" || print_warning "Red no encontrada"
}

# 11. Soluciones sugeridas
suggest_solutions() {
    print_section "11. SOLUCIONES SUGERIDAS"

    echo "Si los agentes se reinician constantemente:"
    echo ""
    echo "1. Verificar que Ollama esté completamente listo:"
    echo "   docker-compose logs -f ollama | grep 'Started Llama Server'"
    echo ""
    echo "2. Aumentar timeout en docker-compose.yml:"
    echo "   depends_on:"
    echo "     ollama:"
    echo "       condition: service_healthy"
    echo ""
    echo "3. Detener y limpiar:"
    echo "   docker-compose down"
    echo "   docker-compose up -d"
    echo ""
    echo "4. Ver logs completos de un agente:"
    echo "   docker-compose logs bias-agent --follow"
    echo ""
    echo "5. Entrar a un contenedor para depurar:"
    echo "   docker-compose exec bias-agent bash"
    echo ""
    echo "6. Verificar salud del servicio:"
    echo "   docker-compose exec -T ollama ollama list"
}

# Main
main() {
    print_header

    check_docker || {
        print_error "Docker no está disponible. Instala Docker Desktop primero."
        exit 1
    }

    check_docker_compose
    check_containers
    check_configs
    check_ollama_model
    check_ollama_connectivity
    check_docker_network
    check_endpoints
    check_resources
    check_logs
    suggest_solutions

    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   📊 DIAGNÓSTICO COMPLETADO                               ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

main
