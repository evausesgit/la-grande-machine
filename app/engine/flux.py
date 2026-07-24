"""Le bassin versant de l'argent — les grandes masses et les flux entre elles.

Trois étages, de gauche à droite : les **sources** (d'où l'argent part), les
**collecteurs** (qui le rassemblent), les **mers d'actifs** (où il se pose).

Le point délicat — et la raison pour laquelle chaque chiffre porte une étiquette :
personne ne publie gratuitement les flux mondiaux en temps réel. Cette page mêle
donc trois natures de chiffres, et le dit à chaque fois :

  « mesuré »    — calculé depuis notre base (cours collectés, encours 13F déposés) ;
  « lu »        — déduit de nos données sans être une mesure de flux : quand une mer
                  monte un mois durant, l'argent a penché de ce côté — c'est une
                  lecture, pas un relevé de virements ;
  « documenté » — ordre de grandeur publié par une institution, avec sa source.

Rien n'est inventé : ce qu'on ne sait pas mesurer reste explicitement documenté.
"""
import datetime
import statistics

from sqlalchemy import select

from ..models import AssetManager, FundSnapshot, Fund, Instrument, PriceDaily

# Une once troy par tonne — pour valoriser le stock d'or au cours du jour.
ONCES_PAR_TONNE = 32_150.7
# Stock d'or extrait depuis toujours, fin 2024 (World Gold Council).
STOCK_OR_TONNES = 216_265
# Bitcoins en circulation (protocole, ~2026) — le reste de la crypto n'est pas dans notre base.
BITCOINS_EN_CIRCULATION = 19_900_000

# Sensibilité d'une obligation 10 ans à son taux : 1 point de taux en moins ≈ +8 % de prix.
DURATION_10_ANS = 8.0

FENETRE_COURANT = 30  # séances : « le mois écoulé »

# --- Les lacs : les grandes masses, en milliers de milliards de dollars (T$) -----------
#
# `stock` est un ordre de grandeur documenté ; il sert à dimensionner le dessin.
# Les lacs marqués `mesure_13f` reçoivent en plus la part que notre base mesure
# vraiment — c'est le cœur honnête de la page : on montre ce qu'on sait, éclairé,
# dans ce qu'on ne sait qu'estimer.

