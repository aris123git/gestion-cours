from datetime import datetime, timedelta

def get_lundi_week_courante():
    today = datetime.now().date()
    lundi = today - timedelta(days=today.weekday())
    return lundi.isoformat()

def format_date_fr(date_iso):
    dt = datetime.fromisoformat(date_iso)
    return dt.strftime("%d/%m/%Y")

def get_semaine_precedente(date_lundi):
    dt = datetime.fromisoformat(date_lundi)
    dt -= timedelta(days=7)
    return dt.isoformat()

def get_semaine_suivante(date_lundi):
    dt = datetime.fromisoformat(date_lundi)
    dt += timedelta(days=7)
    return dt.isoformat()