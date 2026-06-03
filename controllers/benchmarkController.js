// controllers/benchmarkController.js - Handles benchmark API logic
const GeminiService = require('../services/geminiService');
const EvaluationService = require('../services/evaluationService');
const MetricsUtil = require('../utils/metricsUtil');
const BenchmarkRun = require('../models/BenchmarkRun');

// POST /run - executes a benchmark for a given prompt dataset entry
exports.runBenchmark = async (req, res, next) => {
  try {
    const { promptId, customPrompt, taskType, model } = req.body;
    // Retrieve prompt from dataset if promptId provided
    let promptData;
    if (promptId) {
      const PromptDataset = require('../models/PromptDataset');
      promptData = await PromptDataset.findById(promptId);
      if (!promptData) return res.status(404).json({ error: 'Prompt not found' });
    } else if (customPrompt) {
      promptData = { prompt: customPrompt, expectedConcepts: [], expectedFormula: null, taskType };
    } else {
      return res.status(400).json({ error: 'Either promptId or customPrompt required' });
    }

    // Call dynamic model with the interactive textbook system prompt
    const start = Date.now();
    const selectedModel = model || GeminiService.getModelName();
    const geminiResponse = await GeminiService.generateResponse(promptData.prompt, GeminiService.SYSTEM_PROMPT, selectedModel);
    const latencyMs = Date.now() - start;
    const resolvedModelName = geminiResponse.model || selectedModel;

    // Extract token usage
    const usage = geminiResponse.usageMetadata || {};
    const inputTokens = usage.promptTokenCount || 0;
    const outputTokens = usage.candidatesTokenCount || 0;
    const totalTokens = usage.totalTokenCount || inputTokens + outputTokens;

    // Compute cost
    const cost = MetricsUtil.calculateCost(inputTokens, outputTokens, resolvedModelName);

    // Evaluate response via Meta Llama 3.1 405B judge
    const evaluation = await EvaluationService.evaluateResponse({
      response: geminiResponse.text(),
      taskType: promptData.taskType,
      expected: promptData,
    });

    // Store benchmark run
    const benchmark = new BenchmarkRun({
      model: resolvedModelName,
      taskType: promptData.taskType,
      prompt: promptData.prompt,
      response: geminiResponse.text(),
      latencyMs,
      inputTokens,
      outputTokens,
      totalTokens,
      estimatedCost: cost,
      accuracyScore: evaluation.accuracyScore,
      qualityScore: evaluation.qualityScore,
      educationalScore: evaluation.educationalScore,
      reliability: 100, // successful run
      hallucinationDetected: evaluation.hallucinationDetected,
      validJson: evaluation.validJson,
      validSvg: evaluation.validSvg,
      feedback: evaluation.feedback || '',
      timestamp: new Date(),
    });
    await benchmark.save();
    res.json({ benchmarkId: benchmark._id, evaluation });
  } catch (err) {
    next(err);
  }
};

// POST /batch-run - executes a benchmark for a prompt against all 12 registered models
exports.runBatchBenchmark = async (req, res, next) => {
  try {
    const { promptId, customPrompt, taskType } = req.body;
    let promptData;
    if (promptId) {
      const PromptDataset = require('../models/PromptDataset');
      promptData = await PromptDataset.findById(promptId);
      if (!promptData) return res.status(404).json({ error: 'Prompt not found' });
    } else if (customPrompt) {
      promptData = { prompt: customPrompt, expectedConcepts: [], expectedFormula: null, taskType };
    } else {
      return res.status(400).json({ error: 'Either promptId or customPrompt required' });
    }

    const config = require('../config');
    const results = [];

    // Run sequentially to prevent OpenRouter rate limits
    for (const model of config.targetModels) {
      const start = Date.now();
      try {
        const geminiResponse = await GeminiService.generateResponse(promptData.prompt, GeminiService.SYSTEM_PROMPT, model);
        const resolvedModelName = geminiResponse.model || (typeof model === 'string' ? model : (model.name || model.id));
        const latencyMs = Date.now() - start;

        const usage = geminiResponse.usageMetadata || {};
        const inputTokens = usage.promptTokenCount || 0;
        const outputTokens = usage.candidatesTokenCount || 0;
        const totalTokens = usage.totalTokenCount || inputTokens + outputTokens;
        const cost = MetricsUtil.calculateCost(inputTokens, outputTokens, resolvedModelName);

        const evaluation = await EvaluationService.evaluateResponse({
          response: geminiResponse.text(),
          taskType: promptData.taskType,
          expected: promptData,
        });

        const benchmark = new BenchmarkRun({
          model: resolvedModelName,
          taskType: promptData.taskType,
          prompt: promptData.prompt,
          response: geminiResponse.text(),
          latencyMs,
          inputTokens,
          outputTokens,
          totalTokens,
          estimatedCost: cost,
          accuracyScore: evaluation.accuracyScore,
          qualityScore: evaluation.qualityScore,
          educationalScore: evaluation.educationalScore,
          reliability: 100,
          hallucinationDetected: evaluation.hallucinationDetected,
          validJson: evaluation.validJson,
          validSvg: evaluation.validSvg,
          feedback: evaluation.feedback || '',
          timestamp: new Date(),
        });
        await benchmark.save();

        results.push({
          model: typeof model === 'string' ? model : (model.name || model.id),
          status: 'Success',
          benchmarkId: benchmark._id,
          evaluation
        });
      } catch (err) {
        const friendlyName = typeof model === 'string' ? model : (model.name || model.id);
        console.error(`Batch run failed for model ${friendlyName}:`, err.message);
        results.push({
          model: friendlyName,
          status: `Failed: ${err.message}`,
          benchmarkId: null,
          evaluation: null
        });
      }
    }

    res.json({
      message: 'Batch benchmark run completed',
      totalModels: config.targetModels.length,
      successful: results.filter(r => r.status === 'Success').length,
      results
    });
  } catch (err) {
    next(err);
  }
};

