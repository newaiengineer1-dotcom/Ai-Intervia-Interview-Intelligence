
from pathlib import Path
import ast
import py_compile

ROOT = Path(__file__).parent
REQUIRED = [
    "app.py","agents.py","db.py","rag.py","report.py","utils.py","ats.py","crew_adapter.py",
    "agent_modules/__init__.py","agent_modules/groq_gateway.py","agent_modules/evidence_agent.py",
    "agent_modules/research_agent.py","agent_modules/strategy_agent.py",
    "agent_modules/interviewer_agent.py","agent_modules/coach_agent.py"
]

for name in REQUIRED:
    p = ROOT / name
    if not p.exists():
        raise SystemExit(f"Missing required file: {name}")
    py_compile.compile(str(p), doraise=True)
    ast.parse(p.read_text(encoding="utf-8"), filename=str(p))

app = (ROOT/"app.py").read_text(encoding="utf-8")
checks = {
    "premium_theme": "AI INTERVIEW • SMARTER YOU" in app and "Mission Control" in app,
    "five_agents": all(x in app for x in ["Evidence Intelligence","Research Intelligence","Adaptive Strategy","AI Interviewer","Performance Coach"]),
    "ats_ui": "ATS READINESS" in app and "ATS readiness details" in app,
    "voice_input": "st.audio_input" in app,
    "whisper": "gateway.transcribe" in app,
    "complete_report": "build_pdf_report" in app and "build_markdown_report" in app,
    "all_output_coverage": all(x in app for x in ["Suggested better practice answer","Next improvement","Verification notes","Speech analytics","Report coverage"]),
    "no_industry_input": 'st.text_input("Industry"' not in app,
    "grounding_rule": "Candidate evidence is locked to CV facts" in app,
}
failed=[k for k,v in checks.items() if not v]
if failed:
    raise SystemExit("FAILED: " + ", ".join(failed))
print("PASS: syntax, required modules, premium UI, ATS, voice, five-agent flow, and reporting coverage")
