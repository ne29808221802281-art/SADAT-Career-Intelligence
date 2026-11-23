/**
 * Application Configuration
 */
const path = require('node:path');

const ROOT_DIR = path.resolve(__dirname, '../../..');
const DATA_DIR = path.join(ROOT_DIR, 'data');
const STORAGE_DIR = path.join(ROOT_DIR, 'storage');

module.exports = {
  PORT: process.env.PORT || 5000,
  PYTHON_SERVICE_URL: process.env.PYTHON_SERVICE_URL || 'http://127.0.0.1:8000',
  PYTHON_EXECUTABLE: process.env.PYTHON_EXECUTABLE || 'C:\\Users\\elmasria\\AppData\\Local\\Programs\\Orange\\python.exe',
  ROOT_DIR,
  DATA_DIR,
  STORAGE_DIR,
  DB_PATH: path.join(ROOT_DIR, 'sadat_career_db.sqlite'),
  SESSION_COOKIE_NAME: 'sadat_session',
  SESSION_SECRET: process.env.SESSION_SECRET || 'sadat_session_secret_2026_salt',
  AUTH_MOCK_ENABLED: process.env.AUTH_MOCK_ENABLED !== 'false',
  DEFAULT_STUDENT_ID: process.env.AUTH_DEFAULT_STUDENT_ID || 'SAD20260001',
  INTERNAL_API_SECRET: process.env.INTERNAL_API_SECRET || 'sadat_internal_secret_2026'
};