// POST /evaluate - re‑evaluate an existing stored response (optional)
exports.evaluateResponse = async (req, res, next) => {
  try {
    const { benchmarkId } = req.body;
    const benchmark = await BenchmarkRun.findById(benchmarkId);
    if (!benchmark) return res.status(404).json({ error: 'Benchmark not found' });
    const evaluation = await EvaluationService.evaluateResponse({
      response: benchmark.response,
      taskType: benchmark.taskType,
      expected: {}, // could be extended
    });
    // Update fields
    Object.assign(benchmark, {
      accuracyScore: evaluation.accuracyScore,
      qualityScore: evaluation.qualityScore,
      educationalScore: evaluation.educationalScore,
      hallucinationDetected: evaluation.hallucinationDetected,
      validJson: evaluation.validJson,
      validSvg: evaluation.validSvg,
      feedback: evaluation.feedback || '',
    });
    await benchmark.save();
    res.json({ evaluation });
  } catch (err) {
    next(err);
  }
};


// GET /results - list benchmark runs with optional query params
exports.getResults = async (req, res, next) => {
  try {
    const filters = {};
    if (req.query.taskType) filters.taskType = req.query.taskType;
    if (req.query.model) filters.model = req.query.model;
    const results = await BenchmarkRun.find(filters).sort({ timestamp: -1 }).limit(100);
    res.json(results);
  } catch (err) {
    next(err);
  }
};

// GET /leaderboard - best scores per task type
exports.getLeaderboard = async (req, res, next) => {
  try {
    const pipeline = [
      { $group: {
        _id: { taskType: '$taskType', model: '$model' },
        avgAccuracy: { $avg: '$accuracyScore' },
        avgEducational: { $avg: '$educationalScore' },
        avgQuality: { $avg: '$qualityScore' },
      }},
      { $sort: { avgAccuracy: -1 } },
      { $limit: 50 },
    ];
    const leaderboard = await BenchmarkRun.aggregate(pipeline);
    res.json(leaderboard);
  } catch (err) {
    next(err);
  }
};

// GET /analytics - aggregate metrics (latency, cost, token usage)
exports.getAnalytics = async (req, res, next) => {
  try {
    const pipeline = [
      { $group: {
        _id: null,
        avgLatency: { $avg: '$latencyMs' },
        totalCost: { $sum: '$estimatedCost' },
        avgInputTokens: { $avg: '$inputTokens' },
        avgOutputTokens: { $avg: '$outputTokens' },
        reliability: { $avg: '$reliability' },
      }},
    ];
    const [stats] = await BenchmarkRun.aggregate(pipeline);
    res.json(stats || {});
  } catch (err) {
    next(err);
  }
};

// GET /history - runs for a specific model or task
exports.getHistory = async (req, res, next) => {
  try {
    const { model, taskType } = req.query;
    const filter = {};
    if (model) filter.model = model;
    if (taskType) filter.taskType = taskType;
    const history = await BenchmarkRun.find(filter).sort({ timestamp: 1 });
    res.json(history);
  } catch (err) {
    next(err);
  }
};
