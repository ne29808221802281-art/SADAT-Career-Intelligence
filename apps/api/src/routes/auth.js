/**
 * Authentication Routes (/api/v1/auth)
 * Implements OIDC session handling and verified student profile resolution.
 */

const config = require('../config');
const db = require('../db');

function parseCookies(cookieHeader) {
  const list = {};
  if (!cookieHeader) return list;
  cookieHeader.split(';').forEach(cookie => {
    let [name, ...rest] = cookie.split('=');
    name = name?.trim();
    if (!name) return;
    const value = rest.join('=').trim();
    list[name] = decodeURIComponent(value);
  });
  return list;
}

function getSessionUser(req) {
  const cookies = parseCookies(req.headers.cookie);
  const sessionToken = cookies[config.SESSION_COOKIE_NAME];

  // In mock mode, check for ?studentId= query param override (for student switching)
  if (config.AUTH_MOCK_ENABLED) {
    let overrideId = null;
    if (req.url && req.url.includes('studentId=')) {
      const qs = req.url.split('?')[1] || '';
      const params = new URLSearchParams(qs);
      overrideId = params.get('studentId');
    }
    const lookupId = overrideId || config.DEFAULT_STUDENT_ID;
    const student = db.prepare('SELECT * FROM students WHERE student_id = ?').get(lookupId);
    if (student) {
      return {
        studentId: student.student_id,
        fullName: student.full_name,
        email: student.email,
        gpa: student.gpa,
        gradeLabel: student.grade_label,
        role: student.role
      };
    }
    // fallback to default if override id not found
    if (overrideId) {
      const fallback = db.prepare('SELECT * FROM students WHERE student_id = ?').get(config.DEFAULT_STUDENT_ID);
      if (fallback) {
        return {
          studentId: fallback.student_id,
          fullName: fallback.full_name,
          email: fallback.email,
          gpa: fallback.gpa,
          gradeLabel: fallback.grade_label,
          role: fallback.role
        };
      }
    }
  }

  if (!sessionToken) return null;

  try {
    const payload = JSON.parse(Buffer.from(sessionToken, 'base64').toString('utf8'));
    const student = db.prepare('SELECT * FROM students WHERE student_id = ?').get(payload.studentId);
    if (!student) return null;
    return {
      studentId: student.student_id,
      fullName: student.full_name,
      email: student.email,
      gpa: student.gpa,
      gradeLabel: student.grade_label,
      role: student.role
    };
  } catch (err) {
    return null;
  }
}

function handleAuthRoutes(req, res, path, method) {
  if (path === '/api/v1/auth/me' && method === 'GET') {
    const user = getSessionUser(req);
    if (!user) {
      res.writeHead(401, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ error: 'Unauthenticated' }));
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify(user));
  }

  if (path === '/api/v1/auth/login' && method === 'GET') {
    // Return mock or OIDC auth redirect
    if (config.AUTH_MOCK_ENABLED) {
      const studentId = config.DEFAULT_STUDENT_ID;
      const sessionData = Buffer.from(JSON.stringify({ studentId, timestamp: Date.now() })).toString('base64');
      res.writeHead(302, {
        'Set-Cookie': `${config.SESSION_COOKIE_NAME}=${sessionData}; Path=/; HttpOnly; SameSite=Lax`,
        'Location': '/'
      });
      return res.end();
    }
    // Redirect to OIDC provider
    res.writeHead(302, { 'Location': `${config.OIDC_AUTHORIZATION_URL}?client_id=${config.OIDC_CLIENT_ID}&response_type=code` });
    return res.end();
  }

  if (path === '/api/v1/auth/logout' && method === 'POST') {
    res.writeHead(200, {
      'Set-Cookie': `${config.SESSION_COOKIE_NAME}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly`,
      'Content-Type': 'application/json'
    });
    return res.end(JSON.stringify({ success: true, message: 'Logged out successfully' }));
  }

  return false;
}

module.exports = {
  handleAuthRoutes,
  getSessionUser
};
