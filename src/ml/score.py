from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from src.services.paths import PATHS


DEFAULT_TOP_PERCENT = 0.01


def load_model_bundle(model_path: Path = PATHS.model) -> dict:
    try:
        with model_path.open("rb") as file:
            return pickle.load(file)
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Не удалось загрузить ML-модель: в окружении не хватает зависимости "
            f"{exc.name}. Обычно нужен scikit-learn из requirements.txt."
        ) from exc


def load_features(features_path: Path = PATHS.features) -> pd.DataFrame:
    return pd.read_csv(
        features_path,
        dtype={"card_id": str, "dominant_cat": str, "segment": str},
    )


def load_known_fraud(labels_path: Path = PATHS.labels) -> set[str]:
    if not labels_path.exists():
        return set()
    labels = pd.read_csv(labels_path, dtype={"card_id": str})
    if "is_fraud" not in labels.columns:
        return set()
    return set(labels.loc[labels["is_fraud"].astype(int).eq(1), "card_id"].astype(str))


def prepare_matrix(features: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    feature_columns = bundle["features"]
    missing = [column for column in feature_columns if column not in features.columns]
    if missing:
        raise ValueError(f"В features.csv не хватает колонок для инференса: {', '.join(missing)}")

    matrix = features[feature_columns]
    matrix = matrix.replace([np.inf, -np.inf], np.nan).fillna(0)
    return matrix


def score_features(features: pd.DataFrame, bundle: dict) -> pd.DataFrame:
    excluded_cats = {str(cat) for cat in bundle.get("excluded_cats", [])}
    scored = features[~features["dominant_cat"].astype(str).isin(excluded_cats)].copy()
    if scored.empty:
        return scored.assign(anomaly_score=[], rank=[])

    matrix = prepare_matrix(scored, bundle)
    matrix = bundle["scaler"].transform(matrix)
    scored["anomaly_score"] = -bundle["model"].decision_function(matrix)
    scored["rank"] = scored["anomaly_score"].rank(method="first", ascending=False).astype(int)
    scored = scored.sort_values(["rank", "card_id"]).reset_index(drop=True)
    scored["model"] = bundle.get("model_name", "discovery_model")
    return scored


def select_top_percent(scored: pd.DataFrame, top_percent: float = DEFAULT_TOP_PERCENT) -> pd.DataFrame:
    if scored.empty:
        return scored.copy()
    top_n = max(1, round(len(scored) * top_percent))
    top_cards = scored.head(top_n).copy()
    top_cards["ml_fraud_flag"] = 1
    return top_cards


def run_inference(
    model_path: Path = PATHS.model,
    features_path: Path = PATHS.features,
    labels_path: Path = PATHS.labels,
    output_dir: Path = PATHS.ml_artifacts,
    top_percent: float = DEFAULT_TOP_PERCENT,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = load_model_bundle(model_path)
    features = load_features(features_path)
    scored = score_features(features, bundle)
    top_cards = select_top_percent(scored, top_percent)

    known_fraud = load_known_fraud(labels_path)
    new_pattern_candidates = top_cards[~top_cards["card_id"].isin(known_fraud)].copy()

    scores_path = output_dir / "inference_scores.csv"
    top_path = output_dir / "prod_top_percent_cards.csv"
    candidates_path = output_dir / "prod_new_candidates.csv"
    summary_path = output_dir / "inference_summary.json"

    scored.to_csv(scores_path, index=False)
    top_cards.to_csv(top_path, index=False)
    new_pattern_candidates.to_csv(candidates_path, index=False)

    summary = {
        "model_name": bundle.get("model_name", "discovery_model"),
        "features_path": str(features_path),
        "model_path": str(model_path),
        "scored_cards": int(len(scored)),
        "top_percent": float(top_percent),
        "top_cards": int(len(top_cards)),
        "known_fraud_excluded": int(len(top_cards) - len(new_pattern_candidates)),
        "new_pattern_candidates": int(len(new_pattern_candidates)),
        "outputs": [
            scores_path.name,
            top_path.name,
            candidates_path.name,
            summary_path.name,
        ],
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(run_inference(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
