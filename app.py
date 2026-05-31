from __future__ import annotations

import inspect
import shutil

import pandas as pd
import streamlit as st

from src.services.paths import PATHS, ProjectPaths
from src.services.pipeline import load_artifacts, run_full_pipeline, run_ml_pipeline, run_rules_pipeline
from src.services.uploads import create_uploaded_workspace
from src.ui.charts import (
    HYPOTHESIS_NAMES,
    hypothesis_bar_chart,
    ml_score_chart,
    ml_segments_chart,
    risk_histogram_chart,
    split_hypotheses,
)
from src.ui.components import (
    format_hypotheses,
    format_period,
    format_segment,
    hypothesis_cards,
    metric_grid,
    page_header,
    panel,
    recommendation_strong,
    render_entity_table,
    render_risk_donut,
    render_ml_table,
)
from src.ui.styles import apply_dashboard_style


st.set_page_config(
    page_title="Дашборд анализа ОТ",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_dashboard_style()
page_header()


def active_paths() -> ProjectPaths | None:
    paths = st.session_state.get("active_paths")
    if st.session_state.get("active_source") == "upload" and paths is not None:
        return paths
    return None


def active_source() -> str:
    return st.session_state.get("active_source", "empty")


if active_source() != "upload":
    st.session_state.pop("active_paths", None)
    st.session_state["active_source"] = "empty"
    st.session_state["uploaded_names"] = []


def run_action(label: str, action):
    with st.spinner(label):
        try:
            result = action()
        except Exception as exc:
            st.error(str(exc))
            return None
    st.success("Готово")
    return result


def _supports_model_path(function) -> bool:
    return "model_path" in inspect.signature(function).parameters


def ensure_workspace_model(paths: ProjectPaths) -> None:
    if paths.model == PATHS.model:
        return
    if not PATHS.model.exists():
        raise FileNotFoundError(f"Не найден файл модели {PATHS.model}")
    paths.model.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PATHS.model, paths.model)


def run_ml_for_paths(paths: ProjectPaths):
    if _supports_model_path(run_ml_pipeline):
        return run_ml_pipeline(paths, model_path=PATHS.model)
    ensure_workspace_model(paths)
    return run_ml_pipeline(paths)


def run_full_for_paths(paths: ProjectPaths):
    if _supports_model_path(run_full_pipeline):
        return run_full_pipeline(paths, model_path=PATHS.model)
    ensure_workspace_model(paths)
    return run_full_pipeline(paths)


def analyze_uploaded_files(uploaded_files: list[object], with_ml: bool) -> dict | None:
    paths, saved_names = create_uploaded_workspace(uploaded_files)
    st.session_state["active_paths"] = paths
    st.session_state["active_source"] = "upload"
    st.session_state["uploaded_names"] = saved_names
    if with_ml:
        return run_full_for_paths(paths)
    return run_rules_pipeline(paths)


def filter_by_hypotheses(frame: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    if not selected or frame.empty:
        return frame
    selected_set = set(selected)
    return frame[
        frame["hypotheses"].fillna("").apply(
            lambda value: bool(selected_set & {part.strip() for part in str(value).split(",")})
        )
    ]


def empty_artifacts() -> dict[str, object]:
    return {
        "rules_summary": {},
        "dashboard": {},
        "fraud_report": pd.DataFrame(),
        "ml_summary": {},
        "inference_summary": {},
        "new_candidates": pd.DataFrame(),
        "prod_candidates": pd.DataFrame(),
        "prod_top_cards": pd.DataFrame(),
        "model_metrics": pd.DataFrame(),
        "top_cards": pd.DataFrame(),
    }


def rules_export_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    rows = []
    for _, row in frame.iterrows():
        entity_type = row.get("entity_type")
        rows.append(
            {
                "Тип объекта": "Карта" if entity_type == "card" else "Валидатор",
                "Идентификатор": row.get("entity_id"),
                "Нарушений": row.get("total_violations"),
                "Гипотез": row.get("total_unique_hypotheses"),
                "Тип нарушения": format_hypotheses(row.get("hypotheses")),
                "Риск": row.get("risk_score"),
                "Период": format_period(row.get("first_seen"), row.get("last_seen")),
            }
        )
    return pd.DataFrame(rows)


def ml_export_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    rename_map = {
        "card_id": "Номер карты",
        "rank": "Ранг",
        "anomaly_score": "Оценка ML",
        "tx_count": "Поездок",
        "active_days": "Активных дней",
        "unique_routes": "Маршрутов",
        "unique_terminals": "Валидаторов",
        "segment": "Сегмент",
        "model": "Модель",
        "ml_fraud_flag": "ML-флаг",
    }
    columns = [column for column in rename_map if column in frame.columns]
    export = frame[columns].rename(columns=rename_map)
    if "Сегмент" in export.columns:
        export["Сегмент"] = export["Сегмент"].apply(format_segment)
    return export


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False).encode("utf-8-sig")


