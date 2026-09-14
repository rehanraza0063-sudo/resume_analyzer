"""
app.py

Flask backend for ResumeAI. Every route returns JSON. All analysis is
done locally via analyzer.py / resume_parser.py (see config.py for how
an AI API could later be plugged in).

Run with:  python app.py
Serves on: http://localhost:5000
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

import config
from analyzer import full_analysis, improve_bullet, job_description_match
from database import get_recent_analyses, init_db, save_analysis
from job_roles import ROLE_NAMES
from resume_parser import DEMO_RESUME_TEXT, ResumeParseError, extract_text, parse_resume

app = Flask(__name__)
CORS(app)

MAX_UPLOAD_BYTES = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@app.errorhandler(413)
def too_large(_err):
    return jsonify({"error": f"File is too large. Max size is {config.MAX_UPLOAD_SIZE_MB}MB."}), 413


@app.errorhandler(500)
def server_error(_err):
    return jsonify({"error": "Something went wrong while processing your request."}), 500


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in config.ALLOWED_EXTENSIONS


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "ai_provider": config.AI_PROVIDER})


@app.route("/api/job-roles", methods=["GET"])
def job_roles():
    return jsonify({"roles": ROLE_NAMES})


@app.route("/api/upload-resume", methods=["POST"])
def upload_resume():
    """Accepts a PDF/DOCX file OR pasted text, returns the parsed structure only."""
    try:
        if "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            if not _allowed_file(file.filename):
                return jsonify({"error": "Unsupported file type. Please upload a PDF or DOCX file."}), 400
            file_bytes = file.read()
            if len(file_bytes) > MAX_UPLOAD_BYTES:
                return jsonify({"error": f"File is too large. Max size is {config.MAX_UPLOAD_SIZE_MB}MB."}), 413
            if not file_bytes:
                return jsonify({"error": "The uploaded file is empty."}), 400
            text = extract_text(file.filename, file_bytes)
        else:
            text = (request.form.get("text") or (request.json or {}).get("text") if request.is_json else request.form.get("text")) or ""
            text = text.strip()
            if not text:
                return jsonify({"error": "No file uploaded and no resume text provided."}), 400

        parsed = parse_resume(text)
        return jsonify({"parsed": parsed})

    except ResumeParseError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive catch-all
        return jsonify({"error": f"Unexpected error while processing the resume: {exc}"}), 500


@app.route("/api/analyze-resume", methods=["POST"])
def analyze_resume():
    """
    Accepts either:
      - multipart/form-data with a 'file' (PDF/DOCX) and optional 'target_role'
      - JSON { "text": "...", "target_role": "..." }
    Returns the full analysis dashboard payload.
    """
    try:
        target_role = None
        text = None

        if request.content_type and "multipart/form-data" in request.content_type:
            target_role = request.form.get("target_role") or None
            if "file" in request.files and request.files["file"].filename:
                file = request.files["file"]
                if not _allowed_file(file.filename):
                    return jsonify({"error": "Unsupported file type. Please upload a PDF or DOCX file."}), 400
                file_bytes = file.read()
                if len(file_bytes) > MAX_UPLOAD_BYTES:
                    return jsonify({"error": f"File is too large. Max size is {config.MAX_UPLOAD_SIZE_MB}MB."}), 413
                if not file_bytes:
                    return jsonify({"error": "The uploaded file is empty."}), 400
                text = extract_text(file.filename, file_bytes)
            else:
                text = (request.form.get("text") or "").strip()
        else:
            payload = request.get_json(silent=True) or {}
            text = (payload.get("text") or "").strip()
            target_role = payload.get("target_role") or None

        if not text:
            return jsonify({"error": "No file uploaded and no resume text provided."}), 400

        if target_role and target_role not in ROLE_NAMES:
            return jsonify({"error": f"Unknown target role: {target_role}"}), 400

        parsed = parse_resume(text)
        result = full_analysis(parsed, target_role=target_role)
        save_analysis(result)
        return jsonify(result)

    except ResumeParseError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": f"Unexpected error while analyzing the resume: {exc}"}), 500


@app.route("/api/demo", methods=["GET"])
def demo():
    """Returns the analysis for a built-in sample resume — no upload needed."""
    try:
        parsed = parse_resume(DEMO_RESUME_TEXT)
        result = full_analysis(parsed, target_role="Data Analyst")
        return jsonify(result)
    except ResumeParseError as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/skill-gap", methods=["POST"])
def skill_gap():
    """Recompute skill-gap for an already-parsed skill list against a new target role."""
    try:
        payload = request.get_json(silent=True) or {}
        skills = payload.get("skills") or []
        target_role = payload.get("target_role")
        if not target_role or target_role not in ROLE_NAMES:
            return jsonify({"error": "Please provide a valid target_role."}), 400
        from analyzer import skill_gap_analysis, build_roadmap
        gap = skill_gap_analysis(skills, target_role)
        roadmap = build_roadmap(target_role, gap["missing_skills"])
        return jsonify({"skill_gap": gap, "roadmap": roadmap})
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": f"Unexpected error: {exc}"}), 500


@app.route("/api/job-match", methods=["POST"])
def job_match():
    try:
        payload = request.get_json(silent=True) or {}
        resume_text = (payload.get("resume_text") or "").strip()
        job_description = (payload.get("job_description") or "").strip()
        resume_skills = payload.get("resume_skills") or []

        if not resume_text:
            return jsonify({"error": "Missing resume text. Analyze your resume first."}), 400
        if not job_description or len(job_description) < 30:
            return jsonify({"error": "Please paste a more complete job description."}), 400

        if not resume_skills:
            parsed = parse_resume(resume_text)
            resume_skills = parsed["skills"]

        result = job_description_match(resume_skills, resume_text, job_description)
        return jsonify(result)
    except ResumeParseError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": f"Unexpected error: {exc}"}), 500


@app.route("/api/improve-bullet", methods=["POST"])
def improve_bullet_route():
    try:
        payload = request.get_json(silent=True) or {}
        bullet = (payload.get("bullet") or "").strip()
        if not bullet:
            return jsonify({"error": "Please enter a bullet point to improve."}), 400
        if len(bullet) > 500:
            return jsonify({"error": "That bullet point is too long. Keep it under 500 characters."}), 400
        result = improve_bullet(bullet)
        return jsonify(result)
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": f"Unexpected error: {exc}"}), 500


@app.route("/api/history", methods=["GET"])
def history():
    return jsonify({"analyses": get_recent_analyses()})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
