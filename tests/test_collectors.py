import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.collectors.run import collect_all, seed_instruments
from app.db import Base
from app.models import Instrument, PriceDaily


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        seed_instruments(self.session)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    @patch("app.collectors.run.time.sleep")
    @patch("app.collectors.run.fred.fetch_history", return_value=[])
    @patch("app.collectors.run.yahoo.fetch_history", return_value=[])
    def test_new_pea_products_bootstrap_with_long_history(self, yahoo_fetch, _fred_fetch, _sleep):
        collect_all(self.session)
        calls = {
            call.args[0]: call.kwargs["range_"]
            for call in yahoo_fetch.call_args_list
        }
        self.assertEqual(calls["PSP5.PA"], "10y")
        self.assertEqual(calls["WPEA.PA"], "10y")
        self.assertEqual(calls["^GSPC"], "1mo")

    @patch("app.collectors.run.time.sleep")
    @patch("app.collectors.run.fred.fetch_history", return_value=[])
    @patch("app.collectors.run.yahoo.fetch_history", return_value=[])
    def test_populated_pea_products_return_to_monthly_collection(self, yahoo_fetch, _fred_fetch, _sleep):
        instrument = self.session.scalar(select(Instrument).where(Instrument.code == "pea_sp500_psp5"))
        self.session.add_all([
            PriceDaily(instrument_id=instrument.id, date=day, close=100)
            for day in series_days(252)
        ])
        self.session.commit()

        collect_all(self.session)
        calls = {
            call.args[0]: call.kwargs["range_"]
            for call in yahoo_fetch.call_args_list
        }
        self.assertEqual(calls["PSP5.PA"], "1mo")
        self.assertEqual(calls["WPEA.PA"], "10y")

    @patch("app.collectors.run.time.sleep")
    @patch("app.collectors.run.fred.fetch_history", return_value=[])
    @patch("app.collectors.run.yahoo.fetch_history", return_value=[])
    def test_collection_can_be_limited_to_pea_family(self, yahoo_fetch, fred_fetch, _sleep):
        report = collect_all(self.session, families={"pea"})

        self.assertEqual(set(report), {"pea_sp500_psp5", "pea_world_wpea"})
        self.assertEqual({call.args[0] for call in yahoo_fetch.call_args_list}, {"PSP5.PA", "WPEA.PA"})
        fred_fetch.assert_not_called()


def series_days(count):
    import datetime

    start = datetime.date(2025, 1, 1)
    return [start + datetime.timedelta(days=index) for index in range(count)]


if __name__ == "__main__":
    unittest.main()
