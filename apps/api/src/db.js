/**
 * Database Initialization & Data Layer
 * Embedded high-performance store with automatic CSV seeding from data/
 */

const fs = require('node:fs');
const path = require('node:path');
const { DatabaseSync } = require('node:sqlite');
const config = require('./config');

// Ensure storage directory exists
if (!fs.existsSync(config.STORAGE_DIR)) {
  fs.mkdirSync(config.STORAGE_DIR, { recursive: true });
}

const db = new DatabaseSync(config.DB_PATH);

// Simple, robust CSV parser for seeding
function parseCsv(content) {
  const lines = content.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
  if (lines.length === 0 || !lines[0].trim()) return [];

  const headers = parseCsvLine(lines[0]);
  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const values = parseCsvLine(lines[i]);
    const obj = {};
    for (let j = 0; j < headers.length; j++) {
      obj[headers[j]] = values[j] !== undefined ? values[j] : null;
    }
    rows.push(obj);
  }
  return rows;
}

function parseCsvLine(text) {
  const result = [];
  let cur = '';
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      if (inQuotes && text[i + 1] === '"') {
        cur += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (c === ',' && !inQuotes) {
      result.push(cur.trim());
      cur = '';
    } else {
      cur += c;
    }
  }
  result.push(cur.trim());
  return result;
}

