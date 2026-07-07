"""Séries FRED via l'export CSV public de fredgraph (pas de clé nécessaire)."""
import csv
import datetime
import io

import httpx

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def fetch_history(series_id: str, start: datetime.date | None = None) -> list[tuple[datetime.date, float]]:
    """Retourne [(date, valeur)] pour une série FRED, en ignorant les jours vides ('.')."""
    params = {"id": series_id}
    if start:
        params["cosd"] = start.isoformat()
    with httpx.Client(timeout=20, follow_redirects=True) as client:
        resp = client.get(URL, params=params)
        resp.raise_for_status()

    out = []
    reader = csv.reader(io.StringIO(resp.text))
    header = next(reader, None)
    if not header or len(header) < 2:
        raise ValueError(f"CSV FRED inattendu pour {series_id}")
    for row in reader:
        if len(row) < 2 or row[1] in (".", ""):
            continue
        out.append((datetime.date.fromisoformat(row[0]), float(row[1])))
    return out
