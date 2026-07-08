# Recensement des sources — Phase F1 du chantier fonds

> Livrable de la phase F1 (voir [SPEC-FONDS.md](SPEC-FONDS.md) §8).
> Vérifié en ligne le 8 juillet 2026. À valider par Eva.

## 1. Les boutiques françaises (6 maisons)

| Maison | Fonds de départ | Où | Recette de collecte | Difficulté |
|---|---|---|---|---|
| **Moneta AM** | Moneta Multi Caps | moneta.fr | PDF à **URL prévisible** : `moneta.fr/documents/Fiche_MMC_FR_fr_2025_12.pdf` (fiche) et `Lettre_MMC_part_C_FR_fr_2025_12.pdf` (lettre). Archives en ligne sur plusieurs années → historique rétroactif possible. | Faible |
| **Indépendance AM** | Indépendance France Small & Mid | independance-am.com | WordPress : PDF datés sous `wp-content/uploads/2026/07/260630-reporting-france-small-mid-x-eur-c2-fr-….pdf`. Suffixes parfois variables → parcourir la page du fonds qui liste les rapports mensuels (archives depuis 2020). | Faible |
| **Amiral Gestion** | Sextant PME, Sextant Grand Large | amiralgestion.com | Page de publication **stable par fonds/part** : `amiralgestion.com/fr/publications-adminmenu/sextant-pme-i-mensuel` → suivre le lien PDF. Lettres trimestrielles en plus des mensuels. | Faible–moyenne |
| **Carmignac** | Carmignac Investissement | carmignac.fr | Page documents par fonds : `carmignac.fr/fr_FR/nos-fonds-notre-gestion/carmignac-investissement-FR0010148981-a-eur-acc/documents` (rapport mensuel avec données ESG) + « Lettre du gérant » trimestrielle publiée en article. | Faible–moyenne |
| **LFDE** | Echiquier Agressor | lfde.com / cdn.lfde.com | Factsheet servie depuis `cdn.lfde.com/upload/documents/FACSHT-FR-FR-<CODE>.pdf` — **URL stable dont le contenu est remplacé chaque mois** : aucune archive publique, notre archivage (hash + copie) est indispensable dès le premier mois. | Moyenne |
| **Comgest** | Comgest Growth Europe | comgest.com | Pages fonds par pays/profil (`comgest.com/en/fr/private-investor/funds/comgest-growth-europe-eur-acc`), monthly report par classe de part, derrière une **porte de profil investisseur** (choix pays/profil, cookie) — mécanique exacte à confirmer à l'implémentation. | Moyenne |

Constats transverses :
- Toutes publient un **rapport mensuel avec principales positions** ; le « pourquoi »
  est mensuel chez Moneta, plutôt **trimestriel** ailleurs (lettres Amiral, lettre du
  gérant Carmignac) — la table `theses` doit accepter les deux rythmes.
- Les documents sont par **classe de part** (C, I, A, X…) : on en choisit une par
  fonds (celle du tableau), les positions sont identiques entre parts.
- Disclaimers : standards (pas un conseil, interdiction « US persons ») — aucun
  bloquant identifié pour un usage de citation avec lien source. Comgest est la
  seule avec une porte d'accès à franchir techniquement.
- La collecte quotidienne vérifie l'apparition des nouveaux documents (fenêtre
  attendue : du 5 au 15 du mois) ; LFDE se détecte par changement de hash.

## 2. L'univers 13F (8 déclarants, CIK vérifiés sur EDGAR le 8 juillet 2026)

| Déclarant | CIK | Famille | Note |
|---|---|---|---|
| Berkshire Hathaway Inc | 0001067983 | Conviction | ~40 lignes, le plus pédagogique |
| Pershing Square Capital Management | 0001336528 | Conviction | ~10 lignes, très concentré |
| Fundsmith LLP | 0001569205 | Conviction | Qualité/croissance, pendant UK de Comgest |
| Scion Asset Management | 0001649339 | Conviction | Petit, mouvements très commentés dans la presse |
| BlackRock Inc | 0001364742 | Géant | Milliers de lignes → top N + concentration seulement |
| Vanguard Group Inc | 0000102909 | Géant | idem |
| State Street Corp | 0000093751 | Géant | idem |
| FMR LLC (Fidelity) | 0000315066 | Géant | idem |

Collecte : `data.sec.gov/submissions/CIK{cik}.json` pour détecter les nouveaux
13F-HR, puis l'information table XML du dépôt. User-Agent déclaré obligatoire,
~10 requêtes/s max. Calendrier : dépôts jusqu'à 45 jours après chaque fin de
trimestre (pics mi-février, mi-mai, mi-août, mi-novembre).

## 3. Ce que ça implique pour F2/F3

1. **F2 (13F)** peut démarrer immédiatement : sources 100 % structurées, zéro
   extraction LLM, les 8 CIK ci-dessus en configuration.
2. **F3 (boutiques)** : ordre d'implémentation recommandé = Moneta →
   Indépendance AM → Amiral → Carmignac → LFDE → Comgest (du plus simple au
   plus fermé). Chaque recette est ~20 lignes de configuration + le
   téléchargeur générique.
3. L'archivage local (PDF + sha256) est **non négociable** dès le premier jour
   à cause de LFDE (URL stable écrasée) et pour la ré-extraction future.
