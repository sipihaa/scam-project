from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def export_to_json(
    all_results: dict[str, pd.DataFrame],
    final_report: pd.DataFrame,
    output_path: Path,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    anomalies = []
    for hypothesis, frame in all_results.items():
        if frame is None or frame.empty:
            continue
        for _, row in frame.iterrows():
            anomalies.append(
                {
                    "hypothesis": hypothesis,
                    "entity_type": row.get("entity_type"),
                    "entity_id": str(row.get("entity_id", "")),
                    "date": str(_json_value(row.get("anomaly_date"))),
                    "metric_name": row.get("metric_name"),
                    "metric_value": _json_value(row.get("metric_value")),
                    "threshold_value": _json_value(row.get("threshold_value")),
                    "severity": row.get("severity"),
                    "details": row.get("details", "{}"),
                }
            )

    hypothesis_stats = {
        hypothesis: int(0 if frame is None else len(frame))
        for hypothesis, frame in all_results.items()
    }

    dashboard_data = {
        "total_anomalies": len(anomalies),
        "hypothesis_stats": hypothesis_stats,
        "anomalies": anomalies,
        "top_cards": (
            final_report[final_report["entity_type"].eq("card")]
            .head(20)
            .to_dict("records")
            if not final_report.empty
            else []
        ),
        "top_validators": (
            final_report[final_report["entity_type"].eq("validator")]
            .head(20)
            .to_dict("records")
            if not final_report.empty
            else []
        ),
    }

    output_path.write_text(
        json.dumps(dashboard_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return dashboard_data
