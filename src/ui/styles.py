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
            padding: 0;
            margin-bottom: 22px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            border: 1px solid rgba(224,224,224,0.6);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 24px;
        }
        .panel-title {
            font-size: 1.25rem;
            margin-bottom: 20px;
            color: var(--primary);
            font-weight: 700;
            border-left: 4px solid var(--primary);
            padding-left: 16px;
            line-height: 1.35;
        }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
        }
        .kpi-card {
            background: #ffffff;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid var(--border);
        }
        .kpi-value {
            font-size: 2.2rem;
            font-weight: 800;
            margin: 10px 0;
            color: var(--primary);
            letter-spacing: 0;
        }
        .kpi-label {
            color: #111111;
            font-size: 0.98rem;
        }
        .hypotheses-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 12px;
        }
        .hypothesis-card {
            background: var(--primary-light);
            padding: 12px 14px;
            border-radius: 12px;
            min-width: 140px;
            min-height: 86px;
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
        }
        .chart-caption {
            color: #666666;
            font-size: 0.88rem;
            font-weight: 650;
            margin-bottom: 6px;
            text-align: center;
        }
        div[data-testid="stVegaLiteChart"] {
            background: #fafafa;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px;
            overflow: hidden;
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
            overflow: hidden;
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
            white-space: nowrap;
        }
        .wide-cell {
            max-width: 360px;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }
        @media (max-width: 900px) {
            .main-header {
                padding: 18px 22px;
            }
            .dashboard-table {
                min-width: 760px;
            }
            .table-wrap {
                overflow-x: auto;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