function initDatabase() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS students (
      student_id TEXT PRIMARY KEY,
      full_name TEXT NOT NULL,
      email TEXT,
      gpa REAL NOT NULL,
      grade_label TEXT NOT NULL,
      cohort_year INTEGER DEFAULT 2026,
      role TEXT DEFAULT 'student',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS courses (
      course_id TEXT PRIMARY KEY,
      year INTEGER NOT NULL,
      course_name TEXT NOT NULL,
      credit_hours INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS course_skill_mappings (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      course_id TEXT NOT NULL,
      skill TEXT NOT NULL,
      relevance REAL NOT NULL,
      evidence_weight REAL,
      confidence TEXT,
      notes TEXT
    );

    CREATE TABLE IF NOT EXISTS student_grades (
      student_id TEXT NOT NULL,
      course_id TEXT NOT NULL,
      course_name TEXT NOT NULL,
      mark REAL NOT NULL,
      credit_hours INTEGER NOT NULL,
      PRIMARY KEY (student_id, course_id)
    );

    CREATE TABLE IF NOT EXISTS jobs (
      job_id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      specialization TEXT NOT NULL,
      company TEXT NOT NULL,
      company_country TEXT,
      job_location TEXT,
      work_mode TEXT NOT NULL,
      level TEXT NOT NULL,
      years_exp_min REAL,
      years_exp_max REAL,
      technical_requirements TEXT NOT NULL,
      certifications_mentioned TEXT,
      employment_type TEXT,
      linkedin_seniority TEXT,
      posted TEXT,
      url TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS market_insights (
      skill TEXT PRIMARY KEY,
      demand_entry_pct REAL,
      demand_all_pct REAL,
      cohort_mean_pct REAL,
      cohort_ready_pct REAL,
      curriculum_evidence REAL,
      gap_score REAL
    );

    CREATE TABLE IF NOT EXISTS role_summaries (
      role TEXT PRIMARY KEY,
      cohort_mean_match REAL,
      cohort_median_match REAL,
      best_student_match REAL,
      ads_used INTEGER,
      entry_level_ads INTEGER,
      basis TEXT,
      core_skills TEXT
    );

    CREATE TABLE IF NOT EXISTS questionnaire_responses (
      student_id TEXT PRIMARY KEY,
      has_experience INTEGER DEFAULT 0,
      experience_months REAL DEFAULT 0,
      experience_role TEXT,
      experience_verified INTEGER DEFAULT 0,
      certificates_json TEXT,
      test_scores_json TEXT,
      self_ratings_json TEXT,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS student_roadmaps (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      student_id TEXT NOT NULL,
      job_id TEXT,
      skill TEXT NOT NULL,
      cause TEXT NOT NULL,
      action_kind TEXT,
      action_name TEXT NOT NULL,
      action_provider TEXT,
      action_cost TEXT,
      est_fit_gain_pts REAL,
      status TEXT DEFAULT 'suggested',
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS document_uploads (
      id TEXT PRIMARY KEY,
      student_id TEXT NOT NULL,
      filename TEXT NOT NULL,
      stored_path TEXT NOT NULL,
      mime_type TEXT NOT NULL,
      file_size INTEGER NOT NULL,
      verification_status TEXT DEFAULT 'pending',
      uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
      event TEXT NOT NULL,
      student_id TEXT,
      details TEXT
    );
  `);

  // Check if initial seeding is needed
  const studentCount = db.prepare('SELECT COUNT(*) as cnt FROM students').get().cnt;
  if (studentCount === 0) {
    console.log('[DB] Seeding database from CSVs in data/ ...');
    seedFromCsv();
  }
}

function seedFromCsv() {
  const dataDir = config.DATA_DIR;

  // 1. Course catalog
  const coursesCsv = path.join(dataDir, 'course_catalog.csv');
  if (fs.existsSync(coursesCsv)) {
    const courses = parseCsv(fs.readFileSync(coursesCsv, 'utf8'));
    const stmt = db.prepare('INSERT OR REPLACE INTO courses (course_id, year, course_name, credit_hours) VALUES (?, ?, ?, ?)');
    for (const c of courses) {
      stmt.run(c.Course_ID, Number(c.Year) || 1, c.Course_Name, Number(c.Credit_Hours) || 3);
    }
    console.log(`[DB] Loaded ${courses.length} courses.`);
  }

  // 2. Course skill map
  const cmapCsv = path.join(dataDir, 'course_skill_map.csv');
  if (fs.existsSync(cmapCsv)) {
    const mappings = parseCsv(fs.readFileSync(cmapCsv, 'utf8'));
    const stmt = db.prepare('INSERT INTO course_skill_mappings (course_id, skill, relevance, evidence_weight, confidence, notes) VALUES (?, ?, ?, ?, ?, ?)');
    for (const m of mappings) {
      if (!m.Course_ID || !m.Skill) continue;
      stmt.run(
        m.Course_ID,
        m.Skill,
        parseFloat(m.rel) || 0.5,
        parseFloat(m.Evidence_Weight) || 1.5,
        m.Confidence || 'M',
        m.Notes || ''
      );
    }
    console.log(`[DB] Loaded ${mappings.length} course-skill mappings.`);
  }

  // 3. Students info
  const studentsCsv = path.join(dataDir, 'students_info.csv');
  if (fs.existsSync(studentsCsv)) {
    const students = parseCsv(fs.readFileSync(studentsCsv, 'utf8'));
    const stmt = db.prepare('INSERT OR REPLACE INTO students (student_id, full_name, email, gpa, grade_label) VALUES (?, ?, ?, ?, ?)');
    for (const s of students) {
      if (!s.Student_ID) continue;
      const email = `${s.Student_ID.toLowerCase()}@sadat.edu.eg`;
      stmt.run(s.Student_ID, s.Student_Name || 'Student', email, parseFloat(s.GPA) || 3.0, s.Grade_Label || 'Good');
    }
    console.log(`[DB] Loaded ${students.length} students.`);
  }

  // 4. Student grades (first 5,000 or full dataset)
  const gradesCsv = path.join(dataDir, 'student_grades.csv');
  if (fs.existsSync(gradesCsv)) {
    console.log('[DB] Loading student grades...');
    const grades = parseCsv(fs.readFileSync(gradesCsv, 'utf8'));
    const stmt = db.prepare('INSERT OR REPLACE INTO student_grades (student_id, course_id, course_name, mark, credit_hours) VALUES (?, ?, ?, ?, ?)');
    db.exec('BEGIN TRANSACTION');
    for (const g of grades) {
      if (!g.Student_ID || !g.Course_ID) continue;
      stmt.run(g.Student_ID, g.Course_ID, g.Course_Name || '', parseFloat(g.M_Mark) || 70, Number(g.C_H_Credit_Hours) || 3);
    }
    db.exec('COMMIT');
    console.log(`[DB] Loaded ${grades.length} transcript grade records.`);
  }

  // 5. Jobs
  const jobsCsv = path.join(dataDir, 'jobs.csv');
  if (fs.existsSync(jobsCsv)) {
    const jobs = parseCsv(fs.readFileSync(jobsCsv, 'utf8'));
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO jobs 
      (job_id, title, specialization, company, company_country, job_location, work_mode, level, years_exp_min, years_exp_max, technical_requirements, certifications_mentioned, employment_type, linkedin_seniority, posted, url)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);
    for (const j of jobs) {
      if (!j.job_id) continue;
      stmt.run(
        j.job_id, j.title, j.specialization, j.company, j.company_country || 'Egypt',
        j.job_location || '', j.work_mode || 'Not specified', j.level || 'Junior',
        j.years_exp_min ? parseFloat(j.years_exp_min) : null,
        j.years_exp_max ? parseFloat(j.years_exp_max) : null,
        j.technical_requirements || '', j.certifications_mentioned || '',
        j.employment_type || 'Full-time', j.linkedin_seniority || '', j.posted || '', j.url || ''
      );
    }
    console.log(`[DB] Loaded ${jobs.length} job postings.`);
  }

  // 6. Market Insights
  const marketCsv = path.join(dataDir, 'market_vs_cohort_skills.csv');
  if (fs.existsSync(marketCsv)) {
    const items = parseCsv(fs.readFileSync(marketCsv, 'utf8'));
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO market_insights
      (skill, demand_entry_pct, demand_all_pct, cohort_mean_pct, cohort_ready_pct, curriculum_evidence, gap_score)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    for (const it of items) {
      if (!it.Skill) continue;
      stmt.run(
        it.Skill,
        parseFloat(it['Demand%_entry_level_ads']) || 0,
        parseFloat(it['Demand%_all_levels']) || 0,
        parseFloat(it['Cohort_mean_level%']) || 0,
        parseFloat(it['Cohort_ready%']) || 0,
        parseFloat(it['Curriculum_evidence']) || 0,
        parseFloat(it['Gap_score']) || 0
      );
    }
    console.log(`[DB] Loaded ${items.length} market skill metrics.`);
  }

  // 7. Role summaries
  const roleCsv = path.join(dataDir, 'role_summary.csv');
  if (fs.existsSync(roleCsv)) {
    const roles = parseCsv(fs.readFileSync(roleCsv, 'utf8'));
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO role_summaries
      (role, cohort_mean_match, cohort_median_match, best_student_match, ads_used, entry_level_ads, basis, core_skills)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);
    for (const r of roles) {
      if (!r.Role) continue;
      stmt.run(
        r.Role,
        parseFloat(r['Cohort_mean_match%']) || 0,
        parseFloat(r['Cohort_median_match%']) || 0,
        parseFloat(r['Best_student_match%']) || 0,
        Number(r.Ads_used) || 0,
        Number(r.Entry_level_ads) || 0,
        r.Basis || '',
        r.Core_skills || ''
      );
    }
    console.log(`[DB] Loaded ${roles.length} role summaries.`);
  }
}

initDatabase();

module.exports = db;
