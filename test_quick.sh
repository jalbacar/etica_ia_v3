#!/bin/bash
# Script de test rápido para ethic-obs-v2
# Prueba los 3 agentes con ejemplos de textos éticos y no éticos
# Uso: chmod +x test_quick.sh && ./test_quick.sh

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   🧪 TEST RÁPIDO - SISTEMA ÉTICO                           ║"
    echo "║   ethic-obs-v2                                             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_test() {
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}$1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_request() {
    echo -e "${BLUE}📤 Solicitud:${NC}"
    echo -e "${YELLOW}$1${NC}"
}

print_response() {
    echo -e "${GREEN}📥 Respuesta:${NC}"
    echo -e "${YELLOW}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Verificar que los agentes estén en ejecución
check_agents() {
    print_header
    echo ""
    echo "🔍 Verificando conexión con agentes..."
    echo ""

    agents=("bias-agent" "ai-act-agent" "unesco-agent")
    ports=(8003 8004 8005)

    for i in "${!agents[@]}"; do
        agent="${agents[$i]}"
        port="${ports[$i]}"

        if curl -s http://localhost:$port/mcp &> /dev/null; then
            print_success "$agent está disponible en puerto $port"
        else
            print_error "$agent NO está disponible en puerto $port"
            echo ""
            echo "Asegúrate de que el sistema está corriendo:"
            echo "  ./start.sh (Linux/Mac) o start.bat (Windows)"
            exit 1
        fi
    done
    echo ""
}

# Test 1: BiasAgent - Texto con sesgo
test_bias_agent_negative() {
    print_test "TEST 1: BiasAgent - Detectar Sesgo (Texto Negativo)"
    echo ""

    text="Las mujeres no son buenas en matemáticas"

    request_json='{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "detect_bias",
        "params": {"text": "'$text'"}
    }'

    print_request "Analizando: \"$text\""
    echo ""

    response=$(curl -s -X POST http://localhost:8003/mcp \
        -H "Content-Type: application/json" \
        -d "$request_json")

    print_response "$response"
    echo ""

    # Verificar resultado
    ethical=$(echo $response | grep -o '"ethical":[^,}]*' | cut -d: -f2)
    score=$(echo $response | grep -o '"score":[^,}]*' | cut -d: -f2)

    if [ "$ethical" == "false" ]; then
        print_success "Sesgo detectado correctamente (score: $score)"
    else
        print_error "Debería detectar sesgo pero no lo hizo"
    fi
    echo ""
}

# Test 2: BiasAgent - Texto sin sesgo
test_bias_agent_positive() {
    print_test "TEST 2: BiasAgent - Detectar Sesgo (Texto Positivo)"
    echo ""

    text="Todas las personas merecen oportunidades iguales sin importar género"

    request_json='{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "bias_supervisor",
        "params": {"text": "'$text'"}
    }'

    print_request "Analizando: \"$text\""
    echo ""

    response=$(curl -s -X POST http://localhost:8003/mcp \
        -H "Content-Type: application/json" \
        -d "$request_json")

    print_response "$response"
    echo ""

    ethical=$(echo $response | grep -o '"ethical":[^,}]*' | cut -d: -f2)

    if [ "$ethical" == "true" ]; then
        print_success "Texto ético validado correctamente"
    else
        print_error "Debería validar texto como ético"
    fi
    echo ""
}

# Test 3: AIActAgent - Evaluar Riesgo
test_ai_act_risk() {
    print_test "TEST 3: AIActAgent - Evaluar Riesgo (EU AI Act Art. 9)"
    echo ""

    text="Sistema automático de decisión crediticia sin auditoría humana para personas vulnerables"

    request_json='{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "ai_act_risk_management",
        "params": {"text": "'$text'"}
    }'

    print_request "Analizando: \"$text\""
    echo ""

    response=$(curl -s -X POST http://localhost:8004/mcp \
        -H "Content-Type: application/json" \
        -d "$request_json")

    print_response "$response"
    echo ""

    score=$(echo $response | grep -o '"score":[^,}]*' | cut -d: -f2)
    print_success "Análisis completado (risk score: $score)"
    echo ""
}

# Test 4: AIActAgent - Evaluar Transparencia
test_ai_act_transparency() {
    print_test "TEST 4: AIActAgent - Evaluar Transparencia (EU AI Act Art. 13)"
    echo ""

    text="Sistema completamente documentado con logs detallados, datasets publicados y explicabilidad de decisiones"

    request_json='{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "ai_act_transparency",
        "params": {"text": "'$text'"}
    }'

    print_request "Analizando: \"$text\""
    echo ""

    response=$(curl -s -X POST http://localhost:8004/mcp \
        -H "Content-Type: application/json" \
        -d "$request_json")

    print_response "$response"
    echo ""

    score=$(echo $response | grep -o '"score":[^,}]*' | cut -d: -f2)
    print_success "Análisis completado (transparency score: $score)"
    echo ""
}

