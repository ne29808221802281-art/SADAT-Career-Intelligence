/**
 * Python Intelligence Service Bridge
 * Dispatches RPC calls to the internal Python execution layer on http://127.0.0.1:8000
 * with graceful in-process CLI fallback if the HTTP daemon is starting.
 */

const { execFileSync } = require('node:child_process');
const path = require('node:path');
const config = require('./config');

const PYTHON_SERVICE_URL = config.PYTHON_SERVICE_URL;

async function checkHealth() {
  try {
    const res = await fetch(`${PYTHON_SERVICE_URL}/internal/health`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    // Return offline status
  }
  return { status: 'offline', message: 'Python service not reachable on ' + PYTHON_SERVICE_URL };
}

async function evaluateStudent(payload) {
  // 1. Try internal HTTP RPC service
  try {
    const res = await fetch(`${PYTHON_SERVICE_URL}/internal/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-Token': config.INTERNAL_API_SECRET
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(6000)
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (httpErr) {
    // Fall back to direct CLI execution via Orange Python
  }

  // 2. Direct Python CLI execution fallback
  try {
    const script = `
import sys, json
import numpy as np
sys.path.insert(0, r"${path.join(config.ROOT_DIR, 'services', 'intelligence')}")
from matcher import evaluate_student

def default_json(o):
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, (np.integer, int)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return float(o)
    return str(o)

payload = json.loads(sys.stdin.read())
res = evaluate_student(
    student_id=payload.get("student_id"),
    custom_grades=payload.get("custom_grades"),
    experience=payload.get("experience"),
    test_scores=payload.get("test_scores"),
    certificates=payload.get("certificates")
)
print(json.dumps(res, default=default_json, ensure_ascii=False))
`;
    const output = execFileSync(
      config.PYTHON_EXECUTABLE,
      ['-c', script],
      {
        input: JSON.stringify(payload),
        encoding: 'utf-8',
        maxBuffer: 20 * 1024 * 1024
      }
    );
    return JSON.parse(output.trim());
  } catch (cliErr) {
    console.error('[PythonBridge Error]:', cliErr.message);
    throw new Error('Failed to execute matching intelligence: ' + cliErr.message);
  }
}

async function getMissingSkills() {
  try {
    const res = await fetch(`${PYTHON_SERVICE_URL}/internal/missing-skills`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) return await res.json();
  } catch (_) {}

  // Fallback
  const script = `
import sys, json
sys.path.insert(0, r"${path.join(config.ROOT_DIR, 'services', 'intelligence')}")
from engine import MISSING_SKILLS_14
print(json.dumps(MISSING_SKILLS_14, ensure_ascii=False))
`;
  const output = execFileSync(config.PYTHON_EXECUTABLE, ['-c', script], { encoding: 'utf-8' });
  return JSON.parse(output.trim());
}

async function getCertificates() {
  try {
    const res = await fetch(`${PYTHON_SERVICE_URL}/internal/certificates`, { signal: AbortSignal.timeout(2000) });
    if (res.ok) return await res.json();
  } catch (_) {}

  const script = `
import sys, json
sys.path.insert(0, r"${path.join(config.ROOT_DIR, 'services', 'intelligence')}")
from engine import CERTIFICATES
certs = [{"name": c[0], "provider": c[1], "skills": c[3]} for c in CERTIFICATES]
print(json.dumps(certs, ensure_ascii=False))
`;
  const output = execFileSync(config.PYTHON_EXECUTABLE, ['-c', script], { encoding: 'utf-8' });
  return JSON.parse(output.trim());
}

module.exports = {
  checkHealth,
  evaluateStudent,
  getMissingSkills,
  getCertificates
};
