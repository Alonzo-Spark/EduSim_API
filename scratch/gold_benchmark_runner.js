// scratch/gold_benchmark_runner.js - Production-Grade resiliant LLM Evaluation Pipeline against Gold Dataset
require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
const fs = require('fs');
const path = require('path');
const mongoose = require('mongoose');

const config = require('../config');
const BenchmarkRun = require('../models/BenchmarkRun');
const MetricsUtil = require('../utils/metricsUtil');
const GeminiService = require('../services/geminiService');

// Flagship target models configured inconfig.js
const targetModels = config.targetModels || [
  { name: 'Gemma-E4B', id: 'google/gemma-3n-e4b-it' },
  { name: 'GPT-4o-mini', id: 'openai/gpt-4o-mini' },
  { name: 'Gemini 2.5 Flash', id: 'google/gemini-2.5-flash' },
  { name: 'Gemini Flash Lite (3.1)', id: 'google/gemini-2.0-flash-lite-001' },
  { name: 'Gemini 3 Flash Preview', id: 'google/gemini-3-flash-preview' },
  { name: 'DeepSeek R1', id: 'deepseek/deepseek-r1' },
  { name: 'Claude 3.5 Sonnet', id: 'anthropic/claude-sonnet-4.6' }
];

// Target directories and file paths
const datasetDir = path.resolve(__dirname, '../benchmark_dataset');
const responsesDir = path.resolve(datasetDir, 'responses');
const judgeResponsesDir = path.resolve(datasetDir, 'judge_responses');
const resultsCsvPath = path.resolve(datasetDir, 'benchmark_results.csv');
const failuresCsvPath = path.resolve(datasetDir, 'failures.csv');
const checkpointPath = path.resolve(datasetDir, 'checkpoint.json');
const goldDatasetCsvPath = path.resolve(__dirname, '../dataset/gold_dataset.csv');

// Create directories if they do not exist
fs.mkdirSync(datasetDir, { recursive: true });
fs.mkdirSync(responsesDir, { recursive: true });
fs.mkdirSync(judgeResponsesDir, { recursive: true });

// Concurrency and timeout configuration (5 minutes timeout for full deep reasoning capability)
const CONCURRENCY_LIMIT = 3; 
const REQUEST_TIMEOUT_MS = 300000;

// CSV Headers matching BOTH list definitions perfectly
const csvHeaders = [
  'question_id',
  'question',
  'gold_answer',
  'model_name',
  'model name',
  'response',
  'accuracy_score',
  'quality_score',
  'educational_score',
  'hallucination_detected',
  'valid_json',
  'valid_svg',
  'latency_ms',
  'prompt_tokens',
  'completion_tokens',
  'total_tokens',
  'retry_count',
  'retries',
  'cost_usd',
  'success',
  'error',
  'timestamp',
  'judge_feedback',
  'judge_model_name',
  'judge model name',
  'judge_score',
  'judge score',
  'judge_input_token',
  'judge input token and output token',
  'judge_output_token',
  'judge_total_token',
  'judge total token',
  'judge_latency',
  'judge latency',
  'judge_cost',
  'judeg cost',
  'input token',
  'output token',
  'total token',
  'latency',
  'cost'
];

let needFreshHeaders = true;
if (fs.existsSync(resultsCsvPath)) {
  try {
    const firstLine = fs.readFileSync(resultsCsvPath, 'utf8').split('\n')[0].trim();
    if (firstLine === csvHeaders.join(',')) {
      needFreshHeaders = false;
    }
  } catch (e) {
    needFreshHeaders = true;
  }
}

const failuresHeaders = ['question_id', 'question', 'gold_answer', 'model_name', 'error', 'timestamp'];

if (needFreshHeaders) {
  console.log('[PIPELINE] Initialising clean benchmark_results.csv with production headers...');
  fs.writeFileSync(resultsCsvPath, csvHeaders.join(',') + '\n');
  fs.writeFileSync(failuresCsvPath, failuresHeaders.join(',') + '\n');
  if (fs.existsSync(checkpointPath)) {
    try { fs.unlinkSync(checkpointPath); } catch (_) {}
  }
}


/**
 * Robust CSV parser for multi-line quoted RFC 4180 CSV formats
 */
