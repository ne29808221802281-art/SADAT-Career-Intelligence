#!/usr/bin/env python3
"""
SADAT matching engine (runs locally; raw jobs and transcripts never leave this machine).

Inputs
  --grades    folder holding the four Sadat_Year_N_Student_Grades.xlsx files (Grades_Long sheet)
  --skill-map Sadat_Course_Skill_Map_DRAFT.xlsx (sheet Course_Skill_Map)
  --jobs      scraper output (.xlsx)
  --evidence  (optional) CSV of what students report on the website, one row per item:
                Student_ID, Source, Skill, Certificate, Level, Months
              Source is one of: certificate_verified, certificate_claimed, online_test,
                                experience_verified, experience_claimed, self_rating
              * certificates: put the certificate name (any wording that contains e.g. "AZ-900") in Certificate;
                it is expanded into the skills it proves (Level is 100)
              * online_test / self_rating: Skill + Level (0-100 score)
              * experience_*: Skill + Months of real work with that skill

Outputs (folder --out)
  student_results.json   <- the ONLY file meant for the website (IDs and results, no names)
  matching_results.xlsx  <- everything in one workbook
  CSVs for the dashboards

How a skill level is computed (every source gives a LEVEL 0-1 and has a WEIGHT)
  transcript : level = SUM(relevance x credit hours x mark)/SUM(relevance x credit hours)/100
               weight = WEIGHTS["transcript"] x min(1, SUM(relevance x credit hours) / FULL_EVIDENCE)
  others     : weight = WEIGHTS[source]; level as above (experience: months/12, capped at 1)
  skill level = SUM(weight x level) / MAX(SUM(weight), 1)
How a job is scored (fit)
  fit(job) = SUM(skill level over the job's skills) / MAX(skills detected in the ad, MIN_JOB_SKILLS)
How a role is scored
  weight(skill) = share of the role's ads that mention it (only skills in >= MIN_DEMAND of ads)
  match(role)   = SUM(weight x skill level) / SUM(weight)
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recommendation_catalog import actions_for   # noqa: E402

# ----------------------------- settings (all are assumptions: tune them with the academy) -----------------------------
MAX_YEARS = 2          # years of experience a fresh graduate is eligible for ...
EXTRA_YEARS_PER_EXP_YEAR = 1.0   # ... plus this many for every full year of work experience the student reports
MIN_ROLE_JOBS = 10     # fewer entry-level ads than this -> the role profile uses ads of all levels
MIN_ROLE_ADS = 5       # fewer ads than this -> role is skipped
MIN_DEMAND = 0.10      # a skill counts for a role only if >= 10% of its ads mention it
FULL_EVIDENCE = 3.0    # relevance x credit hours that counts as full transcript evidence (one 3-credit course)
MIN_EVIDENCE = 1.5     # below this a skill is "not covered by the curriculum"
WEAK_GRADE = 65        # proficiency below this = "weak grades"
READY = 0.5            # skill level at or above this counts as "ready"
MIN_JOB_SKILLS = 4     # an ad with fewer detected skills is scored as if it listed this many
TOP_ROLES, TOP_GAPS, TOP_JOBS, TOP_IMPROVE = 3, 5, 10, 3
# Weight of each evidence source (0-1). Assumptions to agree with the academy.
WEIGHTS = {"transcript": 1.0, "certificate_verified": 0.9, "experience_verified": 0.8, "online_test": 0.7,
           "certificate_claimed": 0.5, "experience_claimed": 0.5, "self_rating": 0.3}
# What a suggested action is assumed to add, for the "estimated fit gain" shown to students:
# (weight, level) of the evidence the student would gain if they pass the certificate / score 80 on a test.
ASSUMED = {"certificate": (WEIGHTS["certificate_verified"], 1.0), "test": (WEIGHTS["online_test"], 0.8)}


# ----------------------------------------------------------------------------- loading
def load_grades(folder):
    files = sorted(glob.glob(os.path.join(folder, "*Student_Grades.xlsx")))
    if not files:
        raise SystemExit(f"No *Student_Grades.xlsx files found in {folder}")
    g = pd.concat([pd.read_excel(f, sheet_name="Grades_Long") for f in files], ignore_index=True)
    return g[["Student_ID", "Course_ID", "Course_Name", "M_Mark", "C_H_Credit_Hours"]]


def load_skill_map(path):
    m = pd.read_excel(path, sheet_name="Course_Skill_Map").rename(columns={"Relevance (0-1)": "rel"})
    if "Faculty_Review" in m:
        m = m[m["Faculty_Review"].fillna("") != "Remove"]
    return m[["Course_ID", "Skill", "rel"]].dropna()


def load_jobs(path):
    from linkedin_jobs_scraper import classify_level
    d = pd.read_excel(path)
    d["years_exp_min"] = pd.to_numeric(d["years_exp_min"], errors="coerce")
    d["linkedin_seniority"] = d["linkedin_seniority"].fillna("")
    d["level"] = [classify_level(t, s, None if pd.isna(y) else int(y))
                  for t, s, y in zip(d["title"], d["linkedin_seniority"], d["years_exp_min"])]
    d["skills"] = d["technical_requirements"].fillna("").map(lambda t: [x for x in t.split(", ") if x])
    before = len(d)
    d = d.drop_duplicates(subset=["title", "company"]).reset_index(drop=True)   # reposts of the same ad
    d["relevant"] = (d["specialization"] != "Other / Unclassified") & (d["skills"].map(len) > 0)
    d["entry"] = d["relevant"] & (d["level"] != "Senior") & (d["years_exp_min"].isna() | (d["years_exp_min"] <= MAX_YEARS))
    d.attrs["dropped_duplicates"] = before - len(d)
    return d


def load_evidence(path):
    """Read the website's evidence CSV into rows: Student_ID, Skill, Source, level (0-1), months."""
    from linkedin_jobs_scraper import CERTIFICATES, extract_certs
    cert_skills = {c[0]: c[3] for c in CERTIFICATES}
    e = pd.read_csv(path).reindex(columns=["Student_ID", "Source", "Skill", "Certificate", "Level", "Months"])
    bad = set(e["Source"].dropna()) - (set(WEIGHTS) - {"transcript"})
    if bad:
        raise SystemExit(f"Unknown evidence Source values {sorted(bad)}; allowed: {sorted(set(WEIGHTS) - {'transcript'})}")
    rows = []
    for r in e.itertuples(index=False):
        months = 0.0 if pd.isna(r.Months) else float(r.Months)
        if isinstance(r.Certificate, str) and r.Certificate.strip():
            names = extract_certs(r.Certificate) or [n for n in cert_skills if n.lower() == r.Certificate.strip().lower()]
            for n in names:
                for s in cert_skills[n]:
                    rows.append((r.Student_ID, s, r.Source, 1.0, months))
            continue
        if pd.isna(r.Skill):
            continue
        if r.Source.startswith("experience"):
            level = min(1.0, months / 12.0) if months > 0 else (0.0 if pd.isna(r.Level) else r.Level / 100.0)
        else:
            level = 1.0 if (pd.isna(r.Level) and r.Source.startswith("certificate")) else (0.0 if pd.isna(r.Level) else r.Level / 100.0)
        rows.append((r.Student_ID, r.Skill, r.Source, float(np.clip(level, 0, 1)), months))
    return pd.DataFrame(rows, columns=["Student_ID", "Skill", "Source", "level", "months"])


