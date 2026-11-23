/**
 * System Diagnostics & Health Routes (/api/v1/system)
 */

const db = require('../db');
const pythonBridge = require('../pythonBridge');

async function handleSystemRoutes(req, res, path, method) {
  if (path === '/api/v1/system/health' && method === 'GET') {
    const pythonHealth = await pythonBridge.checkHealth();
    let dbStatus = 'ok';
    let counts = {};
    try {
      counts.students = db.prepare('SELECT COUNT(*) as cnt FROM students').get().cnt;
      counts.jobs = db.prepare('SELECT COUNT(*) as cnt FROM jobs').get().cnt;
      counts.courses = db.prepare('SELECT COUNT(*) as cnt FROM courses').get().cnt;
    } catch (e) {
      dbStatus = 'error: ' + e.message;
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      nodeVersion: process.version,
      database: { status: dbStatus, counts },
      pythonEngine: pythonHealth
    }));
    return true;
  }

  return false;
}

module.exports = { handleSystemRoutes };
