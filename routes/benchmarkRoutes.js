// routes/benchmarkRoutes.js - Express router for benchmark endpoints
const express = require('express');
const router = express.Router();
const benchmarkController = require('../controllers/benchmarkController');

// Run a new benchmark (accepts prompt dataset entry or custom prompt)
router.post('/run', benchmarkController.runBenchmark);

// Run a batch benchmark across all 12 registered models
router.post('/batch-run', benchmarkController.runBatchBenchmark);

// Evaluate a previously stored response (optional separate endpoint)
router.post('/evaluate', benchmarkController.evaluateResponse);

// Get all benchmark results (with optional filters)
router.get('/results', benchmarkController.getResults);

// Leaderboard based on scores
router.get('/leaderboard', benchmarkController.getLeaderboard);

// Analytics summary
router.get('/analytics', benchmarkController.getAnalytics);

// History of runs for a model or task type
router.get('/history', benchmarkController.getHistory);

module.exports = router;
