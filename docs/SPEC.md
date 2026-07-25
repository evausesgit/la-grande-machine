# Spécification — La Grande Machine (l'observatoire)

> Version 1 — à valider par Eva avant construction.
> Décisions prises ensemble le 6 juillet 2026.

## 1. Ce qu'on construit

Un **observatoire public de la machine financière** : chaque matin, l'app raconte
ce qui a bougé sur les marchés, **qui** a probablement bougé, et **pourquoi** —
chaque mouvement relié à ses causes via la carte des dépendances, en français
clair pour adultes curieux — pédagogie ludique, jargon traduit. L'historique
s'accumule pour voir les évolutions.

**URL** : https://themachine.ia-do-it.com (Coolify, VPS d'Eva)
**Code** : GitHub public (aucun secret dans le repo)
**Avertissement affiché** : outil pédagogique, pas un conseil d'investissement.

## 2. Périmètre suivi (v1 — « tout dès le départ »)

### Quotidien (prix, ~40 séries)

| Famille | Séries | Source |
|---|---|---|
| Indices actions | S&P 500, Nasdaq, Euro Stoxx 50, CAC 40, DAX, FTSE 100, Nikkei 225, Shanghai, MSCI Émergents (proxy EEM) | Yahoo |
| Actions phares | Apple, Nvidia, Microsoft, LVMH, TotalEnergies, ASML, Toyota | Yahoo |
| Taux souverains 10 ans | États-Unis, Allemagne, France, Italie, Japon + US 2 ans | FRED (États-Unis) |
| Spreads dérivés | OAT−Bund, US 10a−2a (pente), spreads crédit IG & High Yield | FRED (BAML) |
| Devises | EUR/USD, USD/JPY, GBP/USD, USD/CNY, indice dollar DXY | Yahoo |
| Matières premières | Brent, WTI, gaz naturel (Henry Hub + TTF si dispo), or, argent, cuivre, blé, maïs | Yahoo |
| Crypto | Bitcoin, Ethereum | Yahoo (CoinGecko en secours) |
| Peur & volatilité | VIX (actions), MOVE si accessible (obligations) | stooq / FRED |

### Hebdomadaire / différé (les acteurs — le « qui »)

| Donnée | Ce qu'elle révèle | Source | Fréquence |
|---|---|---|---|
| CFTC Commitments of Traders | Positions des hedge funds, commerciaux, gérants sur les futures (or, pétrole, blé, devises, taux…) | CFTC (fichiers publics) | hebdo (vendredi, données mardi) |
| Bilan de la Fed (WALCL) et de la BCE | La création/destruction de liquidité centrale | FRED / BCE SDW | hebdo |
| Flux ETF approximés | Entrées/sorties sur SPY, TLT, GLD, HYG… (variation parts × prix) | émetteurs / Yahoo | quotidien, qualité variable |
| SEC 13F | Portefeuilles des gros gérants US | SEC EDGAR | trimestriel (+45 j) |

### Contexte (le calendrier)

Calendrier économique du jour (décisions banques centrales, inflation, emploi) —
source à confirmer en phase 2 (scraping léger ou API gratuite).

## 3. Le moteur du « pourquoi » (le cœur)

Chaque mouvement est expliqué par trois couches croisées :

1. **L'ampleur réelle** — variation du jour ÷ volatilité 30 jours (z-score).
   Un −0,5 % sur le VIX n'est rien ; un −0,5 % sur EUR/USD est un événement.
   Le brief ne parle que de ce qui a *vraiment* bougé.
2. **La mécanique** — la carte des dépendances (graphe en base : nœuds, arêtes
   signées, mécanismes en français — reprise de la v1) + corrélations roulantes
   90 jours calculées sur nos données. Si taux US ↑ et or ↓ le même jour,
   la machine sait relier les deux et citer le mécanisme.
3. **L'actualité** — une recherche web du matin (guidée par ce qui a bougé)
   identifie l'événement déclencheur : décision de banque centrale, chiffre
   d'inflation, choc géopolitique. Avec liens vers les sources.

