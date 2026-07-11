"""Le périmètre suivi — chaque instrument avec sa source et son habillage français."""

# family: indices | actions | taux | credit | devises | matieres | crypto | volatilite
# source: yahoo | fred
INSTRUMENTS = [
    # --- Laboratoire PEA ---
    {"code": "pea_sp500_psp5", "name": "Amundi PEA S&P 500 UCITS ETF Acc", "family": "pea", "source": "yahoo", "symbol": "PSP5.PA", "unit": "€", "decimals": 2},
    {"code": "pea_world_wpea", "name": "iShares MSCI World Swap PEA UCITS ETF", "family": "pea", "source": "yahoo", "symbol": "WPEA.PA", "unit": "€", "decimals": 2},
    {"code": "pea_nasdaq_pust", "name": "Amundi PEA Nasdaq-100 UCITS ETF Acc", "family": "pea", "source": "yahoo", "symbol": "PUST.PA", "unit": "€", "decimals": 2},
    {"code": "pea_europe_pceu", "name": "Amundi PEA MSCI Europe UCITS ETF Acc", "family": "pea", "source": "yahoo", "symbol": "PCEU.PA", "unit": "€", "decimals": 2},
    # --- Indices actions ---
    {"code": "sp500",    "name": "S&P 500 (États-Unis)",        "family": "indices", "source": "yahoo", "symbol": "^GSPC",     "unit": "pts",  "decimals": 0},
    {"code": "nasdaq",   "name": "Nasdaq Composite",             "family": "indices", "source": "yahoo", "symbol": "^IXIC",     "unit": "pts",  "decimals": 0},
    {"code": "stoxx50",  "name": "Euro Stoxx 50",                "family": "indices", "source": "yahoo", "symbol": "^STOXX50E", "unit": "pts",  "decimals": 0},
    {"code": "cac40",    "name": "CAC 40 (France)",              "family": "indices", "source": "yahoo", "symbol": "^FCHI",     "unit": "pts",  "decimals": 0},
    {"code": "dax",      "name": "DAX (Allemagne)",              "family": "indices", "source": "yahoo", "symbol": "^GDAXI",    "unit": "pts",  "decimals": 0},
    {"code": "ftse100",  "name": "FTSE 100 (Royaume-Uni)",       "family": "indices", "source": "yahoo", "symbol": "^FTSE",     "unit": "pts",  "decimals": 0},
    {"code": "nikkei",   "name": "Nikkei 225 (Japon)",           "family": "indices", "source": "yahoo", "symbol": "^N225",     "unit": "pts",  "decimals": 0},
    {"code": "shanghai", "name": "Shanghai Composite (Chine)",   "family": "indices", "source": "yahoo", "symbol": "000001.SS", "unit": "pts",  "decimals": 0},
    {"code": "emergents","name": "Émergents (ETF EEM)",          "family": "indices", "source": "yahoo", "symbol": "EEM",       "unit": "$",    "decimals": 2},
    # --- Actions phares ---
    {"code": "apple",    "name": "Apple",                        "family": "actions", "source": "yahoo", "symbol": "AAPL",   "unit": "$", "decimals": 2},
    {"code": "nvidia",   "name": "Nvidia",                       "family": "actions", "source": "yahoo", "symbol": "NVDA",   "unit": "$", "decimals": 2},
    {"code": "microsoft","name": "Microsoft",                    "family": "actions", "source": "yahoo", "symbol": "MSFT",   "unit": "$", "decimals": 2},
    {"code": "lvmh",     "name": "LVMH (France)",                "family": "actions", "source": "yahoo", "symbol": "MC.PA",  "unit": "€", "decimals": 2},
    {"code": "total",    "name": "TotalEnergies (France)",       "family": "actions", "source": "yahoo", "symbol": "TTE.PA", "unit": "€", "decimals": 2},
    {"code": "asml",     "name": "ASML (Pays-Bas)",              "family": "actions", "source": "yahoo", "symbol": "ASML",   "unit": "$", "decimals": 2},
    {"code": "toyota",   "name": "Toyota (Japon)",               "family": "actions", "source": "yahoo", "symbol": "7203.T", "unit": "¥", "decimals": 0},
    # --- Taux ---
    {"code": "us10y",    "name": "Taux US 10 ans",               "family": "taux", "source": "fred", "symbol": "DGS10",  "unit": "%", "decimals": 2},
    {"code": "us2y",     "name": "Taux US 2 ans",                "family": "taux", "source": "fred", "symbol": "DGS2",   "unit": "%", "decimals": 2},
    {"code": "pente_us", "name": "Pente US (10 ans − 2 ans)",    "family": "taux", "source": "fred", "symbol": "T10Y2Y", "unit": "pt", "decimals": 2},
    # --- Crédit ---
    {"code": "spread_ig","name": "Spread crédit sain (IG, États-Unis)",    "family": "credit", "source": "fred", "symbol": "BAMLC0A0CM",   "unit": "pt", "decimals": 2},
    {"code": "spread_hy","name": "Spread crédit risqué (High Yield, É-U)", "family": "credit", "source": "fred", "symbol": "BAMLH0A0HYM2", "unit": "pt", "decimals": 2},
    # --- Devises ---
    {"code": "eurusd",   "name": "Euro / Dollar",                "family": "devises", "source": "yahoo", "symbol": "EURUSD=X", "unit": "",    "decimals": 4},
    {"code": "usdjpy",   "name": "Dollar / Yen",                 "family": "devises", "source": "yahoo", "symbol": "JPY=X",    "unit": "",    "decimals": 2},
    {"code": "gbpusd",   "name": "Livre / Dollar",               "family": "devises", "source": "yahoo", "symbol": "GBPUSD=X", "unit": "",    "decimals": 4},
    {"code": "usdcny",   "name": "Dollar / Yuan",                "family": "devises", "source": "yahoo", "symbol": "CNY=X",    "unit": "",    "decimals": 3},
    {"code": "dxy",      "name": "Indice dollar (DXY)",          "family": "devises", "source": "yahoo", "symbol": "DX-Y.NYB", "unit": "pts", "decimals": 1},
    # --- Matières premières ---
    {"code": "brent",    "name": "Pétrole Brent",                "family": "matieres", "source": "yahoo", "symbol": "BZ=F", "unit": "$/baril",     "decimals": 2},
    {"code": "wti",      "name": "Pétrole WTI",                  "family": "matieres", "source": "yahoo", "symbol": "CL=F", "unit": "$/baril",     "decimals": 2},
    {"code": "gaz",      "name": "Gaz naturel (Henry Hub)",      "family": "matieres", "source": "yahoo", "symbol": "NG=F", "unit": "$/MMBtu",     "decimals": 2},
    {"code": "or",       "name": "Or",                           "family": "matieres", "source": "yahoo", "symbol": "GC=F", "unit": "$/once",      "decimals": 0},
    {"code": "argent",   "name": "Argent",                       "family": "matieres", "source": "yahoo", "symbol": "SI=F", "unit": "$/once",      "decimals": 2},
    {"code": "cuivre",   "name": "Cuivre",                       "family": "matieres", "source": "yahoo", "symbol": "HG=F", "unit": "$/livre",     "decimals": 2},
    {"code": "ble",      "name": "Blé",                          "family": "matieres", "source": "yahoo", "symbol": "ZW=F", "unit": "¢/boisseau",  "decimals": 0},
    {"code": "mais",     "name": "Maïs",                         "family": "matieres", "source": "yahoo", "symbol": "ZC=F", "unit": "¢/boisseau",  "decimals": 0},
    # --- Crypto ---
    {"code": "bitcoin",  "name": "Bitcoin",                      "family": "crypto", "source": "yahoo", "symbol": "BTC-USD", "unit": "$", "decimals": 0},
    {"code": "ethereum", "name": "Ethereum",                     "family": "crypto", "source": "yahoo", "symbol": "ETH-USD", "unit": "$", "decimals": 0},
    # --- Peur & volatilité ---
    {"code": "vix",      "name": "VIX (peur sur les actions)",   "family": "volatilite", "source": "yahoo", "symbol": "^VIX",  "unit": "pts", "decimals": 1},
    {"code": "move",     "name": "MOVE (peur sur les taux)",     "family": "volatilite", "source": "yahoo", "symbol": "^MOVE", "unit": "pts", "decimals": 1},
]

