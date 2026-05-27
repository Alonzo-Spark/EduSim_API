// server.js - entry point for EduSim benchmarking API
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const mongoose = require('mongoose');
const benchmarkRoutes = require('./routes/benchmarkRoutes');
const loggingMiddleware = require('./middleware/logging');
const errorMiddleware = require('./middleware/error');

const app = express();
const PORT = process.env.PORT || 5000;

// Global Middleware
app.use(cors());
app.use(bodyParser.json());
app.use(loggingMiddleware); // Structured request logging

// Connect to MongoDB
async function connectDB() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('MongoDB connected successfully');
  } catch (err) {
    console.error('MongoDB connection error:', err);
    process.exit(1);
  }
}

connectDB();

// Routes
app.use('/api/benchmark', benchmarkRoutes);

// Friendly root endpoint (optional)
app.get('/', (req, res) => {
  res.send('EduSim Multi-LLM Benchmarking API is running. Use /api/benchmark/* endpoints.');
});

// Centralised Global Error Handler Middleware
app.use(errorMiddleware);

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
