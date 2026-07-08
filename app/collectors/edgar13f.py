"""Portefeuilles 13F via SEC EDGAR (données publiques, structurées).

Chaque gérant américain de plus de 100 M$ d'actions US dépose son portefeuille
complet chaque trimestre (jusqu'à 45 jours après la fin du trimestre).
La SEC impose un User-Agent déclaré et ~10 requêtes/seconde maximum.
Les valeurs sont en dollars pleins (depuis janvier 2023).
"""
import datetime
import io
import logging
import time
from xml.etree import ElementTree

import httpx

HEADERS = {"User-Agent": "La Grande Machine (outil pedagogique) eva.attal@gmail.com"}
SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES = "https://www.sec.gov/Archives/edgar/data/{cik_int}/{accession}"

log = logging.getLogger("collecte.13f")


def _get(client: httpx.Client, url: str) -> httpx.Response:
    resp = client.get(url)
    resp.raise_for_status()
    time.sleep(0.15)  # courtoisie SEC
    return resp


def latest_13f_filings(client: httpx.Client, cik: str, count: int = 1) -> list[dict]:
    """Les derniers dépôts 13F-HR d'un CIK : [{accession, report_date, filing_date}]."""
    data = _get(client, SUBMISSIONS.format(cik=cik)).json()
    recent = data["filings"]["recent"]
    out = []
    for form, accession, report_date, filing_date in zip(
        recent["form"], recent["accessionNumber"], recent["reportDate"], recent["filingDate"]
    ):
        if form != "13F-HR":  # les amendements (13F-HR/A) attendront la v2
            continue
        out.append({"accession": accession, "report_date": report_date, "filing_date": filing_date})
        if len(out) >= count:
            break
    return out


def _info_table_bytes(client: httpx.Client, cik: str, accession: str) -> tuple[bytes, str]:
    """Télécharge l'information table XML d'un dépôt. Retourne (contenu, url)."""
    cik_int, acc = int(cik), accession.replace("-", "")
    base = ARCHIVES.format(cik_int=cik_int, accession=acc)
    index = _get(client, f"{base}/index.json").json()
    candidates = [
        f for f in index["directory"]["item"]
        if f["name"].lower().endswith(".xml") and "primary_doc" not in f["name"].lower()
    ]
    if not candidates:
        raise ValueError(f"pas d'information table dans {base}")
    # en cas de doute, la plus grosse : l'information table domine toujours le dépôt
    name = max(candidates, key=lambda f: int(f.get("size") or 0))["name"]
    url = f"{base}/{name}"
    return _get(client, url).content, url


def parse_info_table(content: bytes) -> list[dict]:
    """Agrège l'information table par CUSIP : [{nom, cusip, valeur}] trié par valeur.

    Les options (putCall) sont écartées : on suit les actions détenues.
    Parcours en flux (iterparse) — les dépôts des géants font des dizaines de Mo.
    """
    holdings: dict[str, dict] = {}
    context = ElementTree.iterparse(io.BytesIO(content), events=("end",))
    for _, elem in context:
        if not elem.tag.endswith("infoTable"):
            continue
        fields = {child.tag.rsplit("}", 1)[-1]: child for child in elem}
        if "putCall" in fields and (fields["putCall"].text or "").strip():
            elem.clear()
            continue
        cusip = (fields["cusip"].text or "").strip()
        name = (fields["nameOfIssuer"].text or "").strip()
        value = float(fields["value"].text or 0)
        entry = holdings.setdefault(cusip, {"nom": name, "cusip": cusip, "valeur": 0.0})
        entry["valeur"] += value
        elem.clear()  # libère la mémoire au fil de l'eau
    return sorted(holdings.values(), key=lambda h: -h["valeur"])


def _quarter_label(report_date: str) -> str:
    day = datetime.date.fromisoformat(report_date)
    return f"{day.year}-T{(day.month - 1) // 3 + 1}"


def collect_13f(session, deep: bool = False) -> dict:
    """Collecte le dernier 13F de chaque gérant configuré (4 derniers si deep)."""
    from sqlalchemy import select

    from ..config import TOP_N_13F
    from ..models import AssetManager, FundSnapshot, Position, Security, SecurityAlias, SourceDocument

    report = {}
    with httpx.Client(headers=HEADERS, timeout=120, follow_redirects=True) as client:
        managers = session.scalars(select(AssetManager).where(AssetManager.cik_sec != "")).all()
        for manager in managers:
            fund = manager.funds[0]
            try:
                filings = latest_13f_filings(client, manager.cik_sec, count=4 if deep else 1)
                added = 0
                for filing in filings:
                    day = datetime.date.fromisoformat(filing["report_date"])
                    exists = session.scalars(select(FundSnapshot).where(
                        FundSnapshot.fund_id == fund.id, FundSnapshot.date == day)).first()
                    if exists:
                        continue
                    content, url = _info_table_bytes(client, manager.cik_sec, filing["accession"])
                    holdings = parse_info_table(content)
                    if not holdings:
                        raise ValueError("information table vide")
                    total = sum(h["valeur"] for h in holdings)
                    document = SourceDocument(
                        fund_id=fund.id, type="13f", periode=_quarter_label(filing["report_date"]),
                        url=url, statut_extraction="extrait")
                    session.add(document)
                    session.flush()
                    snapshot = FundSnapshot(
                        fund_id=fund.id, date=day, source_document_id=document.id,
                        encours=total, nb_lignes_publiees=len(holdings))
                    session.add(snapshot)
                    session.flush()
                    top_n = TOP_N_13F.get(manager.type, 50)
                    for rank, holding in enumerate(holdings[:top_n], start=1):
                        security = _upsert_security(session, holding)
                        session.add(Position(
                            snapshot_id=snapshot.id, security_id=security.id,
                            libelle_brut=holding["nom"], valeur=holding["valeur"],
                            poids_pct=round(holding["valeur"] / total * 100, 2), rang=rank))
                    session.commit()
                    added += 1
                latest = filings[0]["report_date"] if filings else None
                report[manager.slug] = {"ok": True, "snapshots_ajoutes": added, "dernier_trimestre": latest}
            except Exception as exc:  # noqa: BLE001 — un gérant en échec ne bloque pas les autres
                session.rollback()
                log.warning("13F %s en échec : %s", manager.slug, exc)
                report[manager.slug] = {"ok": False, "erreur": str(exc)[:200]}
    return report


def _upsert_security(session, holding: dict):
    from sqlalchemy import select

    from ..models import Security, SecurityAlias

    security = session.scalars(select(Security).where(Security.cusip == holding["cusip"])).first()
    if security is None:
        security = Security(nom_canonique=holding["nom"].title(), cusip=holding["cusip"])
        session.add(security)
        session.flush()
    alias = session.scalars(select(SecurityAlias).where(
        SecurityAlias.security_id == security.id,
        SecurityAlias.libelle_brut == holding["nom"])).first()
    if alias is None:
        session.add(SecurityAlias(security_id=security.id, libelle_brut=holding["nom"], source="13f"))
    return security
