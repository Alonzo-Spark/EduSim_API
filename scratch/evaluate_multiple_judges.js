// scratch/evaluate_multiple_judges.js - Compare 12 different AI models as evaluators
require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
const mongoose = require('mongoose');
const BenchmarkRun = require('../models/BenchmarkRun');

// 12 models to compare (mapped to their standard OpenRouter IDs)
const modelsToCompare = [
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

function buildJudgePrompt({ response, taskType, expected }) {
  const expectations = [];
  if (expected.expectedConcepts && expected.expectedConcepts.length) {
    expectations.push(`Expected concepts: ${expected.expectedConcepts.join(', ')}`);
  }
  if (expected.expectedFormula) {
    expectations.push(`Expected formula (LaTeX): ${expected.expectedFormula}`);
  }
  const expectationText = expectations.length ? expectations.join('\n') : 'No specific expectations provided.';

  return `You are an expert evaluator for educational AI outputs. Score the following response on a scale of 0‑10 for:
- accuracyScore (does it contain the required concepts/formula?)
- qualityScore (clarity, structure, readability)
- educationalScore (how well it would teach a beginner)
Also indicate:
- hallucinationDetected (true/false) – any fabricated concepts or wrong formulas?
- validJson (true/false) – is the response a valid JSON object if the taskType is "json"?
- validSvg (true/false) – is the response a valid SVG string if the taskType is "svg"?
Provide a short feedback sentence explaining the main reason for the scores.

---
Task type: ${taskType}
${expectationText}
---
Response:
${response}

Respond ONLY with a JSON object containing the keys:
{ "accuracyScore": number, "qualityScore": number, "educationalScore": number, "hallucinationDetected": boolean, "validJson": boolean, "validSvg": boolean, "feedback": string }`;
}

function cleanAndParseJson(str) {
  if (!str) throw new Error('Empty response');
  let cleaned = str.trim();
  
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

  return JSON.parse(cleaned);
}

async function callOpenRouter(model, prompt) {
  const apiKey = (process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY || '').trim();
  const modelId = typeof model === 'string' ? model : model.id;
  const requestBody = {
    model: modelId,
    messages: [{ role: 'user', content: prompt }],
    temperature: 0.2, // lower temperature for more deterministic judging
    max_tokens: 1024
  };
  if (model && typeof model === 'object' && model.providerOrder) {
    requestBody.provider = { order: model.providerOrder, allow_fallbacks: false };
  }
  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`,
      'HTTP-Referer': 'http://localhost:5000',
      'X-Title': 'EduSim API Evaluator Benchmarking'
    },
    body: JSON.stringify(requestBody)
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errText}`);
  }

  const data = await response.json();
  if (data.error) {
    throw new Error(data.error.message || JSON.stringify(data.error));
  }

  return data.choices?.[0]?.message?.content || '';
}

async function run() {
  console.log('Connecting to MongoDB...');
  await mongoose.connect(process.env.MONGODB_URI);
  console.log('MongoDB connected.');

  // Fetch the latest run
  const latestRun = await BenchmarkRun.findOne().sort({ timestamp: -1 });
  if (!latestRun) {
    console.error('No benchmark runs found. Please run a benchmark first.');
    process.exit(1);
  }

  console.log(`\nEvaluating stored response from: ${latestRun.model}`);
  console.log(`Prompt: "${latestRun.prompt}"`);
  console.log(`Response length: ${latestRun.response.length} characters\n`);

  const judgePrompt = buildJudgePrompt({
    response: latestRun.response,
    taskType: latestRun.taskType,
    expected: { expectedConcepts: [], expectedFormula: null }
  });

  const results = [];

  for (const model of modelsToCompare) {
    console.log(`Calling judge model: ${model.name} (${model.id})...`);
    const start = Date.now();
    try {
      const rawText = await callOpenRouter(model, judgePrompt);
      const parsed = cleanAndParseJson(rawText);
      const duration = Date.now() - start;
      console.log(`  -> Succeeded in ${duration}ms! Accuracy: ${parsed.accuracyScore}, Quality: ${parsed.qualityScore}, Educational: ${parsed.educationalScore}`);
      
      // Save this judge's evaluation directly into MongoDB as a new BenchmarkRun document
      const judgeRun = new BenchmarkRun({
        model: `Judge: ${model.name}`,
        taskType: latestRun.taskType,
        prompt: `[Eval Run ID: ${latestRun._id}] ${latestRun.prompt}`,
        response: latestRun.response,
        latencyMs: duration,
        inputTokens: 0,
        outputTokens: 0,
        totalTokens: 0,
        estimatedCost: 0,
        accuracyScore: parsed.accuracyScore,
        qualityScore: parsed.qualityScore,
        educationalScore: parsed.educationalScore,
        hallucinationDetected: parsed.hallucinationDetected || false,
        validJson: parsed.validJson || false,
        validSvg: parsed.validSvg || false,
        feedback: parsed.feedback || '',
        timestamp: new Date()
      });
      await judgeRun.save();

      results.push({
        name: model.name,
        id: model.id,
        status: 'Success',
        accuracy: parsed.accuracyScore,
        quality: parsed.qualityScore,
        educational: parsed.educationalScore,
        hallucination: parsed.hallucinationDetected ? 'Yes' : 'No',
        feedback: parsed.feedback || '',
        latencyMs: duration
      });
    } catch (err) {
      console.error(`  -> Failed: ${err.message}`);
      results.push({
        name: model.name,
        id: model.id,
        status: `Failed (${err.message.substring(0, 40)}...)`,
        accuracy: '-',
        quality: '-',
        educational: '-',
        hallucination: '-',
        feedback: err.message,
        latencyMs: Date.now() - start
      });
    }
  }

  // Generate beautiful markdown table
  let md = `# AI Judge Benchmarking Comparison\n\n`;
  md += `Comparing **12 different AI models** acting as judges evaluating the physics response generated by **${latestRun.model}**.\n\n`;
  md += `### Target Response Evaluated:\n`;
  md += `> ${latestRun.response.replace(/\n/g, '\n> ')}\n\n`;
  md += `## Score Comparison Table\n\n`;
  md += `| Judge Model | Status | Accuracy | Quality | Educational | Hallucination? | Latency | Feedback Rationale |\n`;
  md += `| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |\n`;

  for (const r of results) {
    md += `| **${r.name}** | \`${r.status}\` | **${r.accuracy}** | **${r.quality}** | **${r.educational}** | \`${r.hallucination}\` | ${r.latencyMs}ms | ${r.feedback} |\n`;
  }

  md += `\n*Evaluations performed on ${new Date().toLocaleString()}*`;

  // Write comparison file
  const fs = require('fs');
  const path = require('path');
  const outPath = path.resolve(__dirname, '../evaluation_comparison.md');
  fs.writeFileSync(outPath, md);
  console.log(`\nComparison table successfully saved to: ${outPath}`);

  await mongoose.disconnect();
  console.log('MongoDB disconnected.');
}

run().catch(err => {
  console.error('Fatal error running comparison script:', err);
  process.exit(1);
});
