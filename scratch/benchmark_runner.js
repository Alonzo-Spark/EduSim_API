// scratch/benchmark_runner.js - Premium Interactive CLI Benchmark Runner & Realtime Exporter
require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const mongoose = require('mongoose');

const config = require('../config');
const BenchmarkRun = require('../models/BenchmarkRun');
const EvaluationService = require('../services/evaluationService');
const MetricsUtil = require('../utils/metricsUtil');
const GeminiService = require('../services/geminiService');

// Flagship models list matching config.js
const targetModels = config.targetModels || [
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

// Target directories
const datasetDir = path.resolve(__dirname, '../benchmark_dataset');
const responsesDir = path.resolve(datasetDir, 'responses');
const judgeResponsesDir = path.resolve(datasetDir, 'judge_responses');
const mainCsvPath = path.resolve(datasetDir, 'benchmark_results.csv');
const failuresCsvPath = path.resolve(datasetDir, 'failures.csv');

// Create directories if not exists
fs.mkdirSync(datasetDir, { recursive: true });
fs.mkdirSync(responsesDir, { recursive: true });
fs.mkdirSync(judgeResponsesDir, { recursive: true });

// Initialize CSV Headers if file doesn't exist
const csvHeaders = [
  'question',
  'answer',
  'response_file',
  'model_name',
  'judge_model_name',
  'judge_score',
  'judge_input_token',
  'judge_output_token',
  'judge_total_token',
  'judge_latency',
  'judge_cost',
  'input_token',
  'output_token',
  'total_token',
  'latency',
  'cost'
];

if (!fs.existsSync(mainCsvPath)) {
  fs.writeFileSync(mainCsvPath, csvHeaders.join(','));
}

const failuresHeaders = ['question', 'answer', 'model_name', 'error', 'timestamp'];
if (!fs.existsSync(failuresCsvPath)) {
  fs.writeFileSync(failuresCsvPath, failuresHeaders.join(','));
}

/**
 * Escapes fields for writing clean CSV rows
 */
function toCSVRow(arr) {
  return arr.map(val => {
    if (val === null || val === undefined) return '';
    let str = String(val);
    if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
      str = '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
  }).join(',');
}

/**
 * Inspects existing benchmark results to determine the next contiguous question index
 */
function getNextQuestionIndex() {
  if (!fs.existsSync(mainCsvPath)) return 1;
  const content = fs.readFileSync(mainCsvPath, 'utf-8');
  const lines = content.split('\n');
  let maxIndex = 0;
  for (const line of lines) {
    const match = line.match(/responses\/q(\d+)_/);
    if (match) {
      const idx = parseInt(match[1]);
      if (idx > maxIndex) maxIndex = idx;
    }
  }
  return maxIndex + 1;
}

/**
 * Executes a single model generation via OpenRouter
 */
async function executeGeneration(model, promptText, expectedAnswer, category) {
  const start = Date.now();
  const apiKey = (process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY || '').trim();

  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'EduSim CLI Interactive Benchmarking'
      },
      body: JSON.stringify({
        model: model.id,
        messages: [
          { role: 'system', content: GeminiService.SYSTEM_PROMPT },
          { role: 'user', content: promptText }
        ],
        temperature: 0.7,
        max_tokens: 1024,
        ...(model.providerOrder ? { provider: { order: model.providerOrder, allow_fallbacks: false } } : {})
      })
    });

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

    // Call the evaluator judge (Llama 3.3 70B Instruct)
    const evaluation = await EvaluationService.evaluateResponse({
      response: responseText,
      taskType: category.toLowerCase().includes('json') ? 'json' : (category.toLowerCase().includes('svg') ? 'svg' : 'text'),
      expected: { expectedConcepts: expectedAnswer ? [expectedAnswer] : [], expectedFormula: null }
    });

    return {
      success: true,
      response: responseText,
      latency,
      tokenUsage,
      estimatedCost,
      evaluation,
      resolvedModel,
      error: null
    };

  } catch (err) {
    return {
      success: false,
      response: '',
      latency: Date.now() - start,
      tokenUsage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
      estimatedCost: 0,
      evaluation: { accuracyScore: 0, qualityScore: 0, educationalScore: 0, hallucinationDetected: false, validJson: false, validSvg: false, feedback: err.message },
      resolvedModel: model.id,
      error: err.message
    };
  }
}

