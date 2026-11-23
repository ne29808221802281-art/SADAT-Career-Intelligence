/**
 * Document Uploads Routes (/api/v1/documents)
 */

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const config = require('../config');
const db = require('../db');
const { getSessionUser } = require('./auth');

function handleDocumentRoutes(req, res, pathStr, method, bodyBuffer, headers) {
  const user = getSessionUser(req);
  if (!user) {
    res.writeHead(401, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Unauthenticated' }));
    return true;
  }

  if (pathStr === '/api/v1/documents/upload' && method === 'POST') {
    const docId = crypto.randomUUID();
    const contentType = headers['content-type'] || 'application/octet-stream';
    const ext = contentType.includes('pdf') ? '.pdf' : contentType.includes('png') ? '.png' : '.jpg';
    const filename = `doc_${user.studentId}_${Date.now()}${ext}`;
    const storedPath = path.join(config.STORAGE_DIR, filename);

    fs.writeFileSync(storedPath, bodyBuffer);

    db.prepare(`
      INSERT INTO document_uploads (id, student_id, filename, stored_path, mime_type, file_size, verification_status)
      VALUES (?, ?, ?, ?, ?, ?, 'pending')
    `).run(docId, user.studentId, filename, storedPath, contentType, bodyBuffer.length);

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: true,
      documentId: docId,
      filename,
      fileSize: bodyBuffer.length,
      verificationStatus: 'pending'
    }));
    return true;
  }

  if (pathStr === '/api/v1/documents' && method === 'GET') {
    const docs = db.prepare('SELECT id, student_id, filename, mime_type, file_size, verification_status, uploaded_at FROM document_uploads WHERE student_id = ?').all(user.studentId);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ documents: docs }));
    return true;
  }

  return false;
}

module.exports = { handleDocumentRoutes };