def render_download_button(label: str, frame: pd.DataFrame, file_name: str, key: str) -> None:
    st.download_button(
        label,
        data=csv_bytes(frame),
        file_name=file_name,
        mime="text/csv",
        width="stretch",
        disabled=frame.empty,
        key=key,
    )


def render_action_group(title: str, frame: pd.DataFrame, entity_type: str, file_name: str, key: str) -> None:
    with st.expander(f"{title}: {len(frame)}"):
        if frame.empty:
            st.info("В этой группе объектов нет.")
            return
        sorted_frame = frame.sort_values(["risk_score", "total_violations"], ascending=False)
        render_download_button(
            "Скачать полный список",
            rules_export_frame(sorted_frame),
            file_name,
            key,
        )
        render_entity_table(
            sorted_frame,
            entity_type,
            limit=20,
        )
        st.caption("В таблице показаны первые 20 объектов. Полный список можно скачать CSV-файлом.")


def render_upload_panel(paths: ProjectPaths | None) -> None:
    with st.container(border=True):
        panel("📁 Загрузите отчёт")
        uploaded_files = st.file_uploader(
            "📂 Нажмите или перетащите CSV-файлы транзакций",
            type=["csv"],
            accept_multiple_files=True,
            help="Можно загрузить один или несколько CSV. Анализ запускается только по загруженным файлам.",
        )
        has_active_upload = active_source() == "upload" and paths is not None and paths.raw_data.exists()

        left, middle = st.columns(2)
        with left:
            run_rules = st.button(
                "Анализировать правилами",
                width="stretch",
                disabled=not uploaded_files,
            )
        with middle:
            run_full = st.button(
                "Правила + ML",
                type="primary",
                width="stretch",
                disabled=not uploaded_files and not has_active_upload,
            )

        if run_rules and uploaded_files:
            result = run_action(
                "Запускаю анализ правилами для загруженных CSV...",
                lambda: analyze_uploaded_files(uploaded_files, with_ml=False),
            )
            if result is not None:
                st.rerun()
        if run_full:
            if uploaded_files:
                result = run_action(
                    "Запускаю анализ правилами и ML-проверку загруженных CSV. Это может занять пару минут на больших файлах...",
                    lambda: analyze_uploaded_files(uploaded_files, with_ml=True),
                )
            elif has_active_upload:
                result = run_action(
                    "Запускаю ML-проверку активного загруженного набора...",
                    lambda: run_ml_for_paths(paths),
                )
            else:
                st.error("Сначала загрузите CSV-файлы.")
                result = None
            if result is not None:
                st.rerun()

        if active_source() == "upload":
            names = ", ".join(st.session_state.get("uploaded_names", []))
            st.success(f"✅ Активный набор: загруженные файлы ({names})")
        else:
            st.info("Загрузите CSV-файлы, чтобы построить дашборд.")


paths = active_paths()
render_upload_panel(paths)

artifacts = load_artifacts(paths) if paths is not None else empty_artifacts()
report = artifacts["fraud_report"]
dashboard = artifacts["dashboard"]
rules_summary = artifacts["rules_summary"]
ml_summary = artifacts["ml_summary"]
inference_summary = artifacts["inference_summary"]

rules_tab, ml_tab = st.tabs(["Дашборд правил", "ML-поиск"])

