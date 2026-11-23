/**
 * Job Market & Cohort Intelligence Routes (/api/v1/market)
 */

const db = require('../db');

function handleMarketRoutes(req, res, path, method, query) {
  if (path === '/api/v1/market/overview' && method === 'GET') {
    const totalJobs = db.prepare('SELECT COUNT(*) as cnt FROM jobs').get().cnt;
    const totalStudents = db.prepare('SELECT COUNT(*) as cnt FROM students').get().cnt;
    const topGapSkills = db.prepare('SELECT * FROM market_insights ORDER BY gap_score DESC LIMIT 5').all();
    const topRoles = db.prepare('SELECT * FROM role_summaries ORDER BY cohort_mean_match DESC LIMIT 3').all();

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      totalJobs,
      totalStudentsCohort: totalStudents,
      topGapSkills,
      topRoles
    }));
    return true;
  }

  if (path === '/api/v1/market/skills' && method === 'GET') {
    const skills = db.prepare('SELECT * FROM market_insights ORDER BY gap_score DESC').all();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      total: skills.length,
      skills
    }));
    return true;
  }

  if (path === '/api/v1/market/roles' && method === 'GET') {
    const roles = db.prepare('SELECT * FROM role_summaries ORDER BY cohort_mean_match DESC').all();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      total: roles.length,
      roles
    }));
    return true;
  }

  if (path === '/api/v1/market/jobs' && method === 'GET') {
    let sql = 'SELECT * FROM jobs WHERE 1=1';
    const params = [];

    if (query?.specialization) {
      sql += ' AND specialization = ?';
      params.push(query.specialization);
    }
    if (query?.work_mode) {
      sql += ' AND work_mode = ?';
      params.push(query.work_mode);
    }
    if (query?.level) {
      sql += ' AND level = ?';
      params.push(query.level);
    }

    sql += ' ORDER BY job_id ASC LIMIT 100';
    const jobs = db.prepare(sql).all(...params);

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      total: jobs.length,
      jobs
    }));
    return true;
  }

  return false;
}

module.exports = { handleMarketRoutes };
