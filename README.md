# La Grande Machine

Comprendre, visualiser et suivre les flux financiers mondiaux — qui achète, qui vend,
quels actifs, et surtout **pourquoi les prix montent ou descendent**.

## La vision

1. **La carte** — les acteurs (gérants d'actifs, hedge funds, assureurs, fonds de pension,
   fonds souverains, banques centrales), les actifs (actions, obligations, devises,
   matières premières), et les chaînes de transmission entre eux.
2. **Le film** — un suivi régulier des prix et des flux : ce qui a bougé, de combien,
   et l'explication en français simple de ce qui l'a causé.
3. **La transmission** — un guide pour adultes curieux, sans jargon, qui garde
   le plaisir d'apprendre : chaque mouvement relié à sa cause, chaque cause à
   ses conséquences.

## État actuel

- `viz/index.html` — v1 : « La Grande Machine Financière », visualisation statique
  pédagogique (réservoirs, circuit de l'épargne, grands acteurs, croissance sur 25 ans,
  carte interactive des dépendances avec scénarios animés).
  Publiée : https://claude.ai/code/artifact/ef5328e4-54b0-4d79-b523-f53b2d361c21

## Réalité des données (à garder en tête)

Le « qui achète / qui vend » en temps réel n'existe pas en données publiques.
Ce qui existe, gratuitement :

| Donnée | Source | Fréquence | Délai |
|---|---|---|---|
| Prix (indices, taux, FX, matières premières) | Yahoo/stooq, FRED, BCE | quotidien | temps quasi réel |
| Positions par type d'acteur (hedge funds, commerciaux…) sur les futures | CFTC — Commitments of Traders | hebdo | 3 jours |
| Portefeuilles des gros gérants US | SEC 13F | trimestriel | 45 jours |
| Flux entrants/sortants des ETF | émetteurs / agrégateurs | quotidien | 1 jour |
| Bilans des banques centrales | Fed H.4.1, BCE | hebdo | quelques jours |

La stratégie : les **prix quotidiens** donnent le rythme, les **rapports COT/13F/flux ETF**
donnent le « qui », et la **carte des dépendances** donne le « pourquoi ».
