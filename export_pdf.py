import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from database import get_cours, get_filiere_by_id, get_salle_by_id
from config import EXPORT_DIR, ANNEE_COURANTE, JOURS, CRENEAUX, CRENEAUX_LABELS

def export_pour_filiere(filiere_id, date_lundi, output_path, logo_path=None):
    filiere = get_filiere_by_id(filiere_id)
    if not filiere:
        return False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        leftMargin=1.2*cm,
        rightMargin=1.2*cm,
        topMargin=1.8*cm,
        bottomMargin=1.2*cm
    )

    styles = getSampleStyleSheet()

    # Styles modernes (taille confortable)
    title_style = ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a3a5c'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        name='Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12
    )
    header_style = ParagraphStyle(
        name='Header',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )
    cell_style = ParagraphStyle(
        name='Cell',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        leading=15,
        fontName='Helvetica'
    )
    matiere_style = ParagraphStyle(
        name='Matiere',
        parent=cell_style,
        fontSize=12,
        textColor=colors.HexColor('#1a3a5c'),
        fontName='Helvetica-Bold'
    )

    elements = []

    # Logo
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=2.2*cm, height=2.2*cm)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.2*cm))
        except:
            pass

    dt = datetime.fromisoformat(date_lundi)
    titre = Paragraph(f"{filiere.annee} - {filiere.nom}", title_style)
    sous_titre = Paragraph(f"Emploi du temps - Semaine du {dt.strftime('%d/%m/%Y')}", subtitle_style)
    elements.append(titre)
    elements.append(sous_titre)
    elements.append(Spacer(1, 0.5*cm))

    # Tableau
    data = [[""] + JOURS]

    for i, label in enumerate(CRENEAUX_LABELS):
        row = [label]
        for jour in JOURS:
            cours = get_cours(filiere_id, date_lundi, jour, CRENEAUX[i][0])
            if cours:
                salle_nom = ""
                if cours.salle_id:
                    salle = get_salle_by_id(cours.salle_id)
                    if salle:
                        salle_nom = f"<br/><font color='#555555' size=9>Salle : {salle.nom}</font>"
                tc_text = f"<br/><font color='#888888' size=8><i>(TC: {cours.groupe_tc})</i></font>" if cours.groupe_tc else ""
                cell_text = f"<font name='Helvetica-Bold' size='11' color='#1a3a5c'>{cours.matiere}</font><br/>{cours.enseignant}{salle_nom}{tc_text}"
                row.append(Paragraph(cell_text, cell_style))
            else:
                row.append(Paragraph("—", cell_style))
        data.append(row)

    # Largeurs des colonnes : équitable et lisible
    page_width = landscape(A4)[0]
    col_widths = [3.5*cm] + [(page_width - 2*cm - 2.8*cm) / len(JOURS)] * len(JOURS)

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a3a5c')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))

    elements.append(table)
    doc.build(elements)
    return True

def export_all_filieres(date_lundi, annee_univ=ANNEE_COURANTE, logo_path=C:\Users\ARIS\Documents\GestionCours\fichiers\logoist.jpeg):
    from database import get_filieres
    filieres = get_filieres()
    if not filieres:
        return []
    
    # Dossier année (ex: exports/2025-2026)
    annee_dir = os.path.join(EXPORT_DIR, annee_univ)
    
    # Dossier semaine (ex: exports/2025-2026/2025-05-12)
    semaine_dir = os.path.join(annee_dir, date_lundi)
    os.makedirs(semaine_dir, exist_ok=True)
    
    print(f"📁 Export dans : {semaine_dir}")
    
    resultats = []
    for f in filieres:
        pdf_name = f"{f.annee}_{f.nom}.pdf".replace(" ", "_")
        pdf_path = os.path.join(semaine_dir, pdf_name)
        ok = export_pour_filiere(f.id, date_lundi, pdf_path, logo_path)
        resultats.append((f, ok))
    
    return resultats