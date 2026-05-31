from __future__ import annotations

import altair as alt
import pandas as pd


HYPOTHESIS_NAMES = {
    "H1": "Много поездок",
    "H2": "Всплеск маршрута",
    "H3": "Пачка транзакций",
    "H4": "Серия льготников",
    "H7": "Школьник ночью",
    "H8": "Школьник подряд",
    "H10": "Льгота в час пик",
    "H11": "Много наличных",
    "H12": "Мало наличных",
    "H17": "Нулевая сумма",
    "H19": "Неизвестная категория",
    "H20": "Дубли транзакций",
    "H21": "Неслучайный поток",
}

PRIMARY = "#0039A6"
WARNING = "#FFA726"
DANGER = "#D32F2F"
SUCCESS = "#4CAF50"
BORDER = "#e0e0e0"


def split_hypotheses(report: pd.DataFrame) -> pd.DataFrame:
    if report.empty or "hypotheses" not in report.columns:
        return pd.DataFrame(columns=["hypothesis", "label", "count"])
    rows = []
    for value in report["hypotheses"].fillna(""):
        for hypothesis in [item.strip() for item in str(value).split(",") if item.strip()]:
            rows.append({"hypothesis": hypothesis, "label": HYPOTHESIS_NAMES.get(hypothesis, hypothesis)})
    if not rows:
        return pd.DataFrame(columns=["hypothesis", "label", "count"])
    return (
        pd.DataFrame(rows)
        .groupby(["hypothesis", "label"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .reset_index(drop=True)
    )


def _card_rows(report: pd.DataFrame) -> pd.DataFrame:
    if report.empty:
        return report
    if "entity_type" not in report.columns:
        return report
    cards = report[report["entity_type"].eq("card")]
    return cards if not cards.empty else report


def risk_histogram(report: pd.DataFrame) -> pd.DataFrame:
    if report.empty or "risk_score" not in report.columns:
        return pd.DataFrame(columns=["risk_bucket", "count"])
    buckets = list(range(0, 101, 10))
    labels = [f"{start}-{end}" for start, end in zip(buckets[:-1], buckets[1:])]
    data = _card_rows(report).copy()
    data["risk_bucket"] = pd.cut(
        data["risk_score"].clip(0, 100),
        bins=buckets,
        labels=labels,
        include_lowest=True,
        right=False,
    )
    data.loc[data["risk_score"].eq(100), "risk_bucket"] = "90-100"
    return data.groupby("risk_bucket", observed=False).size().reset_index(name="count")


def risk_level_counts(report: pd.DataFrame) -> pd.DataFrame:
    if report.empty or "risk_score" not in report.columns:
        return pd.DataFrame(columns=["risk_level", "count"])
    data = _card_rows(report).copy()
    data["risk_level"] = pd.cut(
        data["risk_score"],
        bins=[-1, 40, 70, 101],
        labels=["Низкий (<40)", "Средний (40-69)", "Высокий (>=70)"],
        right=False,
    )
    return data.groupby("risk_level", observed=False).size().reset_index(name="count")


def _base_config(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_axis(
            grid=True,
            gridColor="#dddddd",
            labelColor="#666666",
            titleColor="#555555",
            labelFont="Segoe UI",
            titleFont="Segoe UI",
        )
        .configure_legend(labelFont="Segoe UI", titleFont="Segoe UI", orient="bottom")
        .configure_view(stroke=BORDER)
    )


def risk_histogram_chart(report: pd.DataFrame) -> alt.Chart:
    data = risk_histogram(report)
    chart = (
        alt.Chart(data)
        .mark_bar(color=PRIMARY, cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("risk_bucket:N", title="", sort=data["risk_bucket"].tolist(), axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("count:Q", title="", axis=alt.Axis(format=",.0f")),
            tooltip=[
                alt.Tooltip("risk_bucket:N", title="Диапазон риска"),
                alt.Tooltip("count:Q", title="Количество карт", format=","),
            ],
        )
        .properties(height=260)
    )
    return _base_config(chart)


def hypothesis_bar_chart(report: pd.DataFrame, limit: int = 6) -> alt.Chart:
    data = split_hypotheses(report).head(limit).copy()
    chart = (
        alt.Chart(data)
        .mark_bar(color=WARNING, cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
        .encode(
            y=alt.Y("label:N", title="", sort="-x", axis=alt.Axis(labelLimit=210)),
            x=alt.X("count:Q", title="", axis=alt.Axis(format=",.0f")),
            tooltip=[
                alt.Tooltip("label:N", title="Гипотеза"),
                alt.Tooltip("count:Q", title="Количество аномалий", format=","),
            ],
        )
        .properties(height=260)
    )
    return _base_config(chart)


def risk_donut_chart(report: pd.DataFrame) -> alt.Chart:
    data = risk_level_counts(report).copy()
    order = {
        "Высокий (>=70)": 0,
        "Средний (40-69)": 1,
        "Низкий (<40)": 2,
    }
    data["order"] = data["risk_level"].astype(str).map(order)
    chart = (
        alt.Chart(data)
        .mark_arc(innerRadius=70, outerRadius=120, stroke="#ffffff", strokeWidth=3)
        .encode(
            theta=alt.Theta("count:Q"),
            color=alt.Color(
                "risk_level:N",
                title="",
                scale=alt.Scale(
                    domain=["Высокий (>=70)", "Средний (40-69)", "Низкий (<40)"],
                    range=[DANGER, WARNING, SUCCESS],
                ),
                legend=alt.Legend(orient="bottom", columns=1),
            ),
            order=alt.Order("order:Q", sort="ascending"),
            tooltip=[
                alt.Tooltip("risk_level:N", title="Уровень риска"),
                alt.Tooltip("count:Q", title="Количество карт", format=","),
            ],
        )
        .properties(height=260)
    )
    return _base_config(chart)


def ml_score_chart(frame: pd.DataFrame) -> alt.Chart:
    if frame.empty or "anomaly_score" not in frame.columns:
        data = pd.DataFrame({"anomaly_score": []})
    else:
        data = frame.copy()
    chart = (
        alt.Chart(data)
        .mark_bar(color=PRIMARY, cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
        .encode(
            x=alt.X("anomaly_score:Q", title="Оценка ML", bin=alt.Bin(maxbins=14)),
            y=alt.Y("count():Q", title="", axis=alt.Axis(format=",.0f")),
            tooltip=[alt.Tooltip("count():Q", title="Количество карт", format=",")],
        )
        .properties(height=250)
    )
    return _base_config(chart)


def ml_segments_chart(frame: pd.DataFrame) -> alt.Chart:
    if frame.empty or "segment" not in frame.columns:
        data = pd.DataFrame(columns=["segment", "count"])
    else:
        data = frame.groupby("segment", dropna=False).size().reset_index(name="count").sort_values("count", ascending=False)
        data["segment"] = data["segment"].fillna("—").astype(str)
    chart = (
        alt.Chart(data.head(8))
        .mark_bar(color=WARNING, cornerRadiusTopRight=8, cornerRadiusBottomRight=8)
        .encode(
            y=alt.Y("segment:N", title="", sort="-x"),
            x=alt.X("count:Q", title="", axis=alt.Axis(format=",.0f")),
            tooltip=[
                alt.Tooltip("segment:N", title="Сегмент"),
                alt.Tooltip("count:Q", title="Количество карт", format=","),
            ],
        )
        .properties(height=250)
    )
    return _base_config(chart)
