/**
 * 14 Missing Skills & Free Tests Center Routes (/api/v1/free-tests)
 */

const { getSessionUser } = require('./auth');
const pythonBridge = require('../pythonBridge');

async function handleFreeTestsRoutes(req, res, path, method, body) {
  if (path === '/api/v1/free-tests' && method === 'GET') {
    try {
      const skills = await pythonBridge.getMissingSkills();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        total: skills.length,
        missingSkills: skills
      }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return true;
  }

  if (path === '/api/v1/free-tests/preview' && method === 'POST') {
    const user = getSessionUser(req);
    const studentId = user ? user.studentId : 'SAD20260001';
    const testScores = body?.testScores || {};

    try {
      // Execute evaluation with preview test scores
      const evaluation = await pythonBridge.evaluateStudent({
        student_id: studentId,
        test_scores: testScores
      });

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        previewScores: testScores,
        topRoles: evaluation.top_roles,
        topJobs: evaluation.top_jobs
      }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return true;
  }

  return false;
}

module.exports = { handleFreeTestsRoutes };
