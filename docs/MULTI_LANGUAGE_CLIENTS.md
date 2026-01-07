# Ethical Guard - Implementaciones sin Decoradores

Para lenguajes que no soportan decoradores, hay múltiples alternativas.

---

## 1. Java - Patrón Proxy + Interceptor

```java
// EthicalGuard.java
import java.net.http.*;
import com.google.gson.*;

public class EthicalGuard {
    private static final String ORCHESTRATOR_URL = 
        System.getenv().getOrDefault("ORCHESTRATOR_URL", "http://localhost:8000");
    private static final double BLOCK_THRESHOLD = 0.65;
    
    public static class EthicalException extends RuntimeException {
        public final String decision;
        public final double riskScore;
        public final String scope;
        
        public EthicalException(String message, String decision, double riskScore, String scope) {
            super(message);
            this.decision = decision;
            this.riskScore = riskScore;
            this.scope = scope;
        }
    }
    
    /**
     * Wrapper manual para validar input/output
     */
    public static <T, R> R withEthicalValidation(
        T input,
        Function<T, R> function,
        String context
    ) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        Gson gson = new Gson();
        
        // 1. Validar INPUT
        Map<String, Object> inputPayload = Map.of(
            "system_prompt", "Java Application",
            "user_input", String.valueOf(input),
            "context", Map.of("domain", context),
            "agents", List.of()
        );
        
        HttpRequest inputRequest = HttpRequest.newBuilder()
            .uri(URI.create(ORCHESTRATOR_URL + "/analyze"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(inputPayload)))
            .build();
        
        HttpResponse<String> inputResponse = client.send(
            inputRequest, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        JsonObject inputResult = gson.fromJson(inputResponse.body(), JsonObject.class);
        double inputRisk = inputResult.getAsJsonObject("decision").get("risk_score").getAsDouble();
        String inputDecision = inputResult.getAsJsonObject("decision").get("decision").getAsString();
        
        if (inputRisk >= BLOCK_THRESHOLD || "block".equals(inputDecision)) {
            throw new EthicalException(
                "Input bloqueado: " + inputRisk,
                inputDecision,
                inputRisk,
                "input"
            );
        }
        
        // 2. Ejecutar función
        R result = function.apply(input);
        
        // 3. Validar OUTPUT
        Map<String, Object> outputPayload = Map.of(
            "system_prompt", "Java Application",
            "user_input", String.valueOf(input),
            "assistant_output", String.valueOf(result),
            "context", Map.of("domain", context),
            "agents", List.of()
        );
        
        HttpRequest outputRequest = HttpRequest.newBuilder()
            .uri(URI.create(ORCHESTRATOR_URL + "/analyze"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(outputPayload)))
            .build();
        
        HttpResponse<String> outputResponse = client.send(
            outputRequest, 
            HttpResponse.BodyHandlers.ofString()
        );
        
        JsonObject outputResult = gson.fromJson(outputResponse.body(), JsonObject.class);
        double outputRisk = outputResult.getAsJsonObject("decision").get("risk_score").getAsDouble();
        String outputDecision = outputResult.getAsJsonObject("decision").get("decision").getAsString();
        
        if (outputRisk >= BLOCK_THRESHOLD || "block".equals(outputDecision)) {
            throw new EthicalException(
                "Output bloqueado: " + outputRisk,
                outputDecision,
                outputRisk,
                "output"
            );
        }
        
        return result;
    }
}

// Uso
public class HiringSystem {
    public String recommendCandidate(String candidateInfo) {
        // Tu lógica
        return "Recomendación basada en méritos";
    }
    
    public String recommendCandidateEthical(String candidateInfo) {
        try {
            return EthicalGuard.withEthicalValidation(
                candidateInfo,
                this::recommendCandidate,
                "hr"
            );
        } catch (EthicalGuard.EthicalException e) {
            System.err.println("Bloqueado: " + e.getMessage());
            throw e;
        }
    }
}
```

---

## 2. C# - Patrón Proxy + Extension Methods

