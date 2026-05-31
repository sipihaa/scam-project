from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.ml.make_features import build_and_save_features
from src.ml.make_labels import build_card_labels
from src.rules.aggregator import aggregate_results
from src.rules.engine import run_hypotheses
from src.rules.export import export_to_json
from src.services.data_loader import load_transactions
from src.services.paths import PATHS, ProjectPaths, ensure_artifact_dirs


def _safe_iso(value: Any) -> str | None:
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def transaction_summary(transactions: pd.DataFrame) -> dict[str, Any]:
    return {
        "transactions": int(len(transactions)),
        "period_start": _safe_iso(transactions["datetime"].min()) if "datetime" in transactions else None,
        "period_end": _safe_iso(transactions["datetime"].max()) if "datetime" in transactions else None,
        "cards": int(transactions["CARD"].nunique()) if "CARD" in transactions else 0,
        "validators": int(transactions["TRM_ID"].nunique()) if "TRM_ID" in transactions else 0,
        "routes": int(transactions["ROUTE_NUM"].nunique()) if "ROUTE_NUM" in transactions else 0,
        "categories": int(transactions["CAT_NUM"].nunique()) if "CAT_NUM" in transactions else 0,
    }


def run_rules_pipeline(
    paths: ProjectPaths = PATHS,
    selected_hypotheses: list[str] | None = None,
) -> dict[str, Any]:
    ensure_artifact_dirs(paths)
    transactions = load_transactions(paths.raw_data)
    results = run_hypotheses(transactions, selected=selected_hypotheses)
    final_report = aggregate_results(results)
    final_report.to_csv(paths.fraud_report, index=False)
    dashboard_data = export_to_json(results, final_report, paths.dashboard_json)

    summary = {
        "stage": "rules",
        **transaction_summary(transactions),
        "entities": int(len(final_report)),
        "total_anomalies": int(dashboard_data["total_anomalies"]),
        "fraud_report": str(paths.fraud_report),
        "dashboard_json": str(paths.dashboard_json),
        "hypotheses": {name: int(len(frame)) for name, frame in results.items()},
    }
    (paths.rules_artifacts / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def run_ml_pipeline(
    paths: ProjectPaths = PATHS,
    model_path: Path | None = None,
) -> dict[str, Any]:
    ensure_artifact_dirs(paths)
    model_path = model_path or paths.model
    if not paths.fraud_report.exists():
        raise FileNotFoundError(
            f"Не найден rule-отчёт {paths.fraud_report}. Сначала запустите rule-пайплайн."
        )
    if not model_path.exists():
        raise FileNotFoundError(
            f"Не найден файл модели {model_path}. Положите готовый discovery_model.pkl в artifacts/ml/."
        )

    labels = build_card_labels(
        data_dir=paths.raw_data,
        fraud_report_path=paths.fraud_report,
        output_path=paths.labels,
    )
    features = build_and_save_features(
        data_dir=paths.raw_data,
        labels_path=paths.labels,
        output_path=paths.features,
    )

    from src.ml.score import run_inference

    inference_summary = run_inference(
        model_path=model_path,
        features_path=paths.features,
        labels_path=paths.labels,
        output_dir=paths.ml_artifacts,
    )

    summary = {
        "stage": "ml",
        "mode": "inference",
        "model_path": str(model_path),
        "labels": int(len(labels)),
        "fraud_labels": int(labels["is_fraud"].sum()),
        "features": int(len(features)),
        "inference": inference_summary,
    }
    (paths.ml_artifacts / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def run_full_pipeline(
    paths: ProjectPaths = PATHS,
    model_path: Path | None = None,
) -> dict[str, Any]:
    rules = run_rules_pipeline(paths)
    ml = run_ml_pipeline(paths, model_path=model_path)
    summary = {"rules": rules, "ml": ml}
    (paths.artifacts / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path, **kwargs: Any) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, **kwargs)


def load_artifacts(paths: ProjectPaths = PATHS) -> dict[str, Any]:
    return {
        "rules_summary": read_json(paths.rules_artifacts / "summary.json"),
        "dashboard": read_json(paths.dashboard_json),
        "fraud_report": read_csv(paths.fraud_report, dtype={"entity_id": str}),
        "ml_summary": read_json(paths.ml_artifacts / "summary.json"),
        "inference_summary": read_json(paths.ml_artifacts / "inference_summary.json"),
        "new_candidates": read_csv(paths.ml_artifacts / "new_candidates.csv", dtype={"card_id": str}),
        "prod_candidates": read_csv(paths.ml_artifacts / "prod_new_candidates.csv", dtype={"card_id": str}),
        "prod_top_cards": read_csv(paths.ml_artifacts / "prod_top_percent_cards.csv", dtype={"card_id": str}),
        "model_metrics": read_csv(paths.ml_artifacts / "model_metrics.csv"),
        "top_cards": read_csv(paths.ml_artifacts / "top_cards.csv", dtype={"card_id": str}),
    }
