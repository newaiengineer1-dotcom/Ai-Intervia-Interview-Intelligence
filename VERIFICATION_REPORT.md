# Intervia Premium Verification Report — 2026-10-02

## Completed
- Static syntax compilation for all application/support Python modules.
- AST parsing for required modules.
- Premium UI feature checks.
- Five logical agent status checks.
- ATS module + UI checks.
- Voice capture + Whisper integration checks.
- Complete PDF/Markdown report integration checks.
- Synthetic ATS calculation.
- Synthetic professional PDF generation.
- Synthetic Markdown generation.
- Hackathon presentation deck generation.
- Master Plan DOCX generation.

## Runtime-dependent checks
Live Groq authentication, quota, model access, optional browser search, microphone permissions and Streamlit Community Cloud infrastructure remain environment-dependent. This package does **not** claim an absolute guarantee for external services.

## Technical validation references
- Streamlit 1.64.0 is the current Streamlit release documented by Streamlit at the build date.
- Groq GPT-OSS 120B supports browser search and structured outputs; Groq documents that browser search is not compatible with structured outputs, so the optional research path remains separate from strict structured-output workflows.
- Groq GPT-OSS 120B documentation lists a 131,072-token context window.
- ReportLab 5.0.1, scikit-learn 1.9.1 and python-dotenv 1.2.3 were checked against their PyPI release pages during preparation.

## Product accuracy notes
- ATS score = deterministic readiness heuristic, not an ATS-vendor certification.
- Voice MVP = turn-based recording/transcription, not continuous WebRTC streaming.
- Evidence-grounded AI = designed to minimize unsupported candidate claims, not a guarantee of zero hallucinations.