# --- Le chantier fonds (docs/SPEC-FONDS.md + docs/RECENSEMENT-FONDS.md) ---
# type: boutique (PDF mensuels, collecte en F3) | conviction_13f | geant_13f (EDGAR)
# Pour un déclarant 13F, le « fonds » est son portefeuille agrégé d'actions US.
GERANTS = [
    # Conviction américaine — portefeuilles courts, très lisibles
    {"slug": "berkshire", "nom": "Berkshire Hathaway", "pays": "États-Unis", "type": "conviction_13f",
     "cik_sec": "0001067983", "site_web": "https://www.berkshirehathaway.com",
     "blurb": "Warren Buffett — une quarantaine de lignes, l'anti-indice.",
     "fonds": [{"slug": "berkshire-13f", "nom": "Portefeuille actions US (13F)", "devise": "USD"}]},
    {"slug": "pershing-square", "nom": "Pershing Square", "pays": "États-Unis", "type": "conviction_13f",
     "cik_sec": "0001336528", "site_web": "https://pershingsquareholdings.com",
     "blurb": "Bill Ackman — une dizaine de lignes, concentration extrême.",
     "fonds": [{"slug": "pershing-13f", "nom": "Portefeuille actions US (13F)", "devise": "USD"}]},
    {"slug": "fundsmith", "nom": "Fundsmith", "pays": "Royaume-Uni", "type": "conviction_13f",
     "cik_sec": "0001569205", "site_web": "https://www.fundsmith.co.uk",
     "blurb": "Terry Smith — qualité/croissance, « n'achetez que de bonnes entreprises ».",
     "fonds": [{"slug": "fundsmith-13f", "nom": "Portefeuille actions US (13F)", "devise": "USD"}]},
    {"slug": "scion", "nom": "Scion Asset Management", "pays": "États-Unis", "type": "conviction_13f",
     "cik_sec": "0001649339", "site_web": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001649339",
     "blurb": "Michael Burry (« The Big Short ») — petit portefeuille, paris tranchés.",
     "fonds": [{"slug": "scion-13f", "nom": "Portefeuille actions US (13F)", "devise": "USD"}]},
    # Les géants — quasi indiciels, on ne garde que le sommet de l'iceberg
    {"slug": "blackrock", "nom": "BlackRock", "pays": "États-Unis", "type": "geant_13f",
     # nouveau CIK depuis la réorganisation en holding d'octobre 2024
     "cik_sec": "0002012383", "site_web": "https://www.blackrock.com",
     "blurb": "Le plus gros gérant du monde (~11 500 Md$) — il possède un peu de tout.",
     "fonds": [{"slug": "blackrock-13f", "nom": "Portefeuille actions US (13F, top 50)", "devise": "USD"}]},
    {"slug": "vanguard", "nom": "Vanguard", "pays": "États-Unis", "type": "geant_13f",
     "cik_sec": "0000102909", "site_web": "https://www.vanguard.com",
     "blurb": "Le pionnier de la gestion indicielle à bas coût.",
     "fonds": [{"slug": "vanguard-13f", "nom": "Portefeuille actions US (13F, top 50)", "devise": "USD"}]},
    {"slug": "state-street", "nom": "State Street", "pays": "États-Unis", "type": "geant_13f",
     "cik_sec": "0000093751", "site_web": "https://www.ssga.com",
     "blurb": "L'inventeur de l'ETF (SPDR), troisième pilier du trio indiciel.",
     "fonds": [{"slug": "state-street-13f", "nom": "Portefeuille actions US (13F, top 50)", "devise": "USD"}]},
    {"slug": "fidelity", "nom": "Fidelity (FMR)", "pays": "États-Unis", "type": "geant_13f",
     "cik_sec": "0000315066", "site_web": "https://www.fidelity.com",
     "blurb": "Le géant de la gestion active américaine.",
     "fonds": [{"slug": "fidelity-13f", "nom": "Portefeuille actions US (13F, top 50)", "devise": "USD"}]},
    # Boutiques françaises — collecte PDF en phase F3
    {"slug": "moneta", "nom": "Moneta AM", "pays": "France", "type": "boutique",
     "site_web": "https://www.moneta.fr",
     "blurb": "Référence du stock-picking France, reporting mensuel très riche.",
     "fonds": [{"slug": "moneta-multi-caps", "nom": "Moneta Multi Caps", "isin": "FR0010298596",
                "strategie": "Actions France, toutes tailles", "note_source": "Fiche + lettre mensuelles PDF, URL prévisible"}]},
    {"slug": "independance-am", "nom": "Indépendance AM", "pays": "France", "type": "boutique",
     "site_web": "https://www.independance-am.com",
     "blurb": "Small caps value — l'un des meilleurs historiques d'Europe.",
     "fonds": [{"slug": "independance-france-small", "nom": "Indépendance France Small & Mid", "isin": "LU0131510165",
                "strategie": "Petites valeurs françaises", "note_source": "Reporting mensuel PDF daté (WordPress)"}]},
    {"slug": "amiral-gestion", "nom": "Amiral Gestion", "pays": "France", "type": "boutique",
     "site_web": "https://www.amiralgestion.com",
     "blurb": "Value, petites capitalisations, lettres de gestion détaillées.",
     "fonds": [{"slug": "sextant-pme", "nom": "Sextant PME",
                "strategie": "PME européennes", "note_source": "Page publication stable par fonds/part"},
               {"slug": "sextant-grand-large", "nom": "Sextant Grand Large",
                "strategie": "Flexible international", "note_source": "Page publication stable par fonds/part"}]},
    {"slug": "carmignac", "nom": "Carmignac", "pays": "France", "type": "boutique",
     "site_web": "https://www.carmignac.fr",
     "blurb": "Gestion globale, lettre du gérant trimestrielle abondante.",
     "fonds": [{"slug": "carmignac-investissement", "nom": "Carmignac Investissement", "isin": "FR0010148981",
                "strategie": "Actions internationales", "note_source": "Page documents par fonds, rapport mensuel"}]},
    {"slug": "lfde", "nom": "La Financière de l'Échiquier", "pays": "France", "type": "boutique",
     "site_web": "https://www.lfde.com",
     "blurb": "Maison historique du stock-picking français.",
     "fonds": [{"slug": "echiquier-agressor", "nom": "Echiquier Agressor",
                "strategie": "Actions européennes opportunistes", "note_source": "Factsheet cdn.lfde.com à URL stable écrasée chaque mois — archivage obligatoire"}]},
    {"slug": "comgest", "nom": "Comgest", "pays": "France", "type": "boutique",
     "site_web": "https://www.comgest.com",
     "blurb": "Qualité/croissance, discipline célèbre, horizon long.",
     "fonds": [{"slug": "comgest-growth-europe", "nom": "Comgest Growth Europe", "isin": "IE0004766675",
                "strategie": "Actions européennes qualité/croissance", "note_source": "Monthly report derrière porte de profil investisseur"}]},
]

