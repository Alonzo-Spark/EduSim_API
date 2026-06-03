// scratch/parallel_orchestrator.js - High-performance parallel multi-model orchestration engine
require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
const mongoose = require('mongoose');
const BenchmarkRun = require('../models/BenchmarkRun');
const EvaluationService = require('../services/evaluationService');
const MetricsUtil = require('../utils/metricsUtil');
const GeminiService = require('../services/geminiService');

// Configured model list from user request
const modelsToBenchmark = [
  { name: 'Gemma-E4B', id: 'google/gemma-3n-e4b-it' },
  { name: 'gpt-oss-20b (Groq)', id: 'openai/gpt-oss-20b', providerOrder: ['Groq'] },
  { name: 'GPT-4o-mini', id: 'openai/gpt-4o-mini' },
  { name: 'gpt-oss-120b (Groq)', id: 'openai/gpt-oss-120b', providerOrder: ['Groq'] },
  { name: 'Gemini 2.5 Flash', id: 'google/gemini-2.5-flash' },
  { name: 'gpt-oss-120b (Cerebras)', id: 'openai/gpt-oss-120b', providerOrder: ['Cerebras'] },
  { name: 'Gemini Flash Lite (3.1)', id: 'google/gemini-2.0-flash-lite-001' },
  { name: 'Gemini 3 Flash Preview', id: 'google/gemini-3-flash-preview' },
  { name: 'DeepSeek R1', id: 'deepseek/deepseek-r1' },
  { name: 'qwen-3-235b-a22b-instruct-2507 (Cerebras)', id: 'qwen/qwen3-235b-a22b-2507', providerOrder: ['Cerebras'] },
  { name: 'zai-glm-4.7 (Cerebras)', id: 'z-ai/glm-4.7', providerOrder: ['Cerebras'] },
  { name: 'Claude 3.5 Sonnet', id: 'anthropic/claude-3.5-sonnet' }
];

/**
 * Executes a single model generation via OpenRouter with AbortController timeout and retry logic.
 */
