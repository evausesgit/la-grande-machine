"""Prix quotidiens via l'API chart de Yahoo Finance (non officielle mais stable).

Un User-Agent de navigateur est requis, sans quoi Yahoo renvoie un 429/403.
"""
import datetime

import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
BASE = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def fetch_history(symbol: str, range_: str = "1mo") -> list[tuple[datetime.date, float]]:
    """Retourne [(date, clôture ajustée des dividendes/splits)] pour un symbole Yahoo, trié par date."""
    params = {"range": range_, "interval": "1d", "events": "div,split"}
    with httpx.Client(headers=HEADERS, timeout=20) as client:
        resp = client.get(BASE.format(symbol=symbol), params=params)
        resp.raise_for_status()
        data = resp.json()

    result = data["chart"]["result"][0]
    gmtoffset = result["meta"].get("gmtoffset", 0)
    timestamps = result.get("timestamp") or []
    # adjclose reflète les dividendes réinvestis et les splits ; la clôture brute
    # sous-estime le rendement réel des ETF distribuants (ex: -13% sur 5 ans pour EUEA).
    indicators = result["indicators"]
    adjclose_series = indicators.get("adjclose")
    if adjclose_series:
        closes = adjclose_series[0].get("adjclose") or []
    else:
        closes = indicators["quote"][0].get("close") or []

    out: dict[datetime.date, float] = {}
    for ts, close in zip(timestamps, closes):
        if close is None:
            continue
        day = datetime.datetime.fromtimestamp(ts + gmtoffset, tz=datetime.timezone.utc).date()
        out[day] = float(close)  # en cas de doublon intrajournalier, la dernière valeur gagne
    return sorted(out.items())
