"""
Export PDF des emplois du temps — design aligné sur l'interface web GestionCours.
"""
import os
import re
import zipfile
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import (
    ANNEE_COURANTE,
    CRENEAUX,
    CRENEAUX_LABELS,
    EXPORT_DIR,
    JOURS,
    RESOURCE_DIR,
)
from database import (
    get_cours,
    get_effectif,
    get_filiere_by_id,
    get_filieres_tc_groupe,
    get_salle_by_id,
)

# Palette alignée sur static/css/app.css
BRAND = colors.HexColor("#0f4c3a")
BRAND_DEEP = colors.HexColor("#0a3328")
BRAND_SOFT = colors.HexColor("#1f6b52")
ACCENT = colors.HexColor("#c45c26")
INK = colors.HexColor("#14201c")
INK_SOFT = colors.HexColor("#3d524a")
MUTED = colors.HexColor("#6a7d74")
CREAM = colors.HexColor("#fffdf9")
PARCHMENT = colors.HexColor("#f3efe6")
LINE = colors.HexColor("#c9d5cf")

FONTS_DIR = os.path.join(RESOURCE_DIR, "static", "fonts")
DEFAULT_LOGO = os.path.join(RESOURCE_DIR, "fichiers", "logoist.jpeg")

_FONTS_READY = False
FONT_BODY = "Helvetica"
FONT_BODY_BOLD = "Helvetica-Bold"
FONT_DISPLAY = "Helvetica-Bold"


def _register_fonts():
    global _FONTS_READY, FONT_BODY, FONT_BODY_BOLD, FONT_DISPLAY
    if _FONTS_READY:
        return
    try:
        regular = os.path.join(FONTS_DIR, "Manrope-Regular.ttf")
        bold = os.path.join(FONTS_DIR, "Manrope-Bold.ttf")
        display = os.path.join(FONTS_DIR, "Syne-ExtraBold.ttf")
        if not os.path.exists(display):
            display = os.path.join(FONTS_DIR, "Syne-Bold.ttf")
        if all(os.path.exists(p) for p in (regular, bold, display)):
            pdfmetrics.registerFont(TTFont("Manrope", regular))
            pdfmetrics.registerFont(TTFont("Manrope-Bold", bold))
            pdfmetrics.registerFont(TTFont("Syne-Bold", display))
            FONT_BODY = "Manrope"
            FONT_BODY_BOLD = "Manrope-Bold"
            FONT_DISPLAY = "Syne-Bold"
    except Exception:
        FONT_BODY = "Helvetica"
        FONT_BODY_BOLD = "Helvetica-Bold"
        FONT_DISPLAY = "Helvetica-Bold"
    _FONTS_READY = True


def _safe_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = re.sub(r"[^\w.\-]+", "_", name, flags=re.UNICODE)
    return name or "emploi_du_temps"


def _default_logo(logo_path=None):
    if logo_path and os.path.exists(logo_path):
        return logo_path
    if os.path.exists(DEFAULT_LOGO):
        return DEFAULT_LOGO
    alt = os.path.join(RESOURCE_DIR, "static", "img", "logo.jpeg")
    return alt if os.path.exists(alt) else None


def _week_end(date_lundi: str) -> str:
    dt = datetime.fromisoformat(date_lundi)
    return (dt + timedelta(days=5)).strftime("%d/%m/%Y")


def _build_styles():
    _register_fonts()
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            name="EdtTitle",
            parent=base["Heading1"],
            fontName=FONT_DISPLAY,
            fontSize=18,
            textColor=BRAND,
            alignment=TA_CENTER,
            spaceAfter=4,
            leading=22,
        ),
        "subtitle": ParagraphStyle(
            name="EdtSubtitle",
            parent=base["Normal"],
            fontName=FONT_BODY,
            fontSize=10,
            textColor=INK_SOFT,
            alignment=TA_CENTER,
            spaceAfter=2,
            leading=13,
        ),
        "meta": ParagraphStyle(
            name="EdtMeta",
            parent=base["Normal"],
            fontName=FONT_BODY,
            fontSize=9,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=10,
            leading=12,
        ),
        "day": ParagraphStyle(
            name="DayHeader",
            parent=base["Normal"],
            fontName=FONT_BODY_BOLD,
            fontSize=10,
            textColor=CREAM,
            alignment=TA_CENTER,
            leading=12,
        ),
        "slot": ParagraphStyle(
            name="SlotLabel",
            parent=base["Normal"],
            fontName=FONT_BODY_BOLD,
            fontSize=9,
            textColor=BRAND_DEEP,
            alignment=TA_CENTER,
            leading=12,
        ),
        "cell": ParagraphStyle(
            name="CellBody",
            parent=base["Normal"],
            fontName=FONT_BODY,
            fontSize=9,
            textColor=INK_SOFT,
            alignment=TA_CENTER,
            leading=12,
        ),
        "empty": ParagraphStyle(
            name="EmptyCell",
            parent=base["Normal"],
            fontName=FONT_BODY,
            fontSize=10,
            textColor=LINE,
            alignment=TA_CENTER,
            leading=12,
        ),
    }