### Qui écrit le brief ?

**Un job planifié dans le container de l'app** (`app/scheduler.py`, 6h45 Europe/Paris,
`app/brief_writer.py`) :
1. calcule les mouvements du jour en interne (même fonction que `GET /api/journee`) ;
2. délègue la recherche d'actualités et la rédaction à `codex exec` (CLI OpenAI Codex,
   accès shell + réseau dans son bac à sable, `--output-schema` pour forcer la forme
   JSON) — authentifié via le login ChatGPT d'Eva monté en lecture seule dans le
   container (`CODEX_AUTH_PATH`, voir `compose.yaml`) plutôt qu'une clé API. Le process
   codex tourne avec un environnement restreint (pas de `DB_PASSWORD`/`ADMIN_TOKEN`),
   pour limiter ce qu'un accès shell+réseau non supervisé pourrait exfiltrer ;
3. publie directement en base via la même logique que `POST /api/brief`.

Historique : la v1 de ce chantier utilisait une routine planifiée externe (claude.ai
`/schedule`, hors du container). Abandonnée le 16 juillet 2026 : son sandbox réseau
n'autorise que des domaines explicitement approuvés, et personne n'est présent pour
approuver l'accès à `lamachine.ia-do-it.com` lors d'une exécution automatique — chaque
appel (lecture des données comme publication) échouait silencieusement. Le container
de l'app a un accès réseau sortant qui fonctionne déjà (Yahoo, FRED, EDGAR), d'où le
déplacement de toute la chaîne à l'intérieur. `POST /api/brief/generer` (jeton admin)
permet de déclencher la rédaction à la demande, pour tester ou rattraper une journée
manquée.

## 4. Le brief du matin (format)

1. **Le titre du jour** — une phrase : « Le pétrole s'enflamme et réveille les taux ».
2. **Ce qui a bougé** — les 5–8 mouvements les plus significatifs (z-score), avec tuiles colorées.
3. **Pourquoi** — le récit causal : événement → chaîne de transmission → conséquences, avec la mini-carte des dépendances du jour mise en évidence et les liens sources.
4. **Le coin des acteurs** — les chiffres et les voix. Les chiffres : quand un
   rapport COT/13F/bilan BC est tombé, qui s'est renforcé, qui a fui (phase 3).
   Les voix : ce que disent les gérants dans leurs notes publiques — BlackRock
   Investment Institute (hebdo), Amundi Investment Institute, PIMCO, mémos
   d'Howard Marks (Oaktree), Vanguard, JPMorgan — quand une note éclaire un
   mouvement du jour. Règles : citation courte reformulée + attribution + lien
   (droit de citation), et toujours présentées comme des opinions de gérants,
   jamais comme des faits.
5. **À surveiller aujourd'hui** — le calendrier éco.
6. **Le coin des curieux** — une notion pédagogique liée à l'actualité du jour (rotation du lexique v1).

## 5. Les pages de l'app

| Route | Contenu |
|---|---|
| `/` | Le brief du jour + tuiles des marchés (vue « instrument de bord ») |
| `/carte` | La carte interactive des dépendances (v1 enrichie), branchée sur les données réelles : les arêtes s'allument selon les corrélations récentes |
| `/marche/{code}` | Historique d'une série, événements marquants annotés, briefs qui la mentionnent |
| `/acteurs` | Les positions COT par type d'acteur, évolution des bilans de banques centrales |
| `/archives` | Tous les briefs passés, navigables par date — « le film » |
| `/comprendre` | La v1 pédagogique (réservoirs, circuit, géants, lexique) |
| `/flux` | Le bassin versant des grandes masses : épargne → collecteurs → mers d'actifs. Scénario « Aujourd'hui » calculé depuis la base (le « souffle » de chaque mer sur 30 séances pilote la largeur des rivières) + 3 scénarios pédagogiques. Chaque chiffre porte sa provenance : mesuré / lu / ordre de grandeur documenté. JSON : `GET /api/flux` |