```csharp
// EthicalGuard.cs
using System.Net.Http;
using System.Text.Json;

public static class EthicalGuard
{
    private const string ORCHESTRATOR_URL = "http://localhost:8000";
    private const double BLOCK_THRESHOLD = 0.65;
    
    public class EthicalException : Exception
    {
        public string Decision { get; set; }
        public double RiskScore { get; set; }
        public string Scope { get; set; }
        
        public EthicalException(string message, string decision, double riskScore, string scope)
            : base(message)
        {
            Decision = decision;
            RiskScore = riskScore;
            Scope = scope;
        }
    }
    
    /// <summary>
    /// Extension method para validar éticamente cualquier función
    /// </summary>
    public static async Task<TResult> WithEthicalValidation<TInput, TResult>(
        this Func<TInput, Task<TResult>> function,
        TInput input,
        string context = "general"
    )
    {
        using var client = new HttpClient();
        
        // 1. Validar INPUT
        var inputPayload = new
        {
            system_prompt = "C# Application",
            user_input = input?.ToString() ?? "",
            context = new { domain = context },
            agents = Array.Empty<string>()
        };
        
        var inputResponse = await client.PostAsJsonAsync(
            $"{ORCHESTRATOR_URL}/analyze",
            inputPayload
        );
        
        var inputResult = await inputResponse.Content.ReadFromJsonAsync<JsonDocument>();
        var inputRisk = inputResult.RootElement
            .GetProperty("decision")
            .GetProperty("risk_score")
            .GetDouble();
        var inputDecision = inputResult.RootElement
            .GetProperty("decision")
            .GetProperty("decision")
            .GetString();
        
        if (inputRisk >= BLOCK_THRESHOLD || inputDecision == "block")
        {
            throw new EthicalException(
                $"Input bloqueado: {inputRisk}",
                inputDecision,
                inputRisk,
                "input"
            );
        }
        
        // 2. Ejecutar función
        var result = await function(input);
        
        // 3. Validar OUTPUT
        var outputPayload = new
        {
            system_prompt = "C# Application",
            user_input = input?.ToString() ?? "",
            assistant_output = result?.ToString() ?? "",
            context = new { domain = context },
            agents = Array.Empty<string>()
        };
        
        var outputResponse = await client.PostAsJsonAsync(
            $"{ORCHESTRATOR_URL}/analyze",
            outputPayload
        );
        
        var outputResult = await outputResponse.Content.ReadFromJsonAsync<JsonDocument>();
        var outputRisk = outputResult.RootElement
            .GetProperty("decision")
            .GetProperty("risk_score")
            .GetDouble();
        var outputDecision = outputResult.RootElement
            .GetProperty("decision")
            .GetProperty("decision")
            .GetString();
        
        if (outputRisk >= BLOCK_THRESHOLD || outputDecision == "block")
        {
            throw new EthicalException(
                $"Output bloqueado: {outputRisk}",
                outputDecision,
                outputRisk,
                "output"
            );
        }
        
        return result;
    }
}

// Uso
public class HiringSystem
{
    private async Task<string> RecommendCandidateCore(string candidateInfo)
    {
        // Tu lógica
        return "Recomendación";
    }
    
    public async Task<string> RecommendCandidate(string candidateInfo)
    {
        // Extension method que valida automáticamente
        return await RecommendCandidateCore
            .WithEthicalValidation(candidateInfo, "hr");
    }
}
```

---

## 3. Go - Wrapper de Funciones

```go
// ethical_guard.go
package ethical

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
    "os"
)

const DefaultBlockThreshold = 0.65

type EthicalException struct {
    Message    string
    Decision   string
    RiskScore  float64
    Scope      string
}

func (e *EthicalException) Error() string {
    return fmt.Sprintf("%s (risk: %.2f, scope: %s)", e.Message, e.RiskScore, e.Scope)
}

type AnalysisResult struct {
    Decision struct {
        Decision  string  `json:"decision"`
        RiskScore float64 `json:"risk_score"`
    } `json:"decision"`
}

// WithEthicalValidation envuelve cualquier función con validación ética
func WithEthicalValidation[T any, R any](
    fn func(T) (R, error),
    input T,
    context string,
) (R, error) {
    var result R
    orchestratorURL := os.Getenv("ORCHESTRATOR_URL")
    if orchestratorURL == "" {
        orchestratorURL = "http://localhost:8000"
    }

    // 1. Validar INPUT
    inputPayload := map[string]interface{}{
        "system_prompt": "Go Application",
        "user_input":    fmt.Sprintf("%v", input),
        "context":       map[string]string{"domain": context},
        "agents":        []string{},
    }

    inputResult, err := analyzeWithOrchestrator(orchestratorURL, inputPayload)
    if err != nil {
        return result, err
    }

    if inputResult.Decision.RiskScore >= DefaultBlockThreshold ||
        inputResult.Decision.Decision == "block" {
        return result, &EthicalException{
            Message:   "Input bloqueado",
            Decision:  inputResult.Decision.Decision,
            RiskScore: inputResult.Decision.RiskScore,
            Scope:     "input",
        }
    }

    // 2. Ejecutar función
    result, err = fn(input)
    if err != nil {
        return result, err
    }

    // 3. Validar OUTPUT
    outputPayload := map[string]interface{}{
        "system_prompt":    "Go Application",
        "user_input":       fmt.Sprintf("%v", input),
        "assistant_output": fmt.Sprintf("%v", result),
        "context":          map[string]string{"domain": context},
        "agents":           []string{},
    }

    outputResult, err := analyzeWithOrchestrator(orchestratorURL, outputPayload)
    if err != nil {
        return result, err
    }

    if outputResult.Decision.RiskScore >= DefaultBlockThreshold ||
        outputResult.Decision.Decision == "block" {
        return result, &EthicalException{
            Message:   "Output bloqueado",
            Decision:  outputResult.Decision.Decision,
            RiskScore: outputResult.Decision.RiskScore,
            Scope:     "output",
        }
    }

    return result, nil
}

func analyzeWithOrchestrator(baseURL string, payload map[string]interface{}) (*AnalysisResult, error) {
    jsonData, err := json.Marshal(payload)
    if err != nil {
        return nil, err
    }

    resp, err := http.Post(
        baseURL+"/analyze",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var result AnalysisResult
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }

    return &result, nil
}

// Uso
type HiringSystem struct{}

func (h *HiringSystem) recommendCandidateCore(info string) (string, error) {
    // Tu lógica
    return "Recomendación", nil
}

func (h *HiringSystem) RecommendCandidate(info string) (string, error) {
    return WithEthicalValidation(h.recommendCandidateCore, info, "hr")
}
```