LACS = [
    {"id": "menages", "nom": "Ménages & entreprises", "etage": "sources",
     "x": 150, "y": 450, "stock": 240, "couleur": "lac-neutre",
     "provenance": "documente",
     "source": "Allianz Global Wealth Report — actifs financiers bruts des ménages, ordre de grandeur 2024",
     "note": "L'épargne du monde entier : dépôts, assurance-vie, titres détenus en direct."},
    {"id": "banques_centrales", "nom": "Banques centrales", "etage": "sources",
     "x": 150, "y": 130, "stock": 24, "couleur": "lac-neutre",
     "provenance": "documente",
     "source": "Bilans publiés Fed (H.4.1) + BCE + Banque du Japon + Banque de Chine, cumul, ordre de grandeur 2025",
     "note": "Le seul acteur qui peut créer l'argent au lieu de le collecter."},

    {"id": "fonds_pension", "nom": "Fonds de pension", "etage": "collecteurs",
     "x": 500, "y": 125, "stock": 55, "couleur": "lac-neutre",
     "provenance": "documente",
     "source": "Thinking Ahead Institute, Global Pension Assets Study, ordre de grandeur 2024",
     "note": "Les retraites des salariés — horizon très long, donc mouvements lents."},
    {"id": "assureurs", "nom": "Assureurs", "etage": "collecteurs",
     "x": 500, "y": 265, "stock": 40, "couleur": "lac-neutre",
     "provenance": "documente",
     "source": "OCDE, statistiques des assureurs — ordre de grandeur 2024",
     "note": "Ils doivent pouvoir payer les sinistres : beaucoup d'obligations, peu d'actions."},
    {"id": "gerants", "nom": "Gérants d'actifs", "etage": "collecteurs",
     "x": 500, "y": 415, "stock": 130, "couleur": "lac-neutre",
     "provenance": "documente",
     "source": "BCG Global Asset Management Report — encours mondial sous gestion, ordre de grandeur 2024",
     "note": "Fonds et ETF : ils investissent l'argent des autres.",
     "mesure_13f": "geant_13f"},
    {"id": "hedge_funds", "nom": "Hedge funds & fonds de conviction", "etage": "collecteurs",
     "x": 500, "y": 545, "stock": 4.5, "couleur": "lac-neutre",
     "provenance": "documente",
     "source": "HFR / BarclayHedge — encours de la gestion alternative, ordre de grandeur 2025",
     "note": "Petits par la taille, bruyants par les paris.",
     "mesure_13f": "conviction_13f"},

    {"id": "actions", "nom": "Actions", "etage": "mers",
     "x": 980, "y": 110, "stock": 120, "couleur": "c-actions",
     "provenance": "documente",
     "source": "World Federation of Exchanges / SIFMA — capitalisation boursière mondiale, ordre de grandeur 2025",
     "note": "Des parts d'entreprises : le rendement le plus élevé, la peur la plus rapide."},
    {"id": "obligations", "nom": "Obligations", "etage": "mers",
     "x": 980, "y": 262, "stock": 140, "couleur": "c-oblig",
     "provenance": "documente",
     "source": "SIFMA Capital Markets Fact Book / BRI — encours obligataire mondial, ordre de grandeur 2025",
     "note": "Des prêts : la plus grande mer du monde, et la plus discrète."},
    {"id": "or", "nom": "Or", "etage": "mers",
     "x": 980, "y": 400, "stock": 16, "couleur": "c-or",
     "provenance": "documente",
     "source": "World Gold Council — stock extrait, valorisé au cours de notre base",
     "note": "Ne rapporte rien, ne fait faillite jamais — l'assurance du système."},
    {"id": "crypto", "nom": "Bitcoin", "etage": "mers",
     "x": 980, "y": 487, "stock": 2, "couleur": "c-crypto",
     "provenance": "documente",
     "source": "Bitcoins en circulation (protocole), valorisés au cours de notre base",
     "note": "Seul le bitcoin est dans notre base : le reste de la crypto n'est pas mesuré ici."},
    {"id": "monetaire", "nom": "Monétaire", "etage": "mers",
     "x": 980, "y": 588, "stock": 10, "couleur": "c-mone",
     "provenance": "documente",
     "source": "ICI (fonds monétaires américains) + équivalents européens, ordre de grandeur 2025",
     "note": "Le parking : de l'argent qui attend, rémunéré au jour le jour."},
]

# --- Les rivières : les débits, en T$ par an -------------------------------------------
#
# Aucun institut ne publie ces débits mondiaux : ils sont **illustratifs**, calibrés
# pour que le dessin respecte les proportions connues (l'épargne va surtout aux
# collecteurs, les collecteurs surtout aux obligations et aux actions). Ce que la
# page prétend montrer de réel, c'est leur **orientation du moment** — voir courants().

RIVIERES = [
    {"id": "menages-fonds_pension", "de": "menages", "vers": "fonds_pension", "base": 3.0, "couleur": "flux-neutre"},
    {"id": "menages-assureurs", "de": "menages", "vers": "assureurs", "base": 2.2, "couleur": "flux-neutre"},
    {"id": "menages-gerants", "de": "menages", "vers": "gerants", "base": 4.0, "couleur": "flux-neutre"},
    {"id": "menages-hedge_funds", "de": "menages", "vers": "hedge_funds", "base": 0.8, "couleur": "flux-neutre"},
    {"id": "menages-monetaire", "de": "menages", "vers": "monetaire", "base": 1.5, "couleur": "c-mone", "courbe": 130},
    {"id": "banques_centrales-obligations", "de": "banques_centrales", "vers": "obligations", "base": 0.6,
     "couleur": "c-oblig", "courbe": -40},

    {"id": "fonds_pension-actions", "de": "fonds_pension", "vers": "actions", "base": 1.6, "couleur": "c-actions"},
    {"id": "fonds_pension-obligations", "de": "fonds_pension", "vers": "obligations", "base": 1.4, "couleur": "c-oblig"},
    {"id": "assureurs-obligations", "de": "assureurs", "vers": "obligations", "base": 1.7, "couleur": "c-oblig"},
    {"id": "assureurs-actions", "de": "assureurs", "vers": "actions", "base": 0.5, "couleur": "c-actions"},
    {"id": "gerants-actions", "de": "gerants", "vers": "actions", "base": 2.4, "couleur": "c-actions"},
    {"id": "gerants-obligations", "de": "gerants", "vers": "obligations", "base": 1.3, "couleur": "c-oblig"},
    {"id": "gerants-or", "de": "gerants", "vers": "or", "base": 0.25, "couleur": "c-or"},
    {"id": "hedge_funds-actions", "de": "hedge_funds", "vers": "actions", "base": 0.5, "couleur": "c-actions"},
    {"id": "hedge_funds-or", "de": "hedge_funds", "vers": "or", "base": 0.2, "couleur": "c-or"},
    {"id": "hedge_funds-crypto", "de": "hedge_funds", "vers": "crypto", "base": 0.25, "couleur": "c-crypto"},
]

