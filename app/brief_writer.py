"""Rédaction et publication du brief du matin, exécutées dans le container.

Remplace l'ancienne routine externe (claude.ai scheduled trigger) : cette
dernière tournait dans un sandbox dont le proxy réseau ne laisse passer que
des domaines explicitement autorisés, et personne n'est là pour approuver
l'accès à lamachine.ia-do-it.com lors d'une exécution automatique — chaque
appel curl (lecture ET publication) échouait donc silencieusement depuis le
début. Le container de l'app, lui, a déjà un accès réseau sortant qui
fonctionne (Yahoo, FRED, EDGAR), donc on y déplace aussi la rédaction.
"""
import datetime
import json
import logging
import os
import re

import anthropic
from sqlalchemy.orm import Session

from .engine.moves import compute_moves

log = logging.getLogger("brief")

MODEL = "claude-sonnet-5"

MISSION = """Tu es la routine rédactrice de https://lamachine.ia-do-it.com — l'observatoire
public des flux financiers d'Eva. Chaque matin tu racontes en français ce qui a bougé sur
les marchés, et surtout POURQUOI. Public : adultes curieux, zéro jargon non traduit, ton
vivant et pédagogique. Métaphore maison : la finance mondiale est un océan — les
réservoirs d'actifs sont des mers, les marchés des courants.

Date du jour (UTC) : {date}

## Les mouvements du jour (déjà calculés, triés par |z-score| décroissant)

{mouvements_json}

Ce sont TES chiffres de référence : cite toujours ces valeurs-là, jamais celles des
articles (heures de cotation différentes). Les familles « taux » et « credit » varient
en points, les autres en pourcentage.

## Étapes

1. Cherche les causes (recherche web) pour les 3 à 5 mouvements les plus notables
   (|z| le plus élevé) : quel événement, quelle chaîne de transmission, quelles
   conséquences probables. Croise au moins deux sources.
2. Écoute les gérants : cherche les publications de moins d'une semaine parmi :
   BlackRock Investment Institute, Amundi Investment Institute, PIMCO Views, mémos
   d'Howard Marks (Oaktree), Vanguard perspectives, JPMorgan. Si une note éclaire un
   mouvement du jour, cite-la dans « LE COIN DES ACTEURS » — citation courte reformulée
   (2-3 phrases d'idées max), attribution nominative + lien, toujours présentée comme
   une OPINION de gérant, jamais comme un fait.
3. Écris le brief en texte brut structuré (pas de rendu markdown, pas de **gras** ni de
   #titres — le corps s'affiche en pre-wrap) :
   - Titre : une phrase imagée qui résume la journée.
   - CE QUI A BOUGÉ — 5 à 8 puces « • » : instrument, valeur, variation, z-score.
   - POURQUOI — le récit causal, mouvement par mouvement : événement → chaîne de
     transmission → conséquences. C'est le cœur du brief.
   - LE COIN DES ACTEURS — ce que disent les gérants (étape 2).
   - À SURVEILLER — 2 ou 3 rendez-vous à venir (calendrier éco, rapports, résultats).
   - LE COIN DES CURIEUX — une notion pédagogique liée à l'actualité du jour, différente
     chaque jour (z-score, carry trade, spread, contango, boisseau…).
   - Dernière ligne : « Sources : … » avec les noms des sources utilisées.

## Réponse attendue

Réponds UNIQUEMENT avec un objet JSON valide, sans balise markdown ni texte autour,
de la forme exacte :
{{"date": "{date}", "titre": "...", "corps_md": "...", "donnees": {{"notables": ["code1", "code2"]}}}}

« notables » liste les codes des instruments cités dans le récit (parmi ceux visibles
dans les mouvements du jour ci-dessus).

Si peu de mouvements sont notables (week-end, jour férié) : brief court et honnête
(« les marchés ont dormi »), c'est très bien aussi — réponds quand même avec ce même
format JSON.
"""


def _extraire_json(texte: str) -> dict:
    texte = texte.strip()
    texte = re.sub(r"^```(?:json)?\s*|\s*```$", "", texte)
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        pass
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut == -1 or fin == -1:
        raise ValueError(f"aucun JSON trouvé dans la réponse : {texte[:200]!r}")
    return json.loads(texte[debut:fin + 1])


def _rediger(mouvements: list[dict]) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    aujourdhui = datetime.date.today().isoformat()
    prompt = MISSION.format(
        date=aujourdhui,
        mouvements_json=json.dumps(mouvements, ensure_ascii=False, default=str),
    )
    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}]

    for _ in range(5):  # borne les allers-retours si l'API pause une recherche longue
        response = client.messages.create(
            model=MODEL, max_tokens=4096, messages=messages, tools=tools,
        )
        if response.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": response.content})
    else:
        raise RuntimeError("la rédaction n'a pas abouti après plusieurs relances (pause_turn)")

    texte = "".join(bloc.text for bloc in response.content if bloc.type == "text")
    return _extraire_json(texte)


def generer_et_publier(session: Session) -> dict:
    from .main import publier_brief  # import tardif : évite un cycle avec main.py

    mouvements = compute_moves(session)
    payload = _rediger(mouvements)
    return publier_brief(session, payload)