---

## 4. Rust - Patrón Wrapper

```rust
// ethical_guard.rs
use reqwest;
use serde::{Deserialize, Serialize};
use std::error::Error;

const BLOCK_THRESHOLD: f64 = 0.65;

#[derive(Debug)]
pub struct EthicalException {
    pub message: String,
    pub decision: String,
    pub risk_score: f64,
    pub scope: String,
}

impl std::fmt::Display for EthicalException {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        write!(f, "{} (risk: {:.2}, scope: {})", 
               self.message, self.risk_score, self.scope)
    }
}

impl Error for EthicalException {}

#[derive(Serialize)]
struct AnalysisRequest {
    system_prompt: String,
    user_input: String,
    assistant_output: Option<String>,
    context: serde_json::Value,
    agents: Vec<String>,
}

#[derive(Deserialize)]
struct AnalysisResult {
    decision: Decision,
}

#[derive(Deserialize)]
struct Decision {
    decision: String,
    risk_score: f64,
}

/// Wrapper para validar éticamente cualquier función
pub async fn with_ethical_validation<F, I, O>(
    input: I,
    func: F,
    context: &str,
) -> Result<O, Box<dyn Error>>
where
    F: FnOnce(&I) -> Result<O, Box<dyn Error>>,
    I: ToString,
    O: ToString,
{
    let orchestrator_url = std::env::var("ORCHESTRATOR_URL")
        .unwrap_or_else(|_| "http://localhost:8000".to_string());
    
    let client = reqwest::Client::new();
    
    // 1. Validar INPUT
    let input_payload = AnalysisRequest {
        system_prompt: "Rust Application".to_string(),
        user_input: input.to_string(),
        assistant_output: None,
        context: serde_json::json!({"domain": context}),
        agents: vec![],
    };
    
    let input_result: AnalysisResult = client
        .post(format!("{}/analyze", orchestrator_url))
        .json(&input_payload)
        .send()
        .await?
        .json()
        .await?;
    
    if input_result.decision.risk_score >= BLOCK_THRESHOLD ||
       input_result.decision.decision == "block" {
        return Err(Box::new(EthicalException {
            message: "Input bloqueado".to_string(),
            decision: input_result.decision.decision,
            risk_score: input_result.decision.risk_score,
            scope: "input".to_string(),
        }));
    }
    
    // 2. Ejecutar función
    let result = func(&input)?;
    
    // 3. Validar OUTPUT
    let output_payload = AnalysisRequest {
        system_prompt: "Rust Application".to_string(),
        user_input: input.to_string(),
        assistant_output: Some(result.to_string()),
        context: serde_json::json!({"domain": context}),
        agents: vec![],
    };
    
    let output_result: AnalysisResult = client
        .post(format!("{}/analyze", orchestrator_url))
        .json(&output_payload)
        .send()
        .await?
        .json()
        .await?;
    
    if output_result.decision.risk_score >= BLOCK_THRESHOLD ||
       output_result.decision.decision == "block" {
        return Err(Box::new(EthicalException {
            message: "Output bloqueado".to_string(),
            decision: output_result.decision.decision,
            risk_score: output_result.decision.risk_score,
            scope: "output".to_string(),
        }));
    }
    
    Ok(result)
}

// Uso
struct HiringSystem;

impl HiringSystem {
    fn recommend_candidate_core(&self, info: &str) -> Result<String, Box<dyn Error>> {
        // Tu lógica
        Ok("Recomendación".to_string())
    }
    
    async fn recommend_candidate(&self, info: String) -> Result<String, Box<dyn Error>> {
        with_ethical_validation(
            info,
            |i| self.recommend_candidate_core(i),
            "hr"
        ).await
    }
}
```

