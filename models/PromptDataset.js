// models/PromptDataset.js - Schema for benchmark prompts
const mongoose = require('mongoose');

const PromptDatasetSchema = new mongoose.Schema({
  prompt: { type: String, required: true },
  expectedConcepts: [{ type: String }], // concepts that should appear in the response
  expectedFormula: { type: String }, // optional LaTeX/formula string
  taskType: { type: String, required: true }, // e.g., 'tutor', 'physics', 'svg', 'json'
  difficulty: { type: String, enum: ['easy', 'medium', 'hard'], default: 'easy' },
  metadata: { type: mongoose.Schema.Types.Mixed }, // any extra info
});

module.exports = mongoose.model('PromptDataset', PromptDatasetSchema);
