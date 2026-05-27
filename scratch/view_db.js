// scratch/view_db.js - Quick, accurate database viewer
require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
const mongoose = require('mongoose');
const BenchmarkRun = require('../models/BenchmarkRun');

async function view() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    const runs = await BenchmarkRun.find().sort({ timestamp: -1 }).lean();
    
    if (runs.length === 0) {
      console.log('No evaluations found in database.');
    } else {
      console.log('\n--- Accurate MongoDB Stored Benchmark Runs ---\n');
      console.table(runs.map(r => ({
        Model: r.model.replace('google/', '').substring(0, 20),
        Task: r.taskType,
        Latency: `${r.latencyMs}ms`,
        Accuracy: r.accuracyScore,
        Quality: r.qualityScore,
        Educational: r.educationalScore,
        Feedback: (r.feedback || '').substring(0, 50) + '...'
      })));
    }
  } catch (err) {
    console.error('Error reading from MongoDB:', err.message);
  } finally {
    await mongoose.disconnect();
  }
}

view();