with rules_tab:
    if report.empty:
        with st.container(border=True):
            panel("📊 Общая статистика")
            st.info("Загрузите CSV и запустите анализ, чтобы построить дашборд.")
    else:
        cards = report[report["entity_type"].eq("card")]
        validators = report[report["entity_type"].eq("validator")]
        high_risk = int(report["risk_score"].ge(70).sum()) if "risk_score" in report else 0

        with st.container(border=True):
            panel("📊 Общая статистика")
            metric_grid(
                [
                    ("Всего аномалий", rules_summary.get("total_anomalies", dashboard.get("total_anomalies", "—"))),
                    ("Подозрительных карт", len(cards)),
                    ("Подозрительных валидаторов", len(validators)),
                    ("С высоким риском", high_risk),
                ]
            )

        with st.container(border=True):
            panel("📈 Визуализация аномалий")
            chart1, chart2 = st.columns(2)
            with chart1:
                st.markdown('<div class="chart-caption">Количество карт по уровню риска</div>', unsafe_allow_html=True)
                st.altair_chart(risk_histogram_chart(report), use_container_width=True)
            with chart2:
                st.markdown('<div class="chart-caption">Количество аномалий по гипотезам</div>', unsafe_allow_html=True)
                st.altair_chart(hypothesis_bar_chart(report), use_container_width=True)
            _, chart3, _ = st.columns([0.25, 0.5, 0.25])
            with chart3:
                st.markdown('<div class="chart-caption chart-caption-wide">Доля карт по уровню риска</div>', unsafe_allow_html=True)
                render_risk_donut(report)

        with st.container(border=True):
            panel("🔍 Что мы искали")
            hypothesis_counts = split_hypotheses(report)
            hypothesis_cards(hypothesis_counts)
            selected = st.multiselect(
                "Фильтр по гипотезам",
                options=hypothesis_counts["hypothesis"].tolist(),
                format_func=lambda value: HYPOTHESIS_NAMES.get(value, value),
                placeholder="Выберите гипотезы",
            )
        filtered = filter_by_hypotheses(report, selected)

        with st.container(border=True):
            panel("🃏 Топ-20 подозрительных карт")
            card_top = (
                filtered[filtered["entity_type"].eq("card")]
                .sort_values(["risk_score", "total_violations"], ascending=False)
                .head(20)
            )
            render_entity_table(card_top, "card", limit=20)

        with st.container(border=True):
            panel("📟 Топ-20 подозрительных валидаторов")
            validator_top = (
                filtered[filtered["entity_type"].eq("validator")]
                .sort_values(["risk_score", "total_violations"], ascending=False)
                .head(20)
            )
            render_entity_table(validator_top, "validator", limit=20)

        with st.container(border=True):
            panel("📋 Что делать?")
            high_risk_card_rows = cards[cards["risk_score"].ge(70)] if not cards.empty else cards
            medium_risk_card_rows = cards[cards["risk_score"].between(40, 69.999)] if not cards.empty else cards
            validator_rows = validators.copy()
            high_risk_cards = len(high_risk_card_rows)
            medium_risk_cards = len(medium_risk_card_rows)
            if high_risk_cards:
                recommendation_strong("Срочно:", f"{high_risk_cards} карт с высоким риском требуют проверки", "🔴")
            if medium_risk_cards:
                recommendation_strong("Внимание:", f"{medium_risk_cards} карт со средним риском", "🟡")
            if len(validators):
                recommendation_strong("Техническая проверка:", f"{len(validators)} валидаторов с аномалиями", "🔧")
            if not high_risk_cards and not medium_risk_cards and validators.empty:
                recommendation_strong("Готово:", "аномалий не обнаружено", "✅")
            render_action_group(
                "Карты с высоким риском",
                high_risk_card_rows,
                "card",
                "cards_high_risk.csv",
                "download_high_risk_cards",
            )
            render_action_group(
                "Карты со средним риском",
                medium_risk_card_rows,
                "card",
                "cards_medium_risk.csv",
                "download_medium_risk_cards",
            )
            render_action_group(
                "Валидаторы с аномалиями",
                validator_rows,
                "validator",
                "validators_with_anomalies.csv",
                "download_validators",
            )

with ml_tab:
    prod_candidates = artifacts["prod_candidates"]

    with st.container(border=True):
        panel("🤖 ML-поиск")
        metric_grid(
            [
                ("Карт с признаками", ml_summary.get("features", "—")),
                ("Метки правил", ml_summary.get("fraud_labels", "—")),
                ("Проскорено карт", inference_summary.get("scored_cards", "—")),
                ("Новых кандидатов", inference_summary.get("new_pattern_candidates", "—")),
            ]
        )
        st.caption(
            "ML ищет нетипичные карты поверх уже рассчитанных признаков. "
            "Для загруженных CSV используйте кнопку «Правила + ML», для уже активного загруженного набора можно запустить только ML."
        )
        if st.button("Запустить ML для активного набора", width="stretch", disabled=paths is None):
            result = run_action(
                "Строю признаки и запускаю ML-проверку...",
                lambda: run_ml_for_paths(paths),
            )
            if result is not None:
                st.rerun()

    with st.container(border=True):
        panel("📈 ML-визуализация")
        ml_chart_source = prod_candidates
        if ml_chart_source.empty:
            st.info("Запустите «Правила + ML», чтобы построить ML-графики.")
        else:
            chart1, chart2 = st.columns(2)
            with chart1:
                st.markdown('<div class="chart-caption">Распределение ML-оценки</div>', unsafe_allow_html=True)
                st.altair_chart(ml_score_chart(ml_chart_source), use_container_width=True)
            with chart2:
                st.markdown('<div class="chart-caption">Сегменты подозрительных карт</div>', unsafe_allow_html=True)
                st.altair_chart(ml_segments_chart(ml_chart_source), use_container_width=True)

    with st.container(border=True):
        panel("🧭 Кандидаты на новые паттерны")
        render_download_button(
            "Скачать полный список новых кандидатов",
            ml_export_frame(prod_candidates),
            "ml_new_pattern_candidates.csv",
            "download_ml_candidates",
        )
        render_ml_table(prod_candidates, limit=20)