## 6. Architecture technique

```
la-grande-machine/
├── app/                  # FastAPI : API + rendu des pages (Jinja2)
│   ├── main.py
│   ├── collectors/       # stooq, FRED, CFTC, CoinGecko… (un module par source)
│   ├── engine/           # z-scores, corrélations, graphe des dépendances
│   ├── models.py         # SQLAlchemy
│   └── templates/ static/  # front vanilla JS (charte graphique v1, palette validée)
├── viz/index.html        # la v1 statique (conservée, servie sous /comprendre)
├── docs/SPEC.md           # ce document
├── Dockerfile
└── compose.yaml           # app + PostgreSQL (déployé par Coolify)
```

- **Python 3.12 / FastAPI / SQLAlchemy / PostgreSQL 16.**
- **Collecte** : APScheduler dans le container — 23h00 Paris (clôtures US) et 6h15 Paris (Asie + pré-calculs du brief). Chaque collecteur est indépendant : une source en panne n'empêche pas les autres (statut visible sur `/api/sante`).
- **Secrets** (jeton du brief, éventuelles clés) : variables d'environnement Coolify uniquement.
- **Charte graphique** : celle de la v1 (papier chaud/sombre, accent laiton, palette catégorielle validée daltonisme).

## 7. Honnêteté des données (affichée dans l'app)

- **Constat du 6 juillet 2026** : stooq est passé derrière un défi anti-robot JavaScript,
  inutilisable côté serveur. **Yahoo Finance (API chart, non officielle) devient la source
  principale** — stable avec un User-Agent de navigateur, mais sans garantie contractuelle :
  le risque est assumé et surveillé via `/api/sante`.
- Taux souverains hors États-Unis (Bund, OAT, BTP, JGB quotidiens) : pas encore de source
  gratuite fiable identifiée — à résoudre en phase 3 (piste : API BCE).
- Le « qui achète/vend » public est **différé** (COT : 3 jours ; 13F : 45 jours) —
  l'app affiche toujours la date de fraîcheur de chaque donnée.
- Après 2 semaines d'exploitation : **rapport des limites** du gratuit et de ce
  qu'une API payante apporterait (fiabilité, intraday, flux ETF propres).

## 8. Phases de construction

| Phase | Livrable | Critère de fin |
|---|---|---|
| **P1 — Squelette** | App déployée sur Coolify à l'URL cible, DB, collecte des prix quotidiens, page `/` avec tuiles | les prix du jour s'affichent en ligne |
| **P2 — Le moteur** | z-scores, corrélations, graphe des dépendances en base, `GET /api/journee`, `POST /api/brief`, routine matinale → **premier brief automatique**. La routine : un cron local lance `claude -p` avec la mission `scripts/brief-du-matin.md` (lit `/api/journee`, cherche les causes, consulte les notes de gérants, publie via `POST /api/brief`). Premier brief publié à la main le 7 juillet 2026. | 5 briefs matinaux consécutifs sans intervention |
| **P3 — Les acteurs** | Collecteurs COT + bilans BC + flux ETF, page `/acteurs`, section « le coin des acteurs » dans le brief | un vendredi avec COT intégré au brief |
| **P4 — La carte vivante** | `/carte` interactive branchée sur les corrélations réelles, `/marche/{code}`, `/archives` | la carte reflète les données de la veille |
| **P5 — Bilan** | Rapport des limites données gratuites + backlog v2 (alertes, version anglaise, études de crises) | décision ensemble sur la suite |

## 9. Ce qui n'est PAS dans la v1 (backlog assumé)

Alertes temps réel, données intraday, version anglaise, comptes utilisateurs,
flux RSS/email du brief, études de cas historiques (2008, 2020, 2022),
positions détaillées par fonds (13F exploité au-delà de l'affichage brut)
— **devenu un chantier à part entière le 8 juillet 2026 : voir [SPEC-FONDS.md](SPEC-FONDS.md)**.
