from __future__ import annotations

from html import escape
from typing import Iterable

import pandas as pd
import streamlit as st

from src.ui.charts import HYPOTHESIS_NAMES


HYPOTHESIS_ICONS = {
    "H1": "📈",
    "H2": "🛣️",
    "H3": "⚡",
    "H4": "👥",
    "H7": "🌙",
    "H8": "🔄",
    "H10": "🎓",
    "H11": "💵",
    "H12": "💳",
    "H17": "💰",
    "H19": "❓",
    "H20": "📄",
    "H21": "📉",
}


def page_header() -> None:
    st.markdown(
        '<div class="main-header">🚌 Минтранс РФ · Сахалинская область</div>',
        unsafe_allow_html=True,
    )


def panel(title: str) -> None:
    st.markdown(f'<div class="panel-title">{escape(title)}</div>', unsafe_allow_html=True)


def format_number(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return escape(str(value))
    if number.is_integer():
        return f"{int(number):,}".replace(",", " ")
    return f"{number:,.2f}".replace(",", " ").replace(".", ",")


def metric_grid(metrics: Iterable[tuple[str, object]]) -> None:
    cards = []
    for label, value in metrics:
        cards.append(
            '<div class="kpi-card">'
            f'<div class="kpi-value">{format_number(value)}</div>'
            f'<div class="kpi-label">{escape(label)}</div>'
            "</div>"
        )
    st.markdown(f'<div class="kpi-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def hypothesis_cards(counts: pd.DataFrame) -> None:
    if counts.empty:
        st.info("Гипотезы пока не запускались.")
        return

    cards = []
    for _, row in counts.iterrows():
        hypothesis = str(row["hypothesis"])
        label = HYPOTHESIS_NAMES.get(hypothesis, str(row["label"]))
        icon = HYPOTHESIS_ICONS.get(hypothesis, "🔎")
        cards.append(
            '<div class="hypothesis-card">'
            f'<div class="hypothesis-count">{format_number(row["count"])}</div>'
            f'<div class="hypothesis-name">{escape(icon)} {escape(label)}</div>'
            "</div>"
        )
    st.markdown(f'<div class="hypotheses-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def risk_class(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def recommendation(text: str) -> None:
    st.markdown(f'<div class="recommendation-card">{escape(text)}</div>', unsafe_allow_html=True)


def recommendation_strong(prefix: str, text: str, marker: str) -> None:
    st.markdown(
        '<div class="recommendation-card">'
        f'<span class="recommendation-marker">{escape(marker)}</span> '
        f'<strong>{escape(prefix)}</strong> {escape(text)}'
        "</div>",
        unsafe_allow_html=True,
    )


def _safe_value(value: object, fallback: str = "—") -> str:
    if value is None:
        return fallback
    if isinstance(value, float) and pd.isna(value):
        return fallback
    text = str(value)
    return text if text and text != "nan" else fallback


def _date_short(value: object) -> str:
    text = _safe_value(value, "")
    if not text:
        return "—"
    parsed = pd.to_datetime(text, errors="coerce")
    if not pd.isna(parsed):
        return parsed.strftime("%d.%m")
    parts = text.split("-")
    if len(parts) == 3:
        return f"{parts[2]}.{parts[1]}"
    return text


def format_period(first: object, last: object) -> str:
    first_short = _date_short(first)
    last_short = _date_short(last)
    if first_short == "—" and last_short == "—":
        return "—"
    if first_short == last_short or last_short == "—":
        return first_short
    if first_short == "—":
        return last_short
    return f"{first_short} — {last_short}"


def short_id(value: object, max_len: int = 20) -> str:
    text = _safe_value(value)
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 3]}..."


def format_risk(value: object) -> tuple[str, str]:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return "—", "low"
    text = str(int(score)) if score.is_integer() else f"{score:.1f}".replace(".", ",")
    return text, risk_class(score)


def format_hypotheses(value: object) -> str:
    items = [item.strip() for item in _safe_value(value, "").split(",") if item.strip()]
    if not items:
        return "—"
    labels = []
    for item in items:
        icon = HYPOTHESIS_ICONS.get(item, "")
        name = HYPOTHESIS_NAMES.get(item, item)
        labels.append(f"{icon} {name}".strip())
    return ", ".join(labels)


def render_entity_table(frame: pd.DataFrame, entity_type: str, limit: int = 20) -> None:
    if frame.empty:
        st.info("Данных пока нет.")
        return

    entity_label = "Номер карты" if entity_type == "card" else "Валидатор"
    rows = []
    for _, row in frame.head(limit).iterrows():
        risk, risk_level = format_risk(row.get("risk_score"))
        rows.append(
            "<tr>"
            f'<td><code>{escape(short_id(row.get("entity_id")))}</code></td>'
            f'<td>{format_number(row.get("total_violations", 0))}</td>'
            f'<td class="wide-cell">{escape(format_hypotheses(row.get("hypotheses")))}</td>'
            f'<td class="risk-{risk_level}">{escape(risk)}</td>'
            f'<td>{escape(format_period(row.get("first_seen"), row.get("last_seen")))}</td>'
            "</tr>"
        )

    st.markdown(
        '<div class="table-wrap"><table class="dashboard-table">'
        "<thead><tr>"
        f"<th>{entity_label}</th><th>Нарушений</th><th>Тип нарушения</th><th>Риск</th><th>Период</th>"
        "</tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table></div>",
        unsafe_allow_html=True,
    )


def render_ml_table(frame: pd.DataFrame, limit: int = 20) -> None:
    if frame.empty:
        st.info("Данных пока нет. Запустите ML-инференс для активного набора.")
        return

    rows = []
    for _, row in frame.head(limit).iterrows():
        score = row.get("anomaly_score")
        try:
            score_text = f"{float(score):.3f}".replace(".", ",")
        except (TypeError, ValueError):
            score_text = "—"
        rows.append(
            "<tr>"
            f'<td><code>{escape(short_id(row.get("card_id")))}</code></td>'
            f'<td>{format_number(row.get("rank", "—"))}</td>'
            f'<td class="risk-high">{escape(score_text)}</td>'
            f'<td>{format_number(row.get("tx_count", "—"))}</td>'
            f'<td>{format_number(row.get("active_days", "—"))}</td>'
            f'<td>{format_number(row.get("unique_routes", "—"))}</td>'
            f'<td>{format_number(row.get("unique_terminals", "—"))}</td>'
            f'<td>{escape(_safe_value(row.get("segment")))}</td>'
            "</tr>"
        )

    st.markdown(
        '<div class="table-wrap"><table class="dashboard-table">'
        "<thead><tr>"
        "<th>Номер карты</th><th>Ранг</th><th>Оценка ML</th><th>Поездок</th>"
        "<th>Активных дней</th><th>Маршрутов</th><th>Валидаторов</th><th>Сегмент</th>"
        "</tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table></div>",
        unsafe_allow_html=True,
    )


def show_dataframe(frame: pd.DataFrame, height: int = 420) -> None:
    if frame.empty:
        st.info("Данных пока нет.")
        return
    st.dataframe(frame, width="stretch", height=height)
