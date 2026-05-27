// middleware/error.js - Production-ready centralised error handling middleware
module.exports = (err, req, res, next) => {
  const timestamp = new Date().toISOString();
  console.error(`[${timestamp}] Unhandled Error at ${req.method} ${req.originalUrl}:`, err);

  const status = err.statusCode || err.status || 500;
  const message = err.message || 'Internal Server Error';

  // Hides stack traces in production, returns standard JSON response
  res.status(status).json({
    error: {
      message,
      statusCode: status,
      timestamp
    }
  });
};
