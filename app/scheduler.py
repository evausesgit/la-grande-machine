"""Collecte planifiée (dans le container) :
23h05 Paris — clôtures américaines ; 06h15 Paris — Asie + fraîcheur pour le brief ;
06h45 Paris — rédaction et publication du brief du matin (recherche web incluse).
Activée par RUN_SCHEDULER=1 (jamais en développement local par défaut)."""
import logging
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

log = logging.getLogger("scheduler")
_scheduler: BackgroundScheduler | None = None


def _collecte():
    from .collectors.run import collect_all
    from .db import SessionLocal

    with SessionLocal() as session:
        report = collect_all(session)
    ok = sum(1 for r in report.values() if r["ok"])
    log.info("collecte planifiée : %s ok, %s échecs", ok, len(report) - ok)


def _bootstrap_pea():
    """Rend le laboratoire utilisable peu après un nouveau déploiement."""
    from .collectors.run import collect_all
    from .db import SessionLocal

    with SessionLocal() as session:
        report = collect_all(session, families={"pea"})
    ok = sum(1 for result in report.values() if result["ok"])
    log.info("initialisation PEA : %s ok, %s échecs", ok, len(report) - ok)


def _collecte_fonds():
    from .collectors.edgar13f import collect_13f
    from .db import SessionLocal

    with SessionLocal() as session:
        report = collect_13f(session)
    ok = sum(1 for r in report.values() if r["ok"])
    log.info("collecte 13F planifiée : %s ok, %s échecs", ok, len(report) - ok)


def _brief_du_matin():
    from .brief_writer import generer_et_publier
    from .db import SessionLocal

    codex_home = os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex"))
    if not os.path.exists(os.path.join(codex_home, "auth.json")):
        log.warning("brief du matin sauté : auth codex absente (%s)", codex_home)
        return
    with SessionLocal() as session:
        try:
            result = generer_et_publier(session)
            log.info("brief du matin publié : %s", result)
        except Exception:
            log.exception("échec de la rédaction du brief du matin")


def start():
    global _scheduler
    if os.environ.get("RUN_SCHEDULER") != "1":
        log.info("scheduler désactivé (RUN_SCHEDULER != 1)")
        return
    _scheduler = BackgroundScheduler(timezone="Europe/Paris")
    _scheduler.add_job(_collecte, CronTrigger(hour=23, minute=5))
    _scheduler.add_job(_collecte, CronTrigger(hour=6, minute=15))
    # 13F : dépôts EDGAR possibles tous les jours ouvrés, vérification quotidienne
    _scheduler.add_job(_collecte_fonds, CronTrigger(hour=5, minute=45))
    _scheduler.add_job(_brief_du_matin, CronTrigger(hour=6, minute=45))
    _scheduler.add_job(_bootstrap_pea, next_run_time=datetime.now() + timedelta(seconds=5))
    _scheduler.start()
    log.info("scheduler démarré (23h05, 06h15, 05h45 fonds et 06h45 brief, Europe/Paris)")


def stop():
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
