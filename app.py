import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except Exception:
    AUTOREFRESH_AVAILABLE = False


# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="投资雷达",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 基础工具函数
# ============================================================

def now_cn():
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def safe_float(x, default=np.nan):
    try:
        if isinstance(x, pd.Series):
            x = x.iloc[0]
        return float(x)
    except Exception:
        return default


def flatten_yfinance_columns(df):
    if df is None or df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            col[0] if isinstance(col, tuple) else col
            for col in df.columns
        ]

    return df


def color_level(level):
    if level == "green":
        return "🟢"
    if level == "yellow":
        return "🟡"
    if level == "red":
        return "🔴"
    if level == "blue":
        return "🔵"
    return "⚪"


def level_class(level):
    if level == "green":
        return "good"
    if level == "yellow":
        return "warn"
    if level == "red":
        return "bad"
    if level == "blue":
        return "info"
    return "neutral"


def delta_text(current, previous, suffix=""):
    try:
        delta = float(current) - float(previous)
        sign = "+" if delta >= 0 else ""
        return f"{sign}{delta:.2f}{suffix}"
    except Exception:
        return "-"


# ============================================================
# 侧边栏：控制区 + 导航
# ============================================================

with st.sidebar:
    st.markdown("## 📊 投资雷达")
    st.caption("个人投资分析系统")
    st.caption(now_cn().strftime("更新时间：%Y-%m-%d %H:%M:%S"))

    st.markdown("---")

    theme_mode = st.radio(
        "显示模式",
        ["🌙 夜间模式", "🌞 明亮模式"],
        index=0
    )

    auto_refresh = st.toggle(
        "自动刷新",
        value=True
    )

    refresh_interval = st.selectbox(
        "刷新频率",
        ["1 分钟", "5 分钟", "15 分钟", "30 秒"],
        index=1
    )

    interval_map = {
        "30 秒": 30,
        "1 分钟": 60,
        "5 分钟": 300,
        "15 分钟": 900
    }

    refresh_seconds = interval_map[refresh_interval]

    if st.button("🔄 立即刷新", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if not AUTOREFRESH_AVAILABLE:
        st.warning("缺少 streamlit-autorefresh，请检查 requirements.txt。")

    st.markdown("---")

    page = st.radio(
        "模块导航",
        [
            "① 周期罗盘",
            "② 市场雷达",
            "③ 原则引擎",
            "④ 执行系统"
        ],
        index=0
    )

    st.markdown("---")
    st.caption("框架：达利欧周期 + 大师原则 + 执行复盘")


if auto_refresh and AUTOREFRESH_AVAILABLE:
    st_autorefresh(
        interval=refresh_seconds * 1000,
        key="investment_radar_refresh"
    )


# ============================================================
# 主题 CSS
# ============================================================

if theme_mode == "🌙 夜间模式":
    PLOT_TEMPLATE = "plotly_dark"
    FONT_COLOR = "#f8fafc"
    PAGE_BG = "#070b12"

    st.markdown(
        """
        <style>
        :root {
            --bg: #070b12;
            --sidebar: #0f172a;
            --panel: #111827;
            --panel2: #172033;
            --panel3: #1e293b;
            --border: #2f3b52;
            --text: #f8fafc;
            --muted: #94a3b8;
            --muted2: #64748b;
            --good: #22c55e;
            --warn: #f59e0b;
            --bad: #ef4444;
            --info: #38bdf8;
            --purple: #8b5cf6;
            --cyan: #06b6d4;
        }

        .stApp {
            background: radial-gradient(circle at top left, #111827 0%, #070b12 42%, #05070d 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 3.1rem;
            padding-left: 4rem;
            padding-right: 4rem;
            max-width: 1280px;
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #0b1220 100%);
            border-right: 1px solid var(--border);
        }

        section[data-testid="stSidebar"] * {
            color: var(--text);
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--text) !important;
            letter-spacing: -0.03em;
        }

        p, li, span, div {
            color: inherit;
        }

        hr {
            border-color: var(--border);
        }

        .main-header {
            background: linear-gradient(135deg, rgba(30,41,59,0.96) 0%, rgba(15,23,42,0.96) 100%);
            border: 1px solid rgba(148,163,184,0.22);
            border-radius: 24px;
            padding: 30px 34px;
            margin-bottom: 28px;
            box-shadow: 0 24px 60px rgba(0,0,0,0.35);
        }

        .main-title {
            font-size: 38px;
            font-weight: 900;
            color: #f8fafc;
            margin-bottom: 8px;
            letter-spacing: -0.04em;
        }

        .main-subtitle {
            font-size: 15px;
            color: var(--muted);
            line-height: 1.6;
        }

        .kpi-card {
            background: linear-gradient(180deg, rgba(30,41,59,0.95), rgba(15,23,42,0.95));
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 22px;
            padding: 22px;
            min-height: 168px;
            box-shadow: 0 18px 45px rgba(0,0,0,0.28);
        }

        .kpi-title {
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 10px;
            font-weight: 650;
        }

        .kpi-value {
            font-size: 30px;
            font-weight: 900;
            color: #f8fafc;
            line-height: 1.2;
        }

        .kpi-desc {
            font-size: 14px;
            color: #cbd5e1;
            margin-top: 8px;
            line-height: 1.55;
        }

        .kpi-note {
            font-size: 12px;
            color: var(--muted);
            margin-top: 10px;
            line-height: 1.45;
        }

        .section-card {
            background: rgba(15,23,42,0.86);
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 22px;
            padding: 24px;
            margin-bottom: 22px;
            box-shadow: 0 18px 45px rgba(0,0,0,0.22);
            line-height: 1.75;
        }

        .good { color: var(--good) !important; font-weight: 850; }
        .warn { color: var(--warn) !important; font-weight: 850; }
        .bad { color: var(--bad) !important; font-weight: 850; }
        .info { color: var(--info) !important; font-weight: 850; }
        .neutral { color: #cbd5e1 !important; font-weight: 850; }

        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, rgba(30,41,59,0.92), rgba(15,23,42,0.92));
            border: 1px solid rgba(148,163,184,0.18);
            padding: 18px;
            border-radius: 18px;
            box-shadow: 0 14px 35px rgba(0,0,0,0.2);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-weight: 650;
        }

        div[data-testid="stMetricValue"] {
            color: #f8fafc;
            font-weight: 850;
        }

        div[data-testid="stMetricDelta"] {
            color: var(--good);
        }

        .custom-table {
            width: 100%;
            border-collapse: collapse;
            border-radius: 18px;
            overflow: hidden;
            margin-top: 12px;
            margin-bottom: 24px;
            background: rgba(15,23,42,0.92);
            border: 1px solid rgba(148,163,184,0.18);
            box-shadow: 0 14px 35px rgba(0,0,0,0.18);
        }

        .custom-table th {
            background: rgba(30,41,59,0.96);
            color: #f8fafc;
            font-weight: 800;
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(148,163,184,0.18);
            font-size: 14px;
        }

        .custom-table td {
            color: #dbeafe;
            padding: 14px 16px;
            border-bottom: 1px solid rgba(148,163,184,0.12);
            font-size: 14px;
            vertical-align: top;
            line-height: 1.55;
        }

        .custom-table tr:nth-child(even) {
            background: rgba(17,24,39,0.72);
        }

        .custom-table tr:hover {
            background: rgba(30,41,59,0.92);
        }

        .alert-box {
            border-radius: 18px;
            padding: 16px 18px;
            margin: 12px 0;
            background: rgba(15,23,42,0.92);
            border: 1px solid rgba(148,163,184,0.16);
            box-shadow: 0 12px 30px rgba(0,0,0,0.18);
            line-height: 1.55;
        }

        .alert-good {
            border-left: 5px solid var(--good);
        }

        .alert-warn {
            border-left: 5px solid var(--warn);
        }

        .alert-bad {
            border-left: 5px solid var(--bad);
        }

        .principle-box {
            background: linear-gradient(180deg, rgba(30,41,59,0.92), rgba(15,23,42,0.92));
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 22px;
            padding: 22px;
            margin-bottom: 18px;
            box-shadow: 0 16px 40px rgba(0,0,0,0.2);
        }

        .principle-title {
            font-size: 21px;
            font-weight: 900;
            color: #f8fafc;
            margin-bottom: 12px;
        }

        .principle-line {
            color: #cbd5e1;
            margin-bottom: 10px;
            font-size: 14px;
            line-height: 1.6;
        }

        .principle-label {
            color: var(--muted);
            font-weight: 850;
        }

        .allocation-card {
            background: linear-gradient(180deg, rgba(30,41,59,0.94), rgba(15,23,42,0.94));
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 22px;
            padding: 22px;
            margin-bottom: 16px;
            box-shadow: 0 18px 45px rgba(0,0,0,0.22);
        }

        .allocation-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 16px;
            font-weight: 850;
            color: #f8fafc;
            margin-bottom: 10px;
        }

        .allocation-role {
            color: var(--muted);
            font-size: 13px;
            margin-bottom: 12px;
            line-height: 1.45;
        }

        .bar-bg {
            width: 100%;
            height: 12px;
            border-radius: 999px;
            background: rgba(51,65,85,0.9);
            overflow: hidden;
        }

        .bar-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #06b6d4, #8b5cf6);
        }

        .action-card {
            background: linear-gradient(180deg, rgba(30,41,59,0.94), rgba(15,23,42,0.94));
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 22px;
            padding: 22px;
            margin-bottom: 16px;
            box-shadow: 0 18px 45px rgba(0,0,0,0.22);
        }

        .action-title {
            font-size: 18px;
            font-weight: 900;
            color: #f8fafc;
            margin-bottom: 10px;
        }

        .action-text {
            color: #cbd5e1;
            font-size: 14px;
            line-height: 1.65;
        }

        div[data-testid="stAlert"] {
            background: rgba(15,23,42,0.9);
            color: var(--text);
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 16px;
        }

        .stTextArea textarea {
            background: rgba(15,23,42,0.92) !important;
            color: var(--text) !important;
            border: 1px solid rgba(148,163,184,0.2) !important;
            border-radius: 16px !important;
        }

        .stButton button {
            background: linear-gradient(90deg, #2563eb, #7c3aed) !important;
            color: white !important;
            border: 0 !important;
            border-radius: 14px !important;
            font-weight: 800 !important;
            min-height: 42px !important;
        }

        .stSelectbox div[data-baseweb="select"] > div {
            background: rgba(15,23,42,0.92) !important;
            border: 1px solid rgba(148,163,184,0.2) !important;
            color: #f8fafc !important;
            border-radius: 14px !important;
        }

        .stRadio label {
            background: transparent !important;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

else:
    PLOT_TEMPLATE = "plotly_white"
    FONT_COLOR = "#111827"
    PAGE_BG = "#ffffff"

    st.markdown(
        """
        <style>
        :root {
            --bg: #ffffff;
            --sidebar: #f8fafc;
            --panel: #ffffff;
            --panel2: #f8fafc;
            --border: #e2e8f0;
            --text: #111827;
            --muted: #64748b;
            --good: #0a8f3c;
            --warn: #b7791f;
            --bad: #c53030;
            --info: #0284c7;
        }

        .stApp {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            color: var(--text);
        }

        .block-container {
            padding-top: 3.1rem;
            padding-left: 4rem;
            padding-right: 4rem;
            max-width: 1280px;
        }

        section[data-testid="stSidebar"] {
            background: #f8fafc;
            border-right: 1px solid var(--border);
        }

        .main-header {
            background: linear-gradient(135deg, #ffffff 0%, #eef2ff 100%);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 30px 34px;
            margin-bottom: 28px;
            box-shadow: 0 16px 40px rgba(15,23,42,0.06);
        }

        .main-title {
            font-size: 38px;
            font-weight: 900;
            color: #111827;
            margin-bottom: 8px;
            letter-spacing: -0.04em;
        }

        .main-subtitle {
            font-size: 15px;
            color: var(--muted);
            line-height: 1.6;
        }

        .kpi-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 22px;
            min-height: 168px;
            box-shadow: 0 14px 35px rgba(15,23,42,0.06);
        }

        .kpi-title {
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 10px;
            font-weight: 650;
        }

        .kpi-value {
            font-size: 30px;
            font-weight: 900;
            color: #111827;
            line-height: 1.2;
        }

        .kpi-desc {
            font-size: 14px;
            color: #334155;
            margin-top: 8px;
            line-height: 1.55;
        }

        .kpi-note {
            font-size: 12px;
            color: var(--muted);
            margin-top: 10px;
            line-height: 1.45;
        }

        .section-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 24px;
            margin-bottom: 22px;
            box-shadow: 0 14px 35px rgba(15,23,42,0.06);
            line-height: 1.75;
        }

        .good { color: var(--good) !important; font-weight: 850; }
        .warn { color: var(--warn) !important; font-weight: 850; }
        .bad { color: var(--bad) !important; font-weight: 850; }
        .info { color: var(--info) !important; font-weight: 850; }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--border);
            padding: 18px;
            border-radius: 18px;
            box-shadow: 0 14px 35px rgba(15,23,42,0.05);
        }

        .custom-table {
            width: 100%;
            border-collapse: collapse;
            border-radius: 18px;
            overflow: hidden;
            margin-top: 12px;
            margin-bottom: 24px;
            background: #ffffff;
            border: 1px solid var(--border);
            box-shadow: 0 14px 35px rgba(15,23,42,0.05);
        }

        .custom-table th {
            background: #f1f5f9;
            color: #111827;
            font-weight: 800;
            padding: 14px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
        }

        .custom-table td {
            color: #1e293b;
            padding: 14px 16px;
            border-bottom: 1px solid #e2e8f0;
            font-size: 14px;
            vertical-align: top;
            line-height: 1.55;
        }

        .custom-table tr:nth-child(even) {
            background: #f8fafc;
        }

        .custom-table tr:hover {
            background: #eef2ff;
        }

        .alert-box {
            border-radius: 18px;
            padding: 16px 18px;
            margin: 12px 0;
            background: #ffffff;
            border: 1px solid var(--border);
            box-shadow: 0 12px 30px rgba(15,23,42,0.05);
            line-height: 1.55;
        }

        .alert-good { border-left: 5px solid var(--good); }
        .alert-warn { border-left: 5px solid var(--warn); }
        .alert-bad { border-left: 5px solid var(--bad); }

        .principle-box, .allocation-card, .action-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 22px;
            margin-bottom: 16px;
            box-shadow: 0 14px 35px rgba(15,23,42,0.05);
        }

        .principle-title, .action-title {
            font-size: 20px;
            font-weight: 900;
            color: #111827;
            margin-bottom: 12px;
        }

        .principle-line, .action-text {
            color: #334155;
            margin-bottom: 10px;
            font-size: 14px;
            line-height: 1.65;
        }

        .principle-label {
            color: var(--muted);
            font-weight: 850;
        }

        .allocation-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 16px;
            font-weight: 850;
            color: #111827;
            margin-bottom: 10px;
        }

        .allocation-role {
            color: var(--muted);
            font-size: 13px;
            margin-bottom: 12px;
            line-height: 1.45;
        }

        .bar-bg {
            width: 100%;
            height: 12px;
            border-radius: 999px;
            background: #e2e8f0;
            overflow: hidden;
        }

        .bar-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #06b6d4, #8b5cf6);
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 数据获取层
# ============================================================