# --- Le courant du moment : ce que nos prix disent de l'orientation de l'argent --------
#
# `mode` dit comment traduire la série en « la mer monte » :
#   prix  — la variation du cours, telle quelle ;
#   taux  — un taux qui baisse fait monter le prix des obligations (× duration).

COURANTS = {
    "actions": {"series": ["sp500", "stoxx50"], "mode": "prix",
                "lecture": "Les grandes Bourses sur le mois écoulé."},
    "obligations": {"series": ["us10y"], "mode": "taux",
                    "lecture": "Le taux américain 10 ans, traduit en prix : un taux qui baisse fait monter les obligations."},
    "or": {"series": ["or"], "mode": "prix", "lecture": "Le cours de l'once."},
    "crypto": {"series": ["bitcoin"], "mode": "prix", "lecture": "Le cours du bitcoin."},
    "monetaire": {"series": ["vix"], "mode": "prix",
                  "lecture": "La peur (VIX) : quand elle monte, l'argent se gare sur le monétaire."},
}


def _serie(session, code: str, points: int = 500) -> list[tuple[datetime.date, float]]:
    """Les `points` dernières clôtures d'un instrument, du plus ancien au plus récent."""
    instrument = session.scalars(select(Instrument).where(Instrument.code == code)).first()
    if instrument is None:
        return []
    rows = session.execute(
        select(PriceDaily.date, PriceDaily.close)
        .where(PriceDaily.instrument_id == instrument.id)
        .order_by(PriceDaily.date.desc())
        .limit(points)
    ).all()
    return [(row[0], row[1]) for row in reversed(rows)]


def _variations_glissantes(closes: list[float], mode: str) -> list[float]:
    """Toutes les variations sur `FENETRE_COURANT` séances, en « rendement de prix »."""
    out = []
    for i in range(FENETRE_COURANT, len(closes)):
        avant, apres = closes[i - FENETRE_COURANT], closes[i]
        if mode == "taux":
            # avant/apres sont des taux en % : −(Δtaux) × duration ≈ variation de prix
            out.append(-(apres - avant) / 100 * DURATION_10_ANS)
        elif avant > 0:
            out.append(apres / avant - 1)
    return out


def _souffle_serie(session, code: str, mode: str) -> dict | None:
    """La variation du mois écoulé, et son ampleur rapportée à l'habitude de la série.

    Le « souffle » est la variation divisée par la dispersion historique des
    variations du même horizon : un mois à +2 % sur les obligations n'a pas la
    même portée qu'un mois à +2 % sur le bitcoin.
    """
    serie = _serie(session, code)
    closes = [close for _, close in serie]
    variations = _variations_glissantes(closes, mode)
    # trois fenêtres au minimum pour que la dispersion veuille dire quelque chose
    if len(variations) < FENETRE_COURANT * 3:
        return None
    derniere = variations[-1]
    ecart = statistics.pstdev(variations)
    souffle = max(-2.5, min(2.5, derniere / ecart)) if ecart else 0.0
    return {"code": code, "variation": derniere, "souffle": souffle, "date": serie[-1][0]}