# Combien de lignes on conserve par snapshot 13F
TOP_N_13F = {"geant_13f": 50, "conviction_13f": 200}

FAMILIES = {
    "pea":        {"label": "Laboratoire PEA",     "blurb": "Supports vérifiés comme éligibles au PEA, étudiés sans passage d'ordre."},
    "indices":    {"label": "Indices actions",      "blurb": "La météo des Bourses mondiales."},
    "actions":    {"label": "Actions phares",       "blurb": "Quelques champions pour incarner les mouvements."},
    "taux":       {"label": "Taux d'intérêt",       "blurb": "Le prix du temps — le marché le plus puissant du monde."},
    "credit":     {"label": "Crédit",               "blurb": "Le pouls : l'écart de taux exigé des emprunteurs risqués."},
    "devises":    {"label": "Devises",              "blurb": "9 600 Md$ échangés par jour — le torrent."},
    "matieres":   {"label": "Matières premières",   "blurb": "L'économie physique : énergie, métaux, céréales."},
    "crypto":     {"label": "Crypto",               "blurb": "Jeune, petit, très sensible à la liquidité."},
    "volatilite": {"label": "Peur & volatilité",    "blurb": "Les sismographes de la machine."},
}

PEA_LAB_PRODUCTS = {
    "pea_sp500_psp5": {
        "label": "Amundi PEA S&P 500 UCITS ETF Acc",
        "ticker": "PSP5",
        "isin": "FR0011871128",
        "index": "S&P 500 Net Total Return",
        "ongoing_cost_pct": 0.12,
        "inception": "2014-05-20",
        "exposure": "500 grandes entreprises américaines",
        "replication": "Synthétique",
        "source_url": "https://www.amundietf.fr/fr/professionnels/produits/equity/amundi-pea-sp-500-ucits-etf-acc/fr0011871128",
    },
    "pea_world_wpea": {
        "label": "iShares MSCI World Swap PEA UCITS ETF",
        "ticker": "WPEA",
        "isin": "IE0002XZSHO1",
        "index": "MSCI World Net Total Return",
        "ongoing_cost_pct": 0.20,
        "inception": "2024-03-26",
        "exposure": "Grandes et moyennes entreprises des marchés développés",
        "replication": "Synthétique",
        "source_url": "https://www.blackrock.com/fr/particuliers/products/335178/ishares-msci-world-swap-pea-ucits-etf",
    },
    "pea_nasdaq_pust": {
        "label": "Amundi PEA Nasdaq-100 UCITS ETF Acc",
        "ticker": "PUST",
        "isin": "FR0011871110",
        "index": "Nasdaq-100",
        "ongoing_cost_pct": 0.30,
        "inception": "2014-05-20",
        "exposure": "100 grandes entreprises non financières cotées au Nasdaq (tech US concentrée)",
        "replication": "Synthétique",
        "source_url": "https://www.amundietf.fr/fr/professionnels/produits/equity/amundi-pea-nasdaq100-ucits-etf-acc/fr0011871110",
    },
    "pea_europe_pceu": {
        "label": "Amundi PEA MSCI Europe UCITS ETF Acc",
        "ticker": "PCEU",
        "isin": "FR0013412038",
        "index": "MSCI Europe Net Total Return",
        "ongoing_cost_pct": 0.15,
        "inception": "2019-04-25",
        "exposure": "Grandes et moyennes entreprises des marchés développés européens",
        "replication": "Synthétique",
        "source_url": "https://www.amundietf.fr/fr/particuliers/produits/equity/amundi-pea-msci-europe-ucits-etf-eur-cd/fr0013412038",
    },
}