@st.cache_data(ttl=60)
def get_yfinance_series(ticker, period="6mo"):
    try:
        data = yf.download(
            ticker,
            period=period,
            progress=False,
            auto_adjust=False,
            threads=False
        )
        if data is None or data.empty:
            return None
        data = flatten_yfinance_columns(data)
        data = data.reset_index()
        return data
    except Exception:
        return None


def latest_close(ticker, period="6mo", divisor=1):
    data = get_yfinance_series(ticker, period)

    if data is None or data.empty:
        return np.nan, np.nan, None

    if "Close" not in data.columns:
        return np.nan, np.nan, data

    current = safe_float(data["Close"].iloc[-1]) / divisor

    if len(data) >= 2:
        previous = safe_float(data["Close"].iloc[-2]) / divisor
    else:
        previous = current

    return current, previous, data


@st.cache_data(ttl=3600)
def fred_series(series_id):
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        df = pd.read_csv(url)
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna()
        return df
    except Exception:
        return None


def latest_fred(series_id):
    df = fred_series(series_id)

    if df is None or df.empty:
        return np.nan, np.nan, None

    current = safe_float(df["value"].iloc[-1])

    if len(df) >= 2:
        previous = safe_float(df["value"].iloc[-2])
    else:
        previous = current

    return current, previous, df


