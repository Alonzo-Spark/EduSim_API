// services/evaluationService.js - AI‑judge evaluator using OpenRouter
const GeminiService = require('./geminiService');
const config = require('../config');

/**
 * Build a rubric prompt for the AI‑judge.
 * The prompt asks Gemini to score the response on a 0‑10 scale for
 *   - accuracyScore
 *   - qualityScore
 *   - educationalScore
 *   - hallucinationDetected (boolean)
 *   - validJson (boolean)
 *   - validSvg (boolean)
 * and return a short textual feedback.
 */
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

Critique & Feedback Rules:
1. Provide a short feedback sentence explaining the main reason for your scores.
2. CRITICAL DIAGNOSIS: If any score (accuracyScore, qualityScore, or educationalScore) is less than 7, the feedback MUST explicitly detail exactly what went wrong, what was missing, or what was incorrect in that specific category so the developer knows why it failed.

---
Task type: ${taskType}
${expectationText}
---
Response:
${response}

Respond ONLY with a JSON object containing the keys:
{ "accuracyScore": number, "qualityScore": number, "educationalScore": number, "hallucinationDetected": boolean, "validJson": boolean, "validSvg": boolean, "feedback": string }`;
}

/**
 * Helper to clean and extract valid JSON from an LLM response.
 * Handles markdown fences, trailing comments, and surrounding conversational text.
 */
function cleanAndParseJson(str) {
  if (!str) throw new Error('Empty response');
  let cleaned = str.trim();
  
  // Remove markdown code fences if present (e.g. ```json ... ``` or ``` ... ```)
  if (cleaned.includes('```')) {
    const matches = cleaned.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
    if (matches && matches[1]) {
      cleaned = matches[1].trim();
    }
  }

  // Find the boundaries of the first valid JSON object
  const firstBrace = cleaned.indexOf('{');
  const lastBrace = cleaned.lastIndexOf('}');
  
  if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
    cleaned = cleaned.substring(firstBrace, lastBrace + 1);
  }

  return JSON.parse(cleaned);
}

/**
 * Calls Gemini (as a judge) and parses the JSON result.
 */
async function evaluateResponse({ response, taskType, expected }) {
  const judgePrompt = buildJudgePrompt({ response, taskType, expected });
  // Start timing for judge latency
  const judgeStart = Date.now();
  const raw = await GeminiService.generateResponse(judgePrompt, null, config.evaluatorModel);
  const judgeLatencyMs = Date.now() - judgeStart;
  const text = raw.text();
  const usageMeta = raw.usageMetadata || {};
  const judgeInputTokens = usageMeta.promptTokenCount || 0;
  const judgeOutputTokens = usageMeta.candidatesTokenCount || 0;
  const judgeTotalTokens = usageMeta.totalTokenCount || (judgeInputTokens + judgeOutputTokens);
  // Estimate cost for judge using same utility
  const judgeEstimatedCost = (() => {
    try {
      const MetricsUtil = require('../utils/metricsUtil');
      return MetricsUtil.calculateCost(judgeInputTokens, judgeOutputTokens, raw.model);
    } catch (_) { return 0; }
  })();
  let parsed;
  try {
    parsed = cleanAndParseJson(text);
  } catch (e) {
    console.error('Judge response parsing failed for raw output:\n', text);
    console.error('Parse error details:', e.message);
    
    // If Gemini didn't return valid JSON, fallback to safe defaults
    parsed = {
      accuracyScore: 0,
      qualityScore: 0,
      educationalScore: 0,
      hallucinationDetected: true,
      validJson: false,
      validSvg: false,
      feedback: `Judge failed to return parseable JSON. Raw: ${text.substring(0, 100)}...`
    };
  }
  // Attach judge metrics to parsed result
  parsed.judgeInputTokens = judgeInputTokens;
  parsed.judgeOutputTokens = judgeOutputTokens;
  parsed.judgeTotalTokens = judgeTotalTokens;
  parsed.judgeLatencyMs = judgeLatencyMs;
  parsed.judgeEstimatedCost = judgeEstimatedCost;
  return parsed;
}

module.exports = { evaluateResponse };
