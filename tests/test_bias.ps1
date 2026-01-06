# test_bias.ps1 - Versión mejorada
Write-Host "🔍 Iniciando pruebas..." -ForegroundColor Cyan

# 1. Verificar conexión con el agente
try {
    $healthCheck = Invoke-RestMethod -Uri "http://localhost:8003/mcp" -Method Post -Body (
        @{ jsonrpc="2.0"; method="health"; params=@{} } | ConvertTo-Json
    ) -ContentType "application/json" -TimeoutSec 3

    Write-Host "🟢 Agente activo. Status: $($healthCheck.result.status)" -ForegroundColor Green
} catch {
    Write-Host "🔴 ERROR: No se pudo conectar al agente" -ForegroundColor Red
    Write-Host "   Mensaje: $($_.Exception.Message)"
    exit 1
}

# 2. Ejecutar casos de prueba
$TestCases = @(
    @{ text="Los hombres son mejores en tecnología"; expected=$true },
    @{ text="Contratamos basado en habilidades"; expected=$false }
)

foreach ($test in $TestCases) {
    Write-Host "`n🔬 Probando: '$($test.text)'" -ForegroundColor Yellow

    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8003/mcp" -Method Post -Body (
            @{
                jsonrpc="2.0";
                method="detect_bias";
                params=@{ text=$test.text }
            } | ConvertTo-Json
        ) -ContentType "application/json" -TimeoutSec 5

        $passed = $response.result.bias_detected -eq $test.expected
        $color = if ($passed) { "Green" } else { "Red" }

        Write-Host "   Resultado: $($response.result.bias_detected)" -ForegroundColor $color
        Write-Host "   Razón: $($response.result.reason)"
    } catch {
        Write-Host "   ⚠️ Error en la prueba: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n🏁 Pruebas completadas" -ForegroundColor Cyan
