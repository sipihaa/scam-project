"""Build card-level features once and save them to artifacts/ml/features.csv."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.services.data_loader import list_input_files, read_any_file
from src.services.paths import PATHS

# STUB_LABEL_SCHEMA: replace these names with real columns from the final labeled file.
LABEL_CARD_COLUMN = "card_id"
LABEL_TARGET_COLUMN = "is_fraud"

TX_CARD_COLUMN = "CARD"
TX_DATE_COLUMN = "DATE"
TX_TERMINAL_COLUMN = "TRM_ID"
TX_ROUTE_COLUMN = "ROUTE_NUM"
TX_CARRIER_COLUMN = "TRC_ID"
TX_CAT_COLUMN = "CAT"
TX_AMOUNT_COLUMN = "SUMM"

DATA_DIR = PATHS.raw_data
LABELS_PATH = PATHS.labels
FEATURES_PATH = PATHS.features
SEGMENT_CATS = ["201", "203", "204"]


def log(message: str) -> None:
    print(message, flush=True)


def sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_labels(path: Path) -> pd.DataFrame:
    labels = pd.read_csv(path, dtype=str, keep_default_na=False)
    labels = labels[[LABEL_CARD_COLUMN, LABEL_TARGET_COLUMN]].rename(
        columns={LABEL_CARD_COLUMN: "card_id", LABEL_TARGET_COLUMN: "is_fraud"}
    )
    labels["card_id"] = labels["card_id"].astype(str).str.strip()
    labels["is_fraud"] = labels["is_fraud"].astype(int)
    return labels.drop_duplicates("card_id")


def load_transactions(data_dir: Path) -> pd.DataFrame:
    frames = []
    for path in list_input_files(data_dir):
        frame = read_any_file(path).fillna("")
        frame.columns = [col.strip() for col in frame.columns]
        for column in frame.columns:
            frame[column] = frame[column].astype(str).str.strip()
        frames.append(frame)

    data = pd.concat(frames, ignore_index=True)
    data = data.rename(
        columns={
            TX_DATE_COLUMN: "date",
            TX_TERMINAL_COLUMN: "terminal_id",
            TX_ROUTE_COLUMN: "route_num",
            TX_CARRIER_COLUMN: "carrier_id",
            TX_CAT_COLUMN: "cat",
            TX_AMOUNT_COLUMN: "amount_raw",
            TX_CARD_COLUMN: "card_id",
        }
    )
    data["date"] = pd.to_datetime(data["date"], format="%d.%m.%Y %H:%M:%S", errors="coerce")
    data["cat"] = data["cat"].astype(str).str.lstrip("0")
    data["amount_rub"] = pd.to_numeric(data["amount_raw"], errors="coerce").fillna(0) / 100
    return data.dropna(subset=["date", "card_id"])


def entropy(values: pd.Series) -> float:
    counts = values.value_counts()
    if counts.empty:
        return 0.0
    probabilities = counts / counts.sum()
    return float(-(probabilities * np.log2(probabilities)).sum())


def top_share(data: pd.DataFrame, column: str) -> pd.Series:
    counts = data.groupby(["card_id", column], observed=True).size()
    top = counts.groupby(level=0).max()
    total = data.groupby("card_id", observed=True).size()
    return top / total


def top_pair_share(data: pd.DataFrame, first_column: str, second_column: str) -> pd.Series:
    counts = data.groupby(["card_id", first_column, second_column], observed=True).size()
    top = counts.groupby(level=0).max()
    total = data.groupby("card_id", observed=True).size()
    return top / total


def dominant_value(data: pd.DataFrame, column: str) -> pd.Series:
    counts = data.groupby(["card_id", column], observed=True).size().rename("count").reset_index()
    counts = counts.sort_values(["card_id", "count", column], ascending=[True, False, True])
    return counts.drop_duplicates("card_id").set_index("card_id")[column]


def max_count_in_time_bucket(data: pd.DataFrame, freq: str) -> pd.Series:
    counts = data.groupby(["card_id", data["date"].dt.floor(freq)], observed=True).size()
    return counts.groupby(level=0).max()


def max_same_terminal_count_in_time_bucket(data: pd.DataFrame, freq: str) -> pd.Series:
    counts = data.groupby(
        ["card_id", "terminal_id", data["date"].dt.floor(freq)],
        observed=True,
    ).size()
    return counts.groupby(level=0).max()


def build_features(transactions: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    data = transactions[transactions["card_id"].isin(labels["card_id"])].copy()
    data = data.sort_values(["card_id", "date"])
    data["day"] = data["date"].dt.date
    data["hour"] = data["date"].dt.hour
    data["weekday"] = data["date"].dt.weekday
    data["is_night"] = data["hour"].between(0, 4).astype(int)
    data["is_weekend"] = data["date"].dt.weekday.ge(5).astype(int)

    grouped = data.groupby("card_id", observed=True)
    features = grouped.agg(
        tx_count=("card_id", "size"),
        active_days=("day", "nunique"),
        unique_routes=("route_num", "nunique"),
        unique_terminals=("terminal_id", "nunique"),
        unique_carriers=("carrier_id", "nunique"),
        unique_cats=("cat", "nunique"),
        mean_amount=("amount_rub", "mean"),
        sum_amount=("amount_rub", "sum"),
        unique_amounts=("amount_rub", "nunique"),
        zero_amount_share=("amount_rub", lambda x: float((x == 0).mean())),
        night_share=("is_night", "mean"),
        weekend_share=("is_weekend", "mean"),
        active_hours_count=("hour", "nunique"),
        active_weekdays_count=("weekday", "nunique"),
    )
    features["tx_per_active_day"] = features["tx_count"] / features["active_days"].clip(lower=1)

    data["prev_date"] = grouped["date"].shift()
    data["prev_terminal_id"] = grouped["terminal_id"].shift()
    data["prev_route_num"] = grouped["route_num"].shift()
    data["gap_sec"] = (data["date"] - data["prev_date"]).dt.total_seconds()
    data["same_terminal"] = data["terminal_id"].eq(data["prev_terminal_id"])
    data["diff_terminal"] = data["prev_terminal_id"].notna() & ~data["same_terminal"]
    data["diff_route"] = data["prev_route_num"].notna() & data["route_num"].ne(data["prev_route_num"])
    data["gap_le_1m"] = data["gap_sec"].le(60)
    data["gap_le_5m"] = data["gap_sec"].le(300)
    data["gap_le_15m"] = data["gap_sec"].le(900)
    data["same_terminal_gap_le_1m"] = data["same_terminal"] & data["gap_le_1m"]
    data["same_terminal_gap_le_5m"] = data["same_terminal"] & data["gap_le_5m"]
    data["same_terminal_gap_le_15m"] = data["same_terminal"] & data["gap_le_15m"]
    data["diff_terminal_gap_le_1m"] = data["diff_terminal"] & data["gap_le_1m"]
    data["diff_terminal_gap_le_3m"] = data["diff_terminal"] & data["gap_sec"].le(180)
    data["diff_terminal_gap_le_5m"] = data["diff_terminal"] & data["gap_le_5m"]
    data["diff_route_gap_le_1m"] = data["diff_route"] & data["gap_le_1m"]
    data["diff_route_gap_le_3m"] = data["diff_route"] & data["gap_sec"].le(180)
    data["diff_route_gap_le_5m"] = data["diff_route"] & data["gap_le_5m"]

    gap_features = data.dropna(subset=["gap_sec"]).groupby("card_id", observed=True).agg(
        min_gap_sec=("gap_sec", "min"),
        median_gap_sec=("gap_sec", "median"),
        gap_le_1m_count=("gap_le_1m", "sum"),
        gap_le_5m_count=("gap_le_5m", "sum"),
        gap_le_15m_count=("gap_le_15m", "sum"),
        same_terminal_gap_le_1m_count=("same_terminal_gap_le_1m", "sum"),
        same_terminal_gap_le_5m_count=("same_terminal_gap_le_5m", "sum"),
        same_terminal_gap_le_15m_count=("same_terminal_gap_le_15m", "sum"),
        diff_terminal_gap_le_1m_count=("diff_terminal_gap_le_1m", "sum"),
        diff_terminal_gap_le_3m_count=("diff_terminal_gap_le_3m", "sum"),
        diff_terminal_gap_le_5m_count=("diff_terminal_gap_le_5m", "sum"),
        diff_route_gap_le_1m_count=("diff_route_gap_le_1m", "sum"),
        diff_route_gap_le_3m_count=("diff_route_gap_le_3m", "sum"),
        diff_route_gap_le_5m_count=("diff_route_gap_le_5m", "sum"),
        terminal_switch_count=("diff_terminal", "sum"),
        route_switch_count=("diff_route", "sum"),
    )
    features = features.join(gap_features, how="left")
    features["min_gap_diff_terminal_sec"] = data[data["diff_terminal"]].groupby(
        "card_id",
        observed=True,
    )["gap_sec"].min()
    features["min_gap_diff_route_sec"] = data[data["diff_route"]].groupby(
        "card_id",
        observed=True,
    )["gap_sec"].min()

    daily_counts = data.groupby(["card_id", "day"], observed=True).size()
    hourly_counts = data.groupby(["card_id", data["date"].dt.floor("h")], observed=True).size()
    features["max_tx_per_day"] = daily_counts.groupby(level=0).max()
    features["max_tx_per_hour"] = hourly_counts.groupby(level=0).max()
    features["max_tx_per_1m"] = max_count_in_time_bucket(data, "1min")
    features["max_tx_per_5m"] = max_count_in_time_bucket(data, "5min")
    features["max_tx_per_15m"] = max_count_in_time_bucket(data, "15min")
    features["max_same_terminal_tx_5m"] = max_same_terminal_count_in_time_bucket(data, "5min")
    features["max_same_terminal_tx_15m"] = max_same_terminal_count_in_time_bucket(data, "15min")
    features["top_terminal_share"] = top_share(data, "terminal_id")
    features["top_route_share"] = top_share(data, "route_num")
    features["top_terminal_route_share"] = top_pair_share(data, "terminal_id", "route_num")
    features["route_entropy"] = grouped["route_num"].agg(entropy)
    features["terminal_entropy"] = grouped["terminal_id"].agg(entropy)
    features["carrier_entropy"] = grouped["carrier_id"].agg(entropy)
    features["hour_entropy"] = grouped["hour"].agg(entropy)
    features["dominant_cat"] = dominant_value(data, "cat")

    daily_span = data.groupby(["card_id", "day"], observed=True)["date"].agg(["min", "max"])
    daily_span_hours = (daily_span["max"] - daily_span["min"]).dt.total_seconds() / 3600
    features["daily_span_hours_mean"] = daily_span_hours.groupby(level=0).mean()
    features["daily_span_hours_max"] = daily_span_hours.groupby(level=0).max()

    for cat in SEGMENT_CATS:
        features[f"cat_{cat}_share"] = grouped["cat"].apply(
            lambda x, cat=cat: float(x.eq(cat).mean())
        )

    features = features.reset_index()
    numeric_columns = features.select_dtypes(include=[np.number]).columns
    features[numeric_columns] = features[numeric_columns].replace([np.inf, -np.inf], np.nan)
    features[numeric_columns] = features[numeric_columns].fillna(0)
    features["terminal_switch_rate"] = features["terminal_switch_count"] / (
        features["tx_count"] - 1
    ).clip(lower=1)
    features["route_switch_rate"] = features["route_switch_count"] / (
        features["tx_count"] - 1
    ).clip(lower=1)

    percentile_columns = {
        "tx_count": "tx_count_percentile_in_cat",
        "unique_routes": "unique_routes_percentile_in_cat",
        "unique_terminals": "unique_terminals_percentile_in_cat",
        "min_gap_sec": "min_gap_percentile_in_cat",
        "same_terminal_gap_le_5m_count": "same_terminal_burst_percentile_in_cat",
        "night_share": "night_share_percentile_in_cat",
    }
    for source_column, output_column in percentile_columns.items():
        features[output_column] = features.groupby("dominant_cat", observed=True)[
            source_column
        ].rank(pct=True)
    features[list(percentile_columns.values())] = features[
        list(percentile_columns.values())
    ].fillna(0)
    features["dominant_cat"] = features["dominant_cat"].astype(str)
    features["segment"] = features["dominant_cat"].where(
        features["dominant_cat"].isin(SEGMENT_CATS),
        "other",
    )
    return features


def build_and_save_features(
    data_dir: Path = DATA_DIR,
    labels_path: Path = LABELS_PATH,
    output_path: Path = FEATURES_PATH,
) -> pd.DataFrame:
    started = time.perf_counter()
    log("Loading labels...")
    labels = load_labels(labels_path)
    log(f"Loaded {len(labels)} labels.")
    log("Loading transactions...")
    transactions = load_transactions(data_dir)
    log(f"Loaded {len(transactions)} transactions.")
    log("Building features...")
    features = build_features(transactions, labels)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(output_path, index=False)
    log(f"Saved {len(features)} cards and {len(features.columns)} columns to {output_path}.")
    log(f"Finished in {time.perf_counter() - started:.1f}s.")
    return features


def main() -> None:
    build_and_save_features()


if __name__ == "__main__":
    main()
