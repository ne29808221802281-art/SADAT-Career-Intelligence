/**
 * SADAT Career Intelligence Portal - Main Node.js API Server
 */

const http = require('node:http');
const url = require('node:url');
const fs = require('node:fs');
const path = require('node:path');
const config = require('./config');

// Route modules
const { handleAuthRoutes } = require('./routes/auth');
const { handleStudentRoutes } = require('./routes/students');
const { handleQuestionnaireRoutes } = require('./routes/questionnaire');
const { handleMatchingRoutes } = require('./routes/matching');
const { handleRecommendationsRoutes } = require('./routes/recommendations');
const { handleFreeTestsRoutes } = require('./routes/freeTests');
const { handleMarketRoutes } = require('./routes/market');
const { handleDocumentRoutes } = require('./routes/documents');
const { handleSystemRoutes } = require('./routes/system');

const WEB_DIR = path.join(config.ROOT_DIR, 'apps', 'web', 'public');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

const server = http.createServer(async (req, res) => {
  // Global CORS & Security Headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'SAMEORIGIN');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    return res.end();
  }

  const parsedUrl = url.parse(req.url, true);
  const pathName = parsedUrl.pathname;
  const method = req.method;
  const query = parsedUrl.query;

  // Buffer incoming request body
  const chunks = [];
  req.on('data', chunk => chunks.push(chunk));
  req.on('end', async () => {
    const rawBuffer = Buffer.concat(chunks);
    let jsonBody = null;
    const contentType = req.headers['content-type'] || '';
    if (contentType.includes('application/json') && rawBuffer.length > 0) {
      try {
        jsonBody = JSON.parse(rawBuffer.toString('utf8'));
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ error: 'Invalid JSON payload' }));
      }
    }

    try {
      // 1. API Route Dispatching
      if (pathName.startsWith('/api/v1/auth')) {
        if (handleAuthRoutes(req, res, pathName, method, jsonBody)) return;
      }
      if (pathName.startsWith('/api/v1/students')) {
        if (await handleStudentRoutes(req, res, pathName, method, jsonBody, query)) return;
      }
      if (pathName.startsWith('/api/v1/questionnaire')) {
        if (await handleQuestionnaireRoutes(req, res, pathName, method, jsonBody)) return;
      }
      if (pathName.startsWith('/api/v1/matching')) {
        if (await handleMatchingRoutes(req, res, pathName, method, jsonBody)) return;
      }
      if (pathName.startsWith('/api/v1/recommendations')) {
        if (await handleRecommendationsRoutes(req, res, pathName, method, jsonBody)) return;
      }
      if (pathName.startsWith('/api/v1/free-tests')) {
        if (await handleFreeTestsRoutes(req, res, pathName, method, jsonBody)) return;
      }
      if (pathName.startsWith('/api/v1/market')) {
        if (handleMarketRoutes(req, res, pathName, method, query)) return;
      }
      if (pathName.startsWith('/api/v1/documents')) {
        if (handleDocumentRoutes(req, res, pathName, method, rawBuffer, req.headers)) return;
      }
      if (pathName.startsWith('/api/v1/system')) {
        if (await handleSystemRoutes(req, res, pathName, method)) return;
      }

      // If it's an API route and not matched:
      if (pathName.startsWith('/api/')) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ error: `API route ${pathName} not found` }));
      }

      // 2. Static Web Serving
      let filePath = path.join(WEB_DIR, pathName === '/' ? 'index.html' : pathName);
      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        filePath = path.join(WEB_DIR, 'index.html');
      }

      if (fs.existsSync(filePath)) {
        const ext = path.extname(filePath).toLowerCase();
        const mimeType = MIME_TYPES[ext] || 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': mimeType });
        return fs.createReadStream(filePath).pipe(res);
      }

      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
    } catch (err) {
      console.error('[Server Error]:', err);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Internal Server Error: ' + err.message }));
    }
  });
});

const PORT = config.PORT;
server.listen(PORT, '0.0.0.0', () => {
  console.log(`[SADAT API Server] Running on http://127.0.0.1:${PORT}`);
});

module.exports = server;
