/**
 * Ejemplos de uso del decorador ético en TypeScript
 */

import { ethicalGuard, withEthicalGuard, EthicalGuardException } from './ethical-decorator';

// ===== OPCIÓN 1: Decorador de Clase (TypeScript) =====

class HiringSystem {
    /**
     * Método decorado que valida automáticamente
     */
    @ethicalGuard({
        context: { domain: 'hr' },
        generateReport: true
    })
    async recommendCandidate(candidateInfo: string): Promise<string> {
        // Tu lógica aquí
        return `Recomiendo a Juan por ser el candidato más calificado`;
    }

    @ethicalGuard({
        context: { domain: 'hr' },
        blockThreshold: 0.5  // Más estricto
    })
    async makeFinalDecision(data: string): Promise<string> {
        return `Decisión basada en ${data}`;
    }
}

// Uso
async function testClassDecorator() {
    const system = new HiringSystem();

    try {
        const result = await system.recommendCandidate("Ana vs Juan");
        console.log('✅ Resultado:', result);
    } catch (error) {
        if (error instanceof EthicalGuardException) {
            console.error('❌ Bloqueado:', error.message);
            console.error('   Risk:', error.riskScore);
            console.error('   Scope:', error.scope);
        }
    }
}

// ===== OPCIÓN 2: Wrapper Funcional (JavaScript/TypeScript) =====

async function hiringDecision(candidateData: string): Promise<string> {
    // Tu lógica
    return `Decisión para ${candidateData}`;
}

// Envolver la función con validación ética
const ethicalHiringDecision = withEthicalGuard(
    hiringDecision,
    { context: { domain: 'hr' } }
);

async function testFunctionalWrapper() {
    try {
        const result = await ethicalHiringDecision('Candidato A');
        console.log('✅ Resultado:', result);
    } catch (error) {
        if (error instanceof EthicalGuardException) {
            console.error('❌ Bloqueado:', error.message);
        }
    }
}

// ===== OPCIÓN 3: JavaScript Vanilla (sin decoradores) =====

// Para JavaScript sin soporte de decoradores experimentales
async function creditApproval(applicantInfo) {
    return `Crédito aprobado para ${applicantInfo}`;
}

// Wrapper manual
async function ethicalCreditApproval(applicantInfo) {
    const orchestratorUrl = 'http://localhost:8000';

    // Validar input
    const inputResponse = await fetch(`${orchestratorUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            system_prompt: 'Sistema de aprobación de créditos',
            user_input: applicantInfo,
            context: { domain: 'finance' },
            agents: []
        })
    });

    const inputResult = await inputResponse.json();

    if (inputResult.decision.risk_score >= 0.65) {
        throw new Error(`Input bloqueado: ${inputResult.decision.risk_score}`);
    }

    // Ejecutar función
    const result = await creditApproval(applicantInfo);

    // Validar output
    const outputResponse = await fetch(`${orchestratorUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            system_prompt: 'Sistema de aprobación de créditos',
            user_input: applicantInfo,
            assistant_output: result,
            context: { domain: 'finance' },
            agents: []
        })
    });

    const outputResult = await outputResponse.json();

    if (outputResult.decision.risk_score >= 0.65) {
        throw new Error(`Output bloqueado: ${outputResult.decision.risk_score}`);
    }

    return result;
}

// ===== OPCIÓN 4: React Hook (para aplicaciones React) =====

// React Hook personalizado
function useEthicalGuard(options = {}) {
    const [isValidating, setIsValidating] = React.useState(false);
    const [error, setError] = React.useState(null);

    const validate = async (userInput, assistantOutput = null) => {
        setIsValidating(true);
        setError(null);

        try {
            const response = await fetch('http://localhost:8000/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    system_prompt: 'React Application',
                    user_input: userInput,
                    assistant_output: assistantOutput,
                    context: options.context || {},
                    agents: options.agents || []
                })
            });

            const result = await response.json();

            if (result.decision.risk_score >= (options.blockThreshold || 0.65)) {
                const error = new EthicalGuardException(
                    `Bloqueado: ${result.decision.decision}`,
                    result.decision.decision,
                    result.decision.risk_score,
                    assistantOutput ? 'output' : 'input'
                );
                setError(error);
                return { blocked: true, result };
            }

            return { blocked: false, result };
        } catch (err) {
            setError(err);
            return { blocked: true, error: err };
        } finally {
            setIsValidating(false);
        }
    };

    return { validate, isValidating, error };
}

// Uso en componente React
function ChatComponent() {
    const { validate, isValidating, error } = useEthicalGuard({
        context: { domain: 'chat' }
    });

    const handleSubmit = async (message) => {
        const { blocked, result } = await validate(message);

        if (blocked) {
            alert(`❌ Mensaje bloqueado: ${error.message}`);
            return;
        }

        // Continuar con tu lógica...
    };

    return <div>{/* tu UI */ } </div>;
}

export {
    testClassDecorator,
    testFunctionalWrapper,
    ethicalCreditApproval,
    useEthicalGuard
};
