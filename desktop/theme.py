"""Thème Qt GestionCours — rendu bureau (comme Gestion_app), couleurs campus."""

PRIMARY = "#0f4c3a"
PRIMARY_DARK = "#0a3328"
PRIMARY_SOFT = "#1f6b52"
ACCENT = "#c45c26"
SUCCESS = "#1f7a4d"
DANGER = "#a12828"
WARNING = "#9a5b12"

LIGHT = {
    "bg": "#f3efe6",
    "surface": "#fffdf9",
    "surface_alt": "#f7f3ea",
    "text": "#14201c",
    "muted": "#6a7d74",
    "border": "#d5ddd8",
    "sidebar": "#0a3328",
    "sidebar_text": "#d7e8df",
    "sidebar_active": PRIMARY_SOFT,
    "input": "#ffffff",
}


def build_stylesheet() -> str:
    c = LIGHT
    return f"""
    QWidget {{
        background-color: {c['bg']};
        color: {c['text']};
        font-family: 'Segoe UI', 'Noto Sans', Arial, sans-serif;
        font-size: 14px;
    }}
    QLabel {{ background: transparent; }}

    #MainWindow {{ background-color: {c['bg']}; }}

    #Sidebar {{
        background-color: {c['sidebar']};
        min-width: 220px;
        max-width: 220px;
    }}
    #SidebarTitle {{
        color: #ffffff;
        font-size: 18px;
        font-weight: 800;
        padding: 4px 8px;
    }}
    #SidebarSubtitle {{
        color: {c['sidebar_text']};
        font-size: 12px;
        padding: 0 8px 12px 8px;
    }}
    QPushButton#NavButton {{
        color: {c['sidebar_text']};
        background: transparent;
        border: none;
        text-align: left;
        padding: 12px 16px;
        border-radius: 10px;
        font-size: 14px;
    }}
    QPushButton#NavButton:hover {{ background-color: rgba(255,255,255,0.08); }}
    QPushButton#NavButton:checked {{
        background-color: {c['sidebar_active']};
        color: #ffffff;
        font-weight: 700;
    }}

    #PageTitle {{
        font-size: 22px;
        font-weight: 800;
        color: {PRIMARY};
    }}
    #PageHint {{
        color: {c['muted']};
        font-size: 13px;
    }}

    #Card, QFrame#Card {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 14px;
    }}
    #StatCard {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 14px;
        padding: 10px;
    }}
    #StatValue {{
        font-size: 24px;
        font-weight: 800;
        color: {PRIMARY};
    }}
    #StatTitle {{
        font-size: 12px;
        color: {c['muted']};
    }}
    #StatHighlight {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {PRIMARY}, stop:1 {PRIMARY_SOFT});
        border: none;
        border-radius: 14px;
    }}
    #StatHighlight #StatValue, #StatHighlight #StatTitle {{
        color: #ffffff;
    }}

    QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {{
        background-color: {c['input']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 8px 10px;
        selection-background-color: {PRIMARY};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {{
        border: 1px solid {PRIMARY};
    }}

    QPushButton {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 9px 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background-color: {c['surface_alt']}; }}
    QPushButton#PrimaryButton {{
        background-color: {PRIMARY};
        color: #ffffff;
        border: none;
    }}
    QPushButton#PrimaryButton:hover {{ background-color: {PRIMARY_SOFT}; }}
    QPushButton#AccentButton {{
        background-color: {ACCENT};
        color: #ffffff;
        border: none;
    }}
    QPushButton#DangerButton {{
        background-color: transparent;
        color: {DANGER};
        border: 1px solid {DANGER};
    }}
    QPushButton#DangerButton:hover {{
        background-color: rgba(161, 40, 40, 0.08);
    }}

    QTableWidget {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        gridline-color: {c['border']};
        selection-background-color: rgba(15, 76, 58, 0.15);
        selection-color: {c['text']};
    }}
    QHeaderView::section {{
        background-color: {PRIMARY};
        color: #fffdf9;
        padding: 8px;
        border: none;
        font-weight: 700;
    }}

    QScrollArea {{ border: none; background: transparent; }}

    #SlotCell {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
    }}
    #SlotCell[filled="true"] {{
        background-color: #f4faf7;
        border: 1px solid rgba(15, 76, 58, 0.25);
    }}
    #SlotCell[tc="true"] {{
        border: 1px solid {ACCENT};
        background-color: #fff6f0;
    }}
    #SlotMatiere {{
        font-weight: 700;
        color: {PRIMARY};
        font-size: 13px;
    }}
    #SlotEnseignant {{
        color: {c['text']};
        font-size: 12px;
    }}
    #SlotMeta {{
        color: {c['muted']};
        font-size: 11px;
    }}
    #SlotEmpty {{
        color: {c['muted']};
        font-size: 12px;
    }}
    #DayHeader {{
        background-color: {PRIMARY};
        color: #fffdf9;
        font-weight: 700;
        border-radius: 10px;
        padding: 8px;
        qproperty-alignment: AlignCenter;
    }}
    #CreneauLabel {{
        background-color: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 8px;
        font-weight: 700;
        color: {PRIMARY_DARK};
    }}

    QDialog {{
        background-color: {c['surface']};
    }}
    QMessageBox {{
        background-color: {c['surface']};
    }}
    """
