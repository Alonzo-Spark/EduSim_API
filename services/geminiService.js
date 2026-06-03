// services/geminiService.js - Wrapper for OpenRouter API supporting Gemini and other models
const config = require('../config');

/**
 * Maps standard model names to OpenRouter model strings.
 */
function mapModelName(model) {
  if (!model) return 'google/gemini-2.5-flash';
  
  // If the model already has a slash (e.g. google/gemini-2.5-flash), use it as is
  if (model.includes('/')) return model;

  // Map known short names to OpenRouter identifiers
  const lower = model.toLowerCase();
  if (lower.startsWith('gemini-2.5-flash')) {
    return 'google/gemini-2.5-flash';
  }
  if (lower.startsWith('gemini-2.5-pro')) {
    return 'google/gemini-2.5-pro';
  }
  if (lower.startsWith('gemini-1.5-flash')) {
    return 'google/gemini-1.5-flash';
  }
  if (lower.startsWith('gemini-1.5-pro')) {
    return 'google/gemini-1.5-pro';
  }

  // Fallback: prefix with google/ if not specified
  return `google/${model}`;
}

const SYSTEM_PROMPT = `The KaTeX rendering and table styling are working, but the AI Tutor still feels like a markdown document.

I do NOT want the output to look like ChatGPT notes.

I want it to look like an interactive textbook.

=========================================================
NEW RENDERING SYSTEM
=========================================================

Instead of rendering markdown sequentially:

# Heading
Paragraph

## Formula

$$F=ma$$

Table

Convert content into structured UI blocks.

=========================================================
SECTION DETECTION
=========================================================

Detect sections automatically:

Introduction
Definition
Key Concepts
Characteristics
Formula
Applications
Advantages
Disadvantages
Important Notes
Summary
Suggested Questions

Render each section as a card.

Example:

┌───────────────────────────┐
│ Quick Definition          │
│                           │
│ Photosynthesis is ...     │
└───────────────────────────┘

=========================================================
FORMULA CARD SYSTEM
=========================================================

Whenever a display formula exists:

$$
...
$$

Render:

┌───────────────────────────┐
│ Main Formula              │
│                           │
│     Rendered Formula      │
│                           │
│ [ Explain Formula ]       │
│ [ Open Formula Lab ]      │
└───────────────────────────┘

Do not leave formulas floating in text.

Every formula must become a dedicated FormulaCard component.

=========================================================
FORMULA EXTRACTION
=========================================================

During markdown parsing:

Extract all display LaTeX blocks.

Store:

{
 formula,
 title,
 surroundingContext,
 variables
}

Use this for Formula Lab.

Do not parse again later.

=========================================================
TABLE RENDERING
=========================================================

Markdown tables must render as:

Card
  -> Responsive table`;

/**
 * Generate a response from OpenRouter for a given prompt.
 * Returns an object with a `text()` method (string) and `usageMetadata`.
 * Includes exponential‑backoff retries (max 2 attempts).
 */
async function generateResponse(prompt, systemPrompt, customModel) {
  const maxAttempts = 2;
  let attempt = 0;
  
  const selectedModel = customModel && typeof customModel === 'object' ? customModel.id : (customModel || config.geminiModel);
  const openRouterModel = mapModelName(selectedModel);
  const apiKey = config.geminiApiKey ? config.geminiApiKey.trim() : '';

  while (attempt <= maxAttempts) {
    try {
      const messages = [];
      if (systemPrompt) {
        messages.push({ role: 'system', content: systemPrompt });
      }
      messages.push({ role: 'user', content: prompt });

      const requestBody = {
        model: openRouterModel,
        messages,
        temperature: 0.7,
        max_tokens: 1024
      };

      if (customModel && typeof customModel === 'object' && customModel.providerOrder) {
        requestBody.provider = { order: customModel.providerOrder, allow_fallbacks: false };
      }

      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
          'HTTP-Referer': 'http://localhost:5000',
          'X-Title': 'EduSim API'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`OpenRouter HTTP error ${response.status}: ${errorText}`);
      }

      const result = await response.json();
      
      if (result.error) {
        throw new Error(`OpenRouter API error: ${JSON.stringify(result.error)}`);
      }

      const text = result.choices?.[0]?.message?.content || '';
      const usage = result.usage || {};
      const resolvedModel = result.model || openRouterModel;
      
      const usageMetadata = {
        promptTokenCount: usage.prompt_tokens || 0,
        candidatesTokenCount: usage.completion_tokens || 0,
        totalTokenCount: usage.total_tokens || (usage.prompt_tokens || 0) + (usage.completion_tokens || 0)
      };

      return {
        text: () => text,
        usageMetadata,
        model: resolvedModel
      };
    } catch (err) {
      attempt++;
      if (attempt > maxAttempts) {
        console.error('OpenRouter request failed after retries:', err);
        throw err;
      }
      const backoff = 200 * Math.pow(2, attempt);
      await new Promise((r) => setTimeout(r, backoff));
    }
  }
}

function getModelName(customModel) {
  return mapModelName(customModel || config.geminiModel);
}

module.exports = { generateResponse, getModelName, SYSTEM_PROMPT };


