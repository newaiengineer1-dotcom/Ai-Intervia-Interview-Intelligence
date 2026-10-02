
import re
from collections import Counter
from typing import Any


STANDARD_SECTIONS = [
    "summary", "experience", "work experience", "education",
    "skills", "projects", "certifications", "achievements"
]

CONTACT_PATTERNS = {
    "email": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    "phone": r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)",
    "linkedin": r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s)]+",
}

COMMON_SKILLS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "sql", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes",
    "aws", "azure", "gcp", "terraform", "ansible", "git", "linux", "django",
    "fastapi", "flask", "react", "node.js", "spring", "api", "rest", "graphql",
    "microservices", "ci/cd", "jenkins", "github actions", "machine learning",
    "data engineering", "pandas", "numpy", "spark", "airflow", "snowflake",
    "communication", "leadership", "project management", "agile", "scrum",
}


def _terms(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9+#./-]{2,}", (text or "").lower())


def _keyword_set(text: str) -> set[str]:
    terms = set(_terms(text))
    # Preserve meaningful multi-word phrases from a small, deterministic dictionary.
    lower = (text or "").lower()
    phrases = {p for p in COMMON_SKILLS if p in lower}
    return terms | phrases


def assess_ats_readiness(cv_text: str, jd_text: str) -> dict[str, Any]:
    cv = cv_text or ""
    jd = jd_text or ""
    lower = cv.lower()
    checks: list[dict[str, Any]] = []

    # 1) Parseability proxy
    chars = len(re.sub(r"\s+", "", cv))
    parseability = 100 if chars >= 800 else (75 if chars >= 400 else 45 if chars >= 150 else 20)
    checks.append({
        "name": "Text parseability",
        "score": parseability,
        "status": "PASS" if parseability >= 75 else "REVIEW",
        "detail": "Extracted resume text is substantial enough for a basic ATS text parser." if parseability >= 75 else "Resume text is short or sparse; verify the source PDF/DOCX is machine-readable."
    })

    # 2) Contact block
    contact_hits = sum(bool(re.search(p, cv, re.I)) for p in CONTACT_PATTERNS.values())
    contact_score = round(contact_hits / len(CONTACT_PATTERNS) * 100)
    checks.append({
        "name": "Contact block",
        "score": contact_score,
        "status": "PASS" if contact_score >= 67 else "REVIEW",
        "detail": f"{contact_hits}/3 common contact signals detected (email, phone, LinkedIn)."
    })

    # 3) Standard headings
    heading_hits = sum(1 for s in STANDARD_SECTIONS if re.search(rf"(?im)^\s*(?:#+\s*)?{re.escape(s)}\s*$", cv))
    heading_score = round(min(100, heading_hits / 5 * 100))
    checks.append({
        "name": "Standard resume sections",
        "score": heading_score,
        "status": "PASS" if heading_hits >= 4 else "REVIEW",
        "detail": f"{heading_hits} standard section headings detected."
    })

    # 4) Achievement evidence
    quantified = len(re.findall(r"(?<!\w)(?:\d+(?:\.\d+)?%|\$[\d,.]+|\d+(?:\.\d+)?\s*(?:years?|months?|ms|s|x|k|m|million|billion))(?!\w)", cv, re.I))
    achievement_score = 100 if quantified >= 6 else 80 if quantified >= 3 else 55 if quantified >= 1 else 25
    checks.append({
        "name": "Quantified achievements",
        "score": achievement_score,
        "status": "PASS" if achievement_score >= 80 else "REVIEW",
        "detail": f"{quantified} quantified achievement signals detected."
    })

    # 5) JD keyword alignment
    cv_terms = _keyword_set(cv)
    jd_terms = _keyword_set(jd)
    meaningful_jd = {t for t in jd_terms if len(t) >= 3 and t not in {"the", "and", "with", "for", "from", "this", "that"}}
    matched = meaningful_jd & cv_terms
    keyword_score = round(len(matched) / max(1, len(meaningful_jd)) * 100)
    checks.append({
        "name": "JD keyword alignment",
        "score": keyword_score,
        "status": "PASS" if keyword_score >= 65 else "REVIEW",
        "detail": f"{len(matched)} of {len(meaningful_jd)} extracted JD terms overlap with the resume. This is a heuristic, not a vendor ATS score."
    })

    # 6) Formatting risk heuristics
    risky = []
    if "|" in cv:
        risky.append("table/pipe-style layout may not parse consistently")
    if len(re.findall(r"[^\x00-\x7F]", cv)) > 25:
        risky.append("heavy special-character usage detected")
    if re.search(r"(?im)^\s*(references|personal details)\s*$", cv):
        risky.append("low-value sections may consume space")
    formatting_score = 100 if not risky else max(50, 100 - 15 * len(risky))
    checks.append({
        "name": "ATS formatting risk",
        "score": formatting_score,
        "status": "PASS" if formatting_score >= 80 else "REVIEW",
        "detail": "No major heuristic formatting risks detected." if not risky else "; ".join(risky) + "."
    })

    weights = {
        "Text parseability": 15,
        "Contact block": 10,
        "Standard resume sections": 15,
        "Quantified achievements": 15,
        "JD keyword alignment": 30,
        "ATS formatting risk": 15,
    }
    weighted = round(sum(c["score"] * weights[c["name"]] for c in checks) / sum(weights.values()))
    if weighted >= 85:
        band = "Strong ATS readiness"
    elif weighted >= 70:
        band = "Good ATS readiness"
    elif weighted >= 55:
        band = "Needs targeted improvement"
    else:
        band = "High-priority ATS cleanup"

    gaps = sorted(meaningful_jd - cv_terms, key=lambda x: (-len(x), x))[:15]
    recommendations = []
    if keyword_score < 70:
        recommendations.append("Mirror important JD terminology only where it truthfully matches the candidate's experience.")
    if achievement_score < 80:
        recommendations.append("Convert responsibilities into measurable outcomes where genuine metrics exist.")
    if heading_score < 80:
        recommendations.append("Use clear, conventional section headings such as Experience, Skills and Education.")
    if contact_score < 100:
        recommendations.append("Ensure email, phone and LinkedIn are present and easy for parsers to extract.")
    if formatting_score < 80:
        recommendations.append("Prefer simple single-column text structure and avoid parser-sensitive decorative layouts.")

    return {
        "score": weighted,
        "band": band,
        "checks": checks,
        "keyword_gaps": gaps,
        "recommendations": recommendations[:6],
        "method": "Deterministic ATS-readiness heuristic based on parseability, contact signals, standard sections, quantified achievements, JD keyword overlap and formatting risk. Not an ATS vendor certification.",
    }
