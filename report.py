
import html
import io
from datetime import datetime
from statistics import mean

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

from utils import average_scores


NAVY = colors.HexColor("#0A1020")
PANEL = colors.HexColor("#111A2E")
PANEL_2 = colors.HexColor("#17213A")
LAVENDER = colors.HexColor("#8B7CFF")
CYAN = colors.HexColor("#58D6FF")
TEXT = colors.HexColor("#EAF0FF")
MUTED = colors.HexColor("#8FA0BD")
GOOD = colors.HexColor("#48E3A3")
WARN = colors.HexColor("#FFD166")
LINE = colors.HexColor("#2A3A5E")


def _safe(v):
    return html.escape("" if v is None else str(v)).replace("\n", "<br/>")


def _all_scores(turns):
    return [t.get("feedback", {}).get("scores", {}) for t in turns if t.get("feedback")]


def build_report_data(
    target_role,
    industry,
    mode,
    duration_minutes,
    question_mode,
    answer_mode,
    categories,
    company,
    turns,
    evidence,
    research=None,
    model="Automatic",
    session_id="",
    started_at=None,
):
    scores = average_scores(_all_scores(turns))
    overall = round(mean(scores.values())) if scores else 0
    ats = (evidence or {}).get("ats_readiness", {})
    elapsed = 0.0
    if started_at:
        elapsed = max(0.0, datetime.now().timestamp() - started_at)
    strengths, improvements, verification = [], [], []
    for t in turns:
        fb = t.get("feedback", {})
        strengths.extend(fb.get("strengths", []) or [])
        improvements.extend(fb.get("next_improvement", []) and [fb.get("next_improvement")] or [])
        verification.extend(fb.get("verification_notes", []) or [])
    def unique(xs):
        out = []
        for x in xs:
            if x and x not in out:
                out.append(x)
        return out
    return {
        "session": {
            "session_id": session_id,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "role": target_role,
            "company": company or "Not specified",
            "industry": industry,
            "mode": mode,
            "duration_minutes": duration_minutes,
            "question_mode": question_mode,
            "answer_mode": answer_mode,
            "categories": categories,
            "model": model,
            "turn_count": len(turns),
            "elapsed_seconds": round(elapsed, 1),
        },
        "evidence": evidence or {},
        "research": research or {},
        "scores": scores,
        "overall": overall,
        "strengths": unique(strengths)[:10],
        "improvements": unique(improvements)[:10],
        "verification_notes": unique(verification)[:10],
        "turns": turns,
        "ats": ats,
    }


