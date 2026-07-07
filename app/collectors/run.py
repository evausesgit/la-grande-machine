"""Orchestration de la collecte : chaque instrument est indépendant,
une source en panne n'empêche pas les autres."""
import datetime
import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import INSTRUMENTS
from ..models import Instrument, PriceDaily
from . import fred, yahoo

log = logging.getLogger("collecte")


def seed_instruments(session: Session) -> None:
    """Crée/met à jour les instruments du périmètre (idempotent)."""
    existing = {i.code: i for i in session.scalars(select(Instrument))}
    for spec in INSTRUMENTS:
        inst = existing.get(spec["code"])
        if inst is None:
            session.add(Instrument(**spec))
        else:
            for key, value in spec.items():
                setattr(inst, key, value)
    session.commit()


def _upsert_prices(session: Session, inst: Instrument, rows: list[tuple[datetime.date, float]]) -> int:
    if not rows:
        return 0
    first_day = rows[0][0]
    known = set(session.scalars(
        select(PriceDaily.date).where(PriceDaily.instrument_id == inst.id, PriceDaily.date >= first_day)
    ))
    added = 0
    for day, close in rows:
        if day in known:
            continue
        session.add(PriceDaily(instrument_id=inst.id, date=day, close=close))
        added += 1
    session.commit()
    return added


def collect_all(session: Session, deep: bool = False) -> dict:
    """Collecte toutes les séries. deep=True : historique long (premier remplissage)."""
    seed_instruments(session)
    report = {}
    for inst in session.scalars(select(Instrument)):
        try:
            if inst.source == "yahoo":
                rows = yahoo.fetch_history(inst.symbol, range_="5y" if deep else "1mo")
                time.sleep(0.4)  # courtoisie : ~40 requêtes par collecte
            elif inst.source == "fred":
                start = None if deep else datetime.date.today() - datetime.timedelta(days=40)
                rows = fred.fetch_history(inst.symbol, start=start)
            else:
                raise ValueError(f"source inconnue : {inst.source}")
            added = _upsert_prices(session, inst, rows)
            report[inst.code] = {"ok": True, "ajoutes": added, "derniere": rows[-1][0].isoformat() if rows else None}
        except Exception as exc:  # noqa: BLE001 — un échec ne bloque pas la suite
            session.rollback()
            log.warning("collecte %s en échec : %s", inst.code, exc)
            report[inst.code] = {"ok": False, "erreur": str(exc)[:200]}
    return report