---

## 5. PHP - Wrapper Manual

```php
<?php
// EthicalGuard.php

class EthicalException extends Exception {
    public string $decision;
    public float $riskScore;
    public string $scope;
    
    public function __construct($message, $decision, $riskScore, $scope) {
        parent::__construct($message);
        $this->decision = $decision;
        $this->riskScore = $riskScore;
        $this->scope = $scope;
    }
}

class EthicalGuard {
    private const ORCHESTRATOR_URL = 'http://localhost:8000';
    private const BLOCK_THRESHOLD = 0.65;
    
    /**
     * Valida éticamente cualquier callable
     */
    public static function withEthicalValidation(
        callable $function,
        $input,
        string $context = 'general'
    ) {
        // 1. Validar INPUT
        $inputPayload = [
            'system_prompt' => 'PHP Application',
            'user_input' => (string)$input,
            'context' => ['domain' => $context],
            'agents' => []
        ];
        
        $inputResult = self::analyzeWithOrchestrator($inputPayload);
        $inputRisk = $inputResult['decision']['risk_score'];
        $inputDecision = $inputResult['decision']['decision'];
        
        if ($inputRisk >= self::BLOCK_THRESHOLD || $inputDecision === 'block') {
            throw new EthicalException(
                "Input bloqueado: $inputRisk",
                $inputDecision,
                $inputRisk,
                'input'
            );
        }
        
        // 2. Ejecutar función
        $result = $function($input);
        
        // 3. Validar OUTPUT
        $outputPayload = [
            'system_prompt' => 'PHP Application',
            'user_input' => (string)$input,
            'assistant_output' => (string)$result,
            'context' => ['domain' => $context],
            'agents' => []
        ];
        
        $outputResult = self::analyzeWithOrchestrator($outputPayload);
        $outputRisk = $outputResult['decision']['risk_score'];
        $outputDecision = $outputResult['decision']['decision'];
        
        if ($outputRisk >= self::BLOCK_THRESHOLD || $outputDecision === 'block') {
            throw new EthicalException(
                "Output bloqueado: $outputRisk",
                $outputDecision,
                $outputRisk,
                'output'
            );
        }
        
        return $result;
    }
    
    private static function analyzeWithOrchestrator(array $payload): array {
        $ch = curl_init(self::ORCHESTRATOR_URL . '/analyze');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($payload));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
        
        $response = curl_exec($ch);
        curl_close($ch);
        
        return json_decode($response, true);
    }
}

// Uso
class HiringSystem {
    private function recommendCandidateCore(string $info): string {
        // Tu lógica
        return "Recomendación";
    }
    
    public function recommendCandidate(string $info): string {
        return EthicalGuard::withEthicalValidation(
            [$this, 'recommendCandidateCore'],
            $info,
            'hr'
        );
    }
}
?>
```

---

## Comparación de Patrones

| Lenguaje | Patrón | Sintaxis |
|----------|--------|----------|
| **Python** | Decorador nativo | `@ethical_guard()` |
| **TypeScript** | Decorador experimental | `@ethicalGuard()` |
| **Java** | Wrapper estático | `EthicalGuard.withValidation()` |
| **C#** | Extension method | `func.WithEthicalValidation()` |
| **Go** | Función genérica | `WithEthicalValidation(fn, input)` |
| **Rust** | Función wrapper | `with_ethical_validation(input, fn)` |
| **PHP** | Callable wrapper | `EthicalGuard::withValidation(fn)` |

---

## Patrón Universal (HTTP Directo)

**Para CUALQUIER lenguaje**, siempre puedes hacer:

```
1. POST /analyze con input → obtener risk_score
2. Si risk_score < 0.65 → ejecutar función
3. POST /analyze con input + output → obtener risk_score
4. Si risk_score < 0.65 → retornar resultado
5. Sino → lanzar error
```

Este enfoque funciona en **todos los lenguajes** que tengan un cliente HTTP.
