import datetime
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import scheduler
from .collectors.edgar13f import collect_13f
from .collectors.run import collect_all, seed_gerants, seed_instruments
from .config import FAMILIES, PEA_LAB_PRODUCTS
from .db import Base, SessionLocal, engine
from .engine.moves import compute_moves
from .engine.pea_lab import LabSettings, simulate_pea
from .models import AssetManager, Brief, Fund, FundSnapshot, Instrument, Position, PriceDaily

logging.basicConfig(level=logging.INFO)
ROOT = Path(__file__).resolve().parent.parent
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        seed_instruments(session)
        seed_gerants(session)
    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(title="La Grande Machine", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "app" / "templates")


def _fmt_valeur(value: float, decimals: int = 2) -> str:
    """1234567.8 → « 1 234 568 » (format français, espace fine insécable)."""
    text = f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")
    return text


def _fmt_variation(move: dict) -> str:
    v = move["variation"]
    if move.get("variation_en_points"):
        return f"{v:+.2f} pt".replace(".", ",")
    return f"{v * 100:+.2f} %".replace(".", ",")


templates.env.filters["fmt_valeur"] = _fmt_valeur
templates.env.filters["fmt_variation"] = _fmt_variation


def get_session():
    with SessionLocal() as session:
        yield session


def require_token(x_token: str = Header(default="")):
    if not ADMIN_TOKEN or x_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="jeton invalide")


@app.get("/")
def accueil(request: Request, session: Session = Depends(get_session)):
    moves = compute_moves(session)
    by_family = {fam: [] for fam in FAMILIES}
    for move in moves:
        by_family.setdefault(move["famille"], []).append(move)
    for fam_moves in by_family.values():
        fam_moves.sort(key=lambda m: -abs(m["z_score"] or 0))
    notables = [m for m in moves if m["z_score"] is not None and abs(m["z_score"]) >= 1.5][:8]
    brief = session.scalars(select(Brief).order_by(Brief.date.desc())).first()
    return templates.TemplateResponse(request, "index.html", {
        "familles": FAMILIES,
        "par_famille": by_family,
        "notables": notables,
        "brief": brief,
        "aujourdhui": datetime.date.today(),
    })


@app.get("/comprendre")
def comprendre():
    return FileResponse(ROOT / "viz" / "index.html", media_type="text/html")


@app.get("/rivieres")
def rivieres():
    return FileResponse(ROOT / "viz" / "rivieres-lacs.html", media_type="text/html")


TYPES_GERANTS = {
    "conviction_13f": {"label": "Les fonds de conviction américains",
                       "blurb": "Portefeuilles courts et assumés, déclarés chaque trimestre à la SEC (13F, jusqu'à 45 jours de délai)."},
    "geant_13f":      {"label": "Les géants de la gestion",
                       "blurb": "Ils possèdent un peu de tout le marché — on ne montre que le sommet de l'iceberg (top 10 affiché, top 50 conservé)."},
    "boutique":       {"label": "Les boutiques françaises de conviction",
                       "blurb": "Leurs positions mensuelles et le pourquoi de leurs mouvements arrivent en phase F3 (extraction des reportings PDF)."},
}


@app.get("/fonds")
def fonds(request: Request, session: Session = Depends(get_session)):
    par_type = {t: [] for t in TYPES_GERANTS}
    for manager in session.scalars(select(AssetManager).order_by(AssetManager.id)):
        blocs_fonds = []
        for fund in manager.funds:
            snapshot = session.scalars(
                select(FundSnapshot).where(FundSnapshot.fund_id == fund.id)
                .order_by(FundSnapshot.date.desc())).first()
            top = []
            if snapshot:
                top = session.scalars(
                    select(Position).where(Position.snapshot_id == snapshot.id)
                    .order_by(Position.rang).limit(10)).all()
            blocs_fonds.append({"fonds": fund, "snapshot": snapshot, "top": top})
        par_type.setdefault(manager.type, []).append({"gerant": manager, "fonds": blocs_fonds})
    return templates.TemplateResponse(request, "fonds.html", {
        "types": TYPES_GERANTS,
        "par_type": par_type,
    })


def _lab_parameters(produit: str, capital: float, versement: float, frais_bps: float, moyenne: int):
    if produit not in PEA_LAB_PRODUCTS:
        raise HTTPException(status_code=404, detail="produit PEA inconnu")
    try:
        settings = LabSettings(
            initial_capital=min(max(float(capital), 100), 1_000_000),
            monthly_contribution=min(max(float(versement), 0), 50_000),
            fee_bps=min(max(float(frais_bps), 0), 500),
            moving_average_days=min(max(int(moyenne), 20), 500),
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"paramètres invalides : {exc}")
    return settings


def _run_lab(session: Session, produit: str, settings: LabSettings):
    instrument = session.scalars(select(Instrument).where(Instrument.code == produit)).first()
    if instrument is None:
        return None, "produit absent de la base : redémarrer l'application pour initialiser le catalogue"
    prices = session.execute(
        select(PriceDaily.date, PriceDaily.close)
        .where(PriceDaily.instrument_id == instrument.id)
        .order_by(PriceDaily.date)
    ).all()
    minimum = max(settings.moving_average_days + 30, 252)
    if len(prices) < minimum:
        return None, f"historique insuffisant ({len(prices)} points, {minimum} requis) : lancer une collecte profonde"
    return {
        "buy_hold": simulate_pea(prices, settings, "buy_hold"),
        "trend": simulate_pea(prices, settings, "trend"),
    }, None


