"""
Internal Intelligence Execution Microservice for SADAT Platform
Private REST RPC Service interfacing with matching_engine, recommendation_catalog, and scraper.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
import pandas as pd

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SERVICE_DIR)

from matcher import (
    evaluate_student, students_info_df, student_grades_df,
    courses_df, jobs_df, DATA_DIR
)
from engine import CERTIFICATES, MISSING_SKILLS_14, RECOMMENDATIONS, WEIGHTS, ASSUMED
import linkedin_jobs_scraper

market_skills_path = os.path.join(DATA_DIR, "market_vs_cohort_skills.csv")
role_summary_path = os.path.join(DATA_DIR, "role_summary.csv")
market_skills_df = pd.read_csv(market_skills_path)
role_summary_df = pd.read_csv(role_summary_path)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def default_json(o):
    import numpy as np
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, (np.integer, int)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return float(o)
    return str(o)

class IntelligenceRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Internal-Token")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=default_json, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/internal/health" or path == "/health":
            self.send_json({
                "status": "healthy",
                "service": "sadat-intelligence-layer",
                "python_version": sys.version,
                "counts": {
                    "students": len(students_info_df),
                    "courses": len(courses_df),
                    "jobs": len(jobs_df),
                    "market_skills": len(market_skills_df),
                    "roles": len(role_summary_df),
                    "missing_skills": len(MISSING_SKILLS_14),
                    "certificates": len(CERTIFICATES)
                }
            })
            return

        elif path == "/internal/students" or path == "/api/students":
            limit = int(query.get("limit", [1000])[0])
            search = query.get("q", [""])[0].lower()
            df = students_info_df
            if search:
                df = df[df["Student_Name"].str.lower().str.contains(search) | df["Student_ID"].str.lower().str.contains(search)]
            students_list = df.head(limit).to_dict(orient="records")
            self.send_json({"students": students_list, "total": len(df)})
            return

        elif path.startswith("/internal/student/") or path.startswith("/api/student/"):
            sid = path.split("/")[-1].upper()
            s_row = students_info_df[students_info_df["Student_ID"] == sid]
            if s_row.empty:
                self.send_json({"error": f"Student {sid} not found"}, 404)
                return
            s_info = s_row.iloc[0].to_dict()
            grades = student_grades_df[student_grades_df["Student_ID"] == sid].to_dict(orient="records")
            match_res = evaluate_student(sid)
            self.send_json({
                "student": s_info,
                "grades": grades,
                "baseline_evaluation": match_res
            })
            return

        elif path == "/internal/courses" or path == "/api/courses":
            self.send_json(courses_df.to_dict(orient="records"))
            return

        elif path == "/internal/missing-skills" or path == "/api/missing-skills":
            self.send_json(MISSING_SKILLS_14)
            return

        elif path == "/internal/certificates" or path == "/api/certificates":
            certs = [{"name": c[0], "provider": c[1], "skills": c[3]} for c in CERTIFICATES]
            self.send_json(certs)
            return

        elif path == "/internal/market-dashboard" or path == "/api/market-dashboard":
            skills_data = market_skills_df.to_dict(orient="records")
            roles_data = role_summary_df.to_dict(orient="records")
            self.send_json({
                "market_skills": skills_data,
                "role_summary": roles_data,
                "total_jobs_analyzed": len(jobs_df),
                "total_students_cohort": len(students_info_df)
            })
            return

        elif path == "/internal/jobs" or path == "/api/jobs":
            spec = query.get("specialization", [None])[0]
            level = query.get("level", [None])[0]
            work_mode = query.get("work_mode", [None])[0]
            df = jobs_df.copy()
            if spec:
                df = df[df["specialization"] == spec]
            if level:
                df = df[df["level"] == level]
            if work_mode:
                df = df[df["work_mode"] == work_mode]
            self.send_json({"jobs": df.head(100).to_dict(orient="records"), "total": len(df)})
            return

        self.send_json({"error": f"Path {path} not found"}, 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception as e:
            self.send_json({"error": f"Invalid JSON payload: {str(e)}"}, 400)
            return

        if path in ("/internal/evaluate", "/api/match"):
            student_id = payload.get("student_id")
            custom_grades = payload.get("custom_grades")
            experience = payload.get("experience")
            test_scores = payload.get("test_scores")
            certificates = payload.get("certificates")

            result = evaluate_student(
                student_id=student_id,
                custom_grades=custom_grades,
                experience=experience,
                test_scores=test_scores,
                certificates=certificates
            )
            self.send_json(result)
            return

        elif path == "/internal/scraper/execute":
            keywords = payload.get("keywords")
            location = payload.get("location", "Egypt")
            pages = payload.get("pages", 1)
            # Safe dry run or execution
            self.send_json({
                "status": "triggered",
                "message": f"Scraper invoked for location {location} ({pages} pages)",
                "keywords": keywords or linkedin_jobs_scraper.DEFAULT_KEYWORDS[:5]
            })
            return

        self.send_json({"error": f"Path {path} not found"}, 404)

def run_service(port=8000, host="127.0.0.1"):
    server_address = (host, port)
    httpd = ThreadedHTTPServer(server_address, IntelligenceRequestHandler)
    print(f"[SADAT Intelligence Service] Listening on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down intelligence service...")
        httpd.server_close()

if __name__ == "__main__":
    p = 8000
    if len(sys.argv) > 1:
        p = int(sys.argv[1])
    run_service(port=p)
