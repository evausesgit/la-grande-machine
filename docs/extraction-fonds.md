# Le contrat d'extraction des fonds — phase F3/F4

> Destiné à n'importe quel agent LLM (Codex en premier, éventuellement une
> routine Claude en secours — voir [SPEC-FONDS.md](SPEC-FONDS.md) §5).
> L'app ne fait que collecter et archiver les PDF (`app/collectors/fonds_pdf.py`) ;
> **lire le PDF et en extraire positions/thèses est un chantier séparé, exécuté
> par cet agent, hors de l'app**.

## 1. Trouver du travail

```
GET /api/fonds/extraction/en-attente
```

Retourne les documents archivés dont l'extraction n'a pas encore eu lieu :

```json
{
  "documents": [
    {
      "document_id": 42,
      "fonds_slug": "moneta-multi-caps",
      "fonds_nom": "Moneta Multi Caps",
      "type": "fiche",
      "periode": "2026-06",
      "url_archive": "https://<host>/api/fonds/documents/42.pdf"
    }
  ]
}
```

`type` vaut `fiche` (document avec le tableau de positions) ou `lettre`
(commentaire de gestion — le « pourquoi »). `url_archive` sert **notre**
copie archivée (pas l'URL d'origine, qui peut avoir été écrasée depuis).

## 2. Lire le PDF

Télécharger `url_archive` (PDF brut). Extraire :
- pour un `fiche` : les positions listées (nom brut tel qu'écrit dans le
  document, poids en %, rang) — le top 10 suffit en v1.
- pour une `lettre` : les passages qui expliquent un achat, un renforcement,
  un allègement ou une vente d'une valeur nommée, **avec la citation exacte**.

## 3. Poster le résultat

```
POST /api/fonds/extraction
X-Token: <ADMIN_TOKEN>
```

```json
{
  "document_id": 42,
  "date": "2026-06-30",
  "encours": 850000000,
  "nb_lignes_publiees": 45,
  "positions": [
    {"rang": 1, "libelle": "LVMH", "poids_pct": 5.6, "isin": "FR0000121014"},
    {"rang": 2, "libelle": "TotalEnergies", "poids_pct": 5.1}
  ],
  "theses": [
    {"valeur": "LVMH", "action": "renforcement",
     "texte": "Renforcement sur LVMH après la publication trimestrielle.",
     "citation": "Nous avons renforcé notre position sur LVMH ce mois-ci.",
     "confiance": 0.85}
  ]
}
```

Champs :
- `document_id` (obligatoire) — celui reçu à l'étape 1.
- `date` (obligatoire) — la date d'arrêté du portefeuille **telle qu'écrite
  dans le document** (pas la date de collecte).
- `encours`, `nb_lignes_publiees` — optionnels.
- `positions` — omis pour un document `lettre` sans tableau de positions.
  `isin` optionnel ; `libelle` est le nom brut du document (le rapprochement
  vers `securities` se fait côté serveur).
- `theses` — `action` ∈ `achat|renforcement|allegement|vente|commentaire` ;
  `citation` **obligatoire et non vide** pour chaque thèse (extrait exact du
  document, vérifiable) ; `confiance` optionnel (0–1).

## 4. Garde-fous (appliqués côté serveur, rejet en 422 sans écriture partielle)

- Si `positions` est fourni : la somme des poids des positions de rang ≤ 10
  doit être plausible, entre **15 % et 80 %**. Hors de cette plage, le
  document reste `en_attente` (probable erreur de lecture — pourcentages en
  points au lieu de fraction, tableau tronqué, etc.).
- Chaque thèse doit avoir une `citation` non vide.
- Le document doit être en statut `en_attente` (déjà extrait ou en erreur :
  rejeté, republier via une nouvelle collecte si besoin de ré-extraire).

En cas de succès : le document passe à `statut_extraction = extrait`, un
`FundSnapshot` est créé (ou réutilisé s'il existe déjà à cette date), les
positions et thèses sont insérées, `securities`/`security_aliases` sont
enrichies au fil de l'eau (rapprochement par libellé exact, sans essai de
fuzzy-matching automatique — un libellé jamais vu crée une nouvelle valeur).

## 5. Fraîcheur et visibilité

Les échecs et les documents en attente restent visibles sur `/api/sante`
(compteurs par fonds et par statut). Rien n'est jamais republié
silencieusement : un document `erreur` doit être corrigé et reposté
explicitement.
