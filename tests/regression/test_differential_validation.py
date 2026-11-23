"""
Automated Differential Validation Suite for SADAT Platform Modernization
Gate 7 Verification: Differential comparison between experimental baseline and modernized platform.
"""

import os
import sys
import json
import unittest
import pandas as pd
import numpy as np

# Paths
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(TEST_DIR))
BASELINE_DIR = os.path.join(os.path.dirname(PROJECT_DIR), "career-matching-platform", "backend")
MODERN_DIR = os.path.join(PROJECT_DIR, "services", "intelligence")

sys.path.insert(0, BASELINE_DIR)
import matcher as baseline_matcher
import engine as baseline_engine

sys.path.insert(0, MODERN_DIR)
import matcher as modern_matcher
import engine as modern_engine

class TestDifferentialValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.student_id = "SAD20260001"
        cls.base_eval = baseline_matcher.evaluate_student(cls.student_id)
        cls.modern_eval = modern_matcher.evaluate_student(cls.student_id)

    def test_top_roles_parity(self):
        """Assert identical role rankings and match percentages"""
        b_roles = self.base_eval["top_roles"]
        m_roles = self.modern_eval["top_roles"]
        self.assertEqual(len(b_roles), len(m_roles), "Role count mismatch")

        for i in range(len(b_roles)):
            b_r = b_roles[i]
            m_r = m_roles[i]
            self.assertEqual(b_r["role"], m_r["role"], f"Role name mismatch at rank {i+1}")
            self.assertAlmostEqual(b_r["match_pct"], m_r["match_pct"], places=1, msg=f"Role match % mismatch at rank {i+1}")

    def test_top_jobs_ranking_and_fit(self):
        """Assert identical top 10 job matches, ranks, and fit percentages"""
        b_jobs = self.base_eval["top_jobs"]
        m_jobs = self.modern_eval["top_jobs"]
        self.assertEqual(len(b_jobs), len(m_jobs), "Job match count mismatch")
        self.assertEqual(len(m_jobs), 10, "Top jobs must return exactly 10 jobs")

        for i in range(len(b_jobs)):
            b_j = b_jobs[i]
            m_j = m_jobs[i]
            self.assertEqual(b_j["job_id"], m_j["job_id"], f"Job ID mismatch at rank {i+1}")
            self.assertEqual(b_j["title"], m_j["title"], f"Job title mismatch at rank {i+1}")
            self.assertEqual(b_j["company"], m_j["company"], f"Company mismatch at rank {i+1}")
            self.assertAlmostEqual(b_j["fit_pct"], m_j["fit_pct"], places=1, msg=f"Job fit % mismatch at rank {i+1}")
            self.assertEqual(b_j["is_eligible"], m_j["is_eligible"], f"Eligibility mismatch at rank {i+1}")

    def test_skill_classifications_parity(self):
        """Assert identical skill breakdown (strong/developing/missing)"""
        b_j1 = self.base_eval["top_jobs"][0]
        m_j1 = self.modern_eval["top_jobs"][0]

        b_skills = {d["skill"]: (d["level_pct"], d["status"]) for d in b_j1["skills_detail"]}
        m_skills = {d["skill"]: (d["level_pct"], d["status"]) for d in m_j1["skills_detail"]}

        self.assertEqual(set(b_skills.keys()), set(m_skills.keys()))
        for sk in b_skills:
            b_lv, b_stat = b_skills[sk]
            m_lv, m_stat = m_skills[sk]
            self.assertAlmostEqual(b_lv, m_lv, places=1, msg=f"Skill {sk} level mismatch")
            self.assertEqual(b_stat, m_stat, f"Skill {sk} status classification mismatch")

    def test_recommendation_and_fit_gain_parity(self):
        """Assert identical gap root cause diagnosis and estimated fit gain points"""
        b_plan = self.base_eval["top_jobs"][0]["improve_plan"]
        m_plan = self.modern_eval["top_jobs"][0]["improve_plan"]

        self.assertEqual(len(b_plan), len(m_plan))
        for i in range(len(b_plan)):
            b_p = b_plan[i]
            m_p = m_plan[i]
            self.assertEqual(b_p["skill"], m_p["skill"])
            self.assertEqual(b_p["cause"], m_p["cause"])
            self.assertEqual(b_p["est_fit_gain_pts"], m_p["est_fit_gain_pts"])
            if b_p["actions"]:
                self.assertEqual(b_p["actions"][0]["name"], m_p["actions"][0]["name"])

    def test_dynamic_questionnaire_recalculation(self):
        """Assert identical recalculation when experience, test scores, and certs are submitted"""
        q_args = {
            "student_id": self.student_id,
            "experience": {"has_experience": True, "months": 14, "verified": True, "role": "AI / ML Engineer"},
            "test_scores": {"Python": 95, "SQL": 90, "Machine Learning": 88, "Docker": 80},
            "certificates": [{"name": "AWS Certified Machine Learning - Associate", "verified": True}]
        }

        b_cust = baseline_matcher.evaluate_student(**q_args)
        m_cust = modern_matcher.evaluate_student(**q_args)

        self.assertEqual(b_cust["top_roles"][0]["role"], m_cust["top_roles"][0]["role"])
        self.assertAlmostEqual(b_cust["top_roles"][0]["match_pct"], m_cust["top_roles"][0]["match_pct"], places=1)
        self.assertEqual(b_cust["top_jobs"][0]["job_id"], m_cust["top_jobs"][0]["job_id"])
        self.assertAlmostEqual(b_cust["top_jobs"][0]["fit_pct"], m_cust["top_jobs"][0]["fit_pct"], places=1)

    def test_14_missing_skills_definitions(self):
        """Assert exact integrity of all 14 missing skills and test providers"""
        self.assertEqual(len(baseline_engine.MISSING_SKILLS_14), len(modern_engine.MISSING_SKILLS_14))
        self.assertEqual(len(modern_engine.MISSING_SKILLS_14), 14)
        for i in range(14):
            self.assertEqual(baseline_engine.MISSING_SKILLS_14[i]["name"], modern_engine.MISSING_SKILLS_14[i]["name"])
            self.assertEqual(baseline_engine.MISSING_SKILLS_14[i]["test_provider"], modern_engine.MISSING_SKILLS_14[i]["test_provider"])
            self.assertEqual(baseline_engine.MISSING_SKILLS_14[i]["test_cost"], modern_engine.MISSING_SKILLS_14[i]["test_cost"])

if __name__ == "__main__":
    unittest.main()