@st.cache_data(ttl=3600)
def get_china_macro_best_effort():
    result = {
        "社融存量同比": {"value": 9.0, "prev": 8.9, "source": "fallback"},
        "M1同比": {"value": 3.8, "prev": 3.5, "source": "fallback"},
        "M2同比": {"value": 9.0, "prev": 8.8, "source": "fallback"},
        "财新PMI": {"value": 51.2, "prev": 50.8, "source": "fallback"},
        "LPR_5Y": {"value": 3.50, "prev": 3.50, "source": "fallback"},
    }

    try:
        import akshare as ak

        try:
            money = ak.macro_china_money_supply()
            if money is not None and not money.empty:
                last = money.iloc[-1]
                prev = money.iloc[-2] if len(money) >= 2 else last

                for col in money.columns:
                    col_text = str(col)

                    if "M1" in col_text and ("同比" in col_text or "增长" in col_text):
                        result["M1同比"] = {
                            "value": safe_float(last[col], result["M1同比"]["value"]),
                            "prev": safe_float(prev[col], result["M1同比"]["prev"]),
                            "source": "akshare"
                        }

                    if "M2" in col_text and ("同比" in col_text or "增长" in col_text):
                        result["M2同比"] = {
                            "value": safe_float(last[col], result["M2同比"]["value"]),
                            "prev": safe_float(prev[col], result["M2同比"]["prev"]),
                            "source": "akshare"
                        }
        except Exception:
            pass

        try:
            lpr = ak.macro_china_lpr()
            if lpr is not None and not lpr.empty:
                last = lpr.iloc[-1]
                prev = lpr.iloc[-2] if len(lpr) >= 2 else last

                for col in lpr.columns:
                    col_text = str(col)
                    if ("5" in col_text and "LPR" in col_text) or ("5年" in col_text):
                        result["LPR_5Y"] = {
                            "value": safe_float(last[col], result["LPR_5Y"]["value"]),
                            "prev": safe_float(prev[col], result["LPR_5Y"]["prev"]),
                            "source": "akshare"
                        }
                        break
        except Exception:
            pass

    except Exception:
        pass

    return result


