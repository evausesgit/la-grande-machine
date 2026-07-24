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
- `/laboratoire` — simulations exclusivement PEA : achat-conservation contre filtre de tendance, avec versements, parts entières et frais de courtage.
- `/flux` — **le bassin versant de l'argent** : les grandes masses (épargne → collecteurs →
  mers d'actifs) et les rivières entre elles, animées. Le scénario « Aujourd'hui » est calculé
  depuis la base ; trois scénarios pédagogiques montrent comment la machine réagirait.
  Chaque chiffre affiche sa provenance — voir « Honnêteté des données » ci-dessous.
  Données brutes : `GET /api/flux`.

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

### Les trois natures de chiffres affichées sur `/flux`

Comme les masses financières mondiales ne sont mesurables ni gratuitement ni en temps réel,
la page du bassin versant étiquette chaque nombre au lieu de faire semblant :

| Étiquette | Ce que ça veut dire | Exemples |
|---|---|---|
| **mesuré** | calculé depuis notre base | le stock d'or (tonnes du World Gold Council × notre cours), le bitcoin en circulation × notre cours, les encours 13F déposés à la SEC |
| **lu** | déduit de nos données sans être une mesure de flux : quand une mer monte un mois durant, l'argent a penché de ce côté | le « souffle » de chaque mer d'actifs, qui pilote la largeur des rivières |
| **ordre de grandeur** | publié par une institution, repris tel quel, jamais recalculé par nous | l'épargne des ménages (Allianz), les encours des gérants (BCG), la capitalisation boursière mondiale (WFE/SIFMA) |

Les **débits** des rivières restent illustratifs : personne ne publie les flux mondiaux.
Ce que les données pilotent, c'est leur *orientation*. Les premiers débits réellement
mesurables viendront des rapports COT (CFTC) et des variations trimestrielles des 13F.