def courants(session) -> dict[str, dict]:
    """Pour chaque mer d'actifs : de quel côté l'argent a penché sur le mois écoulé."""
    out = {}
    for mer_id, spec in COURANTS.items():
        lectures = [s for s in (_souffle_serie(session, code, spec["mode"]) for code in spec["series"]) if s]
        if not lectures:
            continue
        out[mer_id] = {
            "mer": mer_id,
            "variation": sum(l["variation"] for l in lectures) / len(lectures),
            "souffle": sum(l["souffle"] for l in lectures) / len(lectures),
            "date": max(l["date"] for l in lectures),
            "series": [l["code"] for l in lectures],
            "lecture": spec["lecture"],
        }
    return out


def _multiplicateurs_du_jour(lectures: dict[str, dict]) -> dict[str, float]:
    """Traduit les courants en largeur de rivières.

    Une mer qui monte fort attire : ses rivières grossissent. Une mer qui chute
    franchement les inverse — l'argent en sort. Le facteur reste borné : on
    illustre une orientation, on ne prétend pas chiffrer un débit.
    """
    mult = {}
    for riviere in RIVIERES:
        lecture = lectures.get(riviere["vers"])
        if lecture is None:
            continue
        facteur = 1 + 0.55 * lecture["souffle"]
        mult[riviere["id"]] = round(max(-1.2, min(2.6, facteur)), 3)
    return mult


def _note_du_jour(lectures: dict[str, dict], noms: dict[str, str]) -> str:
    """La phrase qui raconte le courant dominant, en français simple."""
    if not lectures:
        return ("<strong>Pas encore de courant lisible.</strong> Il faut plusieurs mois de cours "
                "collectés pour situer le mois écoulé par rapport à l'habitude de chaque marché.")
    classees = sorted(lectures.values(), key=lambda l: -l["souffle"])
    haut, bas = classees[0], classees[-1]
    if haut["souffle"] < 0.4 and bas["souffle"] > -0.4:
        return ("<strong>Le bassin est calme.</strong> Aucune mer n'attire ni ne repousse "
                "franchement l'argent sur le mois écoulé : les rivières coulent à leur débit "
                "habituel.")
    return (f"<strong>Le mois écoulé penche vers « {noms[haut['mer']]} ».</strong> "
            f"C'est la mer qui monte le plus par rapport à ses habitudes, pendant que "
            f"« {noms[bas['mer']]} » est la moins portée. Largeur des rivières : cette "
            f"orientation lue dans les cours — pas un relevé de virements.")


def _mesures_13f(session) -> dict[str, dict]:
    """Ce que notre base mesure vraiment, par type de gérant : le dernier 13F de chacun."""
    par_type: dict[str, dict] = {}
    for manager in session.scalars(select(AssetManager).where(AssetManager.cik_sec != "")):
        for fund in manager.funds:
            snapshot = session.scalars(
                select(FundSnapshot)
                .where(FundSnapshot.fund_id == fund.id)
                .order_by(FundSnapshot.date.desc())
            ).first()
            if snapshot is None or not snapshot.encours:
                continue
            entree = par_type.setdefault(manager.type, {"total_td": 0.0, "gerants": [], "date": snapshot.date})
            entree["total_td"] += snapshot.encours / 1e12
            entree["gerants"].append(manager.nom)
            entree["date"] = max(entree["date"], snapshot.date)
    return par_type


def _fr(valeur: float, decimales: int = 0) -> str:
    """12345.6 → « 12 345,6 » — à n'appliquer qu'au nombre, jamais à la phrase entière."""
    return f"{valeur:,.{decimales}f}".replace(",", " ").replace(".", ",")


def _stocks_mesures(session) -> dict[str, dict]:
    """Les deux mers qu'on sait valoriser depuis nos propres cours : l'or et le bitcoin."""
    out = {}
    serie_or = _serie(session, "or", points=1)
    if serie_or:
        date, cours = serie_or[-1]
        out["or"] = {
            "stock": STOCK_OR_TONNES * ONCES_PAR_TONNE * cours / 1e12,
            "date": date,
            "detail": (f"{_fr(STOCK_OR_TONNES)} tonnes extraites (World Gold Council) "
                       f"× {_fr(cours)} $ l'once — cours de notre base"),
        }
    serie_btc = _serie(session, "bitcoin", points=1)
    if serie_btc:
        date, cours = serie_btc[-1]
        out["crypto"] = {
            "stock": BITCOINS_EN_CIRCULATION * cours / 1e12,
            "date": date,
            "detail": (f"{_fr(BITCOINS_EN_CIRCULATION / 1e6, 1)} millions de bitcoins en circulation "
                       f"× {_fr(cours)} $ — cours de notre base"),
        }
    return out


