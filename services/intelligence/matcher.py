"""
Dynamic Matching Engine & Recommendation Logic
"""

import os
import re
import numpy as np
import pandas as pd
from engine import (
    WEIGHTS, ASSUMED, FULL_EVIDENCE, MIN_EVIDENCE, WEAK_GRADE, READY,
    MIN_JOB_SKILLS, MAX_YEARS, EXTRA_YEARS_PER_EXP_YEAR,
    TOP_ROLES, TOP_GAPS, TOP_JOBS, TOP_IMPROVE,
    CERT_MAP, MISSING_SKILLS_14, actions_for
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
if not os.path.exists(DATA_DIR):
    # Try one more level up for monorepo root: sadat-career-portal/data
    ROOT_DIR = os.path.dirname(BASE_DIR)
    DATA_DIR = os.path.join(ROOT_DIR, "data")

# Load datasets once into memory
courses_df = pd.read_csv(os.path.join(DATA_DIR, "course_catalog.csv"))
cmap_df = pd.read_csv(os.path.join(DATA_DIR, "course_skill_map.csv"))
students_info_df = pd.read_csv(os.path.join(DATA_DIR, "students_info.csv"))
student_grades_df = pd.read_csv(os.path.join(DATA_DIR, "student_grades.csv"))
jobs_df = pd.read_csv(os.path.join(DATA_DIR, "jobs.csv"))

# Parse jobs technical requirements
jobs_df["skills"] = jobs_df["technical_requirements"].fillna("").map(lambda t: [x.strip() for x in t.split(",") if x.strip()])
jobs_df["relevant"] = (jobs_df["specialization"] != "Other / Unclassified") & (jobs_df["skills"].map(len) > 0)
jobs_df["entry"] = jobs_df["relevant"] & (jobs_df["level"] != "Senior") & (jobs_df["years_exp_min"].isna() | (jobs_df["years_exp_min"] <= 2))

# Precompute role profiles
roles = {}
for spec, g in jobs_df[jobs_df["relevant"]].groupby("specialization"):
    e = g[g["entry"]]
    use_entry = len(e) >= 10
    base = e if use_entry else g
    if len(base) < 5:
        continue
    freq = base["skills"].explode().value_counts() / len(base)
    freq = freq[freq >= 0.10]
    roles[spec] = {
        "n_ads": len(base),
        "n_entry_ads": len(e),
        "basis": "entry-level ads" if use_entry else "ads of all levels",
        "weights": freq
    }

# All unique skills in ecosystem
ALL_SKILLS = sorted(set(cmap_df["Skill"].dropna()) |
                    {s for r in roles.values() for s in r["weights"].index} |
                    {s for ss in jobs_df["skills"] for s in ss} |
                    {item["id"] for item in MISSING_SKILLS_14})

skill_courses = cmap_df.groupby("Skill")["Course_ID"].apply(list).to_dict()
course_names = dict(zip(courses_df["Course_ID"], courses_df["Course_Name"]))

def evaluate_student(student_id=None, custom_grades=None, experience=None, test_scores=None, certificates=None):
    """
    Evaluates a student with transcript, experience, test scores, and certificates.
    Returns:
      - student_info
      - top_roles
      - top_jobs (Best 10 matching jobs)
      - skill_breakdown (proficiency & evidence per skill)
      - improvement_plan
    """
    # 1. Base transcript
    if student_id and not custom_grades:
        s_grades = student_grades_df[student_grades_df["Student_ID"] == student_id].copy()
        s_info_row = students_info_df[students_info_df["Student_ID"] == student_id]
        if not s_info_row.empty:
            s_info = s_info_row.iloc[0].to_dict()
        else:
            s_info = {"Student_ID": student_id, "Student_Name": "Custom Candidate", "GPA": 3.0, "Grade_Label": "Good"}
    else:
        # Use custom grades or fallback to student_id overrides
        s_info = {"Student_ID": student_id or "CUSTOM_STUDENT", "Student_Name": "Custom Candidate", "GPA": 3.0, "Grade_Label": "Simulated"}
        if custom_grades:
            # list of dicts: [{"Course_ID": "C026", "M_Mark": 85}, ...]
            c_dict = {item["Course_ID"]: float(item["M_Mark"]) for item in custom_grades}
            rows = []
            for _, cr in courses_df.iterrows():
                cid = cr["Course_ID"]
                mark = c_dict.get(cid, 70.0)
                rows.append({
                    "Student_ID": s_info["Student_ID"],
                    "Course_ID": cid,
                    "Course_Name": cr["Course_Name"],
                    "M_Mark": mark,
                    "C_H_Credit_Hours": cr["Credit_Hours"]
                })
            s_grades = pd.DataFrame(rows)
        else:
            s_grades = student_grades_df[student_grades_df["Student_ID"] == student_id].copy()

    marks_dict = dict(zip(s_grades["Course_ID"], s_grades["M_Mark"]))

    # Calculate transcript proficiency & evidence for all skills
    j = s_grades.merge(cmap_df[["Course_ID", "Skill", "rel"]], on="Course_ID")
    j["w"] = j["rel"] * j["C_H_Credit_Hours"]
    j["wm"] = j["w"] * j["M_Mark"]
    g = j.groupby("Skill")[["w", "wm"]].sum()
    
    prof_series = (g["wm"] / g["w"]).reindex(ALL_SKILLS).fillna(0.0)
    evid_series = g["w"].reindex(ALL_SKILLS).fillna(0.0)

    # Base transcript numerator & denominator
    L = (prof_series / 100.0).values
    M = (np.clip(evid_series / FULL_EVIDENCE, 0, 1) * WEIGHTS["transcript"]).values
    num = M * L
    den = M.copy()
    ext_den = np.zeros_like(M)

    # 2. Add Experience
    exp_months = 0.0
    exp_years = 0.0
    if experience and experience.get("has_experience"):
        exp_months = float(experience.get("months", 0))
        exp_years = exp_months / 12.0
        exp_source = "experience_verified" if experience.get("verified") else "experience_claimed"
        w_exp = WEIGHTS[exp_source]
        lvl_exp = min(1.0, exp_months / 12.0)
        
        # Apply experience to relevant skills if specified, or to all role skills
        exp_skills = experience.get("skills", [])
        if not exp_skills and experience.get("role"):
            role_spec = experience.get("role")
            if role_spec in roles:
                exp_skills = list(roles[role_spec]["weights"].index[:5])

        for sk in exp_skills:
            if sk in ALL_SKILLS:
                idx = ALL_SKILLS.index(sk)
                num[idx] += w_exp * lvl_exp
                den[idx] += w_exp
                ext_den[idx] += w_exp

    # 3. Add Online Test Scores (14 Missing Skills or any skill)
    if test_scores:
        w_test = WEIGHTS["online_test"]
        for sk, score in test_scores.items():
            if sk in ALL_SKILLS and score is not None and score > 0:
                idx = ALL_SKILLS.index(sk)
                lvl_test = float(np.clip(score / 100.0, 0.0, 1.0))
                num[idx] += w_test * lvl_test
                den[idx] += w_test
                ext_den[idx] += w_test

    # 4. Add International Certificates
    if certificates:
        for cert in certificates:
            cert_name = cert.get("name") if isinstance(cert, dict) else cert
            verified = cert.get("verified", True) if isinstance(cert, dict) else True
            w_cert = WEIGHTS["certificate_verified"] if verified else WEIGHTS["certificate_claimed"]
            
            # Find skills proved by this certificate
            proved_skills = CERT_MAP.get(cert_name, [])
            for sk in proved_skills:
                if sk in ALL_SKILLS:
                    idx = ALL_SKILLS.index(sk)
                    num[idx] += w_cert * 1.0
                    den[idx] += w_cert
                    ext_den[idx] += w_cert

    # Combined skill level (0 - 1)
    S = num / np.maximum(den, 1.0)
    S_series = pd.Series(S, index=ALL_SKILLS)

    def explain(skill):
        idx = ALL_SKILLS.index(skill)
        ev = evid_series.iat[idx]
        pr = prof_series.iat[idx]
        lvl = S[idx]
        if lvl >= READY:
            return "Covered", ""
        if ev < MIN_EVIDENCE:
            return ("Not proven strongly yet" if ext_den[idx] > 0 else "Not covered by the curriculum"), ""
        cs = [c for c in skill_courses.get(skill, []) if c in marks_dict]
        weakest = min(cs, key=lambda c: marks_dict[c]) if cs else ""
        wname = f"{course_names.get(weakest, weakest)} (your mark {marks_dict[weakest]:.0f})" if weakest else ""
        return ("Weak grades in related courses" if pr < WEAK_GRADE else "Only partly covered"), wname

    # 5. Role Matching
    role_matches = []
    for role_name, rdata in roles.items():
        w_role = rdata["weights"].reindex(ALL_SKILLS).fillna(0.0)
        sc = float(np.dot(S, w_role.values) / w_role.sum())
        
        # Gaps for this role
        gap_series = (w_role * (1 - S_series)).sort_values(ascending=False)
        open_gaps = gap_series[(w_role[gap_series.index] > 0) & (S_series[gap_series.index] < READY)]
        
        gaps_list = []
        for gskill in open_gaps.head(TOP_GAPS).index:
            cause, wname = explain(gskill)
            acts = actions_for(gskill, cause, wname, max_actions=2)
            gaps_list.append({
                "skill": gskill,
                "demand_pct": round(float(w_role[gskill] * 100), 1),
                "level_pct": round(float(S_series[gskill] * 100), 1),
                "cause": cause,
                "actions": acts
            })

        role_matches.append({
            "role": role_name,
            "match_pct": round(sc * 100, 1),
            "based_on": rdata["basis"],
            "core_skills": [f"{s} ({w_role[s]*100:.0f}%)" for s in rdata["weights"].sort_values(ascending=False).head(6).index],
            "gaps": gaps_list
        })

    role_matches.sort(key=lambda x: x["match_pct"], reverse=True)
    top_roles = role_matches[:TOP_ROLES]

    # 6. Job Matching
    candidate_jobs = jobs_df[jobs_df["relevant"] & (jobs_df["level"] != "Senior")].copy().reset_index(drop=True)
    
    # Eligibility based on experience
    allowed_exp = MAX_YEARS + EXTRA_YEARS_PER_EXP_YEAR * np.floor(exp_years)
    
    scored_jobs = []
    for k, row in candidate_jobs.iterrows():
        jskills = row["skills"]
        n_eff = max(len(jskills), MIN_JOB_SKILLS)
        
        # Check eligibility
        min_y = row["years_exp_min"]
        is_eligible = (pd.isna(min_y) or min_y <= allowed_exp)
        
        # Fit score
        skill_sum = sum(S[ALL_SKILLS.index(s)] for s in jskills if s in ALL_SKILLS)
        fit_val = skill_sum / n_eff
        
        det = []
        missing = []
        for s in jskills:
            if s in ALL_SKILLS:
                lv = S[ALL_SKILLS.index(s)]
                status = "strong" if lv >= READY else ("partial" if lv > 0 else "missing")
                det.append({
                    "skill": s,
                    "level_pct": round(float(lv * 100), 1),
                    "status": status
                })
                if lv < READY:
                    missing.append((lv, s))
            else:
                det.append({"skill": s, "level_pct": 0.0, "status": "missing"})
                missing.append((0.0, s))

        missing.sort()
        improve_actions = []
        for lv, s in missing[:TOP_IMPROVE]:
            cause, wname = explain(s)
            acts = actions_for(s, cause, wname, max_actions=3)
            
            # What-if gain calculation
            gain = None
            if s in ALL_SKILLS:
                sidx = ALL_SKILLS.index(s)
                for a in acts:
                    if a["kind"] in ASSUMED:
                        aw, al = ASSUMED[a["kind"]]
                        new_lvl = (num[sidx] + aw * al) / max(den[sidx] + aw, 1.0)
                        gain = round(100.0 * (new_lvl - lv) / n_eff, 1)
                        break

            improve_actions.append({
                "skill": s,
                "level_pct": round(float(lv * 100), 1),
                "cause": cause,
                "est_fit_gain_pts": gain,
                "actions": acts
            })

        scored_jobs.append({
            "job_id": row["job_id"],
            "title": row["title"],
            "company": row["company"],
            "specialization": row["specialization"],
            "level": row["level"],
            "work_mode": row["work_mode"],
            "years_required": int(min_y) if not pd.isna(min_y) else 0,
            "fit_pct": round(float(fit_val * 100), 1),
            "is_eligible": bool(is_eligible),
            "url": row["url"],
            "skills_detail": det,
            "improve_plan": improve_actions
        })

    # Sort eligible first, then by fit_pct descending
    scored_jobs.sort(key=lambda x: (x["is_eligible"], x["fit_pct"]), reverse=True)
    top_10_jobs = scored_jobs[:TOP_JOBS]

    # Assign rank
    for rank, jb in enumerate(top_10_jobs, 1):
        jb["rank"] = rank

    # 7. Comprehensive Skill Breakdown for UI
    skills_summary = []
    for sk in ALL_SKILLS:
        idx = ALL_SKILLS.index(sk)
        skills_summary.append({
            "skill": sk,
            "level_pct": round(float(S[idx] * 100), 1),
            "transcript_evidence": round(float(evid_series.iat[idx]), 1),
            "status": "ready" if S[idx] >= READY else ("developing" if S[idx] > 0 else "untrained")
        })

    skills_summary.sort(key=lambda x: x["level_pct"], reverse=True)

    return {
        "student": s_info,
        "experience": {"months": exp_months, "years": exp_years},
        "top_roles": top_roles,
        "top_jobs": top_10_jobs,
        "skills_summary": skills_summary
    }