@st.cache_data(ttl=60)
def get_market_data():
    hsi, hsi_prev, hsi_hist = latest_close("^HSI")
    hstech, hstech_prev, hstech_hist = latest_close("3067.HK")
    sh, sh_prev, sh_hist = latest_close("000001.SS")
    spx, spx_prev, spx_hist = latest_close("^GSPC")
    nasdaq, nasdaq_prev, nasdaq_hist = latest_close("^IXIC")
    us10y, us10y_prev, us10y_hist = latest_close("^TNX", divisor=10)
    dxy, dxy_prev, dxy_hist = latest_close("DX-Y.NYB")
    gold_usd, gold_usd_prev, gold_hist = latest_close("GC=F")
    usdcny, usdcny_prev, usdcny_hist = latest_close("CNY=X")

    if not pd.isna(gold_usd) and not pd.isna(usdcny):
        gold_cny_gram = gold_usd * usdcny / 31.1035
    else:
        gold_cny_gram = 752

    if not pd.isna(gold_usd_prev) and not pd.isna(usdcny_prev):
        gold_cny_gram_prev = gold_usd_prev * usdcny_prev / 31.1035
    else:
        gold_cny_gram_prev = 749

    return {
        "恒生指数": {"value": hsi if not pd.isna(hsi) else 26200, "prev": hsi_prev if not pd.isna(hsi_prev) else 26100, "hist": hsi_hist},
        "恒生科技ETF": {"value": hstech if not pd.isna(hstech) else 4.50, "prev": hstech_prev if not pd.isna(hstech_prev) else 4.48, "hist": hstech_hist},
        "上证指数": {"value": sh if not pd.isna(sh) else 3450, "prev": sh_prev if not pd.isna(sh_prev) else 3440, "hist": sh_hist},
        "标普500": {"value": spx if not pd.isna(spx) else 5200, "prev": spx_prev if not pd.isna(spx_prev) else 5180, "hist": spx_hist},
        "纳斯达克": {"value": nasdaq if not pd.isna(nasdaq) else 16500, "prev": nasdaq_prev if not pd.isna(nasdaq_prev) else 16400, "hist": nasdaq_hist},
        "10Y美债": {"value": us10y if not pd.isna(us10y) else 4.43, "prev": us10y_prev if not pd.isna(us10y_prev) else 4.38, "hist": us10y_hist},
        "美元指数": {"value": dxy if not pd.isna(dxy) else 99.2, "prev": dxy_prev if not pd.isna(dxy_prev) else 99.0, "hist": dxy_hist},
        "黄金_人民币每克": {"value": gold_cny_gram, "prev": gold_cny_gram_prev, "hist": gold_hist},
        "美元人民币": {"value": usdcny if not pd.isna(usdcny) else 7.05, "prev": usdcny_prev if not pd.isna(usdcny_prev) else 7.04, "hist": usdcny_hist},
    }


