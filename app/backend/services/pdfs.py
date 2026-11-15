"""PDF generation (reportlab): evidence packet, letters, generic text documents."""
from __future__ import annotations

import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .. import config
from . import evidence as ev_svc
from .letters import _cite

RED = colors.HexColor("#C5050C")
_styles = getSampleStyleSheet()
H1 = ParagraphStyle("h1", parent=_styles["Heading1"], textColor=RED)
H2 = _styles["Heading2"]
BODY = _styles["BodyText"]
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8, leading=10, textColor=colors.HexColor("#555555"))
MONO = ParagraphStyle("mono", parent=BODY, fontName="Courier", fontSize=7, leading=9)


def _p(text: str, style=BODY) -> Paragraph:
    return Paragraph(escape(text or "").replace("\n", "<br/>"), style)


def _doc(buf):
    return SimpleDocTemplate(buf, pagesize=letter, leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                             topMargin=0.7 * inch, bottomMargin=0.7 * inch)


def text_pdf(title: str, body: str) -> bytes:
    buf = io.BytesIO()
    _doc(buf).build([_p(title, H1), Spacer(1, 8), _p(body), Spacer(1, 16), _p(config.DISCLAIMER, SMALL)])
    return buf.getvalue()


def evidence_packet(case: dict) -> bytes:
    buf = io.BytesIO()
    story = [
        _p("FixIt Madison — Tenant Evidence Packet", H1),
        _p("Compiled by the tenant with FixIt. This is NOT an official inspection record, notice or finding. Issues "
           "below were flagged with AI assistance and/or reported by the tenant; only a City of Madison building inspector "
           "can determine a code violation.", SMALL),
        _p(f'Address: {case.get("address") or "—"}   Unit: {case.get("unit") or "—"}'),
        _p(f'Case: {case["request_id"]}   Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'),
        _p(f'Owner/manager: {case.get("landlord")}'),
        Spacer(1, 10), _p("Possible issues (tenant-reported / AI-assisted, not inspector findings)", H2),
    ]
    rows = [["#", "Issue", "FixIt severity", "AI confidence", "Code reference"]]
    for i, v in enumerate(case["violations"], 1):
        cite = "; ".join(f'{s["title"]} ({_cite(s)})' for s in v.get("code_sections", []))
        rows.append([str(i), Paragraph(escape(v["name"]), SMALL), v["severity"], f'{v["confidence"]:.2f}',
                     Paragraph(escape(cite), SMALL)])
    t = Table(rows, colWidths=[0.3 * inch, 2.2 * inch, 0.8 * inch, 0.8 * inch, 2.9 * inch], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), RED), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("FONTSIZE", (0, 0), (-1, -1), 8)]))
    story += [t, Spacer(1, 10)]

    if case.get("calls"):
        story.append(_p("Landlord contact log", H2))
        for c in case["calls"]:
            story.append(_p(f'{c["created_at"]} — {c["mode"]} AI call. Commitment: {c.get("commitment_date") or "none"} '
                            f'({c.get("commitment_text") or "—"}). Tone: {c.get("landlord_tone")}', SMALL))
    if case.get("sent_at"):
        story.append(_p(f'Repair request letter marked sent: {case["sent_at"]}', SMALL))

    story += [PageBreak(), _p("Photo evidence", H2),
              _p("Each file is stored under its SHA-256 hash. Re-hash the original to verify it has not been altered.", SMALL),
              Spacer(1, 6)]
    vio_by_ev = {}
    for v in case["violations"]:
        obs = v.get("observations")
        if obs:  # each photo lists only what was observed in THAT photo, and on what basis
            for o in obs:
                if o.get("evidence_id"):
                    note = f': {o["note"]}' if o.get("note") else ""
                    vio_by_ev.setdefault(o["evidence_id"], []).append(f'{v["name"]} ({o["basis_text"]}{note})')
        else:
            for e in v.get("evidence_ids") or []:
                vio_by_ev.setdefault(e, []).append(v["name"])
    for e in case["evidence"]:
        try:
            img = Image(io.BytesIO(ev_svc.read(e["volume_path"])))
            ratio = img.imageHeight / float(img.imageWidth or 1)
            img.drawWidth, img.drawHeight = 3.2 * inch, 3.2 * inch * ratio
            if img.drawHeight > 3.4 * inch:
                img.drawHeight, img.drawWidth = 3.4 * inch, 3.4 * inch / ratio
        except Exception:
            img = _p("[image unavailable]", SMALL)
        meta = [_p(e["evidence_id"], BODY), _p(f'Captured: {e["captured_at"]}', SMALL),
                _p(f'Uploaded: {e["uploaded_at"]}', SMALL), _p(f'SHA-256: {e["sha256"]}', MONO),
                _p("Flags: " + (", ".join(vio_by_ev.get(e["evidence_id"], [])) or "none"), SMALL)]
        row = Table([[img, meta]], colWidths=[3.4 * inch, 3.6 * inch])
        row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
        story.append(row)
    story += [Spacer(1, 12), _p(config.DISCLAIMER, SMALL)]
    _doc(buf).build(story)
    return buf.getvalue()
