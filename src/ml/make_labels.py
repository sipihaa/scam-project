"""Create card labels from the rule-based fraud report."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.services.data_loader import load_transactions
from src.services.paths import PATHS

OUTPUT_CARD_COLUMN = "card_id"
OUTPUT_LABEL_COLUMN = "is_fraud"

FRAUD_ENTITY_TYPE_COLUMN = "entity_type"
FRAUD_ENTITY_CARD_VALUE = "card"
FRAUD_CARD_COLUMN = "entity_id"

DATA_DIR = PATHS.raw_data
FRAUD_REPORT_PATH = PATHS.fraud_report
OUTPUT_PATH = PATHS.labels


def build_card_labels(
    data_dir: Path = DATA_DIR,
    fraud_report_path: Path = FRAUD_REPORT_PATH,
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    transactions = load_transactions(data_dir)
    all_cards = (
        transactions["CARD"]
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    fraud_report = pd.read_csv(fraud_report_path, dtype=str)
    fraud_cards = set(
        fraud_report.loc[
            fraud_report[FRAUD_ENTITY_TYPE_COLUMN].eq(FRAUD_ENTITY_CARD_VALUE),
            FRAUD_CARD_COLUMN,
        ]
        .astype(str)
        .str.strip()
    )

    labels = pd.DataFrame({OUTPUT_CARD_COLUMN: all_cards})
    labels[OUTPUT_LABEL_COLUMN] = labels[OUTPUT_CARD_COLUMN].isin(fraud_cards).astype(int)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    labels.to_csv(output_path, index=False)
    return labels


def main() -> None:
    labels = build_card_labels()

    print(f"Saved {len(labels)} labels to {OUTPUT_PATH}")
    print(f"Fraud labels: {int(labels[OUTPUT_LABEL_COLUMN].sum())}")


if __name__ == "__main__":
    main()
