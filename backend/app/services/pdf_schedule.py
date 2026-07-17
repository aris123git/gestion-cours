"""Generate a PDF timetable for a student (ReportLab)."""

from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


IST_NAVY = colors.HexColor("#003366")
IST_BLUE = colors.HexColor("#0073BB")
IST_GOLD = colors.HexColor("#D4A017")
IST_LIGHT = colors.HexColor("#E4EEF7")
WHITE = colors.white

DAY_ORDER = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]


def _fmt_time(t) -> str:
    if t is None:
        return ""
    if hasattr(t, "strftime"):
        return t.strftime("%H:%M")
    return str(t)[:5]


def _week_label(week: date) -> str:
    end = week + timedelta(days=5)
    return f"{week.strftime('%d/%m/%Y')} — {end.strftime('%d/%m/%Y')}"


def build_schedule_pdf(
    *,
    student_name: str,
    student_number: str,
    programme: str,
    level: str,
    week: date,
    courses: list,
) -> bytes:
    """Return PDF bytes for the weekly timetable."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.2 * cm,
        title=f"Emploi du temps — {student_name}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "IstTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=IST_NAVY,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "IstSub",
        parent=styles["Normal"],
        fontSize=11,
        textColor=IST_BLUE,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "IstMeta",
        parent=styles["Normal"],
        fontSize=10,
        textColor=IST_NAVY,
        alignment=TA_LEFT,
        spaceAfter=2,
    )
    cell_style = ParagraphStyle(
        "IstCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=IST_NAVY,
        alignment=TA_CENTER,
    )
    head_style = ParagraphStyle(
        "IstHead",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=WHITE,
        alignment=TA_CENTER,
    )

    elements = [
        Paragraph("IST Wayalghin", title_style),
        Paragraph("Pour l'excellence — Emploi du temps", subtitle_style),
        Paragraph(f"<b>Étudiant :</b> {student_name} ({student_number})", meta_style),
        Paragraph(f"<b>Parcours :</b> {level} — {programme}", meta_style),
        Paragraph(f"<b>Semaine :</b> {_week_label(week)}", meta_style),
        Spacer(1, 0.35 * cm),
    ]

    def _val(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    # Group courses by day
    by_day: dict[str, list] = {d: [] for d in DAY_ORDER}
    for c in courses:
        day = _val(c, "day")
        if day in by_day:
            by_day[day].append(c)

    for day in DAY_ORDER:
        by_day[day].sort(key=lambda x: str(_val(x, "start_time") or ""))
    max_rows = max((len(by_day[d]) for d in DAY_ORDER), default=0)
    max_rows = max(max_rows, 1)

    header = [Paragraph(d, head_style) for d in DAY_ORDER]
    data = [header]

    for i in range(max_rows):
        row = []
        for day in DAY_ORDER:
            if i < len(by_day[day]):
                c = by_day[day][i]
                subject = _val(c, "subject") or ""
                teacher = _val(c, "teacher") or ""
                room = _val(c, "room") or "—"
                start = _fmt_time(_val(c, "start_time"))
                end = _fmt_time(_val(c, "end_time"))
                group = _val(c, "group_tc")
                group_line = f"<br/>Groupe : {group}" if group else ""
                text = (
                    f"<b>{subject}</b><br/>{start}–{end}<br/>{teacher}<br/>Salle : {room}{group_line}"
                )
                row.append(Paragraph(text, cell_style))
            else:
                row.append(Paragraph("—", cell_style))
        data.append(row)

    col_w = (doc.width) / 6
    table = Table(data, colWidths=[col_w] * 6, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), IST_NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("BACKGROUND", (0, 1), (-1, -1), IST_LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.6, IST_NAVY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, 0), 2, IST_GOLD),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(
        Paragraph(
            "Campus de Wayalghin · 68 00 23 00 · Route de Fada",
            ParagraphStyle(
                "Footer",
                parent=styles["Normal"],
                fontSize=8,
                textColor=IST_GOLD,
                alignment=TA_CENTER,
            ),
        )
    )

    doc.build(elements)
    return buffer.getvalue()