@st.cache_data(ttl=3600)
def get_us_macro():
    pmi, pmi_prev, pmi_hist = latest_fred("NAPM")

    cpi_df = fred_series("CPIAUCSL")
    if cpi_df is not None and len(cpi_df) >= 14:
        cpi_now = cpi_df["value"].iloc[-1]
        cpi_12m = cpi_df["value"].iloc[-13]
        cpi_prev = cpi_df["value"].iloc[-2]
        cpi_prev_12m = cpi_df["value"].iloc[-14]
        cpi_yoy = (cpi_now / cpi_12m - 1) * 100
        cpi_yoy_prev = (cpi_prev / cpi_prev_12m - 1) * 100
    else:
        cpi_yoy = 2.6
        cpi_yoy_prev = 2.6

    fed, fed_prev, fed_hist = latest_fred("FEDFUNDS")

    return {
        "ISM_PMI": {"value": pmi if not pd.isna(pmi) else 48.5, "prev": pmi_prev if not pd.isna(pmi_prev) else 48.8, "hist": pmi_hist},
        "CPI同比": {"value": cpi_yoy, "prev": cpi_yoy_prev, "hist": cpi_df},
        "联邦基金利率": {"value": fed if not pd.isna(fed) else 3.75, "prev": fed_prev if not pd.isna(fed_prev) else 3.75, "hist": fed_hist}
    }


# ============================================================
# 周期判断层
# ============================================================

def judge_us_season(us_macro):
    pmi = us_macro["ISM_PMI"]["value"]
    cpi = us_macro["CPI同比"]["value"]

    growth_up = pmi >= 50
    inflation_up = cpi >= 2.5

    if growth_up and not inflation_up:
        return {"name": "春", "desc": "增长↑ + 通胀↓", "asset": "股票、信用债", "level": "green"}
    elif growth_up and inflation_up:
        return {"name": "夏", "desc": "增长↑ + 通胀↑", "asset": "商品、资源、抗通胀资产", "level": "yellow"}
    elif (not growth_up) and inflation_up:
        return {"name": "秋 / 滞胀", "desc": "增长↓ + 通胀↑", "asset": "黄金、资源、现金流资产", "level": "red"}
    else:
        return {"name": "冬 / 衰退", "desc": "增长↓ + 通胀↓", "asset": "长债、现金、防御资产", "level": "blue"}


def judge_china_season(china_macro):
    social = china_macro["社融存量同比"]["value"]
    social_prev = china_macro["社融存量同比"]["prev"]
    pmi = china_macro["财新PMI"]["value"]

    credit_up = social >= social_prev
    growth_up = pmi >= 50

    if credit_up and growth_up:
        return {"name": "春", "desc": "信用扩张 + 增长修复", "asset": "A股、港股、科技、消费", "level": "green"}
    elif credit_up and not growth_up:
        return {"name": "结构春", "desc": "信用改善但增长未确认", "asset": "高股息、互联网龙头、黄金", "level": "yellow"}
    elif (not credit_up) and growth_up:
        return {"name": "弱夏", "desc": "增长尚可但信用转弱", "asset": "现金、红利、低估值资产", "level": "yellow"}
    else:
        return {"name": "冬", "desc": "信用收缩 + 增长承压", "asset": "黄金、现金、防御资产", "level": "red"}


def judge_hk_season(us_season, china_season):
    us_name = us_season["name"]
    cn_name = china_season["name"]

    if cn_name == "春" and us_name == "春":
        return {"name": "黄金春", "desc": "中国信用扩张 + 美国流动性改善", "action": "港股进攻窗口，恒生科技、互联网、新消费弹性较大", "level": "green"}
    elif cn_name in ["春", "结构春"] and us_name in ["秋 / 滞胀", "冬 / 衰退"]:
        return {"name": "结构春", "desc": "中国偏暖 + 美国偏紧或放缓", "action": "指数震荡，重点看高股息、互联网龙头、人民币黄金", "level": "yellow"}
    elif cn_name == "冬" and us_name in ["秋 / 滞胀", "冬 / 衰退"]:
        return {"name": "双杀冬", "desc": "中国信用收缩 + 美国分母压力", "action": "降低权益仓位，提高黄金、现金、防御资产", "level": "red"}
    elif cn_name == "冬" and us_name == "春":
        return {"name": "流动性夏", "desc": "美国宽松但中国分子较弱", "action": "成长股有估值反弹，但持续性取决于中国信用", "level": "yellow"}
    else:
        return {"name": "过渡期", "desc": "中美周期错位", "action": "结构性机会强于指数机会，分批配置", "level": "yellow"}


def get_long_cycle_state(market, us_macro):
    debt_gdp = 100.2
    interest_gdp = 3.2
    us10y = market["10Y美债"]["value"]
    cpi = us_macro["CPI同比"]["value"]
    real_rate = us10y - cpi

    if debt_gdp < 80:
        stage = "第四阶段：债务红利期"
        level = "green"
    elif debt_gdp < 130:
        stage = "第五阶段初段：债务压力显性化"
        level = "yellow"
    elif debt_gdp < 170:
        stage = "第五阶段中段：信用动摇期"
        level = "red"
    else:
        stage = "第六阶段前夜：货币秩序重建风险"
        level = "red"

    return {
        "stage": stage,
        "debt_gdp": debt_gdp,
        "interest_gdp": interest_gdp,
        "real_rate": real_rate,
        "level": level
    }


