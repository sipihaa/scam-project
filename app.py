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
    risk_donut_chart,
    risk_histogram_chart,
    split_hypotheses,
)
from src.ui.components import (
    hypothesis_cards,
    metric_grid,
    page_header,
    panel,
    recommendation_strong,
    render_entity_table,
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


def active_paths() -> ProjectPaths:
    return st.session_state.get("active_paths", PATHS)


def active_source() -> str:
    return st.session_state.get("active_source", "project")


def activate_project_data() -> None:
    st.session_state["active_paths"] = PATHS
    st.session_state["active_source"] = "project"
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


def render_upload_panel(paths: ProjectPaths) -> None:
    with st.container(border=True):
        panel("📁 Загрузите отчёт")
        uploaded_files = st.file_uploader(
            "📂 Нажмите или перетащите CSV-файлы транзакций",
            type=["csv"],
            accept_multiple_files=True,
            help="Можно загрузить один или несколько CSV. Файлы проекта в data/raw не изменяются.",
        )
        has_active_upload = active_source() == "upload" and paths.raw_data.exists()

        left, middle, right = st.columns([1.2, 1.2, 1])
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
        with right:
            if st.button("Вернуться к data/raw", width="stretch"):
                activate_project_data()
                st.rerun()

        if run_rules and uploaded_files:
            result = run_action(
                "Запускаю rule-анализ загруженных CSV...",
                lambda: analyze_uploaded_files(uploaded_files, with_ml=False),
            )
            if result is not None:
                st.rerun()
        if run_full:
            if uploaded_files:
                result = run_action(
                    "Запускаю rule-анализ и ML-инференс по загруженным CSV. ML может занять пару минут на больших файлах...",
                    lambda: analyze_uploaded_files(uploaded_files, with_ml=True),
                )
            elif has_active_upload:
                result = run_action(
                    "Запускаю ML-инференс по активному загруженному набору...",
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
            st.info("Активный набор: файлы проекта из data/raw")


paths = active_paths()
render_upload_panel(paths)

artifacts = load_artifacts(paths)
report = artifacts["fraud_report"]
dashboard = artifacts["dashboard"]
rules_summary = artifacts["rules_summary"]
ml_summary = artifacts["ml_summary"]
inference_summary = artifacts["inference_summary"]

rules_tab, ml_tab = st.tabs(["Дашборд правил", "ML discovery"])

with rules_tab:
    if report.empty:
        with st.container(border=True):
            panel("📊 Общая статистика")
            st.info("Загрузите CSV и запустите анализ или вернитесь к уже подготовленным файлам из data/raw.")
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
            chart1, chart2, chart3 = st.columns(3)
            with chart1:
                st.markdown('<div class="chart-caption">Количество карт по уровню риска</div>', unsafe_allow_html=True)
                st.altair_chart(risk_histogram_chart(report), use_container_width=True)
            with chart2:
                st.markdown('<div class="chart-caption">Количество аномалий по гипотезам</div>', unsafe_allow_html=True)
                st.altair_chart(hypothesis_bar_chart(report), use_container_width=True)
            with chart3:
                st.markdown('<div class="chart-caption">Доля карт по уровню риска</div>', unsafe_allow_html=True)
                st.altair_chart(risk_donut_chart(report), use_container_width=True)

        with st.container(border=True):
            panel("🔍 Что мы искали")
            hypothesis_counts = split_hypotheses(report)
            hypothesis_cards(hypothesis_counts)
            selected = st.multiselect(
                "Фильтр по гипотезам",
                options=hypothesis_counts["hypothesis"].tolist(),
                format_func=lambda value: HYPOTHESIS_NAMES.get(value, value),
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
            high_risk_cards = int(cards["risk_score"].ge(70).sum()) if not cards.empty else 0
            medium_risk_cards = int(cards["risk_score"].between(40, 69.999).sum()) if not cards.empty else 0
            if high_risk_cards:
                recommendation_strong("Срочно:", f"{high_risk_cards} карт с высоким риском требуют проверки", "🔴")
            if medium_risk_cards:
                recommendation_strong("Внимание:", f"{medium_risk_cards} карт со средним риском", "🟡")
            if len(validators):
                recommendation_strong("Техническая проверка:", f"{len(validators)} валидаторов с аномалиями", "🔧")
            if not high_risk_cards and not medium_risk_cards and validators.empty:
                recommendation_strong("Готово:", "аномалий не обнаружено", "✅")

with ml_tab:
    prod_candidates = artifacts["prod_candidates"]
    prod_top_cards = artifacts["prod_top_cards"]

    with st.container(border=True):
        panel("🤖 ML discovery")
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
            "Для загруженных CSV используйте кнопку «Правила + ML», для текущего набора можно запустить только ML."
        )
        if st.button("Запустить ML для активного набора", width="stretch"):
            result = run_action(
                "Строю признаки и запускаю ML-инференс...",
                lambda: run_ml_for_paths(paths),
            )
            if result is not None:
                st.rerun()

    with st.container(border=True):
        panel("📈 ML-визуализация")
        chart1, chart2 = st.columns(2)
        ml_chart_source = prod_top_cards if not prod_top_cards.empty else prod_candidates
        with chart1:
            st.markdown('<div class="chart-caption">Распределение ML-оценки</div>', unsafe_allow_html=True)
            st.altair_chart(ml_score_chart(ml_chart_source), use_container_width=True)
        with chart2:
            st.markdown('<div class="chart-caption">Сегменты подозрительных карт</div>', unsafe_allow_html=True)
            st.altair_chart(ml_segments_chart(ml_chart_source), use_container_width=True)

    with st.container(border=True):
        panel("🧭 Кандидаты на новые паттерны")
        render_ml_table(prod_candidates, limit=20)

    with st.container(border=True):
        panel("🏁 Топ карт выбранной модели")
        render_ml_table(prod_top_cards, limit=50)
