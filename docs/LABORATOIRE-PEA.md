# Laboratoire PEA

Le laboratoire compare des règles d'investissement sur des supports explicitement éligibles au PEA, sans transmettre d'ordre. Les 13F restent utiles pour comprendre les convictions américaines, mais leurs actions US ne sont pas achetées directement dans le PEA.

## Univers initial

| Code | Support | ISIN | Rôle |
|---|---|---|---|
| `pea_sp500_psp5` | Amundi PEA S&P 500 UCITS ETF Acc | `FR0011871128` | historique long pour éprouver le moteur |
| `pea_world_wpea` | iShares MSCI World Swap PEA UCITS ETF | `IE0002XZSHO1` | cœur mondial diversifié, historique depuis 2024 |

L'éligibilité n'est jamais déduite du nom : elle est documentée par le producteur et doit être revérifiée auprès du courtier avant une opération réelle.

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
