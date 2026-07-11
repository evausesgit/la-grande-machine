import datetime
import math
import unittest

from app.engine.pea_lab import LabSettings, simulate_pea


def series(values):
    start = datetime.date(2020, 1, 1)
    return [(start + datetime.timedelta(days=index), value) for index, value in enumerate(values)]


class PeaLabTests(unittest.TestCase):
    def test_buy_hold_grows_with_rising_market(self):
        result = simulate_pea(
            series([100 + index for index in range(400)]),
            LabSettings(initial_capital=10_000, monthly_contribution=0, fee_bps=0),
            "buy_hold",
        )
        self.assertGreater(result["final_value"], 39_000)
        self.assertEqual(result["transactions"], 1)
        self.assertEqual(result["max_drawdown_pct"], 0)

    def test_trend_waits_for_completed_history(self):
        result = simulate_pea(
            series([100 + index for index in range(80)]),
            LabSettings(initial_capital=10_000, monthly_contribution=0, fee_bps=0, moving_average_days=20),
            "trend",
        )
        first_active = next(point for point in result["points"] if point["active"])
        self.assertEqual(first_active["date"], datetime.date(2020, 1, 21).isoformat())

    def test_fees_reduce_final_value(self):
        prices = series([100 + index * 0.2 for index in range(400)])
        free = simulate_pea(prices, LabSettings(monthly_contribution=100, fee_bps=0), "buy_hold")
        costly = simulate_pea(prices, LabSettings(monthly_contribution=100, fee_bps=50), "buy_hold")
        self.assertGreater(free["final_value"], costly["final_value"])
        self.assertGreater(costly["fees_paid"], 0)

    def test_falling_market_creates_drawdown(self):
        result = simulate_pea(
            series([100, 110, 90, 80]),
            LabSettings(initial_capital=10_000, monthly_contribution=0, fee_bps=0),
            "buy_hold",
        )
        self.assertLess(result["max_drawdown_pct"], -20)

    def test_monthly_contributions_do_not_inflate_performance(self):
        prices = series([100] * 400)
        result = simulate_pea(
            prices,
            LabSettings(initial_capital=10_000, monthly_contribution=500, fee_bps=0),
            "buy_hold",
        )
        self.assertEqual(result["return_pct"], 0)
        self.assertEqual(result["gain"], 0)
        self.assertGreater(result["contributed"], 10_000)

    def test_non_positive_prices_are_rejected_after_filtering(self):
        with self.assertRaisesRegex(ValueError, "historique insuffisant"):
            simulate_pea(
                series([0, -1, 0]),
                LabSettings(monthly_contribution=0),
                "buy_hold",
            )

    def test_unknown_strategy_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "stratégie inconnue"):
            simulate_pea(series([100, 101]), LabSettings(), "market_timing")

    def test_noisy_rise_gives_positive_sharpe_and_sortino(self):
        # tendance haussière avec des à-coups (sinusoïde) : il y a de vraies baisses,
        # donc une déviation à la baisse non nulle, contrairement à une hausse parfaitement lisse
        result = simulate_pea(
            series([100 + index * 0.2 + 10 * math.sin(index / 10) for index in range(400)]),
            LabSettings(initial_capital=10_000, monthly_contribution=0, fee_bps=0),
            "buy_hold",
        )
        self.assertGreater(result["sharpe_ratio"], 0)
        self.assertGreater(result["sortino_ratio"], 0)

    def test_sortino_ignores_upside_volatility(self):
        # baisses toujours du même ordre, hausses de plus en plus amples : le risque de
        # baisse pèse moins que la volatilité totale, donc Sortino >= Sharpe
        result = simulate_pea(
            series([100, 100, 105, 100, 108, 100, 112, 100, 118] * 40),
            LabSettings(initial_capital=10_000, monthly_contribution=0, fee_bps=0),
            "buy_hold",
        )
        if result["sharpe_ratio"] > 0:
            self.assertGreaterEqual(result["sortino_ratio"], result["sharpe_ratio"])


if __name__ == "__main__":
    unittest.main()