# ----------------------------------------------------------------------------- students
def build_profiles(grades, cmap):
    """Transcript only. Returns (strength, proficiency 0-100, evidence): student x skill DataFrames."""
    j = grades.merge(cmap, on="Course_ID")
    j["w"] = j["rel"] * j["C_H_Credit_Hours"]
    j["wm"] = j["w"] * j["M_Mark"]
    g = j.groupby(["Student_ID", "Skill"])[["w", "wm"]].sum()
    prof = (g["wm"] / g["w"]).unstack()
    evid = g["w"].unstack()
    strength = (prof / 100.0) * np.clip(evid / FULL_EVIDENCE, 0, 1)
    return strength, prof, evid


def combine_evidence(prof, evid, ext, students, skills):
    """Return (S, NUM, DEN): skill level plus the numerator / denominator it came from (used for what-if gains)."""
    L = (prof / 100.0).reindex(index=students, columns=skills).fillna(0.0).values
    M = (np.clip(evid / FULL_EVIDENCE, 0, 1) * WEIGHTS["transcript"]).reindex(index=students, columns=skills).fillna(0.0).values
    num, den, ext_den = M * L, M.copy(), np.zeros_like(M)
    if ext is not None and len(ext):
        best = ext.groupby(["Student_ID", "Skill", "Source"], as_index=False)["level"].max()   # one count per source type
        best["w"] = best["Source"].map(WEIGHTS)
        best["n"] = best["w"] * best["level"]
        agg = best.groupby(["Student_ID", "Skill"])[["n", "w"]].sum()
        an = agg["n"].unstack().reindex(index=students, columns=skills).fillna(0.0).values
        aw = agg["w"].unstack().reindex(index=students, columns=skills).fillna(0.0).values
        num, den, ext_den = num + an, den + aw, aw
    S = pd.DataFrame(num / np.maximum(den, 1.0), index=students, columns=skills)
    return S, num, den, ext_den


