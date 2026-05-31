from __future__ import annotations

import pandas as pd

from src.config.rules_config import get_all_configs
from src.rules.hypotheses import (
    h10_atypical_benefit,
    h11_high_cash,
    h12_low_cash,
    h17_zero_sum,
    h19_unknown_categories,
    h1_high_frequency,
    h20_duplicates,
    h21_poisson_deviation,
    h2_route_spike,
    h3_bursts,
    h4_benefit_series,
    h7_night_school,
    h8_school_card_multiple,
)


HYPOTHESIS_RUNNERS = {
    "H1": h1_high_frequency,
    "H2": h2_route_spike,
    "H3": h3_bursts,
    "H4": h4_benefit_series,
    "H7": h7_night_school,
    "H8": h8_school_card_multiple,
    "H10": h10_atypical_benefit,
    "H11": h11_high_cash,
    "H12": h12_low_cash,
    "H17": h17_zero_sum,
    "H19": h19_unknown_categories,
    "H20": h20_duplicates,
    "H21": h21_poisson_deviation,
}


def run_hypotheses(
    transactions: pd.DataFrame,
    selected: list[str] | None = None,
    configs: dict[str, dict] | None = None,
) -> dict[str, pd.DataFrame]:
    configs = configs or get_all_configs()
    selected_names = selected or list(HYPOTHESIS_RUNNERS)
    results: dict[str, pd.DataFrame] = {}

    for name in selected_names:
        runner = HYPOTHESIS_RUNNERS[name]
        params = configs.get(name, {})
        result = runner(transactions, **params)
        if result is None:
            result = pd.DataFrame()
        results[name] = result

    return results
