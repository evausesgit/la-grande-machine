"""Le périmètre suivi — chaque instrument avec sa source et son habillage français."""

# family: indices | actions | taux | credit | devises | matieres | crypto | volatilite
# source: yahoo | fred
INSTRUMENTS = [
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

FAMILIES = {
    "indices":    {"label": "Indices actions",      "blurb": "La météo des Bourses mondiales."},
    "actions":    {"label": "Actions phares",       "blurb": "Quelques champions pour incarner les mouvements."},
    "taux":       {"label": "Taux d'intérêt",       "blurb": "Le prix du temps — le marché le plus puissant du monde."},
    "credit":     {"label": "Crédit",               "blurb": "Le pouls : l'écart de taux exigé des emprunteurs risqués."},
    "devises":    {"label": "Devises",              "blurb": "9 600 Md$ échangés par jour — le torrent."},
    "matieres":   {"label": "Matières premières",   "blurb": "L'économie physique : énergie, métaux, céréales."},
    "crypto":     {"label": "Crypto",               "blurb": "Jeune, petit, très sensible à la liquidité."},
    "volatilite": {"label": "Peur & volatilité",    "blurb": "Les sismographes de la machine."},
}
