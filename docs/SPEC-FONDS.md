# Spécification — Les fonds des gérants (le chantier « positions »)

> Version 1 — à valider par Eva avant construction.
> Décisions prises ensemble le 8 juillet 2026.

## 1. Ce qu'on construit

L'extension de La Grande Machine au niveau **fonds individuels** : pour chaque
gérant d'actifs suivi, ses fonds, leurs **principales positions** mois par mois,
les **mouvements** (entrées, sorties, renforcements), et surtout le **pourquoi**
— les thèses d'investissement extraites des lettres de gestion.

C'était le point « positions détaillées par fonds » du backlog de la SPEC v1 ;
il devient un chantier à part entière.

### Décisions d'alignement (8 juillet 2026)

| Question | Décision |
|---|---|
| Périmètre | **Les deux univers en parallèle** : boutiques françaises de conviction + géants via SEC 13F |
| Profondeur | **Top 10 mensuel + le pourquoi** (pas d'inventaires complets en v1) |
| Le « pourquoi » | **Extraction LLM pilotée par Codex** (voir §5) |
| Intégration | **Dans La Grande Machine** : même base, mêmes collecteurs, nouvelles pages |

## 2. Les trois mondes de la donnée (réalité du terrain)

| Univers | Source | Format | Fréquence | Le « pourquoi » |
|---|---|---|---|---|
| Boutiques FR/EU de conviction | Site de chaque maison : fiche mensuelle + lettre de gestion | PDF, structure propre à chaque maison | mensuel | **Oui** — les lettres expliquent achats/ventes |
| Gérants US (> 100 M$ actions US) | SEC EDGAR, formulaires 13F | XML structuré, gratuit | trimestriel (+ 45 j) | Non |
| ETF | Fichiers d'inventaire des émetteurs | CSV/Excel quotidien | quotidien | Non (positions d'indice) |

Vérifié sur Moneta (8 juillet 2026) : PDF à URL prévisible
(`moneta.fr/documents/Fiche_MMC_FR_fr_2025_12.pdf`, `Lettre_MMC_part_C_FR_fr_2025_12.pdf`)
avec principales positions chiffrées (Airbus 5,6 %, LVMH 5,4 %, BNP 4,8 %…) et
commentaire de gestion. Chaque maison aura son propre motif — d'où la phase de
recensement (F1).

Les ETF sont **hors v1** (peu de conviction à raconter) ; le collecteur de flux
ETF de la SPEC v1 (P3) reste un chantier distinct.

## 3. Les gérants suivis (proposition de départ)

### Boutiques de conviction (6 pour commencer)

| Maison | Fonds phare | Pourquoi elle |
|---|---|---|
| Moneta AM | Moneta Multi Caps | Référence du stock-picking France, reporting riche |
| Comgest | Comgest Growth Europe | Qualité/croissance, discipline célèbre |
| Amiral Gestion | Sextant PME, Sextant Grand Large | Value, petites capitalisations, lettres détaillées |
| Indépendance AM | Indépendance France Small | Small caps France, track record exceptionnel |
| La Financière de l'Échiquier | Echiquier Agressor | Historique, connue du grand public |
| Carmignac | Carmignac Investissement | Global macro, commentaires abondants |

Extension naturelle ensuite : Sycomore, DNCA, Eleva, Lazard Frères Gestion,
Sextant Autour du Monde… La liste vit dans la base, pas dans le code.

### Univers 13F (5–8 déclarants)

Deux familles, à doser en F1 :

- **Les géants** (BlackRock, Vanguard, State Street, Fidelity) : poids énorme mais
  portefeuilles quasi indiciels, des milliers de lignes — on ne stocke que le
  top N et les indicateurs de concentration. Valeur : montrer « qui possède le marché ».
- **Les fonds de conviction célèbres** (Berkshire Hathaway, Pershing Square,
  Fundsmith, Scion…) : peu de lignes, forte narration, très pédagogique.
  Recommandation : en prendre 3–4 dès le départ, c'est le pendant américain
  des boutiques françaises.

## 4. Modèle de données (nouvelles tables, même base PostgreSQL)

```
asset_managers   id, slug, nom, pays, type (boutique|geant_13f|conviction_13f),
                 aum_mds_eur, site_web, cik_sec (nullable)

funds            id, manager_id, nom, isin (part principale), strategie,
                 devise, note_source (comment/où on collecte)

source_documents id, fund_id, type (fiche|lettre|13f|rapport_annuel),
                 periode (mois ou trimestre), url, sha256, fichier_archive,
                 fetched_at, statut_extraction

fund_snapshots   id, fund_id, date (fin de mois/trimestre), source_document_id,
                 encours, nb_lignes_publiees
                 UNIQUE(fund_id, date)

securities       id, nom_canonique, isin (nullable), ticker (nullable),
                 pays, secteur, instrument_id (FK nullable → instruments)

security_aliases id, security_id, libelle_brut, source
                 -- « LVMH », « LVMH MOET HENNESSY », « LVMH Moët Hennessy SE »…

positions        id, snapshot_id, security_id, libelle_brut, poids_pct, rang

theses           id, snapshot_id, security_id (nullable), action
                 (achat|renforcement|allegement|vente|commentaire),
                 texte_fr, citation_source, confiance
```

Principes :
- **Point-in-time strict** : un snapshot par fonds et par période, jamais écrasé.
  Les mouvements (entrées/sorties/évolutions de poids) se **calculent** en
  comparant deux snapshots consécutifs — pas de table dédiée en v1.
