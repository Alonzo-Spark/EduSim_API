// scratch/benchmark_sequential_model.js - Benchmarks a single model sequentially across 10 diverse educational questions
require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
const mongoose = require('mongoose');
const PromptDataset = require('../models/PromptDataset');
const BenchmarkRun = require('../models/BenchmarkRun');
const EvaluationService = require('../services/evaluationService');
const MetricsUtil = require('../utils/metricsUtil');
const GeminiService = require('../services/geminiService');

// The 12 Flagship Target Models matching config.js
const targetModels = [
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
  { name: 'Claude 3.5 Sonnet', id: 'anthropic/claude-3.5-sonnet' },
  { name: 'Claude Sonnet 4', id: 'anthropic/claude-sonnet-4' },
];

// 10 standardized educational benchmark questions for Grade 10 Physics curriculum
const seedPrompts = [
  {
    prompt: "Explain Newton's First Law of Motion (Law of Inertia) with a clear everyday life example, such as a passenger standing in a suddenly braking bus.",
    expectedConcepts: ["inertia", "first law", "unbalanced external force", "state of rest", "motion"],
    expectedFormula: null,
    taskType: "mechanics",
    difficulty: "easy"
  },
  {
    prompt: "Compare Kinetic Energy and Potential Energy. Explain how energy transitions between them using a textbook example of a roller coaster or a swinging pendulum, and state the Law of Conservation of Energy.",
    expectedConcepts: ["kinetic energy", "potential energy", "conservation of energy", "height", "velocity"],
    expectedFormula: "KE = \\frac{1}{2}mv^2",
    taskType: "work_energy",
    difficulty: "medium"
  },
  {
    prompt: "Explain the difference between Real and Virtual images formed by spherical mirrors. Detail the specific real-world applications where concave mirrors and convex mirrors are used.",
    expectedConcepts: ["real image", "virtual image", "concave mirror", "convex mirror", "converging", "diverging"],
    expectedFormula: "\\frac{1}{f} = \\frac{1}{v} + \\frac{1}{u}",
    taskType: "light_mirrors",
    difficulty: "easy"
  },
  {
    prompt: "What is refraction of light? Explain why a pencil appears bent when partially immersed in water, and clearly state Snell's Law of Refraction.",
    expectedConcepts: ["refraction", "bending of light", "optical density", "refractive index", "Snell's Law"],
    expectedFormula: "\\frac{\\sin i}{\\sin r} = \\text{constant}",
    taskType: "light_lenses",
    difficulty: "medium"
  },
  {
    prompt: "State Ohm's Law. Describe a simple physics lab experiment setup to verify the relationship between voltage, current, and resistance in a copper wire.",
    expectedConcepts: ["Ohm's law", "potential difference", "electric current", "resistance", "proportionality"],
    expectedFormula: "V = IR",
    taskType: "electricity",
    difficulty: "easy"
  },
  {
    prompt: "Compare Series and Parallel combinations of electrical resistors. Explain in detail why household domestic wiring is always connected in parallel rather than in series.",
    expectedConcepts: ["series circuit", "parallel circuit", "independent operation", "voltage division", "equivalent resistance"],
    expectedFormula: "\\frac{1}{R_p} = \\frac{1}{R_1} + \\frac{1}{R_2}",
    taskType: "electricity_circuits",
    difficulty: "medium"
  },
  {
    prompt: "What is an electromagnet? Explain how a current-carrying solenoid behaves like a bar magnet, and list three distinct ways to increase the strength of its magnetic field.",
    expectedConcepts: ["electromagnet", "solenoid", "magnetic field lines", "soft iron core", "number of turns"],
    expectedFormula: null,
    taskType: "magnetism",
    difficulty: "medium"
  },
  {
    prompt: "Explain how a Thermal Power Plant works to generate electricity. List the main step-by-step energy transformations that take place from burning coal to electrical transmission.",
    expectedConcepts: ["coal", "steam", "turbine rotation", "generator", "chemical to thermal", "kinetic to electrical"],
    expectedFormula: null,
    taskType: "energy_sources",
    difficulty: "easy"
  },
  {
    prompt: "Generate a clean, responsive, and beautiful SVG ray diagram representing the refraction of light through a glass prism. Clearly draw and label the incident ray, refracted ray, emergent ray, and the angle of deviation.",
    expectedConcepts: ["svg", "polygon", "line", "text", "incident", "refracted", "emergent", "deviation"],
    expectedFormula: null,
    taskType: "svg",
    difficulty: "hard"
  },
  {
    prompt: "Respond ONLY with a valid JSON object representing a calculation report for a 10th-grade classroom physics lab circuit with 3 resistors (2Ω, 3Ω, and 5Ω) connected in series to a 10V battery. The JSON must contain keys for equivalent resistance, total circuit current, and individual voltage drops across each resistor.",
    expectedConcepts: ["equivalentResistance", "totalCurrent", "voltageDrop2", "voltageDrop3", "voltageDrop5", "10", "1", "2", "3", "5"],
    expectedFormula: null,
    taskType: "json",
    difficulty: "hard"
  }
];

