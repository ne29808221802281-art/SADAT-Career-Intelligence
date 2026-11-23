/**
 * Fit Improvement Recommendations Routes (/api/v1/recommendations)
 */

const db = require('../db');
const { getSessionUser } = require('./auth');
const pythonBridge = require('../pythonBridge');

async function handleRecommendationsRoutes(req, res, path, method, body) {
  const user = getSessionUser(req);
  if (!user) {
    res.writeHead(401, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Unauthenticated' }));
    return true;
  }

  if (path === '/api/v1/recommendations/me' && method === 'GET') {
    // 1. Check if roadmaps exist in DB
    let roadmaps = db.prepare('SELECT * FROM student_roadmaps WHERE student_id = ?').all(user.studentId);
    
    // If not generated yet, generate by calling evaluateStudent
    if (roadmaps.length === 0) {
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
        // Deduplicate by skill: collect all entries, keep highest fit-gain per skill, track affected jobs
        const skillMap = {}; // skill -> { best entry, affectedJobs[] }
        for (const jb of evaluation.top_jobs) {
          if (jb.improve_plan) {
            for (const imp of jb.improve_plan) {
              if (imp.actions && imp.actions.length > 0) {
                const act = imp.actions[0];
                const gain = imp.est_fit_gain_pts !== null ? imp.est_fit_gain_pts : 0;
                const jobLabel = `#${jb.rank} ${jb.title}`;
                if (!skillMap[imp.skill] || gain > skillMap[imp.skill].gain) {
                  skillMap[imp.skill] = {
                    gain,
                    cause: imp.cause,
                    kind: act.kind,
                    name: act.name,
                    provider: act.provider,
                    cost: act.cost,
                    affectedJobs: [jobLabel]
                  };
                } else {
                  if (!skillMap[imp.skill].affectedJobs.includes(jobLabel)) {
                    skillMap[imp.skill].affectedJobs.push(jobLabel);
                  }
                }
              }
            }
          }
        }
        const insertRec = db.prepare(`
          INSERT INTO student_roadmaps 
          (student_id, job_id, skill, cause, action_kind, action_name, action_provider, action_cost, est_fit_gain_pts, status)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'suggested')
        `);
        for (const [skill, entry] of Object.entries(skillMap)) {
          insertRec.run(
            user.studentId,
            JSON.stringify(entry.affectedJobs), // store affected jobs list as job_id
            skill,
            entry.cause,
            entry.kind,
            entry.name,
            entry.provider,
            entry.cost,
            entry.gain || null
          );
        }
        roadmaps = db.prepare('SELECT * FROM student_roadmaps WHERE student_id = ?').all(user.studentId);
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
        return true;
      }
    }

    // Deduplicate existing roadmaps by skill (in case of legacy data) and sort by fit gain
    const deduped = {};
    for (const r of roadmaps) {
      const existing = deduped[r.skill];
      const gain = r.est_fit_gain_pts || 0;
      if (!existing || gain > (existing.est_fit_gain_pts || 0)) {
        deduped[r.skill] = r;
      }
    }
    const dedupedList = Object.values(deduped)
      .sort((a, b) => (b.est_fit_gain_pts || 0) - (a.est_fit_gain_pts || 0))
      .slice(0, 15); // top 15 unique skills max

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      studentId: user.studentId,
      totalRecommendations: dedupedList.length,
      recommendations: dedupedList
    }));
    return true;
  }

  if (path.startsWith('/api/v1/recommendations/me/') && path.endsWith('/progress') && method === 'PATCH') {
    const id = path.split('/')[5];
    const newStatus = body?.status;
    const allowed = ['suggested', 'planned', 'in_progress', 'completed'];
    if (!allowed.includes(newStatus)) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: `Invalid status. Allowed: ${allowed.join(', ')}` }));
      return true;
    }

    db.prepare('UPDATE student_roadmaps SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND student_id = ?').run(newStatus, id, user.studentId);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ success: true, id, status: newStatus }));
    return true;
  }

  return false;
}

module.exports = { handleRecommendationsRoutes };
