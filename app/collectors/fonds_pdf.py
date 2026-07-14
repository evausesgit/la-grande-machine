"""Téléchargement et archivage des reportings PDF des boutiques (phase F3).

Chaque maison a sa recette (```_recipe_*```) : trouver l'URL du reporting du
mois — « fiche » (positions) et « lettre » (le pourquoi, mensuel ou
trimestriel selon la maison). Le contenu est archivé en base (colonne
``SourceDocument.contenu``) avec son sha256 : certaines maisons publient à
une URL stable réécrite chaque mois (Amiral, Carmignac, LFDE), la seule
façon fiable de détecter un nouveau reporting est de comparer le contenu.

L'extraction (positions + thèses) est un chantier séparé, piloté par un
agent LLM (Codex) via ``/api/fonds/extraction`` — voir ``docs/extraction-fonds.md``.
Ce module ne fait que collecter et archiver, jamais d'extraction.
"""
import datetime
import hashlib
import logging
import re

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Fund, SourceDocument

HEADERS = {"User-Agent": "La Grande Machine (outil pedagogique) eva.attal@gmail.com"}
log = logging.getLogger("collecte.fonds_pdf")


def _mois_recul(date_ref: datetime.date, n: int) -> datetime.date:
    """Le 1er du mois n mois avant date_ref (n=0 : mois courant)."""
    month = date_ref.month - n
    year = date_ref.year
    while month <= 0:
        month += 12
        year -= 1
    return datetime.date(year, month, 1)


def _recipe_moneta(client: httpx.Client) -> list[dict]:
    """URL prévisible ``documents/<Nom>_AAAA_MM.pdf`` : mois courant puis jusqu'à 2 mois en arrière."""
    today = datetime.date.today()
    out = []
    for type_doc, nom in (("fiche", "Fiche_MMC_FR_fr"), ("lettre", "Lettre_MMC_part_C_FR_fr")):
        for back in range(3):
            mois = _mois_recul(today, back)
            url = f"https://www.moneta.fr/documents/{nom}_{mois.strftime('%Y_%m')}.pdf"
            resp = client.get(url)
            if resp.status_code == 200 and resp.content:
                out.append({"type": type_doc, "url": url, "periode": mois.strftime("%Y-%m"), "contenu": resp.content})
                break
    return out


def _dernier_reporting_independance(html: str) -> tuple[str | None, str | None]:
    """Le reporting mensuel le plus récent listé sur la page du fonds.

    Nom de fichier préfixé AAMMJJ (WordPress, suffixe parfois variable) :
    ``.../260630-reporting-france-small-mid-x-eur-c2-fr-2-1.pdf``.
    """
    liens = re.findall(
        r'href="(https://www\.independance-am\.com/wp-content/uploads/\d{4}/\d{2}/'
        r'(\d{6})-reporting-france-small-mid[^"]*\.pdf)"', html)
    if not liens:
        return None, None
    url, date_brute = max(liens, key=lambda pair: pair[1])
    periode = f"20{date_brute[:2]}-{date_brute[2:4]}"
    return url, periode


def _recipe_independance(client: httpx.Client) -> list[dict]:
    page = client.get("https://www.independance-am.com/nos-fonds/france-small/")
    page.raise_for_status()
    url, periode = _dernier_reporting_independance(page.text)
    if url is None:
        return []
    resp = client.get(url)
    if resp.status_code != 200:
        return []
    return [{"type": "fiche", "url": url, "periode": periode, "contenu": resp.content}]


def _lien_document_amiral(html: str) -> str | None:
    """URL stable (champ JSON ``docPermalink``), contenu remplacé chaque mois."""
    m = re.search(r'docPermalink:"([^"]+)"', html)
    if m is None:
        return None
    return m.group(1).replace("\\u002F", "/")


def _recipe_amiral(client: httpx.Client, page_slug: str) -> list[dict]:
    page = client.get(f"https://www.amiralgestion.com/fr/publications-adminmenu/{page_slug}")
    page.raise_for_status()
    url = _lien_document_amiral(page.text)
    if url is None:
        return []
    resp = client.get(url)
    if resp.status_code != 200:
        return []
    periode = datetime.date.today().strftime("%Y-%m")
    return [{"type": "fiche", "url": url, "periode": periode, "contenu": resp.content}]


_CARMIGNAC_URLS = {
    "fiche": "https://www.carmignac.com/assets/yoda/FLFPRO_CI_FR0010148981_FR_fr/"
             "Monthly-Factsheet-PRO_Carmignac-Investissement-A-EUR-Acc_FR0010148981_FR_fr.pdf",
    "lettre": "https://www.carmignac.com/assets/yoda/QR_CI_1_FR_fr/"
              "Quarterly-Report_Carmignac-Investissement_FR_fr.pdf",
}