function parseRFC4180CSV(content) {
  const records = [];
  let row = [];
  let field = '';
  let inQuotes = false;
  
  for (let i = 0; i < content.length; i++) {
    const char = content[i];
    const nextChar = content[i + 1];
    
    if (inQuotes) {
      if (char === '"') {
        if (nextChar === '"') {
          field += '"';
          i++; // skip next quote
        } else {
          inQuotes = false;
        }
      } else {
        field += char;
      }
    } else {
      if (char === '"') {
        inQuotes = true;
      } else if (char === ',') {
        row.push(field);
        field = '';
      } else if (char === '\n' || char === '\r') {
        if (char === '\r' && nextChar === '\n') {
          i++; // skip \n
        }
        row.push(field);
        if (row.length > 1 || row[0] !== '') {
          records.push(row);
        }
        row = [];
        field = '';
      } else {
        field += char;
      }
    }
  }
  
  if (field !== '' || row.length > 0) {
    row.push(field);
    records.push(row);
  }
  
  return records;
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
 * Native controlled-concurrency promise pool mapper
 */
async function mapLimit(limit, array, fn) {
  const results = [];
  const executing = new Set();
  for (const item of array) {
    const p = Promise.resolve().then(() => fn(item));
    results.push(p);
    executing.add(p);
    const clean = () => executing.delete(p);
    p.then(clean, clean);
    if (executing.size >= limit) {
      await Promise.race(executing);
    }
  }
  return Promise.allSettled(results);
}

/**
 * Asynchronous, EBUSY-lock resilient append helper
 */
async function safeAppendFileAsync(filePath, content, retries = 5, delay = 500) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      fs.appendFileSync(filePath, content);
      return;
    } catch (err) {
      if (err.code === 'EBUSY' && attempt < retries) {
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw err;
    }
  }
}

/**
 * Asynchronous, EBUSY-lock resilient write helper
 */
async function safeWriteFileAsync(filePath, content, retries = 5, delay = 500) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      fs.writeFileSync(filePath, content);
      return;
    } catch (err) {
      if (err.code === 'EBUSY' && attempt < retries) {
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw err;
    }
  }
}


/**
 * Executes a single model generation via OpenRouter with AbortController timeout and exponential retries
 */
