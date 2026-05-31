from __future__ import annotations

import streamlit as st


def apply_dashboard_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --primary: #0039A6;
            --primary-light: #E6F0FA;
            --danger: #D32F2F;
            --warning: #FFA726;
            --success: #4CAF50;
            --bg: #f5f7fa;
            --card-bg: #ffffff;
            --border: #e0e0e0;
        }
        header[data-testid="stHeader"] {
            background: transparent;
            height: 0;
        }
        #MainMenu,
        footer,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        .stDeployButton {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
        }
        .stApp {
            background: var(--bg);
            color: #1f2933;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--border);
        }
        .block-container {
            max-width: 1400px;
            padding-top: 0;
            padding-left: 2rem;
            padding-right: 2rem;
            padding-bottom: 32px;
        }
        .main-header {
            background: var(--primary);
            color: white;
            padding: 20px max(32px, calc((100vw - 1400px) / 2 + 24px));
            border-radius: 0;
            margin: 0 calc(50% - 50vw) 24px calc(50% - 50vw);
            font-weight: 700;
            font-size: 1.3rem;
            line-height: 1.4;
        }
        .upload-note {
            border: 2px dashed var(--border);
            background: #fafbff;
            border-radius: 12px;
            padding: 26px 18px;
            margin-bottom: 14px;
            color: #111111;
            text-align: center;
            font-size: 1rem;
        }
        [data-testid="stFileUploaderDropzone"] {
            border: 2px dashed var(--border);
            border-radius: 12px;
            background: #fafbff;
            padding: 24px;
        }
        [data-testid="stFileUploaderDropzone"] button {
            min-width: 132px;
            font-size: 0 !important;
            position: relative;
        }
        [data-testid="stFileUploaderDropzone"] button::after {
            content: "Выбрать файл";
            font-size: 0.9rem;
            color: #111111;
            white-space: nowrap;
        }
        [data-testid="stFileUploaderDropzone"] button + div {
            font-size: 0 !important;
        }
        [data-testid="stFileUploaderDropzone"] button + div::after {
            content: "до 200 МБ • CSV";
            font-size: 0.88rem;
            color: #6b7280;
        }
        [data-testid="stFileUploaderDropzone"] small {
            font-size: 0 !important;
        }
        [data-testid="stFileUploaderDropzone"] small::after {
            content: "до 200 МБ • CSV";
            font-size: 0.88rem;
            color: #6b7280;
        }
        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--primary);
            background: #f0f7ff;
        }
        [data-testid="stTabs"] button[role="tab"] {
            font-weight: 650;
            color: var(--primary);
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 8px;
        }
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            background: var(--primary-light);
            border-radius: 10px 10px 0 0;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 24px 26px 28px 26px !important;
            margin: 0 0 24px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid rgba(224,224,224,0.95);
            overflow: visible !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 0 !important;
        }
        .panel-title {
            font-size: 1.25rem;
            margin: 0 0 22px 0;
            color: var(--primary);
            font-weight: 700;
            border-left: 4px solid var(--primary);
            padding-left: 16px;
            line-height: 1.35;
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 20px;
            margin-bottom: 2px;
        }
        .kpi-card {
            background: #ffffff;
            padding: 20px 16px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid var(--border);
            min-height: 132px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .kpi-value {
            font-size: 2rem;
            font-weight: 800;
            margin: 0 0 10px 0;
            color: var(--primary);
            letter-spacing: 0;
            line-height: 1.1;
        }
        .kpi-label {
            color: #111111;
            font-size: 0.96rem;
            line-height: 1.35;
            overflow-wrap: anywhere;
        }
        .hypotheses-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 14px;
            margin: 0 0 18px 0;
        }
        .hypothesis-card {
            background: var(--primary-light);
            padding: 14px 16px;
            border-radius: 12px;
            min-width: 158px;
            min-height: 92px;
            border: 2px solid transparent;
            text-align: center;
            transition: all 0.2s ease;
        }
        .hypothesis-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            background: #ffffff;
            border-color: var(--primary);
        }
        .hypothesis-count {
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--primary);
        }
        .hypothesis-name {
            font-size: 0.85rem;
            color: #555555;
            margin-top: 5px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 5px;
            line-height: 1.25;
        }
        .chart-caption {
            color: #666666;
            font-size: 0.88rem;
            font-weight: 650;
            margin: 0 0 8px 0;
            text-align: center;
            min-height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .chart-caption-wide {
            margin-top: 18px;
        }
        div[data-testid="stVegaLiteChart"] {
            background: #fafafa;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px;
            overflow: visible !important;
            min-height: 292px;
        }
        .donut-card {
            background: #fafafa;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px 18px;
            min-height: 236px;
            display: grid;
            grid-template-columns: minmax(150px, 0.9fr) minmax(170px, 1.1fr);
            gap: 14px;
            align-items: center;
            overflow: hidden;
        }
        .donut-svg {
            width: 100%;
            max-width: 210px;
            height: auto;
            justify-self: center;
            display: block;
        }
        .donut-svg circle {
            vector-effect: non-scaling-stroke;
        }
        .donut-total {
            fill: var(--primary);
            font-size: 1.2rem;
            font-weight: 800;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        .donut-total-label {
            fill: #6b7280;
            font-size: 0.7rem;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        .donut-legend {
            display: flex;
            flex-direction: column;
            gap: 10px;
            color: #4b5563;
            font-size: 0.9rem;
            min-width: 0;
        }
        .donut-legend-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            min-width: 0;
        }
        .donut-label {
            display: flex;
            align-items: center;
            gap: 8px;
            min-width: 0;
            line-height: 1.25;
        }
        .donut-dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
            flex: 0 0 auto;
        }
        .donut-value {
            color: #111111;
            font-weight: 700;
            white-space: nowrap;
        }
        .recommendation-card {
            background: #fff3e0;
            border-left: 4px solid var(--warning);
            padding: 16px 20px;
            border-radius: 12px;
            margin-bottom: 12px;
            color: #111111;
            font-size: 1rem;
        }
        .recommendation-marker {
            font-size: 1.1rem;
            display: inline-block;
            margin-right: 4px;
        }
        .muted {
            color: #6b7280;
            font-size: 0.9rem;
        }
        .risk-high {
            color: var(--danger);
            font-weight: 700;
        }
        .risk-medium {
            color: var(--warning);
            font-weight: 700;
        }
        .risk-low {
            color: var(--success);
            font-weight: 700;
        }
        .table-wrap {
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow-x: auto;
            background: #ffffff;
        }
        .dashboard-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.98rem;
        }
        .dashboard-table th,
        .dashboard-table td {
            padding: 13px 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }
        .dashboard-table th {
            background: var(--primary-light);
            font-weight: 700;
            color: #111111;
        }
        .dashboard-table tr:last-child td {
            border-bottom: 0;
        }
        .dashboard-table code {
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            color: #111111;
            background: transparent;
            padding: 0;
            white-space: normal;
            overflow-wrap: anywhere;
            word-break: break-word;
            line-height: 1.35;
        }
        .id-cell {
            min-width: 210px;
            max-width: 320px;
        }
        .wide-cell {
            max-width: 360px;
            min-width: 260px;
            line-height: 1.35;
        }
        [data-testid="stExpander"] {
            border: 1px solid var(--border);
            border-radius: 12px;
            background: #ffffff;
            margin-top: 12px;
            overflow: hidden;
        }
        [data-testid="stExpander"] details {
            padding: 2px 4px 8px 4px;
        }
        [data-testid="stExpander"] summary {
            color: var(--primary);
            font-weight: 700;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }
        @media (max-width: 1150px) {
            .kpi-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 900px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .main-header {
                padding: 18px 22px;
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                padding: 18px !important;
            }
            .kpi-grid {
                grid-template-columns: 1fr;
            }
            .dashboard-table {
                min-width: 760px;
            }
            .table-wrap {
                overflow-x: auto;
            }
            .donut-card {
                grid-template-columns: 1fr;
            }
            .donut-legend-row {
                justify-content: center;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
