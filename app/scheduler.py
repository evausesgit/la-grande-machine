"""Collecte planifiée (dans le container) :
23h05 Paris — clôtures américaines ; 06h15 Paris — Asie + fraîcheur pour le brief.
Activée par RUN_SCHEDULER=1 (jamais en développement local par défaut)."""
import logging
import os

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


def start():
    global _scheduler
    if os.environ.get("RUN_SCHEDULER") != "1":
        log.info("scheduler désactivé (RUN_SCHEDULER != 1)")
        return
    _scheduler = BackgroundScheduler(timezone="Europe/Paris")
    _scheduler.add_job(_collecte, CronTrigger(hour=23, minute=5))
    _scheduler.add_job(_collecte, CronTrigger(hour=6, minute=15))
    _scheduler.start()
    log.info("scheduler démarré (23h05 et 06h15, Europe/Paris)")


def stop():
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
