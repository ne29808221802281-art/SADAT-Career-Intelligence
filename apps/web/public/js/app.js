/**
 * SADAT Career Intelligence Application Controller
 * Connects UI with REST API (/api/v1/...) with interactive score sliders and real-time recalculation.
 * Refinements: multi-student support, certificate dropdown, roadmap deduplication,
 *              student profile card, 3-step onboarding wizard.
 */

(function () {
  const API_BASE = '/api/v1';

  let currentStudentId = 'SAD20260001';
  let activeStudentData = null;
  let currentEvaluation = null;
  let missingSkillsData = [];
  let marketOverviewData = null;
  let allJobsData = [];
  let previewScores = {};
  let certsList = []; // populated from /api/v1/questionnaire
  let academicRecords = null; // cached transcript for profile tab

  // -------------------------------------------------------------------------
  // Utility: Append ?studentId= to any API path
  // -------------------------------------------------------------------------
  function apiUrl(path) {
    const sep = path.includes('?') ? '&' : '?';
    return `${API_BASE}${path}${sep}studentId=${currentStudentId}`;
  }

  // -------------------------------------------------------------------------
  // Tab Switching
  // -------------------------------------------------------------------------
  window.switchTab = function (tabId) {
    document.querySelectorAll('.tab-pane').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));

    const targetTab = document.getElementById(tabId);
    if (targetTab) targetTab.classList.add('active');

    const btn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
    if (btn) btn.classList.add('active');

    // Lazy-load profile tab
    if (tabId === 'profileTab') renderProfileTab();
    if (tabId === 'roadmapTab') renderRoadmap();
    if (tabId === 'questionnaireTab') loadQuestionnaireResponses();
  };

  // -------------------------------------------------------------------------
  // Student Switching — clears state and re-fetches for the new student
  // -------------------------------------------------------------------------
  window.switchStudent = async function (studentId) {
    currentStudentId = studentId;
    previewScores = {};
    academicRecords = null;
    await loadStudentData();
    window.renderApp();
    // If profile tab is active, re-render it
    if (document.getElementById('profileTab')?.classList.contains('active')) {
      renderProfileTab();
    }
  };

  // -------------------------------------------------------------------------
  // Init Application
  // -------------------------------------------------------------------------
  async function init() {
    window.I18N.init();

    // 1. Fetch cohort list for student picker
    try {
      const cohortRes = await fetch(`${API_BASE}/students/cohort`);
      if (cohortRes.ok) {
        const cohortJson = await cohortRes.json();
        const select = document.getElementById('studentSelect');
        if (select && cohortJson.cohort) {
          select.innerHTML = cohortJson.cohort.map(s =>
            `<option value="${s.student_id}">${s.student_id} – ${s.full_name} (${s.grade_label})</option>`
          ).join('');
          select.value = currentStudentId;
        }
      }
    } catch (_) {}

    // 2. Fetch certificates list from questionnaire endpoint
    try {
      const qRes = await fetch(`${API_BASE}/questionnaire`);
      if (qRes.ok) {
        const qJson = await qRes.json();
        certsList = qJson.recognizedCertificates || [];
      }
    } catch (_) {}

    // 3. Fetch 14 Missing Skills
    try {
      const msRes = await fetch(`${API_BASE}/free-tests`);
      if (msRes.ok) {
        const msJson = await msRes.json();
        missingSkillsData = msJson.missingSkills || [];
      }
    } catch (_) {}

    // 4. Fetch Market Data & All Jobs
    try {
      const mktRes = await fetch(`${API_BASE}/market/overview`);
      if (mktRes.ok) marketOverviewData = await mktRes.json();

      const jobsRes = await fetch(`${API_BASE}/market/jobs`);
      if (jobsRes.ok) {
        const jobsJson = await jobsRes.json();
        allJobsData = jobsJson.jobs || [];
        populateJobTrackFilter();
      }
    } catch (_) {}

    // 5. Load Active Student Data
    await loadStudentData();

    // 6. Initial Render
    window.renderApp();

    // 7. Show onboarding if first visit
    checkOnboarding();
  }

  async function loadStudentData() {
    try {
      const profRes = await fetch(apiUrl('/students/me'));
      if (profRes.ok) activeStudentData = await profRes.json();

      const matchRes = await fetch(apiUrl('/matching/me'));
      if (matchRes.ok) currentEvaluation = await matchRes.json();
    } catch (err) {
      console.warn('API fetch failed, falling back to embedded dataset:', err);
      if (window.PLATFORM_DATA) {
        const sList = window.PLATFORM_DATA.students || [];
        const s = sList.find(x => x.Student_ID === currentStudentId) || sList[0];
        if (s) {
          activeStudentData = {
            studentId: s.Student_ID,
            fullName: s.Student_Name,
            gpa: s.GPA,
            gradeLabel: s.Grade_Label
          };
        }
      }
    }
  }

  // -------------------------------------------------------------------------
  // Populate Job Filter dropdown
  // -------------------------------------------------------------------------
  function populateJobTrackFilter() {
    const sel = document.getElementById('jobTrackFilter');
    if (!sel || allJobsData.length === 0) return;
    const tracks = [...new Set(allJobsData.map(j => j.specialization))].filter(Boolean);
    sel.innerHTML = `<option value="">${window.I18N.t('filterSpecialization')}</option>` +
      tracks.map(t => `<option value="${t}">${t}</option>`).join('');
  }

  // -------------------------------------------------------------------------
  // Global Render Function
  // -------------------------------------------------------------------------
  window.renderApp = function () {
    renderHeader();
    renderHero();
    renderJobCards();
    renderMissingSkills();
    renderMarketCharts();
    renderExploreJobs();
  };

  // -------------------------------------------------------------------------
  // 1. Render Header
  // -------------------------------------------------------------------------
  function renderHeader() {
    const s = activeStudentData || { studentId: currentStudentId, fullName: 'Loading...', gpa: '--', gradeLabel: '--' };
    const nameEl = document.getElementById('studentNameDisplay');
    const metaEl = document.getElementById('studentMetaDisplay');
    const avatarEl = document.getElementById('studentAvatar');

    if (nameEl) nameEl.textContent = s.fullName || s.full_name;
    if (metaEl) metaEl.textContent = `ID: ${s.studentId || s.student_id} • GPA: ${s.gpa} (${s.gradeLabel || s.grade_label})`;
    if (avatarEl) {
      const parts = (s.fullName || s.full_name || 'AG').split(' ');
      avatarEl.textContent = parts.length > 1 ? (parts[0][0] + parts[1][0]).toUpperCase() : parts[0].substring(0, 2).toUpperCase();
    }

    const lang = window.I18N.currentLocale;
    const enBtn = document.getElementById('langEnBtn');
    const arBtn = document.getElementById('langArBtn');
    if (enBtn) enBtn.className = 'lang-btn' + (lang === 'en' ? ' active' : '');
    if (arBtn) arBtn.className = 'lang-btn' + (lang === 'ar' ? ' active' : '');

    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (key) el.textContent = window.I18N.t(key);
    });
  }

  // -------------------------------------------------------------------------
  // 2. Render Hero & Top Roles
  // -------------------------------------------------------------------------
  function renderHero() {
    const s = activeStudentData || { gpa: '--', fullName: 'Loading...' };
    const heroName = document.getElementById('heroStudentName');
    const heroGpa = document.getElementById('heroGpa');
    const heroExp = document.getElementById('heroAllowedExp');

    if (heroName) heroName.textContent = s.fullName || s.full_name;
    if (heroGpa) heroGpa.textContent = s.gpa;
    if (heroExp && currentEvaluation?.experience) {
      const expY = Math.floor(currentEvaluation.experience.years || 0);
      heroExp.textContent = `0 - ${2 + expY} Yrs`;
    }

    const rolesList = document.getElementById('topRolesList');
    if (rolesList && currentEvaluation?.topRoles) {
      rolesList.innerHTML = currentEvaluation.topRoles.map(r => `
        <div class="role-pill">
          <span class="role-name">${r.role}</span>
          <span class="role-pct">${r.match_pct}%</span>
        </div>
      `).join('');
    }
  }

  // -------------------------------------------------------------------------
  // 3. Render Top 10 Job Matches
  // -------------------------------------------------------------------------
  function renderJobCards() {
    const grid = document.getElementById('jobCardsGrid');
    if (!grid) return;

    const jobs = currentEvaluation?.topJobs || [];
    if (jobs.length === 0) {
      grid.innerHTML = '<p class="text-muted">Loading matching job recommendations...</p>';
      return;
    }

    grid.innerHTML = jobs.map(jb => {
      const details = jb.skills_detail || [];
      const strong = details.filter(d => d.status === 'strong');
      const partial = details.filter(d => d.status === 'partial');
      const missing = details.filter(d => d.status === 'missing');

      let growthHtml = '';
      if (jb.improve_plan && jb.improve_plan.length > 0) {
        const imp = jb.improve_plan[0];
        const act = imp.actions?.[0];
        if (act) {
          const gainBadge = imp.est_fit_gain_pts ? `<span class="gain-badge">+${imp.est_fit_gain_pts} pts Fit Gain</span>` : '';
          growthHtml = `
            <div class="job-growth-box">
              <strong>${window.I18N.t('growthOpportunity')}</strong> ${imp.skill} (${imp.cause})<br>
              <span style="color: var(--navy-deep);">${act.name}</span><br>
              ${gainBadge}
            </div>
          `;
        }
      }

      return `
        <div class="job-card">
          <div class="job-card-top">
            <div>
              <span class="job-rank">Rank #${jb.rank} • ${jb.specialization}</span>
              <h3 class="job-title">${jb.title}</h3>
              <span class="job-company">${jb.company}</span>
            </div>
            <div class="fit-circle">
              <span class="fit-val">${jb.fit_pct}%</span>
              <span class="fit-label">Fit</span>
            </div>
          </div>

          <div class="job-meta-row">
            <span class="job-chip"><i class="fas fa-laptop-house"></i> ${jb.work_mode}</span>
            <span class="job-chip"><i class="fas fa-briefcase"></i> ${jb.years_required !== undefined ? jb.years_required + ' Yrs Exp' : 'Entry Level'}</span>
            <span class="job-chip ${jb.is_eligible ? 'text-strong' : 'text-missing'}">
              <i class="fas ${jb.is_eligible ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
              ${jb.is_eligible ? window.I18N.t('eligibilitySatisfied') : window.I18N.t('eligibilityWarning')}
            </span>
          </div>

          <div class="skills-breakdown-box">
            ${strong.length > 0 ? `
              <div class="skills-group">
                <div class="skills-group-label">${window.I18N.t('strongSkills')} (${strong.length}):</div>
                <div class="skill-pills-row">
                  ${strong.map(s => `<span class="skill-tag strong">${s.skill}</span>`).join('')}
                </div>
              </div>
            ` : ''}

            ${partial.length > 0 ? `
              <div class="skills-group">
                <div class="skills-group-label">${window.I18N.t('developingSkills')} (${partial.length}):</div>
                <div class="skill-pills-row">
                  ${partial.map(s => `<span class="skill-tag partial">${s.skill} (${s.level_pct}%)</span>`).join('')}
                </div>
              </div>
            ` : ''}

            ${missing.length > 0 ? `
              <div class="skills-group">
                <div class="skills-group-label">${window.I18N.t('missingSkills')} (${missing.length}):</div>
                <div class="skill-pills-row">
                  ${missing.map(s => `<span class="skill-tag missing">${s.skill}</span>`).join('')}
                </div>
              </div>
            ` : ''}
          </div>

          ${growthHtml}

          <div class="job-card-actions">
            <a href="${jb.url}" target="_blank" rel="noopener noreferrer" class="btn btn-outline" style="flex: 1;">
              <i class="fab fa-linkedin"></i> ${window.I18N.t('applyJob')}
            </a>
          </div>
        </div>
      `;
    }).join('');
  }

  // -------------------------------------------------------------------------
  // 4. Render Student Profile Tab (student card + transcript)
  // -------------------------------------------------------------------------
  async function renderProfileTab() {
    const profileSection = document.getElementById('profileTab');
    if (!profileSection) return;

    const s = activeStudentData || {};
    const gpa = parseFloat(s.gpa) || 0;
    let gradeColor = 'var(--status-developing)';
    let standingLabel = 'Good';
    if (gpa >= 3.75) { gradeColor = 'var(--status-strong)'; standingLabel = 'Excellent'; }
    else if (gpa >= 3.5) { gradeColor = 'var(--ocean-blue)'; standingLabel = 'Very Good'; }
    else if (gpa >= 3.0) { gradeColor = 'var(--ocean-blue)'; standingLabel = 'Good'; }

    // Build initials avatar
    const name = s.fullName || s.full_name || 'Student';
    const parts = name.split(' ');
    const initials = parts.length > 1 ? (parts[0][0] + parts[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase();

    // Count skill readiness from evaluation
    let strongCount = 0, partialCount = 0, missingCount = 0;
    if (currentEvaluation?.topJobs?.[0]?.skills_detail) {
      const d = currentEvaluation.topJobs[0].skills_detail;
      strongCount = d.filter(x => x.status === 'strong').length;
      partialCount = d.filter(x => x.status === 'partial').length;
      missingCount = d.filter(x => x.status === 'missing').length;
    }

    // Fetch transcript if not cached
    let courses = [];
    if (!academicRecords) {
      try {
        const res = await fetch(apiUrl('/students/me/academic-records'));
        if (res.ok) { academicRecords = await res.json(); }
      } catch (_) {}
    }
    if (academicRecords) courses = academicRecords.courses || [];

    // Group courses by year
    const byYear = {};
    for (const c of courses) {
      const yr = c.year || 1;
      if (!byYear[yr]) byYear[yr] = [];
      byYear[yr].push(c);
    }

    const gpaBarWidth = Math.min(100, (gpa / 4.0) * 100).toFixed(1);

    profileSection.innerHTML = `
      <!-- Student Profile Card -->
      <div class="profile-card-hero" style="
        background: linear-gradient(135deg, var(--navy-deep) 0%, var(--ocean-blue) 100%);
        border-radius: var(--radius-lg);
        padding: 2rem;
        margin-bottom: 2rem;
        display: flex;
        gap: 2rem;
        align-items: center;
        flex-wrap: wrap;
        color: white;
      ">
        <div class="profile-avatar-large" style="
          width: 80px; height: 80px;
          border-radius: 50%;
          background: rgba(255,255,255,0.15);
          border: 3px solid rgba(255,255,255,0.4);
          display: flex; align-items: center; justify-content: center;
          font-size: 2rem; font-weight: 800;
          flex-shrink: 0;
        ">${initials}</div>

        <div style="flex: 1; min-width: 200px;">
          <h2 style="font-size: 1.5rem; font-weight: 800; margin-bottom: 0.25rem;">${name}</h2>
          <div style="opacity: 0.8; font-size: 0.9rem; margin-bottom: 0.75rem;">
            <i class="fas fa-id-badge"></i> ${s.studentId || s.student_id} &nbsp;|&nbsp;
            <i class="fas fa-university"></i> Faculty of Computers &amp; Information &nbsp;|&nbsp;
            <i class="fas fa-calendar-alt"></i> Class of 2026
          </div>
          <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
            <span style="background: rgba(255,255,255,0.15); padding: 0.35rem 0.9rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
              <i class="fas fa-star"></i> GPA: ${gpa.toFixed(2)} / 4.00
            </span>
            <span style="background: rgba(255,255,255,0.15); padding: 0.35rem 0.9rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
              <i class="fas fa-award"></i> ${standingLabel} Standing
            </span>
            <span style="background: rgba(255,255,255,0.15); padding: 0.35rem 0.9rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
              <i class="fas fa-book"></i> ${courses.length} Courses Completed
            </span>
          </div>
        </div>

        <div style="min-width: 200px; flex: 1;">
          <div style="font-size: 0.8rem; opacity: 0.8; margin-bottom: 0.5rem; font-weight: 600;">GPA PROGRESS</div>
          <div style="background: rgba(255,255,255,0.15); border-radius: 10px; height: 10px; overflow: hidden; margin-bottom: 0.5rem;">
            <div style="width: ${gpaBarWidth}%; height: 100%; background: rgba(255,255,255,0.8); border-radius: 10px;"></div>
          </div>
          <div style="font-size: 0.75rem; opacity: 0.7;">${gpa.toFixed(2)} / 4.00 &nbsp;–&nbsp; ${standingLabel}</div>

          ${currentEvaluation?.topJobs?.[0] ? `
            <div style="margin-top: 1rem; font-size: 0.8rem; opacity: 0.8; font-weight: 600;">SKILL READINESS (Top Match Job)</div>
            <div style="display: flex; gap: 0.5rem; margin-top: 0.4rem; flex-wrap: wrap;">
              <span style="background: rgba(72,199,120,0.25); border: 1px solid rgba(72,199,120,0.5); padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem;">
                ✓ ${strongCount} Strong
              </span>
              <span style="background: rgba(255,183,77,0.25); border: 1px solid rgba(255,183,77,0.5); padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem;">
                ◑ ${partialCount} Developing
              </span>
              <span style="background: rgba(255,82,82,0.25); border: 1px solid rgba(255,82,82,0.5); padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem;">
                ✗ ${missingCount} Missing
              </span>
            </div>
          ` : ''}
        </div>
      </div>

      <!-- Academic Record & Transcript -->
      <div class="section-header">
        <h2><i class="fas fa-scroll"></i> Official Academic Transcript</h2>
        <p>Institutional 4-year course records from Faculty of Computers and Information.</p>
      </div>

      ${courses.length === 0 ? '<p class="text-muted">Loading transcript...</p>' : Object.entries(byYear).sort(([a],[b]) => a-b).map(([yr, clist]) => `
        <div style="margin-bottom: 1.5rem;">
          <div style="font-weight: 700; color: var(--navy-deep); font-size: 0.9rem; margin-bottom: 0.5rem; padding: 0.4rem 0.75rem; background: var(--ice-blue); border-radius: var(--radius-sm);">
            <i class="fas fa-calendar"></i> Year ${yr}
          </div>
          <div class="data-table-card" style="margin: 0;">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>Course ID</th>
                  <th>Course Title</th>
                  <th>Credit Hours</th>
                  <th>Mark (0–100)</th>
                </tr>
              </thead>
              <tbody>
                ${clist.map(c => `
                  <tr>
                    <td><strong>${c.course_id}</strong></td>
                    <td>${c.course_name}</td>
                    <td>${c.credit_hours} hrs</td>
                    <td><strong style="color: ${c.mark >= 85 ? 'var(--status-strong)' : c.mark >= 65 ? 'var(--ocean-blue)' : 'var(--status-developing)'};">${c.mark}</strong></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `).join('')}
    `;
  }

  // -------------------------------------------------------------------------
  // 5. Render 14 Missing Skills with Interactive Sliders
  // -------------------------------------------------------------------------
  function renderMissingSkills() {
    const grid = document.getElementById('missingSkillsGrid');
    if (!grid || missingSkillsData.length === 0) return;

    grid.innerHTML = missingSkillsData.map(sk => {
      const currentScore = previewScores[sk.id] !== undefined ? previewScores[sk.id] : 0;
      return `
        <div class="skill-test-card">
          <div class="skill-test-header">
            <div class="skill-icon-box">
              <i class="${sk.icon}"></i>
            </div>
            <div class="skill-title-text">
              <h3>${sk.name}</h3>
              <span class="skill-category">${sk.category}</span>
            </div>
            <span class="free-tag">${window.I18N.t('freeTestBadge')}</span>
          </div>

          <p class="test-desc-text">${sk.test_desc}</p>

          <div class="slider-wrapper">
            <div class="slider-label-row">
              <span data-i18n="testScoreSlider">${window.I18N.t('testScoreSlider')}</span>
              <strong id="sliderVal_${sk.id}" style="color: var(--ocean-blue);">${currentScore}%</strong>
            </div>
            <input type="range" class="score-slider" min="0" max="100" value="${currentScore}"
              oninput="window.updateScorePreview('${sk.id}', this.value)">
          </div>

          <div style="font-size: 0.75rem; color: var(--slate); margin-bottom: 1rem;">
            <strong>${window.I18N.t('prepCourse')}</strong> ${sk.prep_course}
          </div>

          <a href="${sk.test_url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="margin-top: auto;">
            <i class="fas fa-arrow-up-right-from-square"></i> ${window.I18N.t('takeFreeTest')}
          </a>
        </div>
      `;
    }).join('');
  }

  // Interactive Slider Live Preview Handler
  let previewDebounceTimer = null;
  window.updateScorePreview = function (skillId, val) {
    const num = Number(val);
    previewScores[skillId] = num;
    const label = document.getElementById(`sliderVal_${skillId}`);
    if (label) label.textContent = `${num}%`;

    clearTimeout(previewDebounceTimer);
    previewDebounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE}/free-tests/preview?studentId=${currentStudentId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ testScores: previewScores })
        });
        if (res.ok) {
          const json = await res.json();
          currentEvaluation.topJobs = json.topJobs;
          currentEvaluation.topRoles = json.topRoles;
          renderHero();
          renderJobCards();
        }
      } catch (err) {
        console.warn('Preview recalculation error:', err);
      }
    }, 250);
  };

  // -------------------------------------------------------------------------
  // 6. Render Roadmap (deduplicated by skill, grouped affected jobs)
  // -------------------------------------------------------------------------
  async function renderRoadmap() {
    const container = document.getElementById('roadmapList');
    if (!container) return;

    container.innerHTML = '<p class="text-muted"><i class="fas fa-spinner fa-spin"></i> Calculating personalized roadmap...</p>';

    try {
      const res = await fetch(apiUrl('/recommendations/me'));
      if (res.ok) {
        const json = await res.json();
        const recs = json.recommendations || [];
        if (recs.length === 0) {
          container.innerHTML = '<p class="text-muted">No pending skill gaps! Your profile strongly covers your top opportunities.</p>';
          return;
        }

        // Parse affected jobs from job_id field (stored as JSON array)
        container.innerHTML = `
          <div style="margin-bottom: 1.5rem; padding: 1rem 1.25rem; background: var(--ice-blue); border-radius: var(--radius-md); border-left: 4px solid var(--ocean-blue);">
            <i class="fas fa-info-circle" style="color: var(--ocean-blue);"></i>
            <strong style="color: var(--navy-deep);"> ${recs.length} unique skill gaps identified</strong>, 
            ranked by estimated fit gain. Each recommendation applies to multiple jobs.
          </div>
          ${recs.map((r, idx) => {
            let affectedJobs = [];
            try { affectedJobs = JSON.parse(r.job_id || '[]'); } catch (_) {
              if (r.job_id) affectedJobs = [r.job_id];
            }
            const gain = r.est_fit_gain_pts || 0;
            const gainColor = gain >= 10 ? 'var(--status-strong)' : gain >= 5 ? 'var(--ocean-blue)' : 'var(--slate)';

            return `
              <div class="roadmap-item-card" style="position: relative;">
                <div style="position: absolute; top: 1rem; right: 1rem; font-size: 1.5rem; font-weight: 800; color: ${gainColor}; opacity: 0.15;">
                  #${idx + 1}
                </div>

                <div style="display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 0.75rem;">
                  <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; flex-wrap: wrap;">
                      <span class="roadmap-skill-badge">${r.skill}</span>
                      <span class="cause-tag"><i class="fas fa-circle-exclamation"></i> ${r.cause}</span>
                      ${gain > 0 ? `<span class="gain-badge" style="background: ${gainColor}; color: white;">+${gain} pts Fit Gain</span>` : ''}
                    </div>

                    <p style="font-size: 0.95rem; color: var(--navy-deep); font-weight: 600; margin-bottom: 0.4rem;">
                      <i class="fas fa-circle-chevron-right" style="color: var(--ocean-blue);"></i> ${r.action_name}
                    </p>
                    <div style="font-size: 0.78rem; color: var(--slate); margin-bottom: 0.5rem;">
                      <strong>Provider:</strong> ${r.action_provider} &nbsp;•&nbsp; <strong>Cost:</strong> ${r.action_cost}
                    </div>

                    ${affectedJobs.length > 0 ? `
                      <div style="font-size: 0.75rem; color: var(--slate);">
                        <strong><i class="fas fa-briefcase"></i> Improves compatibility for:</strong>
                        <div style="margin-top: 0.3rem; display: flex; flex-wrap: wrap; gap: 0.3rem;">
                          ${affectedJobs.slice(0, 5).map(j => `<span style="background: var(--ice-blue); padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.72rem;">${j}</span>`).join('')}
                          ${affectedJobs.length > 5 ? `<span style="font-size: 0.72rem; color: var(--slate);">+${affectedJobs.length - 5} more</span>` : ''}
                        </div>
                      </div>
                    ` : ''}
                  </div>

                  <select class="form-control" style="font-size: 0.8rem; padding: 0.4rem 0.6rem; min-width: 130px; flex-shrink: 0;"
                    onchange="window.updateRoadmapStatus(${r.id}, this.value)">
                    <option value="suggested" ${r.status === 'suggested' ? 'selected' : ''}>${window.I18N.t('statusSuggested')}</option>
                    <option value="planned" ${r.status === 'planned' ? 'selected' : ''}>${window.I18N.t('statusPlanned')}</option>
                    <option value="in_progress" ${r.status === 'in_progress' ? 'selected' : ''}>${window.I18N.t('statusInProgress')}</option>
                    <option value="completed" ${r.status === 'completed' ? 'selected' : ''}>${window.I18N.t('statusCompleted')}</option>
                  </select>
                </div>
              </div>
            `;
          }).join('')}
        `;
      }
    } catch (_) {}
  }

  window.updateRoadmapStatus = async function (id, status) {
    try {
      await fetch(`${API_BASE}/recommendations/me/${id}/progress?studentId=${currentStudentId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
    } catch (_) {}
  };

  // -------------------------------------------------------------------------
  // 7. Render Market Intelligence Charts
  // -------------------------------------------------------------------------
  async function renderMarketCharts() {
    const skillsChart = document.getElementById('marketSkillsChart');
    const roleChart = document.getElementById('roleSummaryChart');

    if (skillsChart) {
      try {
        const res = await fetch(`${API_BASE}/market/skills`);
        if (res.ok) {
          const json = await res.json();
          const topSkills = json.skills.slice(0, 10);
          skillsChart.innerHTML = topSkills.map(sk => `
            <div class="bar-row">
              <span class="bar-label">${sk.skill}</span>
              <div class="bar-track">
                <div class="bar-fill-demand" style="width: ${sk.demand_entry_pct}%;" title="Demand: ${sk.demand_entry_pct}%"></div>
                <div class="bar-fill-cohort" style="width: ${sk.cohort_ready_pct}%;" title="Readiness: ${sk.cohort_ready_pct}%"></div>
              </div>
              <span class="bar-val">${sk.demand_entry_pct}%</span>
            </div>
          `).join('');
        }
      } catch (_) {}
    }

    if (roleChart) {
      try {
        const res = await fetch(`${API_BASE}/market/roles`);
        if (res.ok) {
          const json = await res.json();
          roleChart.innerHTML = json.roles.map(r => `
            <div class="bar-row">
              <span class="bar-label">${r.role}</span>
              <div class="bar-track">
                <div class="bar-fill-demand" style="width: ${r.cohort_mean_match}%;" title="Cohort Mean: ${r.cohort_mean_match}%"></div>
              </div>
              <span class="bar-val">${r.cohort_mean_match}%</span>
            </div>
          `).join('');
        }
      } catch (_) {}
    }
  }

  // -------------------------------------------------------------------------
  // 8. Render All 169 Jobs
  // -------------------------------------------------------------------------
  function renderExploreJobs() {
    const grid = document.getElementById('exploreJobsGrid');
    if (!grid) return;

    const trackFilter = document.getElementById('jobTrackFilter')?.value || '';
    const modeFilter = document.getElementById('jobWorkModeFilter')?.value || '';

    let list = allJobsData;
    if (trackFilter) list = list.filter(j => j.specialization === trackFilter);
    if (modeFilter) list = list.filter(j => j.work_mode === modeFilter);

    grid.innerHTML = list.slice(0, 30).map(jb => `
      <div class="job-card">
        <div class="job-card-top">
          <div>
            <span class="job-rank">${jb.specialization} • ${jb.level}</span>
            <h3 class="job-title">${jb.title}</h3>
            <span class="job-company">${jb.company}</span>
          </div>
        </div>
        <div class="job-meta-row">
          <span class="job-chip"><i class="fas fa-location-dot"></i> ${jb.job_location || 'Egypt'}</span>
          <span class="job-chip"><i class="fas fa-laptop-house"></i> ${jb.work_mode}</span>
          <span class="job-chip"><i class="fas fa-briefcase"></i> ${jb.years_exp_min !== null ? jb.years_exp_min + ' Yrs Exp' : 'Entry Level'}</span>
        </div>
        <p style="font-size: 0.8rem; color: var(--slate); margin-bottom: 1rem;">
          <strong>Requirements:</strong> ${jb.technical_requirements}
        </p>
        <a href="${jb.url}" target="_blank" rel="noopener noreferrer" class="btn btn-outline" style="margin-top: auto;">
          <i class="fab fa-linkedin"></i> ${window.I18N.t('applyJob')}
        </a>
      </div>
    `).join('');
  }

  window.filterJobs = function () {
    renderExploreJobs();
  };

  // -------------------------------------------------------------------------
  // Questionnaire / Experience Form
  // -------------------------------------------------------------------------
  window.toggleExpFields = function (checked) {
    const el = document.getElementById('expFieldsGroup');
    if (el) el.style.display = checked ? 'block' : 'none';
  };

  // Build certificate dropdown options from certsList
  function buildCertOptions() {
    const grouped = {};
    certsList.forEach(c => {
      const prov = c.provider || 'Other';
      if (!grouped[prov]) grouped[prov] = [];
      grouped[prov].push(c.name);
    });
    let opts = '<option value="">— Select a Certificate —</option>';
    for (const [prov, names] of Object.entries(grouped)) {
      opts += `<optgroup label="${prov}">`;
      names.forEach(n => { opts += `<option value="${n}">${n}</option>`; });
      opts += '</optgroup>';
    }
    opts += '<option value="__other__">Other (custom)...</option>';
    return opts;
  }

  window.addCertRow = function () {
    const container = document.getElementById('certsListContainer');
    if (!container) return;
    const row = document.createElement('div');
    row.className = 'cert-row';
    row.style = 'display: flex; gap: 0.5rem; margin-bottom: 0.6rem; align-items: center; flex-wrap: wrap;';

    if (certsList.length > 0) {
      row.innerHTML = `
        <select class="form-control cert-input" style="flex: 1; min-width: 200px;" onchange="window.handleCertSelectChange(this)">
          ${buildCertOptions()}
        </select>
        <input type="text" class="form-control cert-custom-input" placeholder="Enter certificate name" style="flex: 1; display: none; min-width: 160px;">
        <label style="display: flex; align-items: center; gap: 0.35rem; font-size: 0.78rem; white-space: nowrap;">
          <input type="checkbox" class="cert-ver-check" checked> Verified
        </label>
        <button type="button" class="btn btn-outline" style="padding: 0.35rem 0.6rem;" onclick="this.parentElement.remove()">
          <i class="fas fa-trash"></i>
        </button>
      `;
    } else {
      row.innerHTML = `
        <input type="text" class="form-control cert-input" placeholder="e.g. AWS Certified Machine Learning - Associate" style="flex: 1;">
        <label style="display: flex; align-items: center; gap: 0.35rem; font-size: 0.78rem; white-space: nowrap;">
          <input type="checkbox" class="cert-ver-check" checked> Verified
        </label>
        <button type="button" class="btn btn-outline" style="padding: 0.35rem 0.6rem;" onclick="this.parentElement.remove()">
          <i class="fas fa-trash"></i>
        </button>
      `;
    }
    container.appendChild(row);
  };

  window.handleCertSelectChange = function (sel) {
    const row = sel.closest('.cert-row');
    const customInput = row?.querySelector('.cert-custom-input');
    if (!customInput) return;
    if (sel.value === '__other__') {
      customInput.style.display = 'block';
      sel.style.flex = '0 0 auto';
    } else {
      customInput.style.display = 'none';
      sel.style.flex = '1';
    }
  };

  async function loadQuestionnaireResponses() {
    try {
      const res = await fetch(apiUrl('/questionnaire/responses'));
      if (!res.ok) return;
      const data = await res.json();

      const hasExpEl = document.getElementById('hasExpCheckbox');
      const expMonthsEl = document.getElementById('expMonthsInput');
      const expRoleEl = document.getElementById('expRoleSelect');
      const expVerEl = document.getElementById('expVerifiedCheckbox');
      const certsContainer = document.getElementById('certsListContainer');

      if (hasExpEl) { hasExpEl.checked = data.hasExperience; window.toggleExpFields(data.hasExperience); }
      if (expMonthsEl) expMonthsEl.value = data.experienceMonths || 0;
      if (expRoleEl && data.experienceRole) expRoleEl.value = data.experienceRole;
      if (expVerEl) expVerEl.checked = data.experienceVerified;

      // Populate existing certs
      if (certsContainer && data.certificates && data.certificates.length > 0) {
        certsContainer.innerHTML = '';
        data.certificates.forEach(cert => {
          const row = document.createElement('div');
          row.className = 'cert-row';
          row.style = 'display: flex; gap: 0.5rem; margin-bottom: 0.6rem; align-items: center; flex-wrap: wrap;';
          if (certsList.length > 0) {
            const isKnown = certsList.some(c => c.name === cert.name);
            row.innerHTML = `
              <select class="form-control cert-input" style="flex: 1; min-width: 200px;" onchange="window.handleCertSelectChange(this)">
                ${buildCertOptions()}
              </select>
              <input type="text" class="form-control cert-custom-input" placeholder="Enter certificate name" style="flex: 1; display: ${isKnown ? 'none' : 'block'}; min-width: 160px;" value="${isKnown ? '' : cert.name}">
              <label style="display: flex; align-items: center; gap: 0.35rem; font-size: 0.78rem; white-space: nowrap;">
                <input type="checkbox" class="cert-ver-check" ${cert.verified ? 'checked' : ''}> Verified
              </label>
              <button type="button" class="btn btn-outline" style="padding: 0.35rem 0.6rem;" onclick="this.parentElement.remove()">
                <i class="fas fa-trash"></i>
              </button>
            `;
            // Set select value
            const sel = row.querySelector('.cert-input');
            if (isKnown) sel.value = cert.name;
            else sel.value = '__other__';
          } else {
            row.innerHTML = `
              <input type="text" class="form-control cert-input" value="${cert.name}" style="flex: 1;">
              <label style="display: flex; align-items: center; gap: 0.35rem; font-size: 0.78rem; white-space: nowrap;">
                <input type="checkbox" class="cert-ver-check" ${cert.verified ? 'checked' : ''}> Verified
              </label>
              <button type="button" class="btn btn-outline" style="padding: 0.35rem 0.6rem;" onclick="this.parentElement.remove()">
                <i class="fas fa-trash"></i>
              </button>
            `;
          }
          certsContainer.appendChild(row);
        });
      }
    } catch (_) {}
  }

  window.submitQuestionnaire = async function (e) {
    e.preventDefault();
    const hasExp = document.getElementById('hasExpCheckbox')?.checked || false;
    const months = Number(document.getElementById('expMonthsInput')?.value || 0);
    const role = document.getElementById('expRoleSelect')?.value || '';
    const verified = document.getElementById('expVerifiedCheckbox')?.checked || false;

    const certRows = document.querySelectorAll('.cert-row');
    const certs = [];
    certRows.forEach(row => {
      let name = '';
      const sel = row.querySelector('select.cert-input');
      const textInput = row.querySelector('input.cert-input, .cert-custom-input');
      if (sel) {
        if (sel.value === '__other__') {
          name = textInput?.value?.trim() || '';
        } else {
          name = sel.value;
        }
      } else if (textInput) {
        name = textInput.value?.trim() || '';
      }
      const isVer = row.querySelector('.cert-ver-check')?.checked || false;
      if (name) certs.push({ name, verified: isVer });
    });

    const payload = {
      hasExperience: hasExp,
      experienceMonths: months,
      experienceRole: role,
      experienceVerified: verified,
      certificates: certs,
      testScores: previewScores
    };

    const submitBtn = document.querySelector('#questionnaireForm [type="submit"]');
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Saving...'; }

    try {
      const res = await fetch(`${API_BASE}/questionnaire/responses?studentId=${currentStudentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const json = await res.json();
        if (json.evaluation) {
          currentEvaluation = currentEvaluation || {};
          currentEvaluation.topJobs = json.evaluation.top_jobs;
          currentEvaluation.topRoles = json.evaluation.top_roles;
        }
        renderHero();
        renderJobCards();
        window.switchTab('matchesTab');
        showToast('Profile updated! Job matches recalculated.', 'success');
      }
    } catch (err) {
      showToast('Error saving: ' + err.message, 'error');
    } finally {
      if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = 'Save & Recalculate Matching'; }
    }
  };

  // -------------------------------------------------------------------------
  // Toast Notifications (simple, no alert())
  // -------------------------------------------------------------------------
  function showToast(msg, type) {
    const existing = document.getElementById('sadatToast');
    if (existing) existing.remove();
    const toast = document.createElement('div');
    toast.id = 'sadatToast';
    toast.style = `
      position: fixed; bottom: 2rem; right: 2rem; z-index: 9999;
      padding: 1rem 1.5rem;
      background: ${type === 'success' ? 'var(--navy-deep)' : '#c0392b'};
      color: white;
      border-radius: var(--radius-md);
      box-shadow: 0 4px 20px rgba(0,0,0,0.3);
      font-weight: 600;
      font-size: 0.9rem;
      max-width: 360px;
      animation: slideInRight 0.3s ease;
    `;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  // -------------------------------------------------------------------------
  // Onboarding Wizard (3-step, uses actual student data)
  // -------------------------------------------------------------------------
  function checkOnboarding() {
    if (localStorage.getItem('sadat_onboarded_' + currentStudentId)) return;
    showOnboarding();
  }

  function showOnboarding() {
    const s = activeStudentData || {};
    const name = s.fullName || s.full_name || 'Student';
    const gpa = parseFloat(s.gpa) || 0;
    let standing = 'Good';
    if (gpa >= 3.75) standing = 'Excellent';
    else if (gpa >= 3.5) standing = 'Very Good';

    // Top 5 courses preview
    const topCourses = (academicRecords?.courses || []).slice(0, 5);

    const overlay = document.createElement('div');
    overlay.id = 'onboardingOverlay';
    overlay.style = `
      position: fixed; inset: 0; z-index: 10000;
      background: rgba(21, 53, 75, 0.85);
      display: flex; align-items: center; justify-content: center;
      padding: 1rem;
      animation: fadeIn 0.3s ease;
    `;

    overlay.innerHTML = `
      <div id="onboardingModal" style="
        background: var(--surface);
        border-radius: var(--radius-lg);
        max-width: 600px;
        width: 100%;
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
        overflow: hidden;
      ">
        <!-- Progress bar -->
        <div style="height: 4px; background: var(--ice-blue);">
          <div id="onboardProgress" style="height: 100%; background: var(--ocean-blue); transition: width 0.4s ease; width: 33%;"></div>
        </div>

        <div id="onboardStep1" class="onboard-step" style="padding: 2.5rem;">
          <div style="text-align: center; margin-bottom: 2rem;">
            <div style="width: 72px; height: 72px; background: linear-gradient(135deg, var(--navy-deep), var(--ocean-blue)); border-radius: 50%; margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center;">
              <i class="fas fa-graduation-cap" style="font-size: 2rem; color: white;"></i>
            </div>
            <h2 style="font-size: 1.6rem; font-weight: 800; color: var(--navy-deep); margin-bottom: 0.5rem;">Welcome, ${name.split(' ')[0]}! 👋</h2>
            <p style="color: var(--slate); font-size: 0.95rem;">Your SADAT Career Intelligence profile is ready.</p>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 2rem;">
            <div style="background: var(--ice-blue); border-radius: var(--radius-md); padding: 1.25rem; text-align: center;">
              <div style="font-size: 2rem; font-weight: 800; color: var(--navy-deep);">${gpa.toFixed(2)}</div>
              <div style="font-size: 0.8rem; color: var(--slate);">Your GPA</div>
            </div>
            <div style="background: var(--ice-blue); border-radius: var(--radius-md); padding: 1.25rem; text-align: center;">
              <div style="font-size: 1.3rem; font-weight: 800; color: var(--ocean-blue);">${standing}</div>
              <div style="font-size: 0.8rem; color: var(--slate);">Academic Standing</div>
            </div>
          </div>
          <p style="color: var(--slate); font-size: 0.9rem; margin-bottom: 1.5rem; line-height: 1.6;">
            This platform evaluates your <strong>4-year transcript</strong>, work experience, and international certifications 
            against <strong>169 real Egyptian tech jobs</strong> using evidence-weighted AI algorithms.
          </p>
          <button class="btn btn-primary" style="width: 100%; padding: 0.9rem;" onclick="window.onboardNext(2)">
            Next: See Your Transcript <i class="fas fa-arrow-right"></i>
          </button>
        </div>

        <div id="onboardStep2" class="onboard-step" style="padding: 2.5rem; display: none;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: var(--navy-deep); margin-bottom: 0.5rem;">
            <i class="fas fa-scroll" style="color: var(--ocean-blue);"></i> Your Academic Record
          </h2>
          <p style="color: var(--slate); font-size: 0.85rem; margin-bottom: 1.25rem;">
            Your transcript is already loaded. The engine reads your course marks to calculate skill proficiency scores.
          </p>
          <div style="border-radius: var(--radius-md); overflow: hidden; margin-bottom: 1.5rem; border: 1px solid var(--border);">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem;">
              <thead>
                <tr style="background: var(--navy-deep); color: white;">
                  <th style="padding: 0.6rem 0.75rem; text-align: left;">Course</th>
                  <th style="padding: 0.6rem 0.75rem; text-align: right;">Mark</th>
                </tr>
              </thead>
              <tbody>
                ${topCourses.length > 0 ? topCourses.map((c, i) => `
                  <tr style="background: ${i % 2 === 0 ? 'var(--ice-blue)' : 'white'};">
                    <td style="padding: 0.5rem 0.75rem;">${c.course_name}</td>
                    <td style="padding: 0.5rem 0.75rem; text-align: right; font-weight: 700; color: ${c.mark >= 85 ? 'var(--status-strong)' : c.mark >= 65 ? 'var(--ocean-blue)' : 'var(--status-developing)'};">${c.mark}</td>
                  </tr>
                `).join('') : '<tr><td colspan="2" style="padding: 0.75rem; color: var(--slate); text-align: center;">Loading your transcript...</td></tr>'}
                <tr style="background: var(--ice-blue);">
                  <td style="padding: 0.5rem 0.75rem; color: var(--slate); font-style: italic;" colspan="2">
                    + ${Math.max(0, (academicRecords?.totalCourses || 0) - 5)} more courses... View full transcript in Profile tab.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div style="display: flex; gap: 0.75rem;">
            <button class="btn btn-outline" style="flex: 1;" onclick="window.onboardNext(1)">
              <i class="fas fa-arrow-left"></i> Back
            </button>
            <button class="btn btn-primary" style="flex: 2;" onclick="window.onboardNext(3)">
              Next: Enhance Your Profile <i class="fas fa-arrow-right"></i>
            </button>
          </div>
        </div>

        <div id="onboardStep3" class="onboard-step" style="padding: 2.5rem; display: none;">
          <h2 style="font-size: 1.3rem; font-weight: 800; color: var(--navy-deep); margin-bottom: 0.5rem;">
            <i class="fas fa-user-plus" style="color: var(--ocean-blue);"></i> Enhance Your Profile
          </h2>
          <p style="color: var(--slate); font-size: 0.85rem; margin-bottom: 1.5rem;">
            Add your work experience, internships, and professional certifications to improve your job match accuracy.
          </p>

          <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1.5rem;">
            <div style="display: flex; gap: 1rem; padding: 1rem; background: var(--ice-blue); border-radius: var(--radius-md); align-items: center;">
              <i class="fas fa-briefcase" style="font-size: 1.5rem; color: var(--ocean-blue); flex-shrink: 0;"></i>
              <div>
                <strong style="color: var(--navy-deep);">Work Experience & Internships</strong>
                <p style="font-size: 0.8rem; color: var(--slate); margin: 0;">Verified experience boosts your skill evidence weight (0.8× multiplier)</p>
              </div>
            </div>
            <div style="display: flex; gap: 1rem; padding: 1rem; background: var(--ice-blue); border-radius: var(--radius-md); align-items: center;">
              <i class="fas fa-certificate" style="font-size: 1.5rem; color: var(--ocean-blue); flex-shrink: 0;"></i>
              <div>
                <strong style="color: var(--navy-deep);">Professional Certifications</strong>
                <p style="font-size: 0.8rem; color: var(--slate); margin: 0;">International certs (AWS, Google, etc.) apply a 0.9× evidence weight</p>
              </div>
            </div>
          </div>

          <div style="display: flex; gap: 0.75rem; margin-bottom: 0.75rem;">
            <button class="btn btn-outline" style="flex: 1; display: flex; align-items: center; gap: 0.5rem; justify-content: center;" onclick="window.onboardFinish('profile')">
              <i class="fas fa-upload"></i> Upload CV
            </button>
            <button class="btn btn-outline" style="flex: 1; display: flex; align-items: center; gap: 0.5rem; justify-content: center; opacity: 0.5; cursor: not-allowed;" disabled title="Coming Soon">
              <i class="fas fa-wand-magic-sparkles"></i> AI CV Builder <span style="font-size: 0.65rem; background: var(--ocean-blue); color: white; padding: 0.1rem 0.4rem; border-radius: 8px;">Soon</span>
            </button>
          </div>

          <div style="display: flex; gap: 0.75rem;">
            <button class="btn btn-outline" style="flex: 1;" onclick="window.onboardNext(2)">
              <i class="fas fa-arrow-left"></i> Back
            </button>
            <button class="btn btn-primary" style="flex: 2;" onclick="window.onboardFinish('questionnaire')">
              Add Experience & Certs Now <i class="fas fa-arrow-right"></i>
            </button>
          </div>
          <button class="btn" style="width: 100%; margin-top: 0.75rem; color: var(--slate); font-size: 0.82rem;" onclick="window.onboardFinish('matches')">
            Skip for now — Take me to my job matches
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);
  }

  window.onboardNext = function (step) {
    document.querySelectorAll('.onboard-step').forEach(el => el.style.display = 'none');
    document.getElementById(`onboardStep${step}`).style.display = 'block';
    const progress = document.getElementById('onboardProgress');
    if (progress) progress.style.width = `${Math.round(step / 3 * 100)}%`;
  };

  window.onboardFinish = function (dest) {
    localStorage.setItem('sadat_onboarded_' + currentStudentId, '1');
    const overlay = document.getElementById('onboardingOverlay');
    if (overlay) overlay.remove();
    if (dest === 'questionnaire') window.switchTab('questionnaireTab');
    else if (dest === 'profile') window.switchTab('profileTab');
    else window.switchTab('matchesTab');
  };

  // -------------------------------------------------------------------------
  // Launch on DOM ready
  // -------------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', init);
})();