/**
 * Wraps executeGeneration with automatic retries and exponential backoff
 */
async function executeGenerationWithRetry(model, promptText, expectedAnswer, category, maxAttempts = 3) {
  let attempt = 1;
  while (attempt <= maxAttempts) {
    if (attempt > 1) {
      console.log(`    ⚠️ Retry Attempt ${attempt}/${maxAttempts} for model ${model.name}...`);
    }
    const outcome = await executeGeneration(model, promptText, expectedAnswer, category);
    
    if (outcome.success) {
      return outcome;
    }

    console.error(`    ❌ Attempt ${attempt} failed: ${outcome.error}`);
    if (attempt < maxAttempts) {
      const backoff = 2000 * attempt;
      console.log(`    Retrying in ${backoff / 1000}s...`);
      await new Promise(r => setTimeout(r, backoff));
    }
    attempt++;
  }
  
  return {
    success: false,
    error: `Failed after ${maxAttempts} attempts.`
  };
}

async function main() {
  console.log(`================================================================`);
  console.log(`🌟 EDUSIM INTERACTIVE CLI BENCHMARK RUNNER`);
  console.log(`   - Connected Flagship Models: ${targetModels.length}`);
  console.log(`   - Auto-Retry Limit: 3 attempts with exponential backoff`);
  console.log(`   - Append Target: ${mainCsvPath}`);
  console.log(`================================================================\n`);

  // Connect to MongoDB
  console.log(`[DATABASE] Connecting to MongoDB...`);
  await mongoose.connect(process.env.MONGODB_URI);
  console.log(`[DATABASE] Connected successfully.\n`);

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const ask = (query) => new Promise(resolve => rl.question(query, resolve));

  while (true) {
    console.log(`----------------------------------------------------------------`);
    const prompt = await ask(`\n📝 Enter Physics Question (or type 'exit' to quit):\n> `);
    
    if (prompt.trim().toLowerCase() === 'exit') {
      console.log('\nExiting benchmark. Disconnecting database...');
      break;
    }

    if (prompt.trim() === '') {
      console.log('Question cannot be empty. Please try again.');
      continue;
    }

    const expectedAnswer = await ask(`💡 Enter Expected Answer / Keywords (optional, press Enter to skip):\n> `);
    const category = await ask(`🏷️ Enter Category / Task Type (optional, default: text):\n> `) || 'text';

    const questionIndex = getNextQuestionIndex();
    console.log(`\n🚀 Initialising evaluation for Question #${questionIndex} across all ${targetModels.length} models...`);

    const qStart = Date.now();
    let successes = 0;

    for (let mIdx = 0; mIdx < targetModels.length; mIdx++) {
      const model = targetModels[mIdx];
      console.log(`\n[${mIdx + 1}/${targetModels.length}] Evaluating Model: ${model.name}`);
      
      const outcome = await executeGenerationWithRetry(model, prompt, expectedAnswer, category);

      if (outcome.success) {
        successes++;
        console.log(`    ✅ SUCCESS! Accuracy: ${outcome.evaluation.accuracyScore}/10 | Quality: ${outcome.evaluation.qualityScore}/10 | Latency: ${(outcome.latency / 1000).toFixed(2)}s`);

        // Save BenchmarkRun in MongoDB
        const benchmark = new BenchmarkRun({
          model: outcome.resolvedModel,
          taskType: category,
          prompt: prompt,
          response: outcome.response || '<no response>',
          latencyMs: outcome.latency,
          inputTokens: outcome.tokenUsage.promptTokens,
          outputTokens: outcome.tokenUsage.completionTokens,
          totalTokens: outcome.tokenUsage.totalTokens,
          // Judge metrics
          judgeInputTokens: outcome.evaluation.judgeInputTokens || 0,
          judgeOutputTokens: outcome.evaluation.judgeOutputTokens || 0,
          judgeTotalTokens: outcome.evaluation.judgeTotalTokens || 0,
          judgeLatencyMs: outcome.evaluation.judgeLatencyMs || 0,
          judgeEstimatedCost: outcome.evaluation.judgeEstimatedCost || 0,
          estimatedCost: outcome.estimatedCost,
          accuracyScore: outcome.evaluation.accuracyScore,
          qualityScore: outcome.evaluation.qualityScore,
          educationalScore: outcome.evaluation.educationalScore,
          reliability: 100,
          hallucinationDetected: outcome.evaluation.hallucinationDetected,
          validJson: outcome.evaluation.validJson,
          validSvg: outcome.evaluation.validSvg,
          feedback: outcome.evaluation.feedback || '',
          timestamp: new Date()
        });
        await benchmark.save();

        // Determine appropriate extension
        let ext = 'md';
        if (category.toLowerCase().includes('json')) ext = 'json';
        else if (category.toLowerCase().includes('svg')) ext = 'svg';
        else if (outcome.response.trim().startsWith('{')) ext = 'json';
        else if (outcome.response.trim().startsWith('<svg')) ext = 'svg';

        const modelSafe = outcome.resolvedModel.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
        const responseFilename = `q${questionIndex}_${modelSafe}.${ext}`;
        const judgeFilename = `q${questionIndex}_${modelSafe}_judge.json`;

        // Save raw response file
        fs.writeFileSync(path.resolve(responsesDir, responseFilename), outcome.response);

        // Save detailed judge payload
        const judgePayload = {
          model_evaluated: outcome.resolvedModel,
          prompt: prompt,
          judge_model: config.evaluatorModel,
          scores: {
            accuracy: outcome.evaluation.accuracyScore,
            quality: outcome.evaluation.qualityScore,
            educational: outcome.evaluation.educationalScore
          },
          boolean_validations: {
            hallucination_detected: outcome.evaluation.hallucinationDetected,
            valid_json: outcome.evaluation.validJson,
            valid_svg: outcome.evaluation.validSvg
          },
          feedback: outcome.evaluation.feedback,
          token_usage: {
            input_tokens: outcome.evaluation.judgeInputTokens,
            output_tokens: outcome.evaluation.judgeOutputTokens,
            total_tokens: outcome.evaluation.judgeTotalTokens
          },
          latency_ms: outcome.evaluation.judgeLatencyMs,
          estimated_cost_usd: outcome.evaluation.judgeEstimatedCost,
          timestamp: new Date()
        };
        fs.writeFileSync(path.resolve(judgeResponsesDir, judgeFilename), JSON.stringify(judgePayload, null, 2));

        // Append to benchmark_results.csv
        const csvRow = toCSVRow([
          prompt,
          expectedAnswer || 'N/A',
          `responses/${responseFilename}`,
          outcome.resolvedModel,
          config.evaluatorModel,
          outcome.evaluation.accuracyScore != null ? outcome.evaluation.accuracyScore : '',
          outcome.evaluation.judgeInputTokens || 0,
          outcome.evaluation.judgeOutputTokens || 0,
          outcome.evaluation.judgeTotalTokens || 0,
          outcome.evaluation.judgeLatencyMs != null ? (outcome.evaluation.judgeLatencyMs / 1000).toFixed(2) : '0.00',
          outcome.evaluation.judgeEstimatedCost != null ? outcome.evaluation.judgeEstimatedCost.toFixed(6) : '0.000000',
          outcome.tokenUsage.promptTokens || 0,
          outcome.tokenUsage.completionTokens || 0,
          outcome.tokenUsage.totalTokens || 0,
          outcome.latency ? (outcome.latency / 1000).toFixed(2) : '0.00',
          outcome.estimatedCost != null ? outcome.estimatedCost.toFixed(6) : '0.000000'
        ]);
        fs.appendFileSync(mainCsvPath, '\n' + csvRow);

      } else {
        console.error(`    ❌ ALL RETRIES EXHAUSTED FOR: ${model.name}`);
        
        // Append to failures.csv
        const failuresRow = toCSVRow([
          prompt,
          expectedAnswer || 'N/A',
          model.name,
          outcome.error,
          new Date().toISOString()
        ]);
        fs.appendFileSync(failuresCsvPath, '\n' + failuresRow);
      }

      // Add a small 1s breather to prevent upstream rate-limit flooding
      await new Promise(r => setTimeout(r, 1000));
    }

    const qDuration = (Date.now() - qStart) / 1000;
    console.log(`\n✨ Finished Question #${questionIndex} in ${qDuration.toFixed(1)}s! (${successes}/${targetModels.length} models successful)`);
  }

  rl.close();
  await mongoose.disconnect();
  console.log(`[DATABASE] MongoDB disconnected. Goodbye!`);
  process.exit(0);
}

main().catch(err => {
  console.error('[FATAL CRASH]', err);
  process.exit(1);
});