async function executeWithRetry(model, promptText, category, maxAttempts = 3) {
  const apiKey = (process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY || '').trim();
  
  let attempt = 1;
  while (attempt <= maxAttempts) {
    const start = Date.now();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    
    try {
      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
          'HTTP-Referer': 'http://localhost:5000',
          'X-Title': 'EduSim Golden Benchmarking'
        },
          body: JSON.stringify({
            model: model.id,
            messages: [
              { role: 'system', content: GeminiService.SYSTEM_PROMPT },
              { role: 'user', content: promptText }
            ],
            temperature: 0.7,
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
      if (!responseText.trim()) {
        throw new Error('Completed with an empty response');
      }

      const usage = result.usage || {};
      const resolvedModel = result.model || model.id;

      const tokenUsage = {
        promptTokens: usage.prompt_tokens || 0,
        completionTokens: usage.completion_tokens || 0,
        totalTokens: usage.total_tokens || (usage.prompt_tokens || 0) + (usage.completion_tokens || 0)
      };

      const estimatedCost = MetricsUtil.calculateCost(tokenUsage.promptTokens, tokenUsage.completionTokens, resolvedModel);

      return {
        success: true,
        response: responseText,
        latency,
        tokenUsage,
        estimatedCost,
        resolvedModel,
        retryCount: attempt - 1,
        error: null
      };

    } catch (err) {
      clearTimeout(timeoutId);
      const isTimeout = err.name === 'AbortError';
      const errMsg = isTimeout ? 'Request timed out after 30s' : err.message;
      
      console.warn(`      ⚠️ Model ${model.name} Attempt ${attempt} failed: ${errMsg}`);
      
      if (attempt < maxAttempts) {
        const backoff = Math.min(1000 * Math.pow(2, attempt), 10000);
        await new Promise(r => setTimeout(r, backoff));
        attempt++;
      } else {
        return {
          success: false,
          response: '',
          latency: Date.now() - start,
          tokenUsage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
          estimatedCost: 0,
          resolvedModel: model.id,
          retryCount: attempt - 1,
          error: errMsg
        };
      }
    }
  }
}

/**
 * Custom AI Judge Evaluator comparing candidate response to gold reference answer
 */
async function evaluateWithGoldReference(question, goldAnswer, response, category) {
  const apiKey = (process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY || '').trim();
  const evaluatorModel = config.evaluatorModel || 'meta-llama/llama-3.3-70b-instruct';
  
  const judgePrompt = `You are an expert AI evaluator for educational physics and science responses.

You are evaluating a candidate response against a high-quality reference "Gold Answer".

Original Question:
"${question}"

Gold Reference Answer:
"${goldAnswer}"

Candidate Response to Evaluate:
"${response}"

Task Category:
"${category}"

Please evaluate the candidate response based on the following three rubrics on a scale of 0 to 10:

1. accuracyScore: Focus on conceptual correctness, formula correctness, semantic alignment with the gold reference answer, and factual accuracy.
2. qualityScore: Focus on layout formatting, structured readability, and overall quality of presentation.
3. educationalScore: Focus on beginner-friendliness, pedagogical effectiveness, and clarity of teaching.

Also determine:
- "hallucinationDetected" (true/false): Are there any fabricated concepts, fake formulas, incorrect physics claims, or unsupported reasoning?
- "validJson" (true/false): If the category is "json", is the response a valid, parseable JSON object? (Otherwise false)
- "validSvg" (true/false): If the category is "svg", is the response a valid SVG XML string? (Otherwise false)

CRITICAL FEEDBACK RULE:
If ANY score (accuracyScore, qualityScore, or educationalScore) is less than 7, you MUST write highly detailed, actionable feedback detailing exactly what failed, why it failed, what concepts/equations were missing, where formatting was poor, or what hallucinations occurred.

Respond ONLY with a valid, parseable JSON object containing exactly the keys:
{
  "accuracyScore": number,
  "qualityScore": number,
  "educationalScore": number,
  "hallucinationDetected": boolean,
  "validJson": boolean,
  "validSvg": boolean,
  "feedback": "string"
}

Return ONLY raw JSON. Do not include markdown code fences or conversational prefix/suffix prose.`;

  const start = Date.now();
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'EduSim Golden Benchmarking Evaluator'
      },
      body: JSON.stringify({
        model: evaluatorModel,
        messages: [{ role: 'user', content: judgePrompt }],
        temperature: 0.1,
        max_tokens: 1024
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      throw new Error(`Judge HTTP error ${res.status}`);
    }

    const data = await res.json();
    if (data.error) {
      throw new Error(data.error.message || JSON.stringify(data.error));
    }

    const text = data.choices?.[0]?.message?.content || '';
    const usage = data.usage || {};
    
    // Clean and Parse JSON safely
    let cleaned = text.trim();
    if (cleaned.includes('```')) {
      const matches = cleaned.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
      if (matches && matches[1]) {
        cleaned = matches[1].trim();
      }
    }
    const firstBrace = cleaned.indexOf('{');
    const lastBrace = cleaned.lastIndexOf('}');
    if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
      cleaned = cleaned.substring(firstBrace, lastBrace + 1);
    }

    const parsed = JSON.parse(cleaned);
    const latency = Date.now() - start;

    const tokenUsage = {
      promptTokens: usage.prompt_tokens || 0,
      completionTokens: usage.completion_tokens || 0,
      totalTokens: usage.total_tokens || (usage.prompt_tokens || 0) + (usage.completion_tokens || 0)
    };

    // Llama-3.3 pricing fallback: $0.60 per 1M input / $2.40 per 1M output
    const estimatedCost = tokenUsage.promptTokens * 0.00000060 + tokenUsage.completionTokens * 0.00000240;

    return {
      success: true,
      scores: parsed,
      latency,
      tokenUsage,
      estimatedCost,
      judgeModel: evaluatorModel,
      error: null
    };

  } catch (err) {
    clearTimeout(timeoutId);
    return {
      success: false,
      scores: {
        accuracyScore: 0,
        qualityScore: 0,
        educationalScore: 0,
        hallucinationDetected: false,
        validJson: false,
        validSvg: false,
        feedback: `Judge evaluation failed: ${err.message}`
      },
      latency: Date.now() - start,
      tokenUsage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
      estimatedCost: 0,
      judgeModel: evaluatorModel,
      error: err.message
    };
  }
}

/**
 * Re-reads results file to dynamically generate global leaderboard and markdown summary
 */
