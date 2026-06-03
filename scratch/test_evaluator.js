// scratch/test_evaluator.js - Diagnostic script to test different Claude and Gemini models
require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });

const apiKey = (process.env.GEMINI_API_KEY || process.env.OPENROUTER_API_KEY || '').trim();

const modelsToTest = [
  'anthropic/claude-3.5-sonnet',
  'anthropic/claude-3.5-haiku',
  'anthropic/claude-3-haiku',
  'google/gemini-2.0-flash-lite-001',
  'qwen/qwen3-235b-a22b-2507'
];

async function testModel(modelId) {
  console.log(`[TEST] Testing model: ${modelId}...`);
  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'EduSim Model Test'
      },
      body: JSON.stringify({
        model: modelId,
        messages: [{ role: 'user', content: 'Say "hello" and nothing else.' }],
        temperature: 0.2,
        max_tokens: 10
      })
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error(`  -> Failed with HTTP ${response.status}: ${errText}`);
      return false;
    }

    const data = await response.json();
    if (data.error) {
      console.error(`  -> Failed with API error: ${JSON.stringify(data.error)}`);
      return false;
    }

    console.log(`  -> Success! Response: "${data.choices?.[0]?.message?.content?.trim()}"`);
    return true;
  } catch (err) {
    console.error(`  -> Failed with error: ${err.message}`);
    return false;
  }
}

async function run() {
  console.log(`Using API key: ${apiKey.substring(0, 10)}...${apiKey.substring(apiKey.length - 4)}`);
  for (const model of modelsToTest) {
    await testModel(model);
    console.log('');
  }
}

run();