EXPORT_NOTES = (
    "NB : Ce programme peut subir des modifications en cours de semaine !",
    "Les salles dont les numéros se terminent par la lettre B se situent en haut "
    "de l'immeuble BOA et C pour le 2è bâtiment à côté de BOA 1er niveau",
)


def _tc_autres_filieres(cours, filiere_id):
    """Noms des autres filières partageant le même tronc commun."""
    if not cours or not cours.groupe_tc:
        return []
    ids = get_filieres_tc_groupe(
        cours.groupe_tc, cours.date_lundi, cours.jour, cours.creneau
    )
    labels = []
    for fid in ids:
        if fid == filiere_id:
            continue
        f = get_filiere_by_id(fid)
        if f:
            labels.append(f"{f.annee} {f.nom}")
    return labels


def _cell_content(cours, styles, filiere_id=None):
    if not cours or not (cours.matiere or "").strip():
        return Paragraph("—", styles["empty"])

    matiere = escape((cours.matiere or "").strip())
    enseignant = escape((cours.enseignant or "").strip())
    parts = [
        f"<font name='{FONT_BODY_BOLD}' size='10' color='#0f4c3a'>{matiere}</font>"
    ]
    if enseignant:
        parts.append(f"<font color='#3d524a'>{enseignant}</font>")

    if cours.salle_id:
        salle = get_salle_by_id(cours.salle_id)
        if salle:
            parts.append(
                f"<font color='#6a7d74' size='8'>Salle · {escape(salle.nom)}</font>"
            )

    if cours.groupe_tc:
        autres = _tc_autres_filieres(cours, filiere_id)
        if autres:
            liste = escape(", ".join(autres))
            parts.append(
                f"<font color='#c45c26' size='8'><b>TC avec</b> {liste}</font>"
            )
        else:
            parts.append(
                f"<font color='#c45c26' size='8'><b>Tronc commun</b></font>"
            )

    return Paragraph("<br/>".join(parts), styles["cell"])


def _draw_page(canvas, doc, meta):
    canvas.saveState()
    width, height = landscape(A4)

    # Bandeau supérieur
    canvas.setFillColor(BRAND_DEEP)
    canvas.rect(0, height - 1.55 * cm, width, 1.55 * cm, fill=1, stroke=0)
    canvas.setFillColor(BRAND_SOFT)
    canvas.rect(0, height - 1.65 * cm, width, 0.12 * cm, fill=1, stroke=0)

    # Accent terracotta en coin
    canvas.setFillColor(ACCENT)
    canvas.rect(0, height - 1.55 * cm, 0.22 * cm, 1.55 * cm, fill=1, stroke=0)

    logo_path = meta.get("logo_path")
    text_x = 1.4 * cm
    if logo_path and os.path.exists(logo_path):
        try:
            canvas.drawImage(
                logo_path,
                1.1 * cm,
                height - 1.35 * cm,
                width=1.05 * cm,
                height=1.05 * cm,
                preserveAspectRatio=True,
                mask="auto",
            )
            text_x = 2.4 * cm
        except Exception:
            pass

    canvas.setFillColor(CREAM)
    canvas.setFont(FONT_DISPLAY, 13)
    canvas.drawString(text_x, height - 0.75 * cm, "GestionCours")
    canvas.setFont(FONT_BODY, 7.5)
    canvas.setFillColor(colors.HexColor("#d7e8df"))
    canvas.drawString(text_x, height - 1.15 * cm, "Planning universitaire")

    canvas.setFillColor(CREAM)
    canvas.setFont(FONT_BODY_BOLD, 9)
    etab = meta.get("etablissement") or ""
    type_cours = meta.get("type_cours") or ""
    bits = [b for b in (etab, type_cours, "Emploi du temps") if b]
    canvas.drawRightString(width - 1.2 * cm, height - 0.7 * cm, "  ·  ".join(bits))
    canvas.setFont(FONT_BODY, 8)
    canvas.setFillColor(colors.HexColor("#d7e8df"))
    canvas.drawRightString(
        width - 1.2 * cm,
        height - 1.1 * cm,
        f"Année {meta.get('annee_univ', ANNEE_COURANTE)}",
    )

    # Pied de page (génération)
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.6)
    canvas.line(1.2 * cm, 0.85 * cm, width - 1.2 * cm, 0.85 * cm)
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT_BODY, 7.5)
    generated = datetime.now().strftime("%d/%m/%Y à %H:%M")
    canvas.drawString(1.2 * cm, 0.45 * cm, f"Généré le {generated} · GestionCours")
    canvas.drawRightString(width - 1.2 * cm, 0.45 * cm, f"Page {doc.page}")
    canvas.restoreState()


