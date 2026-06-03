// config.js - central configuration
require('dotenv').config();

module.exports = {
  port: process.env.PORT || 5000,
  mongoUri: process.env.MONGODB_URI,
  geminiApiKey: process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY,
  geminiModel: process.env.GEMINI_MODEL || 'google/gemini-2.5-flash',
  
  // Flagship Evaluator model (Meta Llama 3.1 405B - world-class objective reasoning)
  evaluatorModel: process.env.EVALUATOR_MODEL || 'meta-llama/llama-3.3-70b-instruct',
  
  // The 12 Benchmarked Flagship Target Models (production-grade, 100% online)
  targetModels: [
    { name: 'Gemma-E4B', id: 'google/gemma-3n-e4b-it' },
    { name: 'gpt-oss-20b (Groq)', id: 'openai/gpt-oss-20b', providerOrder: ['Groq'] },
    { name: 'GPT-4o-mini', id: 'openai/gpt-4o-mini' },
    { name: 'gpt-oss-120b (Groq)', id: 'openai/gpt-oss-120b', providerOrder: ['Groq'] },
    { name: 'Gemini 2.5 Flash', id: 'google/gemini-2.5-flash' },
    { name: 'gpt-oss-120b (Cerebras)', id: 'openai/gpt-oss-120b', providerOrder: ['Cerebras'] },
    { name: 'Gemini Flash Lite (3.1)', id: 'google/gemini-2.0-flash-lite-001' },
    { name: 'Gemini 3 Flash Preview', id: 'google/gemini-3-flash-preview' },
    { name: 'DeepSeek R1', id: 'deepseek/deepseek-r1' },
    { name: 'qwen-3-235b-a22b-instruct-2507', id: 'qwen/qwen3-235b-a22b-2507' },
    { name: 'zai-glm-4.7 (Cerebras)', id: 'z-ai/glm-4.7', providerOrder: ['Cerebras'] },
    { name: 'Claude 3.5 Sonnet', id: 'anthropic/claude-sonnet-4.6' }
  ],

  // Pricing (example values, replace with actual rates)
  pricing: {
    inputPerToken: 0.000001, // USD per input token
    outputPerToken: 0.000002, // USD per output token
  },
};