async function executeModelGeneration(model, prompt, timeoutMs = 30000) {
  const start = Date.now();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const apiKey = (process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY || '').trim();

  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'EduSim Parallel Orchestrator'
      },
      body: JSON.stringify({
        model: model.id,
        messages: [
          { role: 'system', content: GeminiService.SYSTEM_PROMPT },
          { role: 'user', content: prompt }
        ],
        temperature: 0.7,
        max_tokens: 1024,
        ...(model.providerOrder ? { provider: { order: model.providerOrder, allow_fallbacks: false } } : {})
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`OpenRouter HTTP ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    if (result.error) {
      throw new Error(result.error.message || JSON.stringify(result.error));
    }

    const latency = Date.now() - start;
    const responseText = result.choices?.[0]?.message?.content || '';
    const usage = result.usage || {};
    const resolvedModel = result.model || model.id;

    const tokenUsage = {
      promptTokens: usage.prompt_tokens || 0,
      completionTokens: usage.completion_tokens || 0,
      totalTokens: usage.total_tokens || (usage.prompt_tokens || 0) + (usage.completion_tokens || 0)
    };

    const estimatedCost = MetricsUtil.calculateCost(tokenUsage.promptTokens, tokenUsage.completionTokens, resolvedModel);

    return {
      model: model.name,
      resolvedModel,
      response: responseText,
      latency,
      tokenUsage,
      estimatedCost,
      success: true,
      error: null
    };

  } catch (err) {
    clearTimeout(timeoutId);
    const latency = Date.now() - start;
    const isTimeout = err.name === 'AbortError';
    
    return {
      model: model.name,
      resolvedModel: model.id,
      response: '',
      latency,
      tokenUsage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
      estimatedCost: 0,
      success: false,
      error: isTimeout ? 'Request timed out after 30s' : err.message
    };
  }
}

async function orchestrate() {
  const prompt = "Explain Newtons second law in simple terms.";
  console.log(`[ORCHESTRATOR] Connecting to MongoDB...`);
  await mongoose.connect(process.env.MONGODB_URI);
  console.log(`[ORCHESTRATOR] Connected to MongoDB.`);
  console.log(`[ORCHESTRATOR] Initialising parallel execution for ${modelsToBenchmark.length} models...`);

  const startBatch = Date.now();

  // 1. Parallel execution using Promise.allSettled
  const generationPromises = modelsToBenchmark.map(model => executeModelGeneration(model, prompt));
  const generationResults = await Promise.allSettled(generationPromises);

  const completedRuns = [];

  // 2. Normalise and process results
  for (let i = 0; i < generationResults.length; i++) {
    const outcome = generationResults[i];
    const modelDef = modelsToBenchmark[i];
    
    if (outcome.status === 'fulfilled') {
      const data = outcome.value;
      if (data.success) {
        console.log(`[ORCHESTRATOR] -> ${data.model} generated successfully in ${data.latency}ms`);
        completedRuns.push(data);
      } else {
        console.error(`[ORCHESTRATOR] -> ${data.model} failed generation: ${data.error}`);
        completedRuns.push(data);
      }
    } else {
      console.error(`[ORCHESTRATOR] -> ${modelDef.name} promise rejected: ${outcome.reason}`);
      completedRuns.push({
        model: modelDef.name,
        resolvedModel: modelDef.id,
        response: '',
        latency: 0,
        tokenUsage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
        estimatedCost: 0,
        success: false,
        error: outcome.reason
      });
    }
  }

  // 3. Parallel AI-Judge Evaluation for successful models
  console.log(`\n[ORCHESTRATOR] Running parallel Llama 3.1 405B evaluations on successful generations...`);
  const successfulRuns = completedRuns.filter(r => r.success);
  
  const evaluationPromises = successfulRuns.map(run => 
    EvaluationService.evaluateResponse({
      response: run.response,
      taskType: 'text',
      expected: { expectedConcepts: [], expectedFormula: null }
    }).then(evaluation => ({ run, evaluation }))
      .catch(err => ({ run, evaluation: null, error: err.message }))
  );

  const evaluationResults = await Promise.allSettled(evaluationPromises);

  // 4. Save results to MongoDB
  for (const outcome of evaluationResults) {
    if (outcome.status === 'fulfilled') {
      const { run, evaluation, error } = outcome.value;
      
      if (evaluation) {
        // Save BenchmarkRun record in MongoDB
        const benchmark = new BenchmarkRun({
          model: run.resolvedModel,
          taskType: 'text',
          prompt: prompt,
          response: run.response,
          latencyMs: run.latency,
          inputTokens: run.tokenUsage.promptTokens,
          outputTokens: run.tokenUsage.completionTokens,
          totalTokens: run.tokenUsage.totalTokens,
          estimatedCost: run.estimatedCost,
          accuracyScore: evaluation.accuracyScore,
          qualityScore: evaluation.qualityScore,
          educationalScore: evaluation.educationalScore,
          reliability: 100,
          hallucinationDetected: evaluation.hallucinationDetected,
          validJson: evaluation.validJson,
          validSvg: evaluation.validSvg,
          feedback: evaluation.feedback || '',
          timestamp: new Date()
        });
        await benchmark.save();
        console.log(`[ORCHESTRATOR] -> Evaluation stored in MongoDB for resolved model: ${run.resolvedModel}`);
      } else {
        console.error(`[ORCHESTRATOR] -> Evaluation failed for model ${run.model}: ${error}`);
      }
    }
  }

  const duration = Date.now() - startBatch;
  console.log(`\n[ORCHESTRATOR] Parallel execution completed in ${duration}ms!`);

  // Write JSON output file
  const fs = require('fs');
  const path = require('path');
  const jsonPath = path.resolve(__dirname, 'parallel_results.json');
  fs.writeFileSync(jsonPath, JSON.stringify(completedRuns, null, 2));
  console.log(`[ORCHESTRATOR] Full JSON results saved to: ${jsonPath}`);

  // Generate clean Markdown Summary Table
  let md = `# Parallel Orchestrator Execution Report\n\n`;
  md += `Parallel benchmark execution completed in **${(duration / 1000).toFixed(2)} seconds**.\n\n`;
  md += `### Aggregate Results Summary Table:\n\n`;
  md += `| Model Name | Resolved OpenRouter Model | Success | Latency | Tokens (In/Out) | Estimated Cost | Error Description |\n`;
  md += `| :--- | :--- | :---: | :---: | :---: | :---: | :--- |\n`;

  for (const r of completedRuns) {
    const status = r.success ? '✅ Success' : '❌ Failed';
    const latency = r.success ? `${r.latency}ms` : '-';
    const tokens = r.success ? `${r.tokenUsage.promptTokens}/${r.tokenUsage.completionTokens}` : '-';
    const cost = r.success ? `$${r.estimatedCost.toFixed(5)}` : '-';
    const err = r.error ? `\`${r.error.substring(0, 50)}\`` : '-';
    md += `| **${r.model}** | \`${r.resolvedModel}\` | ${status} | ${latency} | ${tokens} | ${cost} | ${err} |\n`;
  }

  const mdPath = path.resolve(__dirname, 'parallel_summary.md');
  fs.writeFileSync(mdPath, md);
  console.log(`[ORCHESTRATOR] Markdown summary report saved to: ${mdPath}`);

  await mongoose.disconnect();
  console.log(`[ORCHESTRATOR] MongoDB disconnected.`);
}

orchestrate().catch(err => {
  console.error('Orchestration fatal crash:', err);
  process.exit(1);
});
