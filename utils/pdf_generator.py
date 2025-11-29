import json
import os
from fpdf import FPDF
from typing import Dict

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, "data")
PDF_DIR = os.path.join(DATA_DIR, "reports")
os.makedirs(PDF_DIR, exist_ok=True)


def generate_pdf(session_data: Dict) -> str:
    # Create a simple PDF report summarizing the interview
    fn = f"session_{session_data.get('session_id', 'unknown')}.pdf"
    out_path = os.path.join(PDF_DIR, fn)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Interview Session Report", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.ln(4)

    def _sanitize(s: str) -> str:
        if not s:
            return ''
        if not isinstance(s, str):
            s = str(s)
        # Replace unicode dashes and unsupported characters for latin-1
        s = s.replace('\u2014', '-')
        # fall back to latin-1 safe string (non-representable chars become '?')
        try:
            s = s.encode('latin-1', 'replace').decode('latin-1')
        except Exception:
            s = ''.join([c if ord(c) < 256 else '?' for c in s])
        return s

    pdf.cell(0, 8, _sanitize(f"Session: {session_data.get('session_id', '')}"), ln=True)
    pdf.cell(0, 8, _sanitize(f"Job: {session_data.get('job', '')}"), ln=True)
    pdf.cell(0, 8, _sanitize(f"Candidate: {session_data.get('candidate_id', '')}"), ln=True)
    # interviewer metadata
    interviewer = session_data.get('interviewer', {}) or {}
    if interviewer:
        name = interviewer.get('name', '')
        title = interviewer.get('title', '')
        bio = interviewer.get('bio', '')
        if name or title:
            label = f"Interviewer: {name}"
            if title:
                label += f" - {title}"
            pdf.cell(0, 8, _sanitize(label), ln=True)
        if bio:
            pdf.multi_cell(0, 6, _sanitize(f"Bio: {bio}"))
        pdf.ln(4)
    pdf.ln(6)

    for idx, r in enumerate(session_data.get('responses', []), start=1):
        q = r.get('question', {}).get('text', '')
        a = r.get('answer', '')
        ev = r.get('evaluation', {})
        pdf.set_font("Arial", "B", 12)
        pdf.multi_cell(0, 7, _sanitize(f"Q{idx}: {q}"))
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 6, _sanitize(f"A: {a}"))
        pdf.multi_cell(0, 6, _sanitize(f"Eval: {json.dumps(ev)}"))
        pdf.ln(3)

    pdf.output(out_path)
    return out_path