def generate_alerts(china, us, market):
    alerts = []

    us10y = market["10Y美债"]["value"]
    dxy = market["美元指数"]["value"]
    social = china["社融存量同比"]["value"]
    cpi = us["CPI同比"]["value"]

    if us10y >= 4.5:
        alerts.append(("bad", f"10Y 美债收益率达到 {us10y:.2f}%，接近或突破港股分母端警戒线。"))
    elif us10y <= 4.0:
        alerts.append(("good", f"10Y 美债收益率降至 {us10y:.2f}%，港股成长资产估值压力下降。"))

    if dxy >= 105:
        alerts.append(("bad", f"美元指数达到 {dxy:.2f}，新兴市场和港股流动性压力上升。"))
    elif dxy <= 95:
        alerts.append(("good", f"美元指数降至 {dxy:.2f}，利好黄金、港股和非美资产。"))

    if social < 8:
        alerts.append(("bad", f"社融存量同比为 {social:.2f}%，中国信用周期偏弱。"))
    elif social > 10:
        alerts.append(("good", f"社融存量同比为 {social:.2f}%，中国信用扩张信号较强。"))

    if cpi >= 3:
        alerts.append(("warn", f"美国 CPI 同比为 {cpi:.2f}%，通胀粘性仍需警惕。"))

    if not alerts:
        alerts.append(("good", "核心指标暂无极端异动，维持当前观察框架。"))

    return alerts


# ============================================================
# 渲染组件
# ============================================================

