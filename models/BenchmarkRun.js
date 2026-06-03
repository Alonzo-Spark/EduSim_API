// models/BenchmarkRun.js - Mongoose schema for a benchmark execution
const mongoose = require('mongoose');

const BenchmarkRunSchema = new mongoose.Schema({
  model: { type: String, required: true },
  taskType: { type: String, required: true },
  prompt: { type: String, required: true },
  response: { type: String, required: true },
  latencyMs: { type: Number, required: true },
  inputTokens: { type: Number, required: true },
  outputTokens: { type: Number, required: true },
  totalTokens: { type: Number, required: true },
  // Judge (Meta Llama) token usage and cost
  judgeInputTokens: { type: Number, default: null },
  judgeOutputTokens: { type: Number, default: null },
  judgeTotalTokens: { type: Number, default: null },
  judgeLatencyMs: { type: Number, default: null },
  judgeEstimatedCost: { type: Number, default: null },
  estimatedCost: { type: Number, required: true },
  accuracyScore: { type: Number, default: null },
  qualityScore: { type: Number, default: null },
  educationalScore: { type: Number, default: null },
  reliability: { type: Number, default: 100 },
  hallucinationDetected: { type: Boolean, default: false },
  validJson: { type: Boolean, default: null },
  validSvg: { type: Boolean, default: null },
  feedback: { type: String, default: '' },
  timestamp: { type: Date, default: Date.now },
});

module.exports = mongoose.model('BenchmarkRun', BenchmarkRunSchema);

