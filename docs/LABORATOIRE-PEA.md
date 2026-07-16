# Laboratoire PEA

Le laboratoire compare des règles d'investissement sur des supports explicitement éligibles au PEA, sans transmettre d'ordre. Les 13F restent utiles pour comprendre les convictions américaines, mais leurs actions US ne sont pas achetées directement dans le PEA.

## Univers

| Code | Support | ISIN | Rôle |
|---|---|---|---|
| `pea_sp500_psp5` | Amundi PEA S&P 500 UCITS ETF Acc | `FR0011871128` | historique long pour éprouver le moteur |
| `pea_world_wpea` | iShares MSCI World Swap PEA UCITS ETF | `IE0002XZSHO1` | cœur mondial diversifié, historique depuis 2024 |
| `pea_eurostoxx50_euea` | iShares Core EURO STOXX 50 UCITS ETF EUR (Dist) | `IE0008471009` | zone euro, réplication physique, historique depuis 2000 |
| `pea_cac40_cac` | Amundi CAC 40 UCITS ETF Dist (ex-Lyxor) | `FR0007052782` | France, réplication physique, historique depuis 2000 |
| `pea_world_dcam` | Amundi PEA Monde (MSCI World) UCITS ETF Acc | `FR001400U5Q4` | cœur mondial éligible PEA par swap, alternative à `pea_world_wpea`, historique depuis mars 2025 |

Ajout du 13 juillet 2026 : ces trois derniers supports ont été identifiés en comparant un relevé de courtage tiers (5 ETF hors PEA, détenus dans un compte britannique). Sur les 5, seuls deux étaient directement éligibles PEA (EURO STOXX 50 et CAC 40) ; les trois autres (MSCI World LU1781541179, S&P 500 Info Tech IE00B3WJKG14, Vanguard S&P 500 IE00BFMXXD54) ne le sont pas. Pour l'exposition MSCI World, `pea_world_dcam` est le substitut PEA-éligible réel (ISIN différent, structuré par swap chez Amundi) — pas le fonds détenu dans le relevé d'origine. Aucune donnée du relevé source (identité, montants, historique de transactions) n'a été reprise : seuls les caractéristiques publiques des instruments sont documentées ici.

L'éligibilité n'est jamais déduite du nom : elle est documentée par le producteur et doit être revérifiée auprès du courtier avant une opération réelle. Note technique : les fiches producteur (blackrock.com, amundietf.fr) bloquent la récupération automatisée (403) — les caractéristiques ci-dessus sont corroborées par plusieurs agrégateurs indépendants (justetf.com, sicavonline.fr) mais le lien de chaque support pointe vers la fiche officielle, à consulter directement avant toute décision.

Correction du 16 juillet 2026 : le collecteur Yahoo utilisait la clôture brute plutôt que la
clôture ajustée des dividendes, ce qui sous-estimait le rendement réel des ETF distribuants
(-13% sur 5 ans mesuré sur EUEA). `app/collectors/yahoo.py` utilise désormais `adjclose` quand
Yahoo le fournit, avec repli sur la clôture brute sinon.

## Mon portefeuille

Stratégie réelle décidée le 16 juillet 2026, suivie sur `/portefeuille` (pas une exploration —
une décision) : lump sum 2000€ S&P 500 + 1000€ MSCI World (WPEA) + 1000€ EURO STOXX 50 dans le
PEA, puis versements mensuels 100€ / 50€ / 50€. Un investissement complémentaire de 1000€ en or
(ETC physique) est prévu hors PEA sur compte-titres ordinaire (non éligible PEA, non simulé par
cet outil). La configuration vit dans `MON_PORTEFEUILLE` (`app/config.py`) ; le champ `depuis` de
chaque ligne est `None` tant que l'ordre n'est pas passé (affichage de l'historique complet du
support) et doit être renseigné à la date réelle d'achat une fois les ordres exécutés, pour que
le suivi reflète la performance réelle plutôt que l'historique du fonds depuis son lancement.

## Stratégies

- **Achat-conservation** : chaque versement achète le maximum de parts entières.
- **Tendance** : achat lorsque la clôture précédente est supérieure à sa moyenne mobile ; sinon les espèces restent dans le PEA.

Les deux simulations reçoivent les mêmes versements. La performance est calculée sur une valeur de part interne afin de ne pas confondre rendement et effort d'épargne. Les frais de gestion de l'ETF sont déjà reflétés dans son cours ; les frais de courtage sont simulés séparément.

## Utilisation

1. Lancer une collecte profonde : `POST /api/collecte?deep=true` avec l'en-tête `X-Token`.
2. Ouvrir `/laboratoire`.
3. Modifier capital, versement, frais et fenêtre de tendance.

En production, une collecte PEA est aussi lancée quelques secondes après le démarrage afin qu'un premier déploiement n'attende pas la prochaine collecte planifiée.

Le modèle suppose une exécution à la clôture, sans fiscalité, spread ni rémunération des espèces. Il sert à comparer des règles, pas à prévoir les rendements futurs.
