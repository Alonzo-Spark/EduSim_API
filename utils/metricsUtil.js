const config = require('../config');

// Exact pricing rates (per individual token) for all 12 models
const pricingMap = {
  'gemma-e4b': { input: 0.000000020, output: 0.000000040 },
  'gpt-oss-20b': { input: 0.000000075, output: 0.000000300 },
  'gpt-4o-mini': { input: 0.000000150, output: 0.000000600 },
  'gpt-oss-120b-groq': { input: 0.000000150, output: 0.000000600 },
  'gpt-oss-120b-cerebras': { input: 0.000000350, output: 0.000000750 },
  'gemini-2.5-flash': { input: 0.000000300, output: 0.000002500 },
  'gemini-3.1-flash-lite': { input: 0.000000450, output: 0.000002700 },
  'gemini-2.5-flash-lite': { input: 0.000000450, output: 0.000002700 },
  'gemini-2.0-flash-lite': { input: 0.000000450, output: 0.000002700 },
  'gemini-3-flash-preview': { input: 0.000000500, output: 0.000003000 },
  'deepseek-r1': { input: 0.000000550, output: 0.000002190 },
  'qwen-3-235b': { input: 0.000000600, output: 0.000001200 },
  'zai-glm-4.7': { input: 0.000002250, output: 0.000002750 },
  'claude-3.5-sonnet': { input: 0.000003000, output: 0.000015000 }
};

/**
 * Searches the pricing map dynamically for a model keyword match.
 */
function getPricingForModel(modelName) {
  if (!modelName) return null;
  const lowerName = modelName.toLowerCase();

  // Handle specific endpoints/providers
  if (lowerName.includes('gpt-oss-120b')) {
    if (lowerName.includes('cerebras')) {
      return pricingMap['gpt-oss-120b-cerebras'];
    }
    return pricingMap['gpt-oss-120b-groq'];
  }

  for (const [key, pricing] of Object.entries(pricingMap)) {
    if (lowerName.includes(key) || key.includes(lowerName)) {
      return pricing;
    }
  }
  return null;
}

/**
 * Calculate estimated cost (USD) based on token counts.
 * Uses exact model rates if model is passed, otherwise falls back to config.
 */
function calculateCost(inputTokens, outputTokens, model) {
  let inputPrice = parseFloat(config.pricing?.inputPerToken ?? 0);
  let outputPrice = parseFloat(config.pricing?.outputPerToken ?? 0);

  const modelPricing = getPricingForModel(model);
  if (modelPricing) {
    inputPrice = modelPricing.input;
    outputPrice = modelPricing.output;
  }

  const cost = inputTokens * inputPrice + outputTokens * outputPrice;
  // Round to 8 decimal places since individual token costs are extremely small
  return Math.round(cost * 1e8) / 1e8;
}

/**
 * Simple helper to compute average of an array of numbers.
 */
function average(arr) {
  if (!Array.isArray(arr) || arr.length === 0) return 0;
  return arr.reduce((sum, v) => sum + v, 0) / arr.length;
}

module.exports = { calculateCost, average };
