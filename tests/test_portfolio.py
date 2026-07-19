import datetime
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.collectors.run import seed_instruments
from app.db import Base
from app.main import _run_portfolio_line
from app.models import Instrument, PriceDaily


def series_days(count, start=datetime.date(2024, 1, 1)):
    return [start + datetime.timedelta(days=index) for index in range(count)]


class PortfolioLineTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        seed_instruments(self.session)
        instrument = self.session.scalar(select(Instrument).where(Instrument.code == "pea_sp500_psp5"))
        self.session.add_all([
            PriceDaily(instrument_id=instrument.id, date=day, close=100 + index)
            for index, day in enumerate(series_days(400))
        ])
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def test_runs_buy_hold_over_full_history_by_default(self):
        resultat, erreur = _run_portfolio_line(
            self.session, {"produit": "pea_sp500_psp5", "capital": 2000, "versement": 100, "depuis": None}
        )
        self.assertIsNone(erreur)
        self.assertEqual(resultat["start_date"], "2024-01-01")
        self.assertEqual(resultat["contributed"], 2000 + 100 * 13)  # ~13 mois glissés dans 400 jours

    def test_depuis_filters_history_to_the_real_purchase_date(self):
        resultat, erreur = _run_portfolio_line(
            self.session,
            {"produit": "pea_sp500_psp5", "capital": 2000, "versement": 100, "depuis": "2024-06-01"},
        )
        self.assertIsNone(erreur)
        self.assertEqual(resultat["start_date"], "2024-06-01")

    def test_unknown_product_reports_an_error(self):
        resultat, erreur = _run_portfolio_line(
            self.session, {"produit": "inconnu", "capital": 1000, "versement": 0, "depuis": None}
        )
        self.assertIsNone(resultat)
        self.assertIn("absent", erreur)

    def test_month_over_month_perf_reflects_a_jump_after_previous_month_end(self):
        instrument = self.session.scalar(select(Instrument).where(Instrument.code == "pea_world_wpea"))
        today = datetime.date.today()
        fin_mois_precedent = today.replace(day=1) - datetime.timedelta(days=1)
        debut = today - datetime.timedelta(days=100)
        rows = []
        day = debut
        while day <= today:
            price = 100.0 if day <= fin_mois_precedent else 120.0
            rows.append(PriceDaily(instrument_id=instrument.id, date=day, close=price))
            day += datetime.timedelta(days=1)
        self.session.add_all(rows)
        self.session.commit()

        resultat, erreur = _run_portfolio_line(
            self.session, {"produit": "pea_world_wpea", "capital": 1000, "versement": 0, "depuis": None}
        )
        self.assertIsNone(erreur)
        self.assertIsNotNone(resultat["perf_mois_precedent_pct"])
        self.assertGreater(resultat["perf_mois_precedent_pct"], 15)


if __name__ == "__main__":
    unittest.main()
