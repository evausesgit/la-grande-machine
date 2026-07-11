import datetime
import math
import statistics
from dataclasses import dataclass


@dataclass(frozen=True)
class LabSettings:
    initial_capital: float = 10_000
    monthly_contribution: float = 200
    fee_bps: float = 10
    moving_average_days: int = 200


def _metrics(nav_points: list[dict]) -> dict:
    if len(nav_points) < 2:
        return {"return_pct": 0.0, "cagr_pct": 0.0, "volatility_pct": 0.0, "max_drawdown_pct": 0.0}
    values = [1.0, *[point["nav"] for point in nav_points]]
    daily_returns = [values[index] / values[index - 1] - 1 for index in range(1, len(values)) if values[index - 1]]
    elapsed_days = (nav_points[-1]["date"] - nav_points[0]["date"]).days
    years = elapsed_days / 365.25
    cagr = (values[-1] / values[0]) ** (1 / years) - 1 if years > 0 else 0.0
    volatility = statistics.pstdev(daily_returns) * math.sqrt(252) if len(daily_returns) > 1 else 0.0
    peak = values[0]
    max_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1)
    return {
        "return_pct": round((values[-1] / values[0] - 1) * 100, 2),
        "cagr_pct": round(cagr * 100, 2),
        "volatility_pct": round(volatility * 100, 2),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
    }


def simulate_pea(
    prices: list[tuple[datetime.date, float]],
    settings: LabSettings,
    strategy: str,
) -> dict:
    if strategy not in {"buy_hold", "trend"}:
        raise ValueError(f"stratégie inconnue : {strategy}")
    if settings.initial_capital <= 0 or settings.monthly_contribution < 0:
        raise ValueError("montants invalides")
    if not 0 <= settings.fee_bps <= 500:
        raise ValueError("frais invalides")
    if not 20 <= settings.moving_average_days <= 500:
        raise ValueError("fenêtre de tendance invalide")

    prices = sorted((day, float(price)) for day, price in prices if price > 0)
    if len(prices) < 2:
        raise ValueError("historique insuffisant")
    fee_rate = settings.fee_bps / 10_000
    cash = settings.initial_capital
    shares = 0
    contributed = settings.initial_capital
    units = settings.initial_capital
    fees_paid = 0.0
    transactions = 0
    nav_points = []
    active = False
    previous_month = None
    closes = []

    for index, (day, price) in enumerate(prices):
        if previous_month is not None and (day.year, day.month) != previous_month and settings.monthly_contribution:
            value_before = cash + shares * price
            nav_before = value_before / units
            cash += settings.monthly_contribution
            contributed += settings.monthly_contribution
            units += settings.monthly_contribution / nav_before
        previous_month = (day.year, day.month)

        if strategy == "buy_hold":
            target_active = True
        else:
            history = closes[-settings.moving_average_days:]
            target_active = len(history) == settings.moving_average_days and closes[-1] > statistics.fmean(history)

        if target_active and (not active or cash > price * (1 + fee_rate)):
            bought = math.floor(cash / (price * (1 + fee_rate)))
            if bought:
                gross = bought * price
                fee = gross * fee_rate
                cash -= gross + fee
                shares += bought
                fees_paid += fee
                transactions += 1
        elif not target_active and active and shares:
            gross = shares * price
            fee = gross * fee_rate
            cash += gross - fee
            shares = 0
            fees_paid += fee
            transactions += 1

        active = target_active
        value = cash + shares * price
        nav_points.append({"date": day, "nav": value / units, "value": value, "active": active})
        closes.append(price)

    metrics = _metrics(nav_points)
    metrics.update({
        "strategy": strategy,
        "start_date": nav_points[0]["date"].isoformat(),
        "end_date": nav_points[-1]["date"].isoformat(),
        "final_value": round(nav_points[-1]["value"], 2),
        "contributed": round(contributed, 2),
        "gain": round(nav_points[-1]["value"] - contributed, 2),
        "fees_paid": round(fees_paid, 2),
        "transactions": transactions,
        "invested_now": active,
        "points": [
            {"date": point["date"].isoformat(), "nav": round(point["nav"], 6), "active": point["active"]}
            for point in nav_points
        ],
    })
    return metrics
