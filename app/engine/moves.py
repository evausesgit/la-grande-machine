"""Le premier étage du moteur du « pourquoi » : qu'est-ce qui a VRAIMENT bougé ?

Variation du jour rapportée à la volatilité des 30 dernières séances (z-score).
Pour les séries en pourcentage ou en points (taux, spreads, pente), la variation
pertinente est la différence absolue, pas le pourcentage.
"""
import statistics

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Instrument, PriceDaily

# familles dont la variation se lit en points (delta), pas en %
DELTA_FAMILIES = {"taux", "credit"}
WINDOW = 30


def compute_moves(session: Session) -> list[dict]:
    """Pour chaque instrument : dernière valeur, variation, z-score, fraîcheur."""
    moves = []
    for inst in session.scalars(select(Instrument)):
        rows = session.execute(
            select(PriceDaily.date, PriceDaily.close)
            .where(PriceDaily.instrument_id == inst.id)
            .order_by(PriceDaily.date.desc())
            .limit(WINDOW + 2)
        ).all()
        if len(rows) < 2:
            continue
        rows.reverse()
        closes = [r.close for r in rows]
        dates = [r.date for r in rows]

        use_delta = inst.family in DELTA_FAMILIES
        if use_delta:
            changes = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        else:
            changes = [
                (closes[i] - closes[i - 1]) / closes[i - 1]
                for i in range(1, len(closes))
                if closes[i - 1]
            ]
        if not changes:
            continue
        last_change = changes[-1]
        history = changes[:-1]
        z = None
        if len(history) >= 10:
            sigma = statistics.pstdev(history)
            if sigma > 1e-12:
                z = last_change / sigma

        moves.append({
            "code": inst.code,
            "nom": inst.name,
            "famille": inst.family,
            "unite": inst.unit,
            "decimales": inst.decimals,
            "valeur": closes[-1],
            "date": dates[-1].isoformat(),
            "variation": last_change,          # % (fraction) ou points selon le type
            "variation_en_points": use_delta,
            "z_score": round(z, 2) if z is not None else None,
        })
    moves.sort(key=lambda m: abs(m["z_score"] or 0), reverse=True)
    return moves
