/**
 * Questionnaire & Evidence Routes (/api/v1/questionnaire)
 */

const db = require('../db');
const { getSessionUser } = require('./auth');
const pythonBridge = require('../pythonBridge');

async function handleQuestionnaireRoutes(req, res, path, method, body) {
  const user = getSessionUser(req);
  if (!user) {
    res.writeHead(401, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Unauthenticated' }));
    return true;
  }

  if (path === '/api/v1/questionnaire' && method === 'GET') {
    const certs = await pythonBridge.getCertificates();
    const roles = db.prepare('SELECT role FROM role_summaries').all().map(r => r.role);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      recognizedCertificates: certs,
      technicalTracks: roles,
      evidenceSources: [
        { id: 'certificate_verified', name: 'Verified International Certificate', weight: 0.9 },
        { id: 'experience_verified', name: 'Verified Work Experience', weight: 0.8 },
        { id: 'online_test', name: 'Online Test Score', weight: 0.7 },
        { id: 'certificate_claimed', name: 'Claimed Certificate', weight: 0.5 },
        { id: 'experience_claimed', name: 'Claimed Work Experience', weight: 0.5 },
        { id: 'self_rating', name: 'Self-Rating', weight: 0.3 }
      ]
    }));
    return true;
  }

  if (path === '/api/v1/questionnaire/responses' && method === 'GET') {
    const row = db.prepare('SELECT * FROM questionnaire_responses WHERE student_id = ?').get(user.studentId);
    if (!row) {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        hasExperience: false,
        experienceMonths: 0,
        experienceRole: '',
        experienceVerified: false,
        certificates: [],
        testScores: {},
        selfRatings: {}
      }));
      return true;
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      hasExperience: Boolean(row.has_experience),
      experienceMonths: row.experience_months || 0,
      experienceRole: row.experience_role || '',
      experienceVerified: Boolean(row.experience_verified),
      certificates: row.certificates_json ? JSON.parse(row.certificates_json) : [],
      testScores: row.test_scores_json ? JSON.parse(row.test_scores_json) : {},
      selfRatings: row.self_ratings_json ? JSON.parse(row.self_ratings_json) : {}
    }));
    return true;
  }

  if (path === '/api/v1/questionnaire/responses' && method === 'POST') {
    const payload = body || {};
    const hasExp = Boolean(payload.hasExperience);
    const expMonths = Math.max(0, Math.min(240, Number(payload.experienceMonths) || 0));
    const expRole = payload.experienceRole || '';
    const expVerified = Boolean(payload.experienceVerified);
    const certsJson = JSON.stringify(Array.isArray(payload.certificates) ? payload.certificates : []);
    const testsJson = JSON.stringify(payload.testScores && typeof payload.testScores === 'object' ? payload.testScores : {});
    const ratingsJson = JSON.stringify(payload.selfRatings && typeof payload.selfRatings === 'object' ? payload.selfRatings : {});

    // Save to database
    db.prepare(`
      INSERT OR REPLACE INTO questionnaire_responses
      (student_id, has_experience, experience_months, experience_role, experience_verified, certificates_json, test_scores_json, self_ratings_json, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    `).run(user.studentId, hasExp ? 1 : 0, expMonths, expRole, expVerified ? 1 : 0, certsJson, testsJson, ratingsJson);

    // Trigger full reevaluation with the authoritative Python engine
    try {
      const evaluation = await pythonBridge.evaluateStudent({
        student_id: user.studentId,
        experience: {
          has_experience: hasExp,
          months: expMonths,
          role: expRole,
          verified: expVerified
        },
        test_scores: payload.testScores,
        certificates: payload.certificates
      });

      // Update student roadmap recommendations table - deduplicated by skill
      db.prepare('DELETE FROM student_roadmaps WHERE student_id = ?').run(user.studentId);
      const insertRec = db.prepare(`
        INSERT INTO student_roadmaps 
        (student_id, job_id, skill, cause, action_kind, action_name, action_provider, action_cost, est_fit_gain_pts, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'suggested')
      `);

      // Collect all recommendations, deduplicate by skill (keep highest fit-gain)
      const skillMap = {};
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
      for (const [skill, entry] of Object.entries(skillMap)) {
        insertRec.run(
          user.studentId,
          JSON.stringify(entry.affectedJobs),
          skill,
          entry.cause,
          entry.kind,
          entry.name,
          entry.provider,
          entry.cost,
          entry.gain || null
        );
      }

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: true,
        message: 'Questionnaire updated and matching re-evaluated successfully',
        evaluation
      }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return true;
  }

  return false;
}

module.exports = { handleQuestionnaireRoutes };
