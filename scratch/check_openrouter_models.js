require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });

async function checkModels() {
  const apiKey = process.env.OPENROUTER_API_KEY;
  console.log(`Checking OpenRouter API Key: ${apiKey ? apiKey.substring(0, 15) + '...' : 'MISSING'}`);
  
  try {
    const res = await fetch('https://openrouter.ai/api/v1/models', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    });
    
    if (!res.ok) {
      console.error(`HTTP Error: ${res.status} ${res.statusText}`);
      const text = await res.text();
      console.error(text);
      return;
    }
    
    const data = await res.json();
    console.log(`Total models found on OpenRouter: ${data.data?.length || 0}`);
    
    const matches = (data.data || []).filter(m => 
      m.id.toLowerCase().includes('claude') || 
      m.id.toLowerCase().includes('qwen') || 
      m.id.toLowerCase().includes('glm')
    );
    
    console.log('\nMatching Models:');
    matches.forEach(m => {
      console.log(`- ID: ${m.id} | Name: ${m.name} | Context: ${m.context_length}`);
    });
  } catch (err) {
    console.error('Error fetching models:', err);
  }
}

checkModels();
