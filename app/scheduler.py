"""Collecte planifiée (dans le container) :
23h05 Paris — clôtures américaines ; 06h15 Paris — Asie + fraîcheur pour le brief.
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


def _collecte_fonds_pdf():
    from .collectors.fonds_pdf import collect_boutiques_pdf
    from .db import SessionLocal

    with SessionLocal() as session:
        report = collect_boutiques_pdf(session)
    ok = sum(1 for r in report.values() if r["ok"])
    log.info("collecte PDF boutiques planifiée : %s ok, %s échecs", ok, len(report) - ok)


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
    # Boutiques : les fiches/lettres tombent entre le 5 et le 15 du mois, vérification quotidienne
    _scheduler.add_job(_collecte_fonds_pdf, CronTrigger(hour=5, minute=50))
    _scheduler.add_job(_bootstrap_pea, next_run_time=datetime.now() + timedelta(seconds=5))
    _scheduler.start()
    log.info("scheduler démarré (23h05, 06h15, 05h45 pour les 13F et 05h50 pour les boutiques, Europe/Paris)")


def stop():
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