SCENARIOS_PEDAGOGIQUES = {
    "calme": {
        "label": "Journée calme",
        "nature": "pedagogique",
        "note": "<strong>Journée calme.</strong> L'épargne des ménages coule régulièrement vers les "
                "collecteurs, qui la répartissent entre les grandes mers. Rien ne déborde, rien ne s'assèche.",
        "mult": {},
    },
    "qe": {
        "label": "La banque centrale injecte",
        "nature": "pedagogique",
        "note": "<strong>La banque centrale injecte (« QE »).</strong> Elle crée de la monnaie et achète "
                "des obligations : sa rivière gonfle d'un coup. L'argent déplacé cherche du rendement "
                "ailleurs — les rivières vers les actions grossissent à leur tour.",
        "mult": {"banques_centrales-obligations": 8, "fonds_pension-actions": 1.5, "assureurs-actions": 1.5,
                 "gerants-actions": 1.5, "hedge_funds-actions": 1.4, "menages-monetaire": 1.2},
    },
    "riskoff": {
        "label": "Fuite vers la sécurité",
        "nature": "pedagogique",
        "note": "<strong>Fuite vers la sécurité.</strong> Une peur traverse les marchés : les rivières vers "
                "les actions et le bitcoin <strong>s'inversent</strong> (l'argent en sort), pendant que l'or, "
                "les obligations et le monétaire reçoivent des torrents.",
        "mult": {"fonds_pension-actions": -0.7, "assureurs-actions": -0.7, "gerants-actions": -0.7,
                 "hedge_funds-actions": -0.9, "hedge_funds-crypto": -0.9, "gerants-or": 3, "hedge_funds-or": 3,
                 "fonds_pension-obligations": 1.8, "assureurs-obligations": 1.8, "gerants-obligations": 1.8,
                 "menages-monetaire": 2.2, "menages-hedge_funds": 0.5},
    },
}


def bassin(session) -> dict:
    """Le bassin complet : les lacs, les rivières, et le courant lu dans nos données."""
    mesures_13f = _mesures_13f(session)
    stocks_mesures = _stocks_mesures(session)
    noms = {lac["id"]: lac["nom"] for lac in LACS}

    lacs = []
    for modele in LACS:
        lac = {k: v for k, v in modele.items() if k != "mesure_13f"}
        mesure = stocks_mesures.get(lac["id"])
        if mesure:
            lac["stock"] = round(mesure["stock"], 2)
            lac["provenance"] = "mesure"
            lac["mesure"] = {"detail": mesure["detail"], "date": mesure["date"].isoformat()}
        type_13f = modele.get("mesure_13f")
        if type_13f and type_13f in mesures_13f:
            part = mesures_13f[type_13f]
            lac["part_mesuree"] = {
                "stock": round(part["total_td"], 2),
                "date": part["date"].isoformat(),
                "detail": ("actions américaines déclarées à la SEC (13F) par "
                           + ", ".join(sorted(part["gerants"]))),
            }
        lacs.append(lac)

    lectures = courants(session)
    scenarios = {
        "aujourdhui": {
            "label": "Aujourd'hui",
            "nature": "donnees",
            "note": _note_du_jour(lectures, noms),
            "mult": _multiplicateurs_du_jour(lectures),
        },
        **SCENARIOS_PEDAGOGIQUES,
    }

    return {
        "genere_le": datetime.date.today().isoformat(),
        "lacs": lacs,
        "rivieres": RIVIERES,
        "scenarios": scenarios,
        "courants": [
            {**lecture, "nom": noms[mer_id], "date": lecture["date"].isoformat(),
             "variation_pct": round(lecture["variation"] * 100, 2),
             "souffle": round(lecture["souffle"], 2)}
            for mer_id, lecture in sorted(lectures.items(), key=lambda kv: -kv[1]["souffle"])
        ],
        "fenetre_seances": FENETRE_COURANT,
    }