def export_pour_filiere(
    filiere_id,
    date_lundi,
    output_path,
    logo_path=None,
    type_cours=None,
):
    filiere = get_filiere_by_id(filiere_id)
    if not filiere:
        return False

    _register_fonts()
    logo_path = _default_logo(logo_path)
    styles = _build_styles()

    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    type_cours = (type_cours or "").strip() or None
    meta = {
        "logo_path": logo_path,
        "etablissement": getattr(filiere, "etablissement", None) or "",
        "annee_univ": ANNEE_COURANTE,
        "type_cours": type_cours or "",
    }

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=1.2 * cm,
        rightMargin=1.2 * cm,
        topMargin=2.1 * cm,
        bottomMargin=1.4 * cm,
        title=f"EDT {filiere.annee} {filiere.nom}",
        author="GestionCours",
    )

    elements = []
    dt = datetime.fromisoformat(date_lundi)
    effectif = get_effectif(ANNEE_COURANTE, filiere_id)

    elements.append(Paragraph(f"{escape(filiere.annee)} — {escape(filiere.nom)}", styles["title"]))
    elements.append(
        Paragraph(
            f"Semaine du {dt.strftime('%d/%m/%Y')} au {_week_end(date_lundi)}",
            styles["subtitle"],
        )
    )
    meta_bits = []
    if meta["etablissement"]:
        meta_bits.append(escape(meta["etablissement"]))
    if type_cours:
        meta_bits.append(f"Type · {escape(type_cours)}")
    meta_bits.append(f"Année universitaire {ANNEE_COURANTE}")
    if effectif:
        meta_bits.append(f"Effectif · {effectif}")
    elements.append(Paragraph("  ·  ".join(meta_bits), styles["meta"]))
    elements.append(Spacer(1, 0.2 * cm))

    header = [Paragraph("Créneau", styles["day"])] + [
        Paragraph(jour, styles["day"]) for jour in JOURS
    ]
    data = [header]

    for i, label in enumerate(CRENEAUX_LABELS):
        creneau_id, debut, fin = CRENEAUX[i]
        slot_label = f"{creneau_id}<br/><font size='7' color='#6a7d74'>{debut[:-3]}–{fin[:-3]}</font>"
        row = [Paragraph(slot_label, styles["slot"])]
        for jour in JOURS:
            cours = get_cours(filiere_id, date_lundi, jour, creneau_id)
            row.append(_cell_content(cours, styles, filiere_id=filiere_id))
        data.append(row)

    page_width = landscape(A4)[0]
    usable = page_width - 2.4 * cm
    slot_w = 3.2 * cm
    day_w = (usable - slot_w) / len(JOURS)
    col_widths = [slot_w] + [day_w] * len(JOURS)

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND),
                ("TEXTCOLOR", (0, 0), (-1, 0), CREAM),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BODY_BOLD),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BACKGROUND", (0, 1), (0, -1), PARCHMENT),
                ("BACKGROUND", (1, 1), (-1, -1), CREAM),
                ("ROWBACKGROUNDS", (1, 1), (-1, -1), [CREAM, colors.HexColor("#f7f3ea")]),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.6, LINE),
                ("BOX", (0, 0), (-1, -1), 1.2, BRAND_SOFT),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, 0), 7),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
            ]
        )
    )
    elements.append(table)

    # Légende
    elements.append(Spacer(1, 0.35 * cm))
    elements.append(
        Paragraph(
            f"<font color='#0f4c3a'><b>Matière</b></font>  ·  "
            f"<font color='#3d524a'>Enseignant</font>  ·  "
            f"<font color='#6a7d74'>Salle</font>  ·  "
            f"<font color='#c45c26'><b>TC avec [filières]</b></font>",
            ParagraphStyle(
                name="Legend",
                fontName=FONT_BODY,
                fontSize=8,
                textColor=MUTED,
                alignment=TA_CENTER,
            ),
        )
    )

    # Notes réglementaires / pratiques
    elements.append(Spacer(1, 0.35 * cm))
    note_style = ParagraphStyle(
        name="ExportNotes",
        fontName=FONT_BODY,
        fontSize=8,
        textColor=INK_SOFT,
        leading=11,
        alignment=TA_CENTER,
        leftIndent=0.5 * cm,
        rightIndent=0.5 * cm,
    )
    elements.append(
        Paragraph(f"<b>{escape(EXPORT_NOTES[0])}</b>", note_style)
    )
    elements.append(Spacer(1, 0.12 * cm))
    elements.append(Paragraph(escape(EXPORT_NOTES[1]), note_style))

    def _on_page(canvas, doc_):
        _draw_page(canvas, doc_, meta)

    doc.build(elements, onFirstPage=_on_page, onLaterPages=_on_page)
    return True