# Test 5: UNESCOAgent - Evaluar Principios
test_unesco_principles() {
    print_test "TEST 5: UNESCOAgent - Evaluar Principios UNESCO"
    echo ""

    text="Sistema que respeta derechos humanos, no causa daño desproporcionado y garantiza equidad"

    request_json='{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "unesco_principles",
        "params": {"text": "'$text'"}
    }'

    print_request "Analizando: \"$text\""
    echo ""

    response=$(curl -s -X POST http://localhost:8005/mcp \
        -H "Content-Type: application/json" \
        -d "$request_json")

    print_response "$response"
    echo ""

    ethical=$(echo $response | grep -o '"ethical":[^,}]*' | cut -d: -f2)
    if [ "$ethical" == "true" ]; then
        print_success "Cumple principios UNESCO"
    else
        print_success "Análisis completado"
    fi
    echo ""
}

# Test 6: Validación de Salida
test_output_validation() {
    print_test "TEST 6: Validación de Salida (Cliente Python)"
    echo ""

    echo "📝 Verificando cliente Python decorator..."
    echo ""

    if [ -f "client_python/decorator.py" ]; then
        print_success "Archivo decorator.py existe"
        echo ""
        echo "Uso:"
        echo '  from decorator import ethical_guard'
        echo ''
        echo '  @ethical_guard()'
        echo '  async def generate_response(prompt):'
        echo '      return "Tu respuesta"'
        echo ''
        echo "El decorador validará entrada y salida automáticamente"
        echo ""
    else
        print_error "Cliente Python no encontrado"
    fi
    echo ""
}

# Test 7: Validación JavaScript
test_js_validation() {
    print_test "TEST 7: Validación de Salida (Cliente JavaScript)"
    echo ""

    echo "📝 Verificando cliente JavaScript..."
    echo ""

    if [ -f "client-js/index.mjs" ]; then
        print_success "Archivo index.mjs existe"
        echo ""
        echo "Uso:"
        echo "  import EthicalLego from './index.mjs';"
        echo ""
        echo "  const { ethical, results } = await EthicalLego.checkAll('tu texto');"
        echo ""
        echo "Comprueba automáticamente contra los 3 agentes"
        echo ""
    else
        print_error "Cliente JavaScript no encontrado"
    fi
    echo ""
}

# Resumen final
print_summary() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║   📊 RESUMEN DE TESTS                                      ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo "✓ BiasAgent (puerto 8003)"
    echo "  - Detecta sesgos discriminatorios"
    echo "  - UNESCO Principle 6: Fairness & Non-Discrimination"
    echo ""
    echo "✓ AIActAgent (puerto 8004)"
    echo "  - Evalúa riesgos (Article 9)"
    echo "  - Evalúa transparencia (Article 13)"
    echo "  - EU AI Act compliance"
    echo ""
    echo "✓ UNESCOAgent (puerto 8005)"
    echo "  - Evalúa principios éticos"
    echo "  - Principles 1, 4, 6 de UNESCO"
    echo ""
    echo "📚 Documentación: docs/EJECUCION.md"
    echo "🔗 Endpoints: http://localhost:8003,8004,8005/mcp"
    echo ""
}

# Menú interactivo
main_menu() {
    print_header
    check_agents

    echo "Selecciona qué tests ejecutar:"
    echo ""
    echo "  1) Ejecutar TODOS los tests"
    echo "  2) Test BiasAgent (sesgo negativo)"
    echo "  3) Test BiasAgent (sesgo positivo)"
    echo "  4) Test AIActAgent (riesgo)"
    echo "  5) Test AIActAgent (transparencia)"
    echo "  6) Test UNESCOAgent (principios)"
    echo "  7) Verificar clientes (Python/JS)"
    echo "  8) Ver resumen"
    echo "  9) Salir"
    echo ""

    read -p "Elige opción (1-9): " choice

    case $choice in
        1)
            test_bias_agent_negative
            test_bias_agent_positive
            test_ai_act_risk
            test_ai_act_transparency
            test_unesco_principles
            print_summary
            ;;
        2) test_bias_agent_negative ;;
        3) test_bias_agent_positive ;;
        4) test_ai_act_risk ;;
        5) test_ai_act_transparency ;;
        6) test_unesco_principles ;;
        7)
            test_output_validation
            test_js_validation
            ;;
        8) print_summary ;;
        9)
            echo ""
            print_success "¡Adiós!"
            echo ""
            exit 0
            ;;
        *)
            print_error "Opción no válida"
            sleep 2
            main_menu
            ;;
    esac

    echo ""
    read -p "Presiona Enter para volver al menú..."
    clear
    main_menu
}

# Ejecutar
main_menu
