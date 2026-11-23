/**
 * Job Matching Routes (/api/v1/matching)
 */

const db = require('../db');
const { getSessionUser } = require('./auth');
const pythonBridge = require('../pythonBridge');

async function handleMatchingRoutes(req, res, path, method, body) {
  const user = getSessionUser(req);
  if (!user) {
    res.writeHead(401, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Unauthenticated' }));
    return true;
  }

  if (path === '/api/v1/matching/me' && method === 'GET') {
    // Check saved questionnaire responses
    const qRow = db.prepare('SELECT * FROM questionnaire_responses WHERE student_id = ?').get(user.studentId);
    let payload = { student_id: user.studentId };
    if (qRow) {
      payload.experience = {
        has_experience: Boolean(qRow.has_experience),
        months: qRow.experience_months || 0,
        role: qRow.experience_role || '',
        verified: Boolean(qRow.experience_verified)
      };
      if (qRow.certificates_json) {
        try { payload.certificates = JSON.parse(qRow.certificates_json); } catch (_) {}
      }
      if (qRow.test_scores_json) {
        try { payload.test_scores = JSON.parse(qRow.test_scores_json); } catch (_) {}
      }
    }

    try {
      const evaluation = await pythonBridge.evaluateStudent(payload);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        student: evaluation.student,
        experience: evaluation.experience,
        topRoles: evaluation.top_roles,
        topJobs: evaluation.top_jobs
      }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return true;
  }

  if (path.startsWith('/api/v1/matching/me/') && method === 'GET') {
    const jobId = path.split('/')[5];
    const jobRow = db.prepare('SELECT * FROM jobs WHERE job_id = ?').get(jobId);
    if (!jobRow) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: `Job with ID ${jobId} not found` }));
      return true;
    }

    // Get evaluation
    try {
      const evaluation = await pythonBridge.evaluateStudent({ student_id: user.studentId });
      const jobMatch = evaluation.top_jobs.find(j => String(j.job_id) === String(jobId));
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        job: jobRow,
        matchDetails: jobMatch || null
      }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return true;
  }

  if (path === '/api/v1/matching/evaluate' && method === 'POST') {
    const payload = body || {};
    payload.student_id = payload.student_id || user.studentId;

    try {
      const evaluation = await pythonBridge.evaluateStudent(payload);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(evaluation));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return true;
  }

  return false;
}

module.exports = { handleMatchingRoutes };
