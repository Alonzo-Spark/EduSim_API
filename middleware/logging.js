// middleware/logging.js - Production-ready structured request logging middleware
module.exports = (req, res, next) => {
  const start = Date.now();

  // Attach finish event listener to calculate duration and log metrics
  res.on('finish', () => {
    const duration = Date.now() - start;
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] ${req.method} ${req.originalUrl} - Status: ${res.statusCode} (${duration}ms)`);
  });

  next();
};