@app.get("/laboratoire")
def laboratoire(
    request: Request,
    produit: str = "pea_sp500_psp5",
    capital: float = 10_000,
    versement: float = 200,
    frais_bps: float = 10,
    moyenne: int = 200,
    session: Session = Depends(get_session),
):
    settings = _lab_parameters(produit, capital, versement, frais_bps, moyenne)
    results, error = _run_lab(session, produit, settings)
    return templates.TemplateResponse(request, "laboratoire.html", {
        "produits": PEA_LAB_PRODUCTS,
        "produit_id": produit,
        "produit": PEA_LAB_PRODUCTS[produit],
        "settings": settings,
        "results": results,
        "error": error,
    })


@app.get("/api/laboratoire")
def api_laboratoire(
    produit: str = "pea_sp500_psp5",
    capital: float = 10_000,
    versement: float = 200,
    frais_bps: float = 10,
    moyenne: int = 200,
    session: Session = Depends(get_session),
):
    settings = _lab_parameters(produit, capital, versement, frais_bps, moyenne)
    results, error = _run_lab(session, produit, settings)
    if error:
        raise HTTPException(status_code=409, detail=error)
    return {"produit": PEA_LAB_PRODUCTS[produit], "parametres": settings.__dict__, "resultats": results}


@app.get("/api/journee")
def api_journee(session: Session = Depends(get_session)):
    return {"mouvements": compute_moves(session)}


@app.get("/api/sante")
def api_sante(session: Session = Depends(get_session)):
    rows = session.execute(
        select(Instrument.code, Instrument.source, func.max(PriceDaily.date), func.count(PriceDaily.id))
        .join(PriceDaily, PriceDaily.instrument_id == Instrument.id, isouter=True)
        .group_by(Instrument.id)
    ).all()
    fonds_rows = session.execute(
        select(Fund.slug, func.max(FundSnapshot.date), func.count(FundSnapshot.id))
        .join(FundSnapshot, FundSnapshot.fund_id == Fund.id, isouter=True)
        .group_by(Fund.id)
    ).all()
    return {
        "instruments": [
            {"code": code, "source": source,
             "derniere_donnee": last.isoformat() if last else None, "points": count}
            for code, source, last, count in rows
        ],
        "fonds": [
            {"fonds": slug, "dernier_portefeuille": last.isoformat() if last else None, "snapshots": count}
            for slug, last, count in fonds_rows
        ],
    }


@app.post("/api/collecte", dependencies=[Depends(require_token)])
def api_collecte(deep: bool = False, session: Session = Depends(get_session)):
    report = collect_all(session, deep=deep)
    ok = sum(1 for r in report.values() if r["ok"])
    return {"ok": ok, "echecs": len(report) - ok, "detail": report}


@app.post("/api/collecte-fonds", dependencies=[Depends(require_token)])
def api_collecte_fonds(deep: bool = False, session: Session = Depends(get_session)):
    report = collect_13f(session, deep=deep)
    ok = sum(1 for r in report.values() if r["ok"])
    return {"ok": ok, "echecs": len(report) - ok, "detail": report}


def publier_brief(session: Session, payload: dict) -> dict:
    try:
        day = datetime.date.fromisoformat(payload["date"])
        title, body = payload["titre"], payload["corps_md"]
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"payload invalide : {exc}")
    brief = session.scalars(select(Brief).where(Brief.date == day)).first()
    if brief is None:
        brief = Brief(date=day, title=title, body_md=body, payload=payload.get("donnees", {}))
        session.add(brief)
    else:
        brief.title, brief.body_md, brief.payload = title, body, payload.get("donnees", {})
    session.commit()
    return {"publie": day.isoformat()}


@app.post("/api/brief", dependencies=[Depends(require_token)])
def api_brief_publier(payload: dict, session: Session = Depends(get_session)):
    """Publication directe du brief (payload déjà rédigé)."""
    return publier_brief(session, payload)


@app.post("/api/brief/generer", dependencies=[Depends(require_token)])
def api_brief_generer(session: Session = Depends(get_session)):
    """Déclenche la rédaction + publication du brief du jour, dans le container
    (recherche web incluse). Utilisé par le scheduler quotidien, et disponible
    en manuel pour tester ou rattraper une journée manquée."""
    from .brief_writer import generer_et_publier
    try:
        return generer_et_publier(session)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"échec de la rédaction : {exc}")


@app.get("/api/brief/dernier")
def api_brief_dernier(session: Session = Depends(get_session)):
    brief = session.scalars(select(Brief).order_by(Brief.date.desc())).first()
    if brief is None:
        return JSONResponse({"brief": None})
    return {"brief": {"date": brief.date.isoformat(), "titre": brief.title, "corps_md": brief.body_md}}
