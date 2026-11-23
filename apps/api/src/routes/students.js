/**
 * Student & Academic Records Routes (/api/v1/students)
 */

const db = require('../db');
const { getSessionUser } = require('./auth');
const pythonBridge = require('../pythonBridge');

async function handleStudentRoutes(req, res, path, method) {
  const user = getSessionUser(req);
  if (!user) {
    res.writeHead(401, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Unauthenticated' }));
    return true;
  }

  if (path === '/api/v1/students/me' && method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(user));
    return true;
  }

  if (path === '/api/v1/students/me/academic-records' && method === 'GET') {
    const grades = db.prepare(`
      SELECT sg.course_id, sg.course_name, c.year, sg.mark, sg.credit_hours 
      FROM student_grades sg
      LEFT JOIN courses c ON sg.course_id = c.course_id
      WHERE sg.student_id = ?
      ORDER BY c.year ASC, sg.course_id ASC
    `).all(user.studentId);

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      studentId: user.studentId,
      totalCourses: grades.length,
      courses: grades
    }));
    return true;
  }

  if (path === '/api/v1/students/me/skills' && method === 'GET') {
    // Check if questionnaire exists for this student
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
        studentId: user.studentId,
        skills: evaluation.skills_summary,
        topRoles: evaluation.top_roles
      }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    }
    return true;
  }

  // Support cohort switching for academic advisors / simulation
  if (path === '/api/v1/students/cohort' && method === 'GET') {
    const students = db.prepare('SELECT student_id, full_name, gpa, grade_label FROM students ORDER BY student_id ASC LIMIT 50').all();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ cohort: students }));
    return true;
  }

  return false;
}

module.exports = { handleStudentRoutes };