def _recipe_carmignac(client: httpx.Client) -> list[dict]:
    """URL stables (page « documents » du fonds), contenu remplacé à chaque publication."""
    periode = datetime.date.today().strftime("%Y-%m")
    out = []
    for type_doc, url in _CARMIGNAC_URLS.items():
        resp = client.get(url)
        if resp.status_code == 200 and resp.content:
            out.append({"type": type_doc, "url": url, "periode": periode, "contenu": resp.content})
    return out


def _recipe_lfde(client: httpx.Client, isin: str) -> list[dict]:
    """URL stable par ISIN (``cdn.lfde.com``), écrasée chaque mois sans archive publique."""
    url = f"https://cdn.lfde.com/upload/documents/FACSHT-FR-FR-{isin}.pdf"
    resp = client.get(url)
    if resp.status_code != 200 or not resp.content:
        return []
    periode = datetime.date.today().strftime("%Y-%m")
    return [{"type": "fiche", "url": url, "periode": periode, "contenu": resp.content}]


def _liens_documents_comgest(html: str) -> dict[str, tuple[str, str]]:
    """{"Monthly Report": (url, "AAAA-MM-JJ"), "Quarterly Report": (...)} depuis le bloc « Key Documents »."""
    blocs = re.findall(
        r'fund-key-document-type[^>]*>\s*([^<]+?)\s*</span>.*?href="([^"]+\.pdf)"[^>]*data-documentDate="([^"]*)"',
        html, re.S)
    out = {}
    for label, url, date in blocs:
        out.setdefault(label.strip(), (url, date))
    return out


def _recipe_comgest(client: httpx.Client) -> list[dict]:
    page = client.get("https://www.comgest.com/en/fr/private-investor/funds/comgest-growth-europe-eur-acc")
    page.raise_for_status()
    liens = _liens_documents_comgest(page.text)
    out = []
    for label, type_doc in (("Monthly Report", "fiche"), ("Quarterly Report", "lettre")):
        candidat = liens.get(label)
        if candidat is None:
            continue
        url, date = candidat
        resp = client.get(url)
        if resp.status_code != 200:
            continue
        periode = date[:7] if len(date) >= 7 else datetime.date.today().strftime("%Y-%m")
        out.append({"type": type_doc, "url": url, "periode": periode, "contenu": resp.content})
    return out


# Une recette par fonds boutique (slug → fonction acceptant le client HTTP en premier argument).
_RECETTES = {
    "moneta-multi-caps": lambda client, fund: _recipe_moneta(client),
    "independance-france-small": lambda client, fund: _recipe_independance(client),
    "sextant-pme": lambda client, fund: _recipe_amiral(client, "sextant-pme-i-mensuel"),
    "sextant-grand-large": lambda client, fund: _recipe_amiral(client, "sextant-grand-large-a-mensuel"),
    "carmignac-investissement": lambda client, fund: _recipe_carmignac(client),
    "echiquier-agressor": lambda client, fund: _recipe_lfde(client, fund.isin),
    "comgest-growth-europe": lambda client, fund: _recipe_comgest(client),
}


def _archiver(session: Session, fund: Fund, candidat: dict) -> bool:
    """Enregistre un nouveau SourceDocument si le contenu diffère du dernier connu (fonds+type).

    Retourne True si un document a été ajouté."""
    sha = hashlib.sha256(candidat["contenu"]).hexdigest()
    dernier = session.scalars(
        select(SourceDocument)
        .where(SourceDocument.fund_id == fund.id, SourceDocument.type == candidat["type"])
        .order_by(SourceDocument.fetched_at.desc())
    ).first()
    if dernier is not None and dernier.sha256 == sha:
        return False
    session.add(SourceDocument(
        fund_id=fund.id, type=candidat["type"], periode=candidat["periode"], url=candidat["url"],
        sha256=sha, contenu=candidat["contenu"], statut_extraction="en_attente"))
    return True


def collect_boutiques_pdf(session: Session) -> dict:
    """Collecte les reportings PDF de chaque fonds boutique configuré avec une recette."""
    report = {}
    with httpx.Client(headers=HEADERS, timeout=60, follow_redirects=True) as client:
        for fund_slug, recette in _RECETTES.items():
            fund = session.scalars(select(Fund).where(Fund.slug == fund_slug)).first()
            if fund is None:
                report[fund_slug] = {"ok": False, "erreur": "fonds absent de la base"}
                continue
            try:
                candidats = recette(client, fund)
                ajoutes = sum(1 for c in candidats if _archiver(session, fund, c))
                session.commit()
                report[fund_slug] = {"ok": True, "documents_ajoutes": ajoutes, "trouves": len(candidats)}
            except Exception as exc:  # noqa: BLE001 — une maison en échec ne bloque pas les autres
                session.rollback()
                log.warning("collecte PDF %s en échec : %s", fund_slug, exc)
                report[fund_slug] = {"ok": False, "erreur": str(exc)[:200]}
    return report