def build_markdown_report(
    target_role, industry, mode, turns, evidence,
    duration_minutes=0, question_mode="Text Questions", answer_mode="Type Answers",
    categories=None, company="", research=None, model="Automatic", session_id="", started_at=None
):
    data = build_report_data(
        target_role, industry, mode, duration_minutes, question_mode, answer_mode,
        categories or [], company, turns, evidence, research, model, session_id, started_at
    )
    s = data["session"]
    lines = [
        "# Intervia — Premium Interview Intelligence Report",
        f"Generated: {s['generated_at']}",
        f"Session ID: {s['session_id']}",
        "",
        "## Executive summary",
        f"- Target role: {s['role']}",
        f"- Company: {s['company']}",
        f"- Interview mode: {s['mode']}",
        f"- Duration: {s['duration_minutes']} minutes",
        f"- Question mode: {s['question_mode']}",
        f"- Answer mode: {s['answer_mode']}",
        f"- Categories: {', '.join(s['categories'])}",
        f"- AI model: {s['model']}",
        f"- Questions completed: {s['turn_count']}",
        f"- Overall score: {data['overall']}/100",
        "",
        "## Performance scorecard",
    ]
    for k, v in data["scores"].items():
        lines.append(f"- {k.title()}: {v}/100")
    lines += [
        "",
        "## Candidate evidence & ATS readiness",
        f"- Candidate facts captured: {len(data['evidence'].get('candidate_facts', []))}",
        f"- JD requirements captured: {len(data['evidence'].get('jd_requirements', []))}",
        f"- Grounding matches: {len(data['evidence'].get('matches', []))}",
        f"- ATS readiness heuristic: {data['ats'].get('score', 0)}/100 — {data['ats'].get('band', 'Not calculated')}",
        "",
        "### ATS checks",
    ]
    for c in data["ats"].get("checks", []):
        lines.append(f"- {c['name']}: {c['score']}/100 — {c['status']} — {c['detail']}")
    if data["ats"].get("keyword_gaps"):
        lines.append(f"- JD keyword gaps to review: {', '.join(data['ats']['keyword_gaps'])}")
    lines += ["", "## Strengths"]
    lines += [f"- {x}" for x in data["strengths"]] or ["- No strengths recorded."]
    lines += ["", "## Improvement plan"]
    lines += [f"- {x}" for x in data["improvements"]] or ["- No improvement items recorded."]
    lines += ["", "## Verification notes"]
    lines += [f"- {x}" for x in data["verification_notes"]] or ["- No verification notes recorded."]
    if data["research"]:
        lines += ["", "## External role/company research", data["research"].get("summary", "Not available.")]
    lines += ["", "## Turn-by-turn coaching"]
    for i, t in enumerate(turns, 1):
        fb = t.get("feedback", {})
        lines += [
            "",
            f"### Question {i} — {t.get('category', 'General')}",
            t.get("question", ""),
            "",
            "**Candidate answer**",
            t.get("answer", ""),
            "",
            "**Scores**",
            ", ".join(f"{k.title()}: {v}/100" for k, v in fb.get("scores", {}).items()),
            f"**Overall:** {fb.get('overall', 0)}/100",
            "",
            "**Strengths**",
            *[f"- {x}" for x in fb.get("strengths", [])],
            "",
            "**Missing / improve**",
            *[f"- {x}" for x in fb.get("missing_points", [])],
            "",
            "**Verification notes**",
            *[f"- {x}" for x in fb.get("verification_notes", [])],
            "",
            "**Suggested better practice answer**",
            fb.get("practice_answer", ""),
            "",
            "**Next improvement**",
            fb.get("next_improvement", ""),
        ]
        if t.get("speech_metrics"):
            lines += ["", f"**Speech analytics:** {t['speech_metrics']}"]
        if t.get("presentation_cues"):
            lines += ["", f"**Presentation cues:** {t['presentation_cues']}"]
    lines += [
        "",
        "## Grounding policy",
        data["evidence"].get("grounding_rule", "Candidate evidence is kept separate from job-description requirements and external research."),
        "",
        "## Report note",
        "ATS readiness is a deterministic heuristic, not a guarantee of acceptance by a specific ATS vendor. AI coaching is evidence-grounded and designed to minimize unsupported candidate claims; it does not guarantee zero hallucinations.",
    ]
    return "\n".join(lines)


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 10 * mm, "Intervia • Evidence-Grounded Interview Intelligence")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _card(title, value, accent=LAVENDER):
    t = Table([
        [Paragraph(_safe(title), ParagraphStyle("ct", fontName="Helvetica-Bold", fontSize=8, textColor=MUTED))],
        [Paragraph(_safe(value), ParagraphStyle("cv", fontName="Helvetica-Bold", fontSize=17, textColor=TEXT))],
    ], colWidths=[52 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PANEL),
        ("BOX", (0,0), (-1,-1), 0.7, LINE),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LINEBEFORE", (0,0), (0,-1), 3, accent),
    ]))
    return t