// Helper to query OpenRouter using dynamic parameters and custom provider configurations
async function executeGeneration(model, prompt, promptData) {
  const start = Date.now();
  const apiKey = (process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY || '').trim();

  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'EduSim Model Evaluator Benchmarking'
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

    // Call the dedicated evaluator judge (Llama 3.3 70B Instruct)
    const evaluation = await EvaluationService.evaluateResponse({
      response: responseText,
      taskType: promptData.taskType,
      expected: promptData
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

async function run() {
  console.log(`[SEQUENTIAL EVALUATOR] Connecting to MongoDB...`);
  await mongoose.connect(process.env.MONGODB_URI);
  console.log(`[SEQUENTIAL EVALUATOR] Connected to MongoDB.`);

  // 1. Force drop and seed to populate the Grade-10 Physics curriculum
  console.log(`[SEQUENTIAL EVALUATOR] Seeding PromptDataset with 10th-grade Physics curriculum...`);
  await PromptDataset.deleteMany({});
  await PromptDataset.insertMany(seedPrompts);
  console.log(`[SEQUENTIAL EVALUATOR] PromptDataset populated successfully!`);

  // 2. Select Model from args or fallback
  const args = process.argv.slice(2);
  const selectedName = args[0] || 'GPT-4o-mini';
  const modelMatch = targetModels.find(m => m.name.toLowerCase().includes(selectedName.toLowerCase()));

  if (!modelMatch) {
    console.error(`\n[ERROR] Model "${selectedName}" is not registered in targetModels.`);
    console.log(`Registered Model Names:`, targetModels.map(m => m.name).join(', '));
    await mongoose.disconnect();
    process.exit(1);
  }

  console.log(`\n===============================================================`);
  console.log(`🚀 STARTING SEQUENTIAL BENCHMARK FOR MODEL: ${modelMatch.name}`);
  console.log(`OpenRouter ID: \`${modelMatch.id}\``);
  console.log(`Questions Count: ${seedPrompts.length}`);
  console.log(`===============================================================\n`);

  const fetchedPrompts = await PromptDataset.find().sort({ taskType: 1 });
  const results = [];
  
  for (let idx = 0; idx < fetchedPrompts.length; idx++) {
    const promptData = fetchedPrompts[idx];
    console.log(`[${idx + 1}/10] Evaluating: "${promptData.prompt.substring(0, 50)}..." [Task: ${promptData.taskType}]`);
    
    // Add small delay to prevent upstream rate limit exhaustion
    await new Promise(r => setTimeout(r, 1000));
    
    const outcome = await executeGeneration(modelMatch, promptData.prompt, promptData);
    
    if (outcome.success) {
      console.log(`  -> SUCCESS in ${outcome.latency}ms! Accuracy: ${outcome.evaluation.accuracyScore}/10 | Quality: ${outcome.evaluation.qualityScore}/10 | Cost: $${outcome.estimatedCost.toFixed(6)}`);
      
      // Save BenchmarkRun in MongoDB
      const benchmark = new BenchmarkRun({
        model: outcome.resolvedModel,
        taskType: promptData.taskType,
        prompt: promptData.prompt,
        response: outcome.response || '<no response>', // fallback if empty
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
    } else {
      console.error(`  -> FAILED: ${outcome.error}`);
    }
    
    results.push({
      prompt: promptData.prompt,
      taskType: promptData.taskType,
      difficulty: promptData.difficulty,
      ...outcome
    });
  }

  // 3. Compile Aggregate Metrics
  const successfulRuns = results.filter(r => r.success);
  const totalCost = results.reduce((sum, r) => sum + r.estimatedCost, 0);
  const avgLatency = successfulRuns.length ? results.reduce((sum, r) => sum + r.latency, 0) / results.length : 0;
  const avgAccuracy = successfulRuns.length ? successfulRuns.reduce((sum, r) => sum + r.evaluation.accuracyScore, 0) / successfulRuns.length : 0;
  const avgQuality = successfulRuns.length ? successfulRuns.reduce((sum, r) => sum + r.evaluation.qualityScore, 0) / successfulRuns.length : 0;
  const avgEducational = successfulRuns.length ? successfulRuns.reduce((sum, r) => sum + r.evaluation.educationalScore, 0) / successfulRuns.length : 0;
  const successRate = (successfulRuns.length / results.length) * 100;

  console.log(`\n===============================================================`);
  console.log(`🏁 BENCHMARK COMPLETED FOR MODEL: ${modelMatch.name}`);
  console.log(`Success Rate    : ${successRate.toFixed(2)}% (${successfulRuns.length}/10)`);
  console.log(`Average Latency : ${avgLatency.toFixed(2)}ms`);
  console.log(`Total Cost (USD): $${totalCost.toFixed(8)}`);
  console.log(`Average Scores  : Accuracy: ${avgAccuracy.toFixed(2)}/10 | Quality: ${avgQuality.toFixed(2)}/10 | Educational: ${avgEducational.toFixed(2)}/10`);
  console.log(`===============================================================\n`);

  // Write Markdown Report File
  const fs = require('fs');
  const path = require('path');
  const fileSafeName = modelMatch.name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
  
  let md = `# Sequential Benchmark Report - ${modelMatch.name}\n\n`;
  md += `Completed evaluation across **${seedPrompts.length} standardized educational questions**.\n\n`;
  md += `### Aggregate Metrics:\n`;
  md += `* **Success Rate**: ${successRate.toFixed(2)}% (${successfulRuns.length}/10)\n`;
  md += `* **Average Latency**: ${avgLatency.toFixed(2)}ms\n`;
  md += `* **Total Estimated Cost**: $${totalCost.toFixed(8)}\n`;
  md += `* **Average Accuracy**: ${avgAccuracy.toFixed(2)}/10\n`;
  md += `* **Average Quality**: ${avgQuality.toFixed(2)}/10\n`;
  md += `* **Average Educational Value**: ${avgEducational.toFixed(2)}/10\n\n`;
  
  md += `### Question-by-Question Evaluation Table:\n\n`;
  md += `| # | Prompt Topic | Success | Latency | InputTokens | OutputTokens | TotalTokens | JudgeInputTokens | JudgeOutputTokens | JudgeTotalTokens | JudgeCost | JudgeLatency | Accuracy | Quality | Educational | Cost | Rationale / Error |\n`;
  md += `| :-: | :--- | :---: | :---: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :---: | :---: | :---: | :---: | :---: | :--- |\n`;
  
  for (let idx = 0; idx < results.length; idx++) {
    const r = results[idx];
    const status = r.success ? '✅ Success' : '❌ Failed';
    const lat = r.success ? `${r.latency}ms` : '-';
    const acc = r.success ? r.evaluation.accuracyScore : '-';
    const qual = r.success ? r.evaluation.qualityScore : '-';
    const edu = r.success ? r.evaluation.educationalScore : '-';
    const cost = r.success ? `$${r.estimatedCost.toFixed(5)}` : '-';
    const feedback = r.success ? (r.evaluation.feedback || '-') : `\`${r.error}\``;
    const modelIn = r.success ? r.tokenUsage.promptTokens : '-';
    const modelOut = r.success ? r.tokenUsage.completionTokens : '-';
    const modelTot = r.success ? r.tokenUsage.totalTokens : '-';
    const judgeIn = r.success ? r.evaluation.judgeInputTokens : '-';
    const judgeOut = r.success ? r.evaluation.judgeOutputTokens : '-';
    const judgeTot = r.success ? r.evaluation.judgeTotalTokens : '-';
    const judgeCost = r.success ? `$${(r.evaluation.judgeEstimatedCost || 0).toFixed(6)}` : '-';
    const judgeLat = r.success ? `${r.evaluation.judgeLatencyMs || 0}ms` : '-';
    
    md += `| ${idx + 1} | **${r.taskType}** (${r.difficulty}) | ${status} | ${lat} | ${modelIn} | ${modelOut} | ${modelTot} | ${judgeIn} | ${judgeOut} | ${judgeTot} | ${judgeCost} | ${judgeLat} | **${acc}** | **${qual}** | **${edu}** | ${cost} | ${feedback} |\n`;
  }
  
  const reportPath = path.resolve(__dirname, `model_${fileSafeName}_report.md`);
  fs.writeFileSync(reportPath, md);
  console.log(`[REPORT SAVED] Markdown summary saved to: ${reportPath}`);

  await mongoose.disconnect();
  console.log(`[SEQUENTIAL EVALUATOR] MongoDB disconnected.`);
}

run().catch(err => {
  console.error('[SEQUENTIAL EVALUATOR] Fatal crash:', err);
  process.exit(1);
});
