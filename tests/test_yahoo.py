import datetime
import unittest
from unittest.mock import MagicMock, patch

from app.collectors import yahoo


def _chart_response(quote_close, adjclose=None):
    indicators = {"quote": [{"close": quote_close}]}
    if adjclose is not None:
        indicators["adjclose"] = [{"adjclose": adjclose}]
    return {
        "chart": {
            "result": [
                {
                    "meta": {"gmtoffset": 0},
                    "timestamp": [1704067200 + day * 86400 for day in range(len(quote_close))],
                    "indicators": indicators,
                }
            ]
        }
    }


class YahooFetchHistoryTests(unittest.TestCase):
    @patch("app.collectors.yahoo.httpx.Client")
    def test_prefers_adjusted_close_over_raw_close(self, client_cls):
        response = MagicMock()
        response.json.return_value = _chart_response(
            quote_close=[100.0, 101.0], adjclose=[87.0, 101.0]
        )
        client_cls.return_value.__enter__.return_value.get.return_value = response

        history = yahoo.fetch_history("EUEA.AS", range_="5y")

        self.assertEqual([price for _, price in history], [87.0, 101.0])

    @patch("app.collectors.yahoo.httpx.Client")
    def test_falls_back_to_raw_close_when_adjclose_missing(self, client_cls):
        response = MagicMock()
        response.json.return_value = _chart_response(quote_close=[100.0, 101.0])
        client_cls.return_value.__enter__.return_value.get.return_value = response

        history = yahoo.fetch_history("PSP5.PA", range_="5y")

        self.assertEqual([price for _, price in history], [100.0, 101.0])


if __name__ == "__main__":
    unittest.main()
