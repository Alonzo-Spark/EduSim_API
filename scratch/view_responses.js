// scratch/view_responses.js - View full model responses and judge feedback in the terminal
require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
const mongoose = require('mongoose');
const BenchmarkRun = require('../models/BenchmarkRun');

async function run() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    
    // Fetch the latest 5 benchmark runs
    const runs = await BenchmarkRun.find().sort({ timestamp: -1 }).limit(5).lean();
    
    if (runs.length === 0) {
      console.log('No benchmark runs found in MongoDB.');
      await mongoose.disconnect();
      return;
    }
    
    console.log(`\n===============================================================`);
    console.log(`🔍 VIEWING THE LATEST ${runs.length} DETAILED BENCHMARK RUN RESPONSES`);
    console.log(`===============================================================\n`);
    
    for (let idx = 0; idx < runs.length; idx++) {
      const r = runs[idx];
      console.log(`---------------------------------------------------------------`);
      console.log(`[RUN ${idx + 1}] Model   : ${r.model}`);
      console.log(`        Task    : ${r.taskType}`);
      console.log(`        Latency : ${r.latencyMs}ms`);
      console.log(`        Cost    : $${r.estimatedCost.toFixed(6)}`);
      console.log(`        Scores  : Accuracy: ${r.accuracyScore}/10 | Quality: ${r.qualityScore}/10 | Educational: ${r.educationalScore}/10`);
      console.log(`---------------------------------------------------------------`);
      console.log(`\nPROMPT:\n"${r.prompt}"\n`);
      console.log(`LLM RESPONSE:\n`);
      console.log(r.response);
      console.log(`\nAI JUDGE FEEDBACK:\n"${r.feedback}"\n`);
      console.log(`===============================================================\n`);
    }
    
  } catch (err) {
    console.error('Error reading responses from MongoDB:', err.message);
  } finally {
    await mongoose.disconnect();
  }
}

run();