def export_all_filieres(
    date_lundi,
    annee_univ=ANNEE_COURANTE,
    logo_path=None,
    etablissement=None,
    type_cours=None,
):
    from database import get_filieres

    filieres = get_filieres(etablissement=etablissement) if etablissement else get_filieres()
    if not filieres:
        return []

    logo_path = _default_logo(logo_path)
    semaine_dir = os.path.join(EXPORT_DIR, annee_univ, date_lundi)
    os.makedirs(semaine_dir, exist_ok=True)

    print(f"Export dans : {semaine_dir}")

    resultats = []
    for f in filieres:
        pdf_name = _safe_filename(f"{f.annee}_{f.nom}.pdf")
        pdf_path = os.path.join(semaine_dir, pdf_name)
        ok = export_pour_filiere(
            f.id, date_lundi, pdf_path, logo_path, type_cours=type_cours
        )
        resultats.append((f, ok, pdf_path if ok else None))

    return resultats


def export_une_filiere(
    filiere_id,
    date_lundi,
    annee_univ=ANNEE_COURANTE,
    logo_path=None,
    type_cours=None,
):
    logo_path = _default_logo(logo_path)
    filiere = get_filiere_by_id(filiere_id)
    if not filiere:
        return None

    semaine_dir = os.path.join(EXPORT_DIR, annee_univ, date_lundi)
    os.makedirs(semaine_dir, exist_ok=True)
    pdf_name = _safe_filename(f"{filiere.annee}_{filiere.nom}.pdf")
    pdf_path = os.path.join(semaine_dir, pdf_name)
    ok = export_pour_filiere(
        filiere_id, date_lundi, pdf_path, logo_path, type_cours=type_cours
    )
    return pdf_path if ok else None


def export_all_filieres_zip(
    date_lundi,
    annee_univ=ANNEE_COURANTE,
    logo_path=None,
    etablissement=None,
    type_cours=None,
):
    """Génère tous les PDF puis un ZIP téléchargeable."""
    resultats = export_all_filieres(
        date_lundi,
        annee_univ=annee_univ,
        logo_path=logo_path,
        etablissement=etablissement,
        type_cours=type_cours,
    )
    if not resultats:
        return None, []

    semaine_dir = os.path.join(EXPORT_DIR, annee_univ, date_lundi)
    suffix = f"_{_safe_filename(etablissement)}" if etablissement else ""
    zip_name = _safe_filename(f"EDT_{date_lundi}{suffix}.zip")
    zip_path = os.path.join(semaine_dir, zip_name)

    written = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f, ok, path in resultats:
            if ok and path and os.path.isfile(path):
                zf.write(path, arcname=os.path.basename(path))
                written += 1

    if written == 0:
        try:
            os.remove(zip_path)
        except OSError:
            pass
        return None, resultats

    return zip_path, resultats