def build_pdf_report(
    target_role, industry, mode, turns, evidence,
    duration_minutes=0, question_mode="Text Questions", answer_mode="Type Answers",
    categories=None, company="", research=None, model="Automatic", session_id="", started_at=None
):
    data = build_report_data(
        target_role, industry, mode, duration_minutes, question_mode, answer_mode,
        categories or [], company, turns, evidence, research, model, session_id, started_at
    )
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=17 * mm,
        title="Intervia Premium Interview Intelligence Report",
        author="Intervia",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=TEXT, spaceAfter=8)
    h1 = ParagraphStyle("H1X", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=CYAN, spaceBefore=12, spaceAfter=7)
    h2 = ParagraphStyle("H2X", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=TEXT, spaceBefore=8, spaceAfter=5)
    body = ParagraphStyle("BodyX", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.6, leading=12, textColor=TEXT, spaceAfter=4)
    small = ParagraphStyle("SmallX", parent=body, fontSize=7.4, leading=10, textColor=MUTED)
    quote = ParagraphStyle("QuoteX", parent=body, fontSize=9, leading=13, textColor=TEXT, leftIndent=8, borderColor=LINE, borderWidth=0.5, borderPadding=7, backColor=PANEL)

    story = []
    s = data["session"]
    story += [
        Paragraph("INTERVIA", ParagraphStyle("Brand", fontName="Helvetica-Bold", fontSize=9, textColor=LAVENDER, letterSpacing=1.5)),
        Paragraph("Premium Interview Intelligence Report", title),
        Paragraph(_safe(f"{s['role']} • {s['company']}"), ParagraphStyle("Sub", fontName="Helvetica-Bold", fontSize=11, textColor=TEXT)),
        Spacer(1, 5),
        Paragraph(_safe(f"Session {s['session_id']} • Generated {s['generated_at']}"), small),
        Spacer(1, 12),
    ]

    cards = Table([[
        _card("OVERALL SCORE", f"{data['overall']}/100", LAVENDER),
        _card("ATS READINESS", f"{data['ats'].get('score', 0)}/100", CYAN),
        _card("QUESTIONS", str(s["turn_count"]), GOOD),
    ]], colWidths=[58 * mm, 58 * mm, 58 * mm], hAlign="LEFT")
    cards.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 5)]))
    story.append(cards)
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. Session configuration", h1))
    cfg = [
        ["Target role", s["role"], "Interview mode", s["mode"]],
        ["Duration", f"{s['duration_minutes']} min", "Question mode", s["question_mode"]],
        ["Answer mode", s["answer_mode"], "AI model", s["model"]],
        ["Categories", ", ".join(s["categories"]), "Questions completed", str(s["turn_count"])],
    ]
    table = Table([[Paragraph(_safe(x), small) for x in row] for row in cfg], colWidths=[28*mm, 63*mm, 30*mm, 53*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), PANEL),
        ("GRID", (0,0), (-1,-1), 0.5, LINE),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(table)

    story.append(Paragraph("2. Performance scorecard", h1))
    score_rows = [[Paragraph("Dimension", small), Paragraph("Score", small)]]
    for k, v in data["scores"].items():
        score_rows.append([Paragraph(_safe(k.title()), body), Paragraph(f"{v}/100", body)])
    stbl = Table(score_rows, colWidths=[120*mm, 40*mm])
    stbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), PANEL_2),
        ("BACKGROUND", (0,1), (-1,-1), PANEL),
        ("GRID", (0,0), (-1,-1), 0.45, LINE),
        ("TEXTCOLOR", (0,0), (-1,-1), TEXT),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(stbl)

    story.append(Paragraph("3. Candidate evidence & ATS readiness", h1))
    ev = data["evidence"]
    story.append(Paragraph(_safe(ev.get("grounding_rule", "")), body))
    story.append(Spacer(1, 3))
    ats = data["ats"]
    story.append(Paragraph(_safe(f"{ats.get('band', 'Not calculated')} — {ats.get('method', '')}"), small))
    ats_rows = [[Paragraph("ATS check", small), Paragraph("Score", small), Paragraph("Status", small), Paragraph("Detail", small)]]
    for c in ats.get("checks", []):
        ats_rows.append([Paragraph(_safe(c["name"]), body), Paragraph(f"{c['score']}/100", body), Paragraph(_safe(c["status"]), body), Paragraph(_safe(c["detail"]), small)])
    atbl = Table(ats_rows, colWidths=[42*mm, 20*mm, 20*mm, 78*mm], repeatRows=1)
    atbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), PANEL_2),
        ("BACKGROUND", (0,1), (-1,-1), PANEL),
        ("GRID", (0,0), (-1,-1), 0.45, LINE),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ALIGN", (1,1), (2,-1), "CENTER"),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(atbl)
    if ats.get("keyword_gaps"):
        story.append(Paragraph("<b>JD keyword gaps to review:</b> " + _safe(", ".join(ats["keyword_gaps"])), body))
    if ats.get("recommendations"):
        story.append(Paragraph("<b>ATS recommendations:</b> " + _safe(" • ".join(ats["recommendations"])), body))

    story.append(Paragraph("4. Executive coaching summary", h1))
    for label, items in [
        ("Strengths", data["strengths"]),
        ("Improvement priorities", data["improvements"]),
        ("Verification notes", data["verification_notes"]),
    ]:
        story.append(Paragraph(label, h2))
        if items:
            for item in items:
                story.append(Paragraph("• " + _safe(item), body))
        else:
            story.append(Paragraph("No items recorded.", small))

    if data["research"]:
        story.append(Paragraph("5. External role/company research", h1))
        story.append(Paragraph(_safe(data["research"].get("summary", "Not available.")), body))
        story.append(Paragraph("Research is intentionally kept separate from candidate evidence.", small))

    story.append(PageBreak())
    story.append(Paragraph("6. Turn-by-turn interview record", h1))
    for i, t in enumerate(data["turns"], 1):
        fb = t.get("feedback", {})
        header = Table([[
            Paragraph(_safe(f"Question {i} • {t.get('category', 'General')}"), ParagraphStyle("TurnH", fontName="Helvetica-Bold", fontSize=10, textColor=TEXT)),
            Paragraph(_safe(f"Overall {fb.get('overall', 0)}/100"), ParagraphStyle("TurnS", fontName="Helvetica-Bold", fontSize=10, textColor=GOOD)),
        ]], colWidths=[125*mm, 35*mm])
        header.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), PANEL_2), ("BOX", (0,0), (-1,-1), 0.5, LINE), ("LEFTPADDING", (0,0), (-1,-1), 7), ("RIGHTPADDING", (0,0), (-1,-1), 7), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
        story.append(header)
        story.append(Spacer(1, 5))
        story.append(Paragraph("<b>Question</b>", h2))
        story.append(Paragraph(_safe(t.get("question", "")), quote))
        story.append(Paragraph("<b>Candidate answer</b>", h2))
        story.append(Paragraph(_safe(t.get("answer", "")), body))
        story.append(Paragraph("<b>Score breakdown</b>", h2))
        breakdown = " • ".join(f"{k.title()}: {v}/100" for k, v in fb.get("scores", {}).items())
        story.append(Paragraph(_safe(breakdown), small))
        for label, key in [
            ("Strengths", "strengths"),
            ("Missing / improve", "missing_points"),
            ("Verification notes", "verification_notes"),
        ]:
            story.append(Paragraph(label, h2))
            vals = fb.get(key, []) or []
            story.append(Paragraph(_safe(" • ".join(vals) if vals else "None recorded."), body))
        story.append(Paragraph("Suggested better practice answer", h2))
        story.append(Paragraph(_safe(fb.get("practice_answer", "")), quote))
        story.append(Paragraph("Next improvement", h2))
        story.append(Paragraph(_safe(fb.get("next_improvement", "")), body))
        sm = t.get("speech_metrics")
        if sm:
            story.append(Paragraph("Speech analytics", h2))
            story.append(Paragraph(_safe(json_like(sm)), body))
        if t.get("presentation_cues"):
            story.append(Paragraph("Presentation cues", h2))
            story.append(Paragraph(_safe(json_like(t["presentation_cues"])), body))
        story.append(Spacer(1, 8))

    story.append(Paragraph("7. Evidence ledger", h1))
    story.append(Paragraph(f"Candidate facts captured: {len(ev.get('candidate_facts', []))}", body))
    for fact in ev.get("candidate_facts", [])[:25]:
        story.append(Paragraph("• " + _safe(fact), small))
    story.append(Paragraph(f"JD requirements captured: {len(ev.get('jd_requirements', []))}", body))
    for req in ev.get("jd_requirements", [])[:25]:
        story.append(Paragraph("• " + _safe(req), small))

    story.append(Paragraph("8. Professional action plan", h1))
    action_items = []
    if data["overall"] < 70:
        action_items.append("Repeat the weakest competency with a focused practice round before increasing difficulty.")
    if data["ats"].get("score", 0) < 75:
        action_items.append("Apply the ATS recommendations, then re-run the ATS readiness check.")
    action_items.extend(data["improvements"][:5])
    if not action_items:
        action_items = ["Maintain the current practice cadence and progressively increase question difficulty."]
    for item in action_items:
        story.append(Paragraph("• " + _safe(item), body))

    story.append(Paragraph("9. Report integrity notes", h1))
    story.append(Paragraph("Candidate evidence, JD requirements and external research are kept as separate evidence classes. The ATS section is a deterministic readiness heuristic and is not a guarantee of any specific ATS vendor outcome. AI coaching is designed to minimize unsupported candidate claims; no generative system can truthfully guarantee zero hallucinations.", small))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


def json_like(obj):
    if isinstance(obj, dict):
        return "; ".join(f"{k}: {v}" for k, v in obj.items())
    return str(obj)
