from __future__ import annotations

import numpy as np
import pandas as pd


REPORT_COLUMNS = [
    "entity_type",
    "entity_id",
    "total_unique_hypotheses",
    "total_violations",
    "hypotheses",
    "max_severity",
    "risk_score",
    "first_seen",
    "last_seen",
]


def _stringify_date(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    if hasattr(value, "date"):
        return value.date().isoformat()
    return str(value)


def _empty_report() -> pd.DataFrame:
    return pd.DataFrame(columns=REPORT_COLUMNS)


def aggregate_results(
    results: dict[str, pd.DataFrame],
    target_percentile: float = 95,
    min_weight: float = 0.01,
    max_weight: float = 10.0,
) -> pd.DataFrame:
    violations = []

    for hypothesis, frame in results.items():
        if frame is None or frame.empty:
            continue
        for _, row in frame.iterrows():
            violations.append(
                {
                    "entity_type": row.get("entity_type", "unknown"),
                    "entity_id": str(row.get("entity_id", "")),
                    "hypothesis": hypothesis,
                    "severity": row.get("severity", "raw"),
                    "anomaly_date": _stringify_date(row.get("anomaly_date")),
                }
            )

    if not violations:
        return _empty_report()

    violations_frame = pd.DataFrame(violations)
    aggregated = (
        violations_frame.groupby(["entity_type", "entity_id"], dropna=False)
        .agg(
            total_violations=("hypothesis", "size"),
            unique_hypotheses=("hypothesis", lambda value: sorted(set(value))),
            max_severity=("severity", lambda value: "strong" if "strong" in set(value) else "raw"),
            first_seen=(
                "anomaly_date",
                lambda value: min([str(item) for item in value if item]) if any(value) else "",
            ),
            last_seen=(
                "anomaly_date",
                lambda value: max([str(item) for item in value if item]) if any(value) else "",
            ),
        )
        .reset_index()
    )

    weights = {}
    for entity_type, group in aggregated.groupby("entity_type"):
        percentile_value = np.percentile(group["total_violations"], target_percentile)
        if percentile_value <= 0:
            weight = 1.0
        else:
            weight = 75 / percentile_value
        weights[entity_type] = max(min_weight, min(max_weight, float(weight)))

    aggregated["risk_score"] = aggregated.apply(
        lambda row: min(100.0, row["total_violations"] * weights.get(row["entity_type"], 1.0)),
        axis=1,
    ).round(1)
    aggregated["hypotheses"] = aggregated["unique_hypotheses"].apply(lambda value: ", ".join(value))
    aggregated["total_unique_hypotheses"] = aggregated["unique_hypotheses"].apply(len)
    aggregated = aggregated[REPORT_COLUMNS].sort_values("risk_score", ascending=False)
    return aggregated.reset_index(drop=True)


def get_risk_level(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"