def render_header(title, subtitle):
    st.markdown(
        f"""
        <div class="main-header">
            <div class="main-title">{title}</div>
            <div class="main-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_kpi(title, value, desc, note, level="yellow"):
    badge = color_level(level)
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{badge} {value}</div>
            <div class="kpi-desc">{desc}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_table(df):
    html = df.to_html(index=False, escape=False, classes="custom-table")
    st.markdown(html, unsafe_allow_html=True)


def render_alerts(alerts):
    for level, msg in alerts:
        if level == "bad":
            cls = "alert-box alert-bad"
            icon = "🔴"
        elif level == "warn":
            cls = "alert-box alert-warn"
            icon = "🟡"
        else:
            cls = "alert-box alert-good"
            icon = "🟢"

        st.markdown(
            f"""
            <div class="{cls}">
                {icon} {msg}
            </div>
            """,
            unsafe_allow_html=True
        )


def make_line_chart(df, title, y_col=None):
    if df is None or df.empty:
        st.info("暂无可用走势图数据")
        return

    fig = go.Figure()

    try:
        if y_col is None:
            if "Close" in df.columns:
                y_col = "Close"
            elif "value" in df.columns:
                y_col = "value"
            else:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if not numeric_cols:
                    st.info("暂无可用走势图数据")
                    return
                y_col = numeric_cols[-1]

        if "Date" in df.columns:
            x_col = "Date"
        elif "Datetime" in df.columns:
            x_col = "Datetime"
        elif "date" in df.columns:
            x_col = "date"
        else:
            x_col = df.columns[0]

        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode="lines",
                name=title,
                line=dict(width=2)
            )
        )

        fig.update_layout(
            title=title,
            height=380,
            margin=dict(l=20, r=20, t=55, b=20),
            hovermode="x unified",
            template=PLOT_TEMPLATE,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=FONT_COLOR),
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(color=FONT_COLOR)
            )
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning(f"图表生成失败：{e}")


def render_principle_box(title, core, scenario, rule, mistake):
    st.markdown(
        f"""
        <div class="principle-box">
            <div class="principle-title">{title}</div>
            <div class="principle-line"><span class="principle-label">核心思想：</span>{core}</div>
            <div class="principle-line"><span class="principle-label">适用场景：</span>{scenario}</div>
            <div class="principle-line"><span class="principle-label">执行规则：</span>{rule}</div>
            <div class="principle-line"><span class="principle-label">反面错误：</span>{mistake}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 加载数据
# ============================================================

with st.spinner("正在获取数据，首次加载可能需要 20-60 秒..."):
    china_macro = get_china_macro_best_effort()
    us_macro = get_us_macro()
    market = get_market_data()

us_season = judge_us_season(us_macro)
china_season = judge_china_season(china_macro)
hk_season = judge_hk_season(us_season, china_season)
long_cycle = get_long_cycle_state(market, us_macro)
alerts = generate_alerts(china_macro, us_macro, market)


# ============================================================
# 页面 1：周期罗盘
# ============================================================

def render_cycle_page():
    render_header(
        "① 周期罗盘",
        f"从大周期到短周期定位当前市场环境｜自动刷新：{'开启' if auto_refresh else '关闭'}｜频率：{refresh_interval}｜{now_cn().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_kpi(
            "长周期",
            long_cycle["stage"].split("：")[0],
            long_cycle["stage"],
            f"债务/GDP {long_cycle['debt_gdp']:.1f}%，实际利率 {long_cycle['real_rate']:.2f}%",
            long_cycle["level"]
        )

    with c2:
        render_kpi(
            "美国短周期",
            us_season["name"],
            us_season["desc"],
            f"主导资产：{us_season['asset']}",
            us_season["level"]
        )

    with c3:
        render_kpi(
            "中国短周期",
            china_season["name"],
            china_season["desc"],
            f"主导资产：{china_season['asset']}",
            china_season["level"]
        )

    with c4:
        render_kpi(
            "港股双周期",
            hk_season["name"],
            hk_season["desc"],
            hk_season["action"],
            hk_season["level"]
        )

    st.markdown("### 当前结论")

    st.markdown(
        f"""
        <div class="section-card">
        当前系统判断为：<span class="{level_class(hk_season['level'])}">{hk_season['name']}</span>。<br><br>
        <b>周期含义：</b>{hk_season['desc']}。<br><br>
        <b>核心动作：</b>{hk_season['action']}。<br><br>
        <b>长周期底层约束：</b>{long_cycle['stage']}。这意味着黄金、优质股权、现金流资产和货币多元化仍然是战略底仓。
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 关键风险信号")
    render_alerts(alerts)

    st.markdown("### 周期判断依据")

    df = pd.DataFrame({
        "层级": ["长周期", "美国短周期", "中国短周期", "港股双周期"],
        "当前状态": [
            long_cycle["stage"],
            us_season["name"],
            china_season["name"],
            hk_season["name"]
        ],
        "核心变量": [
            "美国债务/GDP、利息支出/GDP、实际利率",
            "ISM PMI、CPI、联邦基金利率、10Y美债",
            "社融、M1/M2、PMI、LPR",
            "中国信用周期 × 美国流动性周期"
        ],
        "配置含义": [
            "提高硬资产和货币多元化权重",
            us_season["asset"],
            china_season["asset"],
            hk_season["action"]
        ]
    })

    render_table(df)


# ============================================================
# 页面 2：市场雷达
# ============================================================

def render_market_page():
    render_header(
        "② 市场雷达",
        "观察关键指标、价格、利率和风险触发器"
    )

    st.markdown("### 核心市场快照")

    items = [
        ("恒生指数", "恒生指数", ""),
        ("恒生科技ETF", "恒生科技ETF", ""),
        ("上证指数", "上证指数", ""),
        ("标普500", "标普500", ""),
        ("纳斯达克", "纳斯达克", ""),
        ("10Y美债", "10Y美债", "%"),
        ("美元指数", "美元指数", ""),
        ("人民币黄金", "黄金_人民币每克", " 元/克"),
        ("美元人民币", "美元人民币", "")
    ]

    rows = []
    for label, key, suffix in items:
        current = market[key]["value"]
        prev = market[key]["prev"]
        rows.append({
            "指标": label,
            "当前值": f"{current:.2f}{suffix}",
            "较前值": delta_text(current, prev, suffix),
            "状态": "观察"
        })

    render_table(pd.DataFrame(rows))

    st.markdown("### 中国指标")

    china_rows = []
    for key in ["社融存量同比", "M1同比", "M2同比", "财新PMI", "LPR_5Y"]:
        item = china_macro[key]
        suffix = "%" if key != "财新PMI" else ""
        china_rows.append({
            "指标": key,
            "当前值": f"{item['value']:.2f}{suffix}",
            "变化": delta_text(item["value"], item["prev"], suffix),
            "数据源": item.get("source", "unknown")
        })

    render_table(pd.DataFrame(china_rows))

    st.markdown("### 美国指标")

    us_rows = []
    for key in ["ISM_PMI", "CPI同比", "联邦基金利率"]:
        item = us_macro[key]
        suffix = "%" if key != "ISM_PMI" else ""
        us_rows.append({
            "指标": key,
            "当前值": f"{item['value']:.2f}{suffix}",
            "变化": delta_text(item["value"], item["prev"], suffix),
            "解释": "增长" if key == "ISM_PMI" else "通胀/政策"
        })

    us_rows.append({
        "指标": "10Y美债",
        "当前值": f"{market['10Y美债']['value']:.2f}%",
        "变化": delta_text(market["10Y美债"]["value"], market["10Y美债"]["prev"], "%"),
        "解释": "估值分母"
    })

    render_table(pd.DataFrame(us_rows))

    st.markdown("### 走势图")

    chart_choice = st.selectbox(
        "选择指标",
        ["恒生指数", "恒生科技ETF", "上证指数", "标普500", "纳斯达克", "10Y美债", "美元指数", "人民币黄金", "美元人民币"]
    )

    if chart_choice == "人民币黄金":
        make_line_chart(
            market["黄金_人民币每克"]["hist"],
            "COMEX 黄金走势（首页人民币每克为估算值）"
        )
    else:
        make_line_chart(market[chart_choice]["hist"], chart_choice)


# ============================================================
# 页面 3：原则引擎
# ============================================================

def render_principle_page():
    render_header(
        "③ 原则引擎",
        "将投资大师思想压缩成可执行的判断规则"
    )

    st.markdown("### 四大原则模块")

    render_principle_box(
        "质量原则：巴菲特 / 芒格",
        "买优秀企业，而不是只买便宜股票。长期收益来自企业质量、护城河、管理层和现金流。",
        "长期股权配置、核心仓位、A股和港股龙头选择。",
        "只在能力圈内行动，优先选择商业模式清晰、现金流稳定、竞争优势长期存在的企业。",
        "因为短期便宜而买入长期劣质资产，或者在看不懂的行业里重仓。"
    )

    render_principle_box(
        "周期原则：达利欧 / 霍华德·马克斯",
        "市场不是线性运行，而是在周期中摆动。最重要的是判断所处位置，而不是预测下一个点位。",
        "大类资产配置、仓位调节、风险控制。",
        "用增长、通胀、信用、利率、债务等变量定位春夏秋冬，再决定进攻、防守或等待。",
        "在周期顶部线性外推，在周期底部因为恐惧而永久离场。"
    )

    render_principle_box(
        "错位原则：索罗斯",
        "市场价格会反过来影响现实，现实又强化价格，直到叙事和现实之间的裂缝扩大并反转。",
        "宏观拐点、泡沫、危机、政策转向和汇率/利率冲击。",
        "寻找市场共识与真实变量之间的偏差，重点观察自我强化是否还能持续。",
        "把趋势当成永恒，把共识当成真理，忽视反身性反转。"
    )

    render_principle_box(
        "执行原则：林奇 / ETF / 长期主义",
        "普通投资者最大的优势不是信息速度，而是耐心、常识、分散、低成本和纪律。",
        "个人长期资产积累、定投、再平衡、家庭资产配置。",
        "建立规则，分散持有，定期复盘，不用短期噪音破坏长期策略。",
        "频繁追热点、过度交易、看懂但拿不住、下跌后忘记原始判断。"
    )

    st.markdown("### 原则 → 系统映射")

    df = pd.DataFrame({
        "原则": ["质量", "周期", "错位", "执行"],
        "代表人物": ["巴菲特 / 芒格", "达利欧 / 马克斯", "索罗斯", "林奇 / 指数化投资"],
        "系统位置": ["资产选择", "周期罗盘", "风险识别", "执行系统"],
        "一句话规则": [
            "只买长期值得拥有的东西",
            "先判断季节，再谈仓位",
            "寻找叙事和现实的裂缝",
            "规则比情绪重要"
        ]
    })

    render_table(df)


# ============================================================
# 页面 4：执行系统
# ============================================================

def render_execution_page():
    render_header(
        "④ 执行系统",
        "把周期判断和原则转化成仓位、触发条件与复盘"
    )

    st.markdown("### 当前建议配置")

    allocation = pd.DataFrame({
        "资产类别": [
            "港股核心仓：高股息 + 互联网龙头",
            "A股核心仓：科技 + 红利",
            "人民币计价黄金",
            "美元货币基金 / 短债",
            "美股科技龙头",
            "现金 / 机动仓"
        ],
        "建议比例": [35, 15, 15, 10, 10, 15],
        "角色": [
            "中国资产离岸弹性，承担组合主要进攻任务",
            "本土信用周期受益，捕捉政策与科技修复",
            "长周期货币对冲，对冲债务周期与法币贬值",
            "美元流动性缓冲，应对外部冲击和汇率波动",
            "全球科技超额收益，保留创新资产敞口",
            "等待极端机会，防止满仓被动"
        ]
    })

    left, right = st.columns([1.15, 0.85])

    with left:
        for _, row in allocation.iterrows():
            pct = int(row["建议比例"])
            st.markdown(
                f"""
                <div class="allocation-card">
                    <div class="allocation-title">
                        <span>{row["资产类别"]}</span>
                        <span>{pct}%</span>
                    </div>
                    <div class="allocation-role">{row["角色"]}</div>
                    <div class="bar-bg">
                        <div class="bar-fill" style="width:{pct}%;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with right:
        st.markdown(
            f"""
            <div class="action-card">
                <div class="action-title">今日系统判断</div>
                <div class="action-text">
                    当前港股双周期为 <span class="{level_class(hk_season['level'])}">{hk_season['name']}</span>。<br><br>
                    <b>含义：</b>{hk_season['desc']}<br><br>
                    <b>动作：</b>{hk_season['action']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="action-card">
                <div class="action-title">长周期约束</div>
                <div class="action-text">
                    当前债务大周期定位为 <span class="{level_class(long_cycle['level'])}">{long_cycle['stage']}</span>。<br><br>
                    因此组合不应只依赖权益资产，需要保留黄金、现金和美元流动性缓冲。
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="action-card">
                <div class="action-title">执行纪律</div>
                <div class="action-text">
                    不追涨，不满仓，不因为单日波动改变长期配置。<br><br>
                    只有当关键指标触发阈值时，才进行 3%-10% 的仓位调整。
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("### 触发条件 → 行动清单")

    decision_df = pd.DataFrame({
        "触发条件": [
            "10Y美债跌破4.0%",
            "10Y美债突破4.5%",
            "美元指数跌破95",
            "美元指数突破105",
            "社融同比突破10%",
            "社融同比跌破8%",
            "美国CPI重新突破3.5%",
            "恒生指数大跌但南向资金逆势流入"
        ],
        "建议动作": [
            "加仓港股成长股，尤其恒生科技",
            "降低港股成长仓位，增加黄金和现金",
            "加仓港股、黄金、非美资产",
            "降低新兴市场和港股风险敞口",
            "加仓A股和港股核心资产",
            "降低权益仓位，提高黄金和现金",
            "提高黄金、资源、现金权重",
            "分批加仓高股息和互联网龙头"
        ],
        "仓位幅度": [
            "+3% 到 +5%",
            "-5% 到 -10%",
            "+3% 到 +5%",
            "-5%",
            "+5%",
            "-5% 到 -10%",
            "+3% 黄金",
            "+3% 到 +5%"
        ]
    })

    render_table(decision_df)

    st.markdown("### 本周检查清单")

    checklist = pd.DataFrame({
        "检查项": [
            "是否确认当前周期位置？",
            "是否有指标触发行动清单？",
            "是否偏离目标仓位超过5%？",
            "是否因为情绪而交易？",
            "是否记录了本周判断？"
        ],
        "目的": [
            "避免盲目交易",
            "让行动有依据",
            "保持风险平衡",
            "防止追涨杀跌",
            "训练自己的原则库"
        ]
    })

    render_table(checklist)

    st.markdown("### 月度复盘记录")

    note = st.text_area(
        "记录本月周期判断、执行动作、错误和下月修正：",
        height=180,
        placeholder="例如：2026年5月，我判断港股处于结构春，理由是中国信用修复但美债仍高位..."
    )

    if st.button("保存复盘记录"):
        st.success("当前版本暂未接数据库。请先复制保存；后续可接 Supabase / SQLite。")


# ============================================================
# 路由
# ============================================================

if page == "① 周期罗盘":
    render_cycle_page()

elif page == "② 市场雷达":
    render_market_page()

elif page == "③ 原则引擎":
    render_principle_page()

elif page == "④ 执行系统":
    render_execution_page()


st.markdown("---")
st.caption("免责声明：本网页仅用于个人研究和框架训练，不构成任何投资建议。投资有风险，决策需谨慎。")