async function rebuildLeaderboard() {
  if (!fs.existsSync(resultsCsvPath)) return;
  const content = fs.readFileSync(resultsCsvPath, 'utf8');
  const lines = parseRFC4180CSV(content);
  if (lines.length <= 1) return;
  
  const headers = lines[0];
  const modelIdx = headers.indexOf('model_name');
  const accIdx = headers.indexOf('accuracy_score');
  const qualIdx = headers.indexOf('quality_score');
  const eduIdx = headers.indexOf('educational_score');
  const latencyIdx = headers.indexOf('latency_ms');
  const costIdx = headers.indexOf('cost_usd');
  const successIdx = headers.indexOf('success');
  
  const modelStats = {};
  
  for (let i = 1; i < lines.length; i++) {
    const row = lines[i];
    if (row.length < headers.length) continue;
    const model = row[modelIdx];
    if (!model) continue;
    
    if (!modelStats[model]) {
      modelStats[model] = {
        model,
        accuracySum: 0,
        qualitySum: 0,
        educationalSum: 0,
        latencySum: 0,
        costSum: 0,
        successCount: 0,
        totalCount: 0
      };
    }
    
    const success = row[successIdx] === 'true';
    modelStats[model].totalCount++;
    
    if (success) {
      modelStats[model].successCount++;
      modelStats[model].accuracySum += parseFloat(row[accIdx] || 0);
      modelStats[model].qualitySum += parseFloat(row[qualIdx] || 0);
      modelStats[model].educationalSum += parseFloat(row[eduIdx] || 0);
      modelStats[model].latencySum += parseFloat(row[latencyIdx] || 0);
      modelStats[model].costSum += parseFloat(row[costIdx] || 0);
    }
  }
  
  const statsList = Object.values(modelStats).map(s => {
    const count = s.successCount || 1;
    return {
      model: s.model,
      avgAccuracy: (s.accuracySum / count).toFixed(2),
      avgQuality: (s.qualitySum / count).toFixed(2),
      avgEducational: (s.educationalSum / count).toFixed(2),
      avgScore: ((s.accuracySum + s.qualitySum + s.educationalSum) / (3 * count)).toFixed(2),
      avgLatencyMs: (s.latencySum / count).toFixed(0),
      totalCostUsd: s.costSum.toFixed(6),
      successRate: ((s.successCount / s.totalCount) * 100).toFixed(1) + '%'
    };
  });
  
  statsList.sort((a, b) => parseFloat(b.avgScore) - parseFloat(a.avgScore));
  
  // Write leaderboard.csv
  const leaderboardHeaders = ['model', 'avgAccuracy', 'avgQuality', 'avgEducational', 'avgScore', 'avgLatencyMs', 'totalCostUsd', 'successRate'];
  let csvContent = leaderboardHeaders.join(',') + '\n';
  for (const s of statsList) {
    csvContent += toCSVRow([
      s.model,
      s.avgAccuracy,
      s.avgQuality,
      s.avgEducational,
      s.avgScore,
      s.avgLatencyMs,
      s.totalCostUsd,
      s.successRate
    ]) + '\n';
  }
  await safeWriteFileAsync(path.resolve(datasetDir, 'leaderboard.csv'), csvContent);
  
  // Write parallel_summary.md
  let mdContent = `# EduSim Golden Dataset LLM Leaderboard\n\n`;
  mdContent += `Generated on: ${new Date().toLocaleString()}\n\n`;
  mdContent += `### Model Performance Summary:\n\n`;
  mdContent += `| Rank | Model Name | Avg Score | Avg Accuracy | Avg Quality | Avg Educational | Avg Latency | Total Cost (USD) | Success Rate |\n`;
  mdContent += `| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n`;
  for (let i = 0; i < statsList.length; i++) {
    const s = statsList[i];
    mdContent += `| **${i + 1}** | **${s.model}** | \`${s.avgScore}\` | ${s.avgAccuracy} | ${s.avgQuality} | ${s.avgEducational} | ${s.avgLatencyMs}ms | $${s.totalCostUsd} | ${s.successRate} |\n`;
  }
  await safeWriteFileAsync(path.resolve(datasetDir, 'parallel_summary.md'), mdContent);
}

/**
 * Main Orchestration Pipeline Loop
 */
