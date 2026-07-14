import datetime
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import scheduler
from .collectors.edgar13f import collect_13f
from .collectors.fonds_pdf import collect_boutiques_pdf
from .collectors.run import collect_all, seed_gerants, seed_instruments
from .config import FAMILIES, PEA_LAB_PRODUCTS
from .db import Base, SessionLocal, engine
from .engine.moves import compute_moves
from .engine.pea_lab import LabSettings, simulate_pea
from .models import (
    AssetManager, Brief, Fund, FundSnapshot, Instrument, Position, PriceDaily,
    Security, SecurityAlias, SourceDocument, These,
)

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
                       "blurb": "Leurs reportings mensuels sont collectés et archivés ; l'extraction des positions et du pourquoi se fait document par document (pipeline Codex, voir docs/extraction-fonds.md)."},
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
    documents_rows = session.execute(
        select(Fund.slug, SourceDocument.statut_extraction, func.count(SourceDocument.id))
        .join(SourceDocument, SourceDocument.fund_id == Fund.id)
        .group_by(Fund.id, SourceDocument.statut_extraction)
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
        "documents_fonds": [
            {"fonds": slug, "statut": statut, "count": count}
            for slug, statut, count in documents_rows
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


@app.post("/api/collecte-fonds-pdf", dependencies=[Depends(require_token)])
def api_collecte_fonds_pdf(session: Session = Depends(get_session)):
    report = collect_boutiques_pdf(session)
    ok = sum(1 for r in report.values() if r["ok"])
    return {"ok": ok, "echecs": len(report) - ok, "detail": report}


@app.get("/api/fonds/documents/{document_id}.pdf", name="fonds_document_pdf")
def api_fonds_document_pdf(document_id: int, session: Session = Depends(get_session)):
    document = session.get(SourceDocument, document_id)
    if document is None or document.contenu is None:
        raise HTTPException(status_code=404, detail="document introuvable ou non archivé")
    return Response(content=document.contenu, media_type="application/pdf")


@app.get("/api/fonds/extraction/en-attente")
def api_fonds_extraction_en_attente(request: Request, session: Session = Depends(get_session)):
    """Les documents archivés (reportings boutiques) dont l'extraction reste à faire.

    Voir docs/extraction-fonds.md — c'est le contrat que suit l'agent d'extraction (Codex)."""
    documents = session.execute(
        select(SourceDocument, Fund)
        .join(Fund, Fund.id == SourceDocument.fund_id)
        .where(SourceDocument.statut_extraction == "en_attente", SourceDocument.contenu.is_not(None))
        .order_by(SourceDocument.fetched_at)
    ).all()
    return {
        "documents": [
            {
                "document_id": doc.id,
                "fonds_slug": fund.slug,
                "fonds_nom": fund.nom,
                "type": doc.type,
                "periode": doc.periode,
                "url_archive": str(request.url_for("fonds_document_pdf", document_id=doc.id)),
            }
            for doc, fund in documents
        ],
    }


def _upsert_security_boutique(session: Session, libelle: str, isin: str | None) -> Security:
    security = None
    if isin:
        security = session.scalars(select(Security).where(Security.isin == isin)).first()
    if security is None:
        security = session.scalars(
            select(Security).join(SecurityAlias).where(SecurityAlias.libelle_brut == libelle)
        ).first()
    if security is None:
        security = Security(nom_canonique=libelle, isin=isin or "")
        session.add(security)
        session.flush()
    alias = session.scalars(select(SecurityAlias).where(
        SecurityAlias.security_id == security.id, SecurityAlias.libelle_brut == libelle)).first()
    if alias is None:
        session.add(SecurityAlias(security_id=security.id, libelle_brut=libelle, source="boutique"))
    return security


@app.post("/api/fonds/extraction", dependencies=[Depends(require_token)])
def api_fonds_extraction_publier(payload: dict, session: Session = Depends(get_session)):
    """Réception du résultat d'extraction d'un document (contrat : docs/extraction-fonds.md)."""
    try:
        document_id = int(payload["document_id"])
        jour = datetime.date.fromisoformat(payload["date"])
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=f"payload invalide : {exc}")

    document = session.get(SourceDocument, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document introuvable")
    if document.statut_extraction != "en_attente":
        raise HTTPException(status_code=409, detail=f"document déjà {document.statut_extraction}")

    positions = payload.get("positions") or []
    theses = payload.get("theses") or []

    top10 = [p for p in positions if p.get("rang", 0) <= 10]
    if top10:
        poids_total = sum(float(p["poids_pct"]) for p in top10)
        if not (15 <= poids_total <= 80):
            document.statut_extraction = "erreur"
            session.commit()
            raise HTTPException(
                status_code=422,
                detail=f"poids du top 10 implausible ({poids_total:.1f} %, attendu entre 15 et 80 %)")
    for t in theses:
        if not (t.get("citation") or "").strip():
            document.statut_extraction = "erreur"
            session.commit()
            raise HTTPException(status_code=422, detail="une thèse sans citation source")

    snapshot = session.scalars(select(FundSnapshot).where(
        FundSnapshot.fund_id == document.fund_id, FundSnapshot.date == jour)).first()
    if snapshot is None:
        snapshot = FundSnapshot(
            fund_id=document.fund_id, date=jour, source_document_id=document.id,
            encours=payload.get("encours"), nb_lignes_publiees=payload.get("nb_lignes_publiees"))
        session.add(snapshot)
        session.flush()

    for p in positions:
        security = _upsert_security_boutique(session, p["libelle"], p.get("isin"))
        session.add(Position(
            snapshot_id=snapshot.id, security_id=security.id, libelle_brut=p["libelle"],
            poids_pct=float(p["poids_pct"]), rang=int(p["rang"])))

    for t in theses:
        security = None
        if t.get("valeur"):
            security = _upsert_security_boutique(session, t["valeur"], None)
        session.add(These(
            snapshot_id=snapshot.id, security_id=security.id if security else None,
            action=t["action"], texte_fr=t["texte"], citation_source=t["citation"],
            confiance=t.get("confiance")))

    document.statut_extraction = "extrait"
    session.commit()
    return {
        "document_id": document.id, "statut": "extrait", "snapshot_id": snapshot.id,
        "positions_inserees": len(positions), "theses_inserees": len(theses),
    }


@app.post("/api/brief", dependencies=[Depends(require_token)])
def api_brief_publier(payload: dict, session: Session = Depends(get_session)):
    """Publication du brief du matin (utilisé par la routine rédactrice — phase 2)."""
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


@app.get("/api/brief/dernier")
def api_brief_dernier(session: Session = Depends(get_session)):
    brief = session.scalars(select(Brief).order_by(Brief.date.desc())).first()
    if brief is None:
        return JSONResponse({"brief": None})
    return {"brief": {"date": brief.date.isoformat(), "titre": brief.title, "corps_md": brief.body_md}}
