# Cliente JavaScript/TypeScript - Ethical Observability

Decoradores y helpers para integrar validación ética en aplicaciones JavaScript/TypeScript.

## Instalación

```bash
npm install
# o con el cliente existente:
# npm install node-fetch
```

## Características

✅ **Decorador TypeScript** (`@ethicalGuard`)  
✅ **Wrapper funcional** para JavaScript vanilla  
✅ **React Hook** (`useEthicalGuard`)  
✅ **Router automático** (usa menos tokens)  
✅ **Generación de reportes** markdown opcional  

---

## Uso

### 1. TypeScript con Decoradores

```typescript
import { ethicalGuard } from './ethical-decorator';

class HiringSystem {
  @ethicalGuard({ context: { domain: 'hr' } })
  async recommendCandidate(info: string): Promise<string> {
    return makeDecision(info);
  }
}

// Uso
const system = new HiringSystem();
try {
  const result = await system.recommendCandidate("Ana vs Juan");
} catch (error) {
  console.error('Bloqueado:', error.message);
}
```

**Configuración TypeScript** (`tsconfig.json`):
```json
{
  "compilerOptions": {
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  }
}
```

---

### 2. JavaScript Vanilla (sin decoradores)

```javascript
import { withEthicalGuard } from './ethical-decorator.js';

async function hiringDecision(data) {
  return `Decisión para ${data}`;
}

// Wrapper
const ethicalDecision = withEthicalGuard(hiringDecision, {
  context: { domain: 'hr' }
});

// Uso
try {
  const result = await ethicalDecision('Candidato A');
} catch (error) {
  console.error('Bloqueado:', error.message);
}
```

---

### 3. React Hook

```jsx
import { useEthicalGuard } from './examples';

function ChatApp() {
  const { validate, isValidating, error } = useEthicalGuard({
    context: { domain: 'chat' },
    blockThreshold: 0.65
  });

  const handleSend = async (message) => {
    const { blocked } = await validate(message);
    
    if (blocked) {
      alert(`❌ Bloqueado: ${error.message}`);
      return;
    }

    // Continuar...
  };

  return <ChatInput onSend={handleSend} />;
}
```

---

### 4. Llamada Directa HTTP (cualquier lenguaje)

```javascript
// Validar input
const response = await fetch('http://localhost:8000/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    system_prompt: "Mi aplicación",
    user_input: "Texto a validar",
    context: { domain: "hr" },
    agents: []  // Router automático
  })
});

const result = await response.json();

if (result.decision.risk_score >= 0.65) {
  throw new Error('Bloqueado por evaluación ética');
}

// Generar reporte (opcional)
const reportResp = await fetch('http://localhost:8000/report', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ analysis_result: result })
});

const report = await reportResp.json();
console.log(report.markdown);  // Informe en markdown
```

---

## Opciones del Decorador

```typescript
interface EthicalGuardOptions {
  orchestratorUrl?: string;      // Default: http://localhost:8000
  blockThreshold?: number;        // Default: 0.65
  warnThreshold?: number;         // Default: 0.35
  context?: Record<string, any>;  // Ej: { domain: 'hr' }
  agents?: string[];              // [] = router automático
  generateReport?: boolean;       // Default: false
  reportPath?: string;            // Default: auto-generado
}
```

---

## Thresholds

| Threshold | Valor | Acción |
|-----------|-------|--------|
| `block_threshold` | 0.65 | Bloquea si `risk_score >= 0.65` |
| `warn_threshold` | 0.35 | Warning si `0.35 <= risk_score < 0.65` |
| allow | < 0.35 | Pasa sin restricciones |

---

## Manejo de Excepciones

```typescript
try {
  const result = await decoratedFunction(input);
} catch (error) {
  if (error instanceof EthicalGuardException) {
    console.error('Decisión:', error.decision);      // 'block' o 'warn'
    console.error('Risk Score:', error.riskScore);   // 0.0 - 1.0
    console.error('Scope:', error.scope);            // 'input' o 'output'
    console.error('Detalles:', error.analysisResult);
  }
}
```

---

## Frameworks Soportados

| Framework | Método | Archivo |
|-----------|--------|---------|
| **TypeScript** | Decorador `@ethicalGuard` | `ethical-decorator.ts` |
| **JavaScript ES6+** | `withEthicalGuard(fn, opts)` | `ethical-decorator.ts` |
| **React** | Hook `useEthicalGuard()` | `examples.ts` |
| **Node.js** | HTTP directo | Cualquiera con `fetch` |
| **Next.js** | API Routes + decorador | `ethical-decorator.ts` |
| **Vue/Angular** | HTTP directo | - |

---

## Arquitectura

```
┌─────────────────┐
│  Tu Aplicación  │
│  (TS/JS/React)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ @ethicalGuard   │
│  Decorador      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ POST /analyze   │
│  Orquestador    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent Router   │ ← Selección automática
│  (determinista) │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌────────┐
│ Bias  │ │EU Act  │ ← Solo los necesarios
└───────┘ └────────┘
```

---

## Comparación con Python

| Característica | Python | TypeScript/JavaScript |
|----------------|--------|----------------------|
| **Decorador** | `@ethical_guard()` | `@ethicalGuard()` |
| **Sintaxis** | Nativo | Experimental (TS) |
| **Fallback** | No necesario | `withEthicalGuard()` wrapper |
| **React** | N/A | Hook `useEthicalGuard()` |
| **HTTP directo** | ✅ | ✅ |

---

## Ejemplos Completos

Ver `examples.ts` para:
- Decorador de clase
- Wrapper funcional
- Implementación manual
- React Hook

---

## Configuración

### Variables de Entorno

```bash
# .env
ORCHESTRATOR_URL=http://localhost:8000
```

### Next.js API Route

```typescript
// pages/api/check-ethics.ts
import { ethicalGuard } from '@/lib/ethical-decorator';

class EthicsAPI {
  @ethicalGuard({ context: { domain: 'api' } })
  async handleRequest(data: string) {
    return processData(data);
  }
}

export default async function handler(req, res) {
  const api = new EthicsAPI();
  try {
    const result = await api.handleRequest(req.body.data);
    res.json({ success: true, result });
  } catch (error) {
    res.status(400).json({ 
      success: false, 
      error: error.message 
    });
  }
}
```

---

## Migración desde Cliente Anterior

El cliente anterior (`index.mjs`) llamaba a agentes directamente.  
**Ahora usa el orquestador** para:
- ✅ Router automático (menos tokens)
- ✅ Generación de reportes
- ✅ Lógica de decisión centralizada

---

## Testing

```bash
# Ejecutar ejemplo
node examples.js

# O con TypeScript
npx ts-node examples.ts
```

---

## Licencia

MIT