- **Le libellé brut est toujours conservé** (`libelle_brut`). Le rapprochement
  vers `securities` passe par la table d'alias, enrichie au fil de l'eau
  (assisté LLM, validé par échantillonnage). C'est LA difficulté du chantier :
  les PDF donnent des noms, pas des ISIN.
- **Pont vers l'existant** : `securities.instrument_id` relie une valeur aux
  prix déjà collectés (LVMH, TotalEnergies… sont déjà dans `instruments`) —
  c'est ce qui permet « Moneta a renforcé Elis en mars, +18 % depuis ».
- **Chaque donnée cite son document source** (URL + copie archivée + hash) :
  traçabilité totale, et ré-extraction possible si le pipeline s'améliore.

## 5. La collecte et l'extraction

### Collecteurs (app/collectors/, pattern existant)

- `edgar13f.py` — un seul collecteur pour tout l'univers 13F : découverte des
  dépôts par CIK, parsing du XML (information table), insertion snapshot+positions.
  Le plus simple, il **valide le modèle de données** avant d'attaquer les PDF.
- `fonds_pdf.py` — le téléchargeur générique : pour chaque fonds « boutique »,
  une **recette par maison** (URL prévisible type Moneta, ou page de documents
  à parcourir) déclarée en configuration. Télécharge, hash, archive, marque
  `statut_extraction = en_attente`. Rythme : vérification quotidienne des
  nouveaux documents (les fiches tombent entre le 5 et le 15 du mois).

### Extraction des PDF (positions + thèses) — pilotée par Codex

Décision d'Eva : l'extraction LLM est faite avec **Codex**. Le pipeline est
donc conçu **agnostique de l'outil** :

1. L'app expose `GET /api/fonds/extraction/en-attente` (liste des documents à
   traiter, avec URL du PDF archivé) et `POST /api/fonds/extraction`
   (résultat en JSON, jeton secret en variable d'env — même pattern que
   `POST /api/brief`).
2. Le **contrat d'extraction** vit dans le repo : `docs/extraction-fonds.md`
   (instructions) + schéma JSON strict (positions : libellé/poids/rang ;
   thèses : valeur/action/texte/citation). N'importe quel agent LLM (Codex,
   routine Claude en secours) exécute le contrat et poste le résultat.
3. Garde-fous : le poids total du top 10 doit être plausible (15–80 %),
   chaque thèse doit citer un extrait exact de la lettre (vérifiable),
   les échecs restent en `statut_extraction = erreur` et sont visibles
   sur `/api/sante`.

## 6. Les pages (dans l'app existante)

| Route | Contenu |
|---|---|
| `/fonds` | Les gérants et fonds suivis : dernière position connue, fraîcheur, mouvements du mois en vedette |
| `/fonds/{slug}` | Un fonds : top positions actuelles et leur évolution, entrées/sorties, thèses du gérant (avec citation et lien vers le PDF source) |
| `/valeur/{slug}` | **La vue croisée — le cœur de la valeur** : qui détient cette valeur, à quel poids, ce que chaque gérant en dit, graphique du prix (si reliée à `instruments`) |
| Brief du matin | Le « coin des acteurs » (SPEC v1 §4.4) s'enrichit : quand des reportings mensuels tombent, les mouvements notables et les thèses marquantes entrent dans le brief |

## 7. Honnêteté et cadre (affiché dans l'app)

- Ces documents sont **publics, destinés aux investisseurs** ; on archive, on
  extrait, on **cite toujours la source** avec lien vers le document original.
  Pas de republication intégrale des PDF.
- Certains sites de gérants ont un disclaimer d'accès (profil investisseur) —
  à vérifier maison par maison en F1 ; toute maison problématique est écartée.
- Fraîcheur affichée partout : un top 10 mensuel a jusqu'à 6 semaines de retard,
  un 13F jusqu'à 4,5 mois. L'outil montre des **convictions**, pas des
  positions temps réel.
- Avertissement pédagogique existant inchangé : pas un conseil d'investissement.

## 8. Phases

| Phase | Livrable | Critère de fin |
|---|---|---|
| **F1 — Recensement** | Pour chaque maison de la liste §3 : URL/format/fréquence des documents, faisabilité, disclaimer. Liste 13F définitive (CIK). Tableau validé ensemble. | on sait exactement quoi collecter, où, comment |
| **F2 — Socle 13F** | Tables en base, collecteur EDGAR, page `/fonds` basique | les portefeuilles 13F de 5+ déclarants s'affichent |
| **F3 — Boutiques (positions)** | Téléchargeur PDF + recettes par maison, contrat d'extraction, pipeline Codex → positions en base | 6 maisons, 2 mois consécutifs de top 10 sans intervention |
| **F4 — Le pourquoi** | Extraction des thèses depuis les lettres, table `theses`, page `/valeur/{slug}` croisée | pour une valeur donnée, l'app montre qui la détient et pourquoi |
| **F5 — Intégration** | Le coin des acteurs du brief branché sur les nouveaux reportings, rapprochement `securities` ↔ `instruments` consolidé | un brief cite spontanément un mouvement de gérant |

## 9. Hors v1 (backlog assumé)

Inventaires complets (rapports annuels UCITS, N-PORT), ETF, alertes sur
mouvements, comparaison de performance des gérants, historique rétroactif
profond (on peut remonter les archives PDF des maisons qui les gardent en
ligne — Moneta remonte à plusieurs années), version anglaise.