async function main() {
  console.log(`================================================================`);
  console.log(`🚀 EDUSIM GOLDEN DATASET AUTOMATED LLM EVALUATION INFRASTRUCTURE`);
  console.log(`================================================================`);

  // Verify gold_dataset.csv presence
  if (!fs.existsSync(goldDatasetCsvPath)) {
    console.error(`❌ Gold Dataset NOT found at: ${goldDatasetCsvPath}`);
    process.exit(1);
  }

  // Load and parse CSV
  console.log(`[DATASET] Loading gold_dataset.csv...`);
  const fileContent = fs.readFileSync(goldDatasetCsvPath, 'utf8');
  const records = parseRFC4180CSV(fileContent);
  
  if (records.length <= 1) {
    console.error(`❌ Empty or invalid CSV records in: ${goldDatasetCsvPath}`);
    process.exit(1);
  }

  const headers = records[0];
  const qIdIdx = headers.indexOf('id');
  const qIdx = headers.indexOf('question');
  const rIdx = headers.indexOf('response');
  const codeIdx = headers.indexOf('call_code');

  const questions = [];
  for (let i = 1; i < records.length; i++) {
    const row = records[i];
    if (row.length < headers.length) continue;
    const qId = parseInt(row[qIdIdx]);
    const questionText = row[qIdx]?.trim();
    const goldAnswer = row[rIdx]?.trim();
    const callCode = row[codeIdx]?.trim();
    
    if (qId && questionText && goldAnswer) {
      // Determine category constraints
      let category = 'text';
      if (questionText.toLowerCase().includes('json') || goldAnswer.toLowerCase().includes('json') || (callCode && callCode.toLowerCase().includes('json'))) {
        category = 'json';
      } else if (questionText.toLowerCase().includes('svg') || goldAnswer.toLowerCase().includes('svg') || (callCode && callCode.toLowerCase().includes('svg'))) {
        category = 'svg';
      }
      
      questions.push({
        id: qId,
        question: questionText,
        goldAnswer,
        category,
        subject: 'physics'
      });
    }
  }

  console.log(`[DATASET] Parsed ${questions.length} golden questions successfully.`);

  // Connect to MongoDB
  console.log(`[DATABASE] Connecting to MongoDB...`);
  await mongoose.connect(process.env.MONGODB_URI);
  console.log(`[DATABASE] Connected to database.\n`);

  // Read checkpoint
  let lastCompletedId = 0;
  if (fs.existsSync(checkpointPath)) {
    try {
      const cp = JSON.parse(fs.readFileSync(checkpointPath, 'utf8'));
      lastCompletedId = cp.lastCompletedQuestionId || 0;
      console.log(`[CHECKPOINT] Resuming from Question ID > ${lastCompletedId}`);
    } catch (e) {
      console.warn(`[CHECKPOINT] Warning: failed to parse checkpoint.json. Starting fresh.`);
    }
  }

  // Filter remaining questions
  const remainingQuestions = questions.filter(q => q.id > lastCompletedId);
  console.log(`[PIPELINE] Remaining Questions to process: ${remainingQuestions.length}/${questions.length}\n`);

  // Process remaining questions
  for (let i = 0; i < remainingQuestions.length; i++) {
    const q = remainingQuestions[i];
    console.log(`----------------------------------------------------------------`);
    console.log(`🔹 QUESTION [${i + 1}/${remainingQuestions.length}] (ID: ${q.id}) | Category: ${q.category.toUpperCase()}`);
    console.log(`   Prompt: "${q.question.substring(0, 75)}${q.question.length > 75 ? '...' : ''}"`);
    console.log(`----------------------------------------------------------------`);

    // STEP 2: Concurrently generate candidate responses across all target models with limit
    console.log(`👉 Step 1: Dispatching candidate response generations concurrently...`);
    const genOutcomes = [];
    
    await mapLimit(CONCURRENCY_LIMIT, targetModels, async (model) => {
      console.log(`   [GENERATOR] Calling model: ${model.name}...`);
      const outcome = await executeWithRetry(model, q.question, q.category);
      genOutcomes.push({ model, outcome });
    });

    // STEP 3: Concurrently evaluate successful candidate responses with AI-Judge
    console.log(`👉 Step 2: Triggering AI-Judge evaluations concurrently...`);
    const finalRuns = [];

    await mapLimit(CONCURRENCY_LIMIT, genOutcomes, async (item) => {
      const { model, outcome } = item;
      
      if (outcome.success) {
        console.log(`   [JUDGE] Evaluating response for ${model.name}...`);
        const evaluation = await evaluateWithGoldReference(q.question, q.goldAnswer, outcome.response, q.category);
        
        finalRuns.push({
          model,
          outcome,
          evaluation
        });
      } else {
        // Record terminal failure
        console.error(`   ❌ [FAILURE] All retries exhausted for ${model.name}: ${outcome.error}`);
        
        // Append failure to failures.csv
        const failRow = toCSVRow([
          q.id,
          q.question,
          q.goldAnswer,
          model.name,
          outcome.error,
          new Date().toISOString()
        ]);
        fs.appendFileSync(failuresCsvPath, failRow + '\n');
        
        finalRuns.push({
          model,
          outcome,
          evaluation: {
            success: false,
            scores: {
              accuracyScore: 0,
              qualityScore: 0,
              educationalScore: 0,
              hallucinationDetected: false,
              validJson: false,
              validSvg: false,
              feedback: `Model generation failed: ${outcome.error}`
            },
            latency: 0,
            tokenUsage: { promptTokens: 0, completionTokens: 0, totalTokens: 0 },
            estimatedCost: 0,
            judgeModel: 'N/A'
          }
        });
      }
    });

    // STEP 4: Persist, export, and record metrics
    console.log(`👉 Step 3: Saving metrics, database syncing, and file exporting...`);
    for (const run of finalRuns) {
      const { model, outcome, evaluation } = run;
      const scores = evaluation.scores;
      const isOk = outcome.success && evaluation.success;
      
      // Determine file extension
      let ext = 'txt';
      if (q.category === 'json') ext = 'json';
      else if (q.category === 'svg') ext = 'svg';

      const modelSafe = model.name.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
      const responseFilename = `q${q.id}_${modelSafe}.${ext}`;
      const judgeFilename = `q${q.id}_${modelSafe}_judge.json`;

      // Export raw response file (if successful)
      if (outcome.success) {
        fs.writeFileSync(path.resolve(responsesDir, responseFilename), outcome.response);
      }

      // Export detailed judge JSON dump
      const judgePayload = {
        model_evaluated: model.name,
        question_id: q.id,
        question: q.question,
        gold_answer: q.goldAnswer,
        candidate_response: outcome.response || '<failed>',
        judge_model: evaluation.judgeModel || 'meta-llama/llama-3.3-70b-instruct',
        scores: {
          accuracy: scores.accuracyScore,
          quality: scores.qualityScore,
          educational: scores.educationalScore,
          overall_average: ((scores.accuracyScore + scores.qualityScore + scores.educationalScore) / 3).toFixed(2)
        },
        boolean_validations: {
          hallucination_detected: scores.hallucinationDetected,
          valid_json: scores.validJson,
          valid_svg: scores.validSvg
        },
        feedback: scores.feedback,
        candidate_token_usage: outcome.tokenUsage,
        candidate_latency_ms: outcome.latency,
        candidate_cost_usd: outcome.estimatedCost,
        judge_token_usage: evaluation.tokenUsage,
        judge_latency_ms: evaluation.latency,
        judge_cost_usd: evaluation.estimatedCost,
        retry_count: outcome.retryCount,
        success: isOk,
        error: outcome.error || evaluation.error,
        timestamp: new Date().toISOString()
      };
      fs.writeFileSync(path.resolve(judgeResponsesDir, judgeFilename), JSON.stringify(judgePayload, null, 2));

      // Save Mongoose Record to MongoDB (if generation was successful)
      if (outcome.success) {
        try {
          const benchmark = new BenchmarkRun({
            model: outcome.resolvedModel,
            taskType: q.category,
            prompt: q.question,
            response: outcome.response,
            latencyMs: outcome.latency,
            inputTokens: outcome.tokenUsage.promptTokens,
            outputTokens: outcome.tokenUsage.completionTokens,
            totalTokens: outcome.tokenUsage.totalTokens,
            judgeInputTokens: evaluation.tokenUsage.promptTokens,
            judgeOutputTokens: evaluation.tokenUsage.completionTokens,
            judgeTotalTokens: evaluation.tokenUsage.totalTokens,
            judgeLatencyMs: evaluation.latency,
            judgeEstimatedCost: evaluation.estimatedCost,
            estimatedCost: outcome.estimatedCost,
            accuracyScore: scores.accuracyScore,
            qualityScore: scores.qualityScore,
            educationalScore: scores.educationalScore,
            reliability: outcome.success ? 100 : 0,
            hallucinationDetected: scores.hallucinationDetected,
            validJson: scores.validJson,
            validSvg: scores.validSvg,
            feedback: scores.feedback || ''
          });
          await benchmark.save();
        } catch (dbErr) {
          console.error(`      ⚠️ Database save failed for ${model.name}: ${dbErr.message}`);
        }
      }

      // Calculate combined scores
      const avgScore = ((scores.accuracyScore + scores.qualityScore + scores.educationalScore) / 3).toFixed(2);
      const judgeTotalTokens = evaluation.tokenUsage.promptTokens + evaluation.tokenUsage.completionTokens;

      // Append row to benchmark_results.csv
      const csvRow = toCSVRow([
        q.id,                                // question_id
        q.question,                          // question
        q.goldAnswer,                        // gold_answer
        model.name,                          // model_name
        model.name,                          // model name
        outcome.response || '',              // response
        scores.accuracyScore,                // accuracy_score
        scores.qualityScore,                 // quality_score
        scores.educationalScore,             // educational_score
        scores.hallucinationDetected,        // hallucination_detected
        scores.validJson,                    // valid_json
        scores.validSvg,                     // valid_svg
        outcome.latency,                     // latency_ms
        outcome.tokenUsage.promptTokens,     // prompt_tokens
        outcome.tokenUsage.completionTokens, // completion_tokens
        outcome.tokenUsage.totalTokens,     // total_tokens
        outcome.retryCount,                  // retry_count
        outcome.retryCount + 1,              // retries (number of tries)
        outcome.estimatedCost,               // cost_usd
        isOk ? 'true' : 'false',             // success
        outcome.error || evaluation.error || '', // error
        new Date().toISOString(),            // timestamp
        scores.feedback || '',               // judge_feedback
        evaluation.judgeModel,               // judge_model_name
        evaluation.judgeModel,               // judge model name
        avgScore,                            // judge_score
        avgScore,                            // judge score
        evaluation.tokenUsage.promptTokens,  // judge_input_token
        `${evaluation.tokenUsage.promptTokens} / ${evaluation.tokenUsage.completionTokens}`, // judge input token and output token
        evaluation.tokenUsage.completionTokens, // judge_output_token
        judgeTotalTokens,                    // judge_total_token
        judgeTotalTokens,                    // judge total token
        evaluation.latency,                  // judge_latency
        evaluation.latency,                  // judge latency
        evaluation.estimatedCost,            // judge_cost
        evaluation.estimatedCost,            // judeg cost
        outcome.tokenUsage.promptTokens,     // input token
        outcome.tokenUsage.completionTokens, // output token
        outcome.tokenUsage.totalTokens,     // total token
        outcome.latency,                     // latency
        outcome.estimatedCost                // cost
      ]);
      
      await safeAppendFileAsync(resultsCsvPath, csvRow + '\n');
      
      if (isOk) {
        console.log(`   ✅ [${model.name}] Acc: ${scores.accuracyScore}/10 | Qual: ${scores.qualityScore}/10 | Edu: ${scores.educationalScore}/10 | Latency: ${(outcome.latency / 1000).toFixed(2)}s`);
      }
    }

    // STEP 5: Rebuild real-time Leaderboard & Markdown summaries
    await rebuildLeaderboard();

    // STEP 6: Write checkpoint
    await safeWriteFileAsync(checkpointPath, JSON.stringify({ lastCompletedQuestionId: q.id }, null, 2));
    console.log(`\n🎉 Question ID ${q.id} completed. Checkpoint saved.\n`);
    
    // Breather to prevent rate-limit flooding
    await new Promise(r => setTimeout(r, 1000));
  }

  // Disconnect Database
  await mongoose.disconnect();
  console.log(`================================================================`);
  console.log(`🏆 PIPELINE COMPLETED SUCCESSFULLY! All leaderboards fully populated.`);
  console.log(`================================================================`);
  process.exit(0);
}

main().catch(err => {
  console.error('[FATAL CRASH] Pipeline failed unexpectedly:', err);
  process.exit(1);
});