def experience_years(ext, students):
    if ext is None or not len(ext):
        return pd.Series(0.0, index=students)
    m = ext[ext["Source"].str.startswith("experience")].groupby("Student_ID")["months"].max() / 12.0
    return m.reindex(students).fillna(0.0)


# ----------------------------------------------------------------------------- roles
def role_profiles(jobs):
    out = {}
    for spec, g in jobs[jobs["relevant"]].groupby("specialization"):
        e = g[g["entry"]]
        use_entry = len(e) >= MIN_ROLE_JOBS
        base = e if use_entry else g
        if len(base) < MIN_ROLE_ADS:
            continue
        freq = base["skills"].explode().value_counts() / len(base)
        freq = freq[freq >= MIN_DEMAND]
        out[spec] = {"n_ads": len(base), "n_entry_ads": len(e),
                     "basis": "entry-level ads" if use_entry else "ads of all levels (few entry-level ads)",
                     "weights": freq}
    return out


# ----------------------------------------------------------------------------- matching
def run(grades, cmap, jobs, ext=None, out_dir="results"):
    os.makedirs(out_dir, exist_ok=True)
    _, prof, evid = build_profiles(grades, cmap)
    roles = role_profiles(jobs)
    students = list(prof.index)
    all_skills = sorted(set(prof.columns) | {s for r in roles.values() for s in r["weights"].index}
                        | {s for ss in jobs["skills"] for s in ss}
                        | (set(ext["Skill"]) if ext is not None and len(ext) else set()))
    S, NUM, DEN, EXTDEN = combine_evidence(prof, evid, ext, students, all_skills)
    P = prof.reindex(index=students, columns=all_skills)
    E = evid.reindex(index=students, columns=all_skills).fillna(0.0)
    sidx = {s: i for i, s in enumerate(students)}
    kidx = {k: i for i, k in enumerate(all_skills)}
    exp_years = experience_years(ext, students)
    names = grades.drop_duplicates("Course_ID").set_index("Course_ID")["Course_Name"]
    marks = grades.pivot(index="Student_ID", columns="Course_ID", values="M_Mark")
    skill_courses = cmap.groupby("Skill")["Course_ID"].apply(list).to_dict()

    role_names = list(roles)
    W = pd.DataFrame({r: roles[r]["weights"].reindex(all_skills).fillna(0.0) for r in role_names})
    scores = pd.DataFrame(S.values @ W.values / W.sum().values, index=students, columns=role_names)

    def explain(sid, skill):
        i, k = sidx[sid], kidx[skill]
        ev, pr, lvl = E.iat[i, k], P.iat[i, k], S.iat[i, k]
        if lvl >= READY:
            return "Covered", ""
        if ev < MIN_EVIDENCE:
            return ("Not proven strongly yet" if EXTDEN[i, k] > 0 else "Not covered by the curriculum"), ""
        cs = [c for c in skill_courses.get(skill, []) if c in marks.columns and not pd.isna(marks.at[sid, c])]
        weakest = min(cs, key=lambda c: marks.at[sid, c]) if cs else ""
        wname = f"{names.get(weakest, weakest)} (your mark {marks.at[sid, weakest]:.0f})" if weakest else ""
        return ("Weak grades in related courses" if pr < WEAK_GRADE else "Only partly covered"), wname

    # candidate jobs: relevant, not Senior; each student is limited by years of experience
    cj = jobs[jobs["relevant"] & (jobs["level"] != "Senior")].reset_index(drop=True)
    J = np.zeros((len(all_skills), len(cj)))
    for k, ss in enumerate(cj["skills"]):
        for s in ss:
            J[kidx[s], k] = 1.0
    denom_job = np.maximum(J.sum(axis=0), MIN_JOB_SKILLS)
    job_scores = (S.values @ J) / denom_job
    yrs = cj["years_exp_min"].values
    allowed = MAX_YEARS + EXTRA_YEARS_PER_EXP_YEAR * np.floor(exp_years.values)[:, None]
    eligible = np.isnan(yrs)[None, :] | (yrs[None, :] <= allowed)
    job_scores = np.where(eligible, job_scores, -1.0)

    gaps, matches, plans, summary, public = [], [], [], [], {}
    for sid in students:
        si = sidx[sid]
        top = scores.loc[sid].sort_values(ascending=False).head(TOP_ROLES)
        row = {"Student_ID": sid, "Experience_years": round(float(exp_years.iat[si]), 1)}
        pub = {"top_roles": [], "top_jobs": []}
        for rank, (role, sc) in enumerate(top.items(), 1):
            row[f"Role{rank}"], row[f"Role{rank}_Match%"] = role, round(100 * sc, 1)
            w = W[role]
            gap = (w * (1 - S.loc[sid])).sort_values(ascending=False)
            open_gaps = gap[(w[gap.index] > 0) & (S.loc[sid, gap.index] < READY)]
            gl = []
            for g_rank, skill in enumerate(open_gaps.head(TOP_GAPS).index, 1):
                cause, wname = explain(sid, skill)
                acts = actions_for(skill, cause, wname)
                rec = {"Student_ID": sid, "Role": role, "Rank": g_rank, "Skill": skill,
                       "Demand%": round(100 * w[skill], 1), "Level%": round(100 * S.at[sid, skill], 1),
                       "Cause": cause, "Suggested_Actions": " | ".join(a["text"] for a in acts)}
                gaps.append(rec)
                gl.append({"skill": skill, "demand_pct": rec["Demand%"], "level_pct": rec["Level%"], "cause": cause,
                           "actions": [{k: a[k] for k in ("kind", "name", "provider", "cost")} for a in acts]})
            pub["top_roles"].append({"role": role, "match_pct": round(100 * sc, 1), "based_on": roles[role]["basis"], "gaps": gl})
        summary.append(row)

        order = np.argsort(-job_scores[si])[:TOP_JOBS]
        for jrank, k in enumerate((o for o in order if job_scores[si, o] >= 0), 1):
            jb = cj.iloc[k]
            n_eff = denom_job[k]
            fit = job_scores[si, k]
            det, missing = [], []
            for s in jb["skills"]:
                lv = S.iat[si, kidx[s]]
                det.append({"skill": s, "level_pct": round(100 * lv, 1),
                            "status": "strong" if lv >= READY else ("partial" if lv > 0 else "missing")})
                if lv < READY:
                    missing.append((lv, s))
            missing.sort()
            improve = []
            for lv, s in missing[:TOP_IMPROVE]:
                cause, wname = explain(sid, s)
                acts = actions_for(s, cause, wname)
                gain = None
                for a in acts:                                   # gain from the first action that counts as evidence
                    if a["kind"] in ASSUMED:
                        aw, al = ASSUMED[a["kind"]]
                        new = (NUM[si, kidx[s]] + aw * al) / max(DEN[si, kidx[s]] + aw, 1.0)
                        gain = round(100 * (new - lv) / n_eff, 1)
                        break
                improve.append({"skill": s, "level_pct": round(100 * lv, 1), "cause": cause,
                                "est_fit_gain_pts": gain,
                                "actions": [{k2: a[k2] for k2 in ("kind", "name", "provider", "cost", "text")} for a in acts]})
                plans.append({"Student_ID": sid, "Job_Rank": jrank, "Job_ID": jb["job_id"], "Job_Title": jb["title"],
                              "Skill": s, "Level%": round(100 * lv, 1), "Cause": cause,
                              "Est_Fit_Gain_pts": gain, "Suggested_Actions": " | ".join(a["text"] for a in acts)})
            rec = {"Student_ID": sid, "Rank": jrank, "Job_ID": jb["job_id"], "Title": jb["title"], "Company": jb["company"],
                   "Specialization": jb["specialization"], "Level": jb["level"], "Work_Mode": jb["work_mode"],
                   "Years_Required": jb["years_exp_min"], "Fit%": round(100 * fit, 1),
                   "Skills_Strong": ", ".join(d["skill"] for d in det if d["status"] == "strong"),
                   "Skills_To_Improve": ", ".join(s for _, s in missing), "URL": jb["url"]}
            matches.append(rec)
            pub["top_jobs"].append({"rank": jrank, "title": rec["Title"], "company": rec["Company"], "level": rec["Level"],
                                    "work_mode": rec["Work_Mode"], "years_required": None if pd.isna(rec["Years_Required"]) else int(rec["Years_Required"]),
                                    "fit_pct": rec["Fit%"], "url": rec["URL"], "skills": det, "improve": improve})
        public[sid] = pub

    gaps, matches, plans, summary = map(pd.DataFrame, (gaps, matches, plans, summary))

    # dashboards: market demand vs cohort supply
    entry = jobs[jobs["entry"]]
    dem = entry["skills"].explode().value_counts() / max(len(entry), 1)
    dem_all = jobs[jobs["relevant"]]["skills"].explode().value_counts() / max(int(jobs["relevant"].sum()), 1)
    sd = pd.DataFrame({"Skill": all_skills})
    sd["Demand%_entry_level_ads"] = sd["Skill"].map(dem).fillna(0).mul(100).round(1)
    sd["Demand%_all_levels"] = sd["Skill"].map(dem_all).fillna(0).mul(100).round(1)
    sd["Cohort_mean_level%"] = (S.mean() * 100).round(1).values
    sd["Cohort_ready%"] = ((S >= READY).mean() * 100).round(1).values
    sd["Curriculum_evidence"] = E.mean().round(1).values
    sd["Gap_score"] = (sd["Demand%_entry_level_ads"] * (100 - sd["Cohort_ready%"]) / 100).round(1)
    sd = sd.sort_values("Gap_score", ascending=False)
    rp = pd.DataFrame([{"Role": r, "Ads_used": v["n_ads"], "Entry_level_ads": v["n_entry_ads"], "Basis": v["basis"],
                        "Core_skills": ", ".join(f"{s} {100*x:.0f}%" for s, x in v["weights"].sort_values(ascending=False).head(12).items())}
                       for r, v in roles.items()])
    role_summary = scores.stack().rename("Match").reset_index().rename(columns={"level_1": "Role"})
    role_summary = role_summary.groupby("Role")["Match"].agg(["mean", "median", "max"]).mul(100).round(1)
    role_summary.columns = ["Cohort_mean_match%", "Cohort_median_match%", "Best_student_match%"]
    role_summary = role_summary.join(rp.set_index("Role")).reset_index().sort_values("Cohort_mean_match%", ascending=False)

    summary.to_csv(f"{out_dir}/student_summary.csv", index=False)
    gaps.to_csv(f"{out_dir}/student_gaps.csv", index=False)
    matches.to_csv(f"{out_dir}/student_job_matches.csv", index=False)
    plans.to_csv(f"{out_dir}/student_improvement_plan.csv", index=False)
    sd.to_csv(f"{out_dir}/market_vs_cohort_skills.csv", index=False)
    role_summary.to_csv(f"{out_dir}/role_summary.csv", index=False)
    with open(f"{out_dir}/student_results.json", "w", encoding="utf-8") as f:
        json.dump(public, f, ensure_ascii=False)
    with pd.ExcelWriter(f"{out_dir}/matching_results.xlsx", engine="openpyxl") as xw:
        for name, df in [("Role_Summary", role_summary), ("Market_vs_Cohort", sd), ("Student_Summary", summary),
                         ("Student_Job_Matches", matches), ("Improvement_Plan", plans), ("Student_Gaps", gaps)]:
            df.to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for i, col in enumerate(df.columns, 1):
                width = 60 if ("Actions" in col) else 40 if col in ("Title", "Company", "Skills_To_Improve", "Skills_Strong", "Job_Title") else max(12, len(str(col)) + 4)
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width
    return {"S": S, "scores": scores, "roles": roles, "summary": summary, "gaps": gaps, "matches": matches,
            "plans": plans, "skills": sd, "role_summary": role_summary, "candidate_jobs": len(cj), "public": public}


def main(argv=None):
    ap = argparse.ArgumentParser(description="SADAT matching engine")
    ap.add_argument("--grades", required=True, help="folder with the Sadat_Year_N_Student_Grades.xlsx files")
    ap.add_argument("--skill-map", required=True)
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--evidence", help="optional CSV of certificates / tests / experience (see the top of this file)")
    ap.add_argument("--out", default="results")
    a, _ = ap.parse_known_args(argv)
    jobs = load_jobs(a.jobs)
    ext = load_evidence(a.evidence) if a.evidence else None
    r = run(load_grades(a.grades), load_skill_map(a.skill_map), jobs, ext, a.out)
    print(f"Jobs: {len(jobs)} after removing {jobs.attrs['dropped_duplicates']} duplicate ads; "
          f"{int(jobs['relevant'].sum())} relevant, {r['candidate_jobs']} candidates for matching (not Senior)")
    print(f"Students: {len(r['S'])}; roles scored: {len(r['roles'])}; evidence rows: {0 if ext is None else len(ext)}")
    print(f"Wrote files to {os.path.abspath(a.out)}")


if __name__ == "__main__":
    main()
