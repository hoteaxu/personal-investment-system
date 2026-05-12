import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
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
    page_title="达利欧周期分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
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
# 顶部控制区
# ============================================================

top_left, top_mid1, top_mid2, top_mid3, top_right = st.columns([2.4, 1.2, 1.2, 1.2, 1.2])

with top_left:
    st.markdown("### 📊 达利欧周期分析系统")
    st.caption(f"更新时间：{now_cn().strftime('%Y-%m-%d %H:%M:%S')}")

with top_mid1:
    theme_mode = st.radio(
        "显示模式",
        ["🌙 夜间", "🌞 明亮"],
        horizontal=True,
        index=0,
        label_visibility="collapsed"
    )

with top_mid2:
    auto_refresh = st.toggle("自动刷新", value=True)

with top_mid3:
    refresh_interval = st.selectbox(
        "刷新频率",
        ["1 分钟", "5 分钟", "15 分钟", "30 秒"],
        index=1,
        label_visibility="collapsed"
    )

with top_right:
    if st.button("🔄 立即刷新", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

interval_map = {
    "30 秒": 30,
    "1 分钟": 60,
    "5 分钟": 300,
    "15 分钟": 900
}

refresh_seconds = interval_map[refresh_interval]

if auto_refresh and AUTOREFRESH_AVAILABLE:
    st_autorefresh(
        interval=refresh_seconds * 1000,
        key="dalio_cycle_refresh"
    )


# ============================================================
# 主题样式
# ============================================================

if theme_mode == "🌙 夜间":
    PLOT_TEMPLATE = "plotly_dark"
    FONT_COLOR = "#f8fafc"

    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }

        .stApp {
            background: radial-gradient(circle at top left, #111827 0%, #070b12 42%, #05070d 100%);
            color: #f8fafc;
        }

        .block-container {
            padding-top: 2rem;
            padding-left: 4rem;
            padding-right: 4rem;
            max-width: 1320px;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #f8fafc !important;
            letter-spacing: -0.03em;
        }

        p, li, span, div {
            color: inherit;
        }

        hr {
            border-color: rgba(148,163,184,0.22);
        }

        .hero {
            background: linear-gradient(135deg, rgba(30,41,59,0.98) 0%, rgba(15,23,42,0.98) 100%);
            border: 1px solid rgba(148,163,184,0.24);
            border-radius: 26px;
            padding: 34px 38px;
            margin-top: 18px;
            margin-bottom: 30px;
            box-shadow: 0 26px 70px rgba(0,0,0,0.38);
        }

        .hero-title {
            font-size: 42px;
            font-weight: 950;
            color: #f8fafc;
            margin-bottom: 10px;
            letter-spacing: -0.05em;
        }

        .hero-subtitle {
            font-size: 16px;
            color: #94a3b8;
            line-height: 1.7;
        }

        .kpi-card {
            background: linear-gradient(180deg, rgba(30,41,59,0.96), rgba(15,23,42,0.96));
            border: 1px solid rgba(148,163,184,0.20);
            border-radius: 24px;
            padding: 24px;
            min-height: 178px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.30);
        }

        .kpi-title {
            font-size: 13px;
            color: #94a3b8;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .kpi-value {
            font-size: 31px;
            font-weight: 950;
            color: #f8fafc;
            line-height: 1.22;
        }

        .kpi-desc {
            font-size: 14px;
            color: #cbd5e1;
            margin-top: 9px;
            line-height: 1.58;
        }

        .kpi-note {
            font-size: 12px;
            color: #94a3b8;
            margin-top: 10px;
            line-height: 1.5;
        }

        .section-card {
            background: rgba(15,23,42,0.90);
            border: 1px solid rgba(148,163,184,0.20);
            border-radius: 24px;
            padding: 26px;
            margin-bottom: 24px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.24);
            line-height: 1.78;
        }

        .section-title {
            font-size: 25px;
            font-weight: 900;
            color: #f8fafc;
            margin-bottom: 14px;
            letter-spacing: -0.03em;
        }

        .good { color: #22c55e !important; font-weight: 900; }
        .warn { color: #f59e0b !important; font-weight: 900; }
        .bad { color: #ef4444 !important; font-weight: 900; }
        .info { color: #38bdf8 !important; font-weight: 900; }
        .neutral { color: #cbd5e1 !important; font-weight: 900; }

        .custom-table {
            width: 100%;
            border-collapse: collapse;
            border-radius: 20px;
            overflow: hidden;
            margin-top: 14px;
            margin-bottom: 26px;
            background: rgba(15,23,42,0.94);
            border: 1px solid rgba(148,163,184,0.20);
            box-shadow: 0 16px 42px rgba(0,0,0,0.22);
        }

        .custom-table th {
            background: rgba(30,41,59,0.98);
            color: #f8fafc;
            font-weight: 850;
            padding: 15px 17px;
            text-align: left;
            border-bottom: 1px solid rgba(148,163,184,0.20);
            font-size: 14px;
        }

        .custom-table td {
            color: #dbeafe;
            padding: 15px 17px;
            border-bottom: 1px solid rgba(148,163,184,0.12);
            font-size: 14px;
            vertical-align: top;
            line-height: 1.62;
        }

        .custom-table tr:nth-child(even) {
            background: rgba(17,24,39,0.72);
        }

        .custom-table tr:hover {
            background: rgba(30,41,59,0.94);
        }

        .alert-box {
            border-radius: 20px;
            padding: 17px 20px;
            margin: 13px 0;
            background: rgba(15,23,42,0.94);
            border: 1px solid rgba(148,163,184,0.18);
            box-shadow: 0 14px 34px rgba(0,0,0,0.20);
            line-height: 1.6;
        }

        .alert-good {
            border-left: 5px solid #22c55e;
        }

        .alert-warn {
            border-left: 5px solid #f59e0b;
        }

        .alert-bad {
            border-left: 5px solid #ef4444;
        }

        .stButton button {
            background: linear-gradient(90deg, #2563eb, #7c3aed) !important;
            color: white !important;
            border: 0 !important;
            border-radius: 14px !important;
            font-weight: 850 !important;
            min-height: 42px !important;
        }

        .stSelectbox div[data-baseweb="select"] > div {
            background: rgba(15,23,42,0.92) !important;
            border: 1px solid rgba(148,163,184,0.22) !important;
            color: #f8fafc !important;
            border-radius: 14px !important;
        }

        .stRadio label {
            color: #f8fafc !important;
        }

        div[data-testid="stAlert"] {
            background: rgba(15,23,42,0.9);
            color: #f8fafc;
            border: 1px solid rgba(148,163,184,0.2);
            border-radius: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

else:
    PLOT_TEMPLATE = "plotly_white"
    FONT_COLOR = "#111827"

    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }

        .stApp {
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            color: #111827;
        }

        .block-container {
            padding-top: 2rem;
            padding-left: 4rem;
            padding-right: 4rem;
            max-width: 1320px;
        }

        .hero {
            background: linear-gradient(135deg, #ffffff 0%, #eef2ff 100%);
            border: 1px solid #e2e8f0;
            border-radius: 26px;
            padding: 34px 38px;
            margin-top: 18px;
            margin-bottom: 30px;
            box-shadow: 0 18px 44px rgba(15,23,42,0.07);
        }

        .hero-title {
            font-size: 42px;
            font-weight: 950;
            color: #111827;
            margin-bottom: 10px;
            letter-spacing: -0.05em;
        }

        .hero-subtitle {
            font-size: 16px;
            color: #64748b;
            line-height: 1.7;
        }

        .kpi-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 24px;
            padding: 24px;
            min-height: 178px;
            box-shadow: 0 16px 40px rgba(15,23,42,0.06);
        }

        .kpi-title {
            font-size: 13px;
            color: #64748b;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .kpi-value {
            font-size: 31px;
            font-weight: 950;
            color: #111827;
            line-height: 1.22;
        }

        .kpi-desc {
            font-size: 14px;
            color: #334155;
            margin-top: 9px;
            line-height: 1.58;
        }

        .kpi-note {
            font-size: 12px;
            color: #64748b;
            margin-top: 10px;
            line-height: 1.5;
        }

        .section-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 24px;
            padding: 26px;
            margin-bottom: 24px;
            box-shadow: 0 16px 40px rgba(15,23,42,0.06);
            line-height: 1.78;
        }

        .section-title {
            font-size: 25px;
            font-weight: 900;
            color: #111827;
            margin-bottom: 14px;
            letter-spacing: -0.03em;
        }

        .good { color: #0a8f3c !important; font-weight: 900; }
        .warn { color: #b7791f !important; font-weight: 900; }
        .bad { color: #c53030 !important; font-weight: 900; }
        .info { color: #0284c7 !important; font-weight: 900; }
        .neutral { color: #334155 !important; font-weight: 900; }

        .custom-table {
            width: 100%;
            border-collapse: collapse;
            border-radius: 20px;
            overflow: hidden;
            margin-top: 14px;
            margin-bottom: 26px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 16px 40px rgba(15,23,42,0.05);
        }

        .custom-table th {
            background: #f1f5f9;
            color: #111827;
            font-weight: 850;
            padding: 15px 17px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
            font-size: 14px;
        }

        .custom-table td {
            color: #1e293b;
            padding: 15px 17px;
            border-bottom: 1px solid #e2e8f0;
            font-size: 14px;
            vertical-align: top;
            line-height: 1.62;
        }

        .custom-table tr:nth-child(even) {
            background: #f8fafc;
        }

        .custom-table tr:hover {
            background: #eef2ff;
        }

        .alert-box {
            border-radius: 20px;
            padding: 17px 20px;
            margin: 13px 0;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 14px 34px rgba(15,23,42,0.05);
            line-height: 1.6;
        }

        .alert-good { border-left: 5px solid #0a8f3c; }
        .alert-warn { border-left: 5px solid #b7791f; }
        .alert-bad { border-left: 5px solid #c53030; }
        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# 数据获取
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
# 周期判断
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
            height=410,
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
# 主页面：达利欧周期分析
# ============================================================

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">达利欧周期分析</div>
        <div class="hero-subtitle">
        用“长周期债务框架 + 增长通胀四季 + 中国信用周期 + 港股双周期”定位当前市场。
        当前自动刷新：{"开启" if auto_refresh else "关闭"}｜刷新频率：{refresh_interval}｜页面时间：{now_cn().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# 第一层：四张周期卡片
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

st.markdown("<br>", unsafe_allow_html=True)

# 第二层：当前结论
st.markdown(
    f"""
    <div class="section-card">
        <div class="section-title">当前周期结论</div>
        当前系统判断为：<span class="{level_class(hk_season['level'])}">{hk_season['name']}</span>。<br><br>
        <b>周期含义：</b>{hk_season['desc']}。<br><br>
        <b>核心动作：</b>{hk_season['action']}。<br><br>
        <b>长周期底层约束：</b>{long_cycle['stage']}。这意味着黄金、优质股权、现金流资产和货币多元化仍然是战略底仓。
    </div>
    """,
    unsafe_allow_html=True
)

# 第三层：风险告警
st.markdown("### 关键风险信号")
render_alerts(alerts)

# 第四层：周期判断依据
st.markdown("### 周期判断依据")

cycle_df = pd.DataFrame({
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

render_table(cycle_df)

# 第五层：核心指标
st.markdown("### 核心指标读数")

market_rows = []
market_items = [
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

for label, key, suffix in market_items:
    current = market[key]["value"]
    prev = market[key]["prev"]
    market_rows.append({
        "指标": label,
        "当前值": f"{current:.2f}{suffix}",
        "较前值": delta_text(current, prev, suffix),
        "作用": "市场价格 / 分母 / 避险 / 汇率"
    })

render_table(pd.DataFrame(market_rows))

macro_col1, macro_col2 = st.columns(2)

with macro_col1:
    st.markdown("### 中国周期指标")

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

with macro_col2:
    st.markdown("### 美国周期指标")

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

# 第六层：走势图
st.markdown("### 关键走势图")

chart_choice = st.selectbox(
    "选择查看指标",
    ["恒生指数", "恒生科技ETF", "上证指数", "标普500", "纳斯达克", "10Y美债", "美元指数", "人民币黄金", "美元人民币"]
)

if chart_choice == "人民币黄金":
    make_line_chart(
        market["黄金_人民币每克"]["hist"],
        "COMEX 黄金走势（人民币每克为估算值）"
    )
else:
    make_line_chart(market[chart_choice]["hist"], chart_choice)

# 第七层：达利欧框架解释
st.markdown("### 达利欧框架解释")

framework_df = pd.DataFrame({
    "框架": [
        "债务大周期",
        "经济四季",
        "中国信用周期",
        "港股双周期",
        "资产配置含义"
    ],
    "核心问题": [
        "国家和货币处于信用扩张、去杠杆还是货币贬值阶段？",
        "增长和通胀分别向上还是向下？",
        "社融、M1、PMI 是否显示信用重新扩张？",
        "中国分子端和美国分母端是否共振？",
        "当前环境更适合进攻、防守还是等待？"
    ],
    "当前使用方式": [
        "用美国债务/GDP、利息支出/GDP、实际利率判断长期阶段",
        "用 ISM PMI 和 CPI 判断美国春夏秋冬",
        "用社融方向和 PMI 判断中国春、结构春、冬等状态",
        "把中国周期和美国周期组合，得到港股环境",
        "用周期状态决定权益、黄金、现金、美元资产的相对权重"
    ]
})

render_table(framework_df)

st.markdown("---")
st.caption("免责声明：本网页仅用于个人研究和框架训练，不构成任何投资建议。投资有风险，决策需谨慎。")
