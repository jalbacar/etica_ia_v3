/**
 * Decorador ético para TypeScript/JavaScript
 * 
 * Usa el orquestador para validar inputs/outputs automáticamente.
 * 
 * Ejemplo:
 * ```typescript
 * import { ethicalGuard } from './ethical-decorator';
 * 
 * class HiringSystem {
 *   @ethicalGuard({ context: { domain: 'hr' } })
 *   async recommendCandidate(candidateInfo: string): Promise<string> {
 *     return "Recomiendo a Juan porque es hombre";  // ← Se bloqueará
 *   }
 * }
 * ```
 */

interface EthicalGuardOptions {
    orchestratorUrl?: string;
    blockThreshold?: number;
    warnThreshold?: number;
    context?: Record<string, any>;
    agents?: string[];
    generateReport?: boolean;
    reportPath?: string;
}

interface AnalysisResult {
    decision: {
        decision: 'allow' | 'warn' | 'block';
        risk_score: number;
    };
    [key: string]: any;
}

class EthicalGuardException extends Error {
    constructor(
        message: string,
        public decision: string,
        public riskScore: number,
        public scope: 'input' | 'output',
        public analysisResult?: AnalysisResult
    ) {
        super(message);
        this.name = 'EthicalGuardException';
    }
}

/**
 * Decorador de método para validación ética
 */
export function ethicalGuard(options: EthicalGuardOptions = {}) {
    const {
        orchestratorUrl = process.env.ORCHESTRATOR_URL || 'http://localhost:8000',
        blockThreshold = 0.65,
        warnThreshold = 0.35,
        context = {},
        agents = [],
        generateReport = false,
        reportPath,
    } = options;

    return function (
        target: any,
        propertyKey: string,
        descriptor: PropertyDescriptor
    ) {
        const originalMethod = descriptor.value;

        descriptor.value = async function (...args: any[]) {
            const systemPrompt = `Método: ${propertyKey}`;
            const userInput = String(args[0] || '');

            // 1. VALIDAR INPUT
            const inputAnalysis = await fetch(`${orchestratorUrl}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    system_prompt: systemPrompt,
                    user_input: userInput,
                    context,
                    agents,
                }),
            });

            const inputResult: AnalysisResult = await inputAnalysis.json();
            const inputDecision = inputResult.decision.decision;
            const inputRisk = inputResult.decision.risk_score;

            // Lógica de bloqueo mejorada
            const shouldBlockInput =
                inputDecision === 'block' ||
                (inputDecision === 'warn' && inputRisk >= blockThreshold);

            if (shouldBlockInput) {
                if (generateReport) {
                    await saveReport(orchestratorUrl, inputResult, reportPath, 'input');
                }
                throw new EthicalGuardException(
                    `🛑 Input bloqueado (risk: ${inputRisk.toFixed(2)}, decision: ${inputDecision})`,
                    inputDecision,
                    inputRisk,
                    'input',
                    inputResult
                );
            }

            if (inputRisk >= warnThreshold && !shouldBlockInput) {
                console.warn(`⚠️  Warning: Input con riesgo medio (score: ${inputRisk.toFixed(2)})`);
            }

            // 2. EJECUTAR MÉTODO ORIGINAL
            const result = await originalMethod.apply(this, args);

            // 3. VALIDAR OUTPUT
            const outputAnalysis = await fetch(`${orchestratorUrl}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    system_prompt: systemPrompt,
                    user_input: userInput,
                    assistant_output: String(result),
                    context,
                    agents,
                }),
            });

            const outputResult: AnalysisResult = await outputAnalysis.json();
            const outputDecision = outputResult.decision.decision;
            const outputRisk = outputResult.decision.risk_score;

            const shouldBlockOutput =
                outputDecision === 'block' ||
                (outputDecision === 'warn' && outputRisk >= blockThreshold);

            if (shouldBlockOutput) {
                if (generateReport) {
                    await saveReport(orchestratorUrl, outputResult, reportPath, 'output');
                }
                throw new EthicalGuardException(
                    `🛑 Output bloqueado (risk: ${outputRisk.toFixed(2)}, decision: ${outputDecision})`,
                    outputDecision,
                    outputRisk,
                    'output',
                    outputResult
                );
            }

            if (outputRisk >= warnThreshold && !shouldBlockOutput) {
                console.warn(`⚠️  Warning: Output con riesgo medio (score: ${outputRisk.toFixed(2)})`);
            }

            // Generar reporte si está habilitado y todo OK
            if (generateReport) {
                await saveReport(orchestratorUrl, outputResult, reportPath, 'success');
            }

            return result;
        };

        return descriptor;
    };
}

/**
 * Helper para guardar reportes
 */
async function saveReport(
    orchestratorUrl: string,
    analysisResult: AnalysisResult,
    reportPath: string | undefined,
    status: string
): Promise<void> {
    try {
        const reportResponse = await fetch(`${orchestratorUrl}/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ analysis_result: analysisResult }),
        });

        const reportData = await reportResponse.json();

        const finalPath =
            reportPath || `ethical_report_${status}_${Date.now()}.md`;

        // Node.js
        if (typeof require !== 'undefined') {
            const fs = require('fs');
            fs.writeFileSync(finalPath, reportData.markdown);
            console.log(`📄 Reporte guardado: ${finalPath}`);
        }
    } catch (error) {
        console.error('⚠️  Error guardando reporte:', error);
    }
}

/**
 * Alternativa funcional (sin decorador) para JavaScript vanilla
 */
export async function withEthicalGuard<T>(
    fn: (...args: any[]) => Promise<T>,
    options: EthicalGuardOptions = {}
): Promise<T> {
    const {
        orchestratorUrl = 'http://localhost:8000',
        blockThreshold = 0.65,
        warnThreshold = 0.35,
        context = {},
        agents = [],
    } = options;

    return async (...args: any[]): Promise<T> => {
        const userInput = String(args[0] || '');

        // Validar input
        const inputAnalysis = await fetch(`${orchestratorUrl}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                system_prompt: fn.name,
                user_input: userInput,
                context,
                agents,
            }),
        });

        const inputResult = await inputAnalysis.json();
        if (inputResult.decision.risk_score >= blockThreshold) {
            throw new EthicalGuardException(
                `Input bloqueado: ${inputResult.decision.risk_score}`,
                inputResult.decision.decision,
                inputResult.decision.risk_score,
                'input'
            );
        }

        // Ejecutar función
        const result = await fn(...args);

        // Validar output
        const outputAnalysis = await fetch(`${orchestratorUrl}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                system_prompt: fn.name,
                user_input: userInput,
                assistant_output: String(result),
                context,
                agents,
            }),
        });

        const outputResult = await outputAnalysis.json();
        if (outputResult.decision.risk_score >= blockThreshold) {
            throw new EthicalGuardException(
                `Output bloqueado: ${outputResult.decision.risk_score}`,
                outputResult.decision.decision,
                outputResult.decision.risk_score,
                'output'
            );
        }

        return result;
    };
}

export { EthicalGuardException };
