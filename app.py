import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except Exception:
    AUTOREFRESH_AVAILABLE = False


# =========================
# 页面基础配置
# =========================

st.set_page_config(
    page_title="投资雷达",
    page_icon="📊",
    layout="wide"
)


# =========================
# 侧边栏：刷新与主题设置
# =========================

with st.sidebar:
    st.markdown("## ⚙️ 仪表盘设置")

    theme_mode = st.radio(
        "显示模式",
        ["🌞 明亮模式", "🌙 夜间模式"],
        index=1
    )

    auto_refresh = st.toggle(
        "自动刷新",
        value=True
    )

    refresh_interval = st.selectbox(
        "刷新频率",
        ["30 秒", "1 分钟", "5 分钟", "15 分钟"],
        index=1
    )

    interval_map = {
        "30 秒": 30,
        "1 分钟": 60,
        "5 分钟": 300,
        "15 分钟": 900
    }

    refresh_seconds = interval_map[refresh_interval]

    if st.button("🔄 立即刷新数据"):
        st.cache_data.clear()
        st.rerun()

    st.caption("市场价格可高频刷新；宏观数据通常为月度或季度更新。")

    if not AUTOREFRESH_AVAILABLE:
        st.warning("未检测到 streamlit-autorefresh，请在 requirements.txt 中加入 streamlit-autorefresh。")


if auto_refresh and AUTOREFRESH_AVAILABLE:
    st_autorefresh(
        interval=refresh_seconds * 1000,
        key="investment_radar_auto_refresh"
    )


# =========================
# 主题样式：明亮模式 / 夜间模式
# =========================

if theme_mode == "🌙 夜间模式":
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #0e1117;
            color: #e6edf3;
        }

        section[data-testid="stSidebar"] {
            background-color: #111827;
            border-right: 1px solid #2d3748;
        }

        .main-title {
            font-size: 34px;
            font-weight: 800;
            margin-bottom: 0px;
            color: #f8fafc;
        }

        .sub-title {
            color: #94a3b8;
            font-size: 14px;
            margin-top: 0px;
        }

        .card {
            background-color: #161b22;
            border-radius: 14px;
            padding: 18px;
            border: 1px solid #30363d;
            height: 160px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.25);
        }

        .big-number {
            font-size: 28px;
            font-weight: 800;
            margin-top: 8px;
            color: #f8fafc;
        }

        .small-note {
            font-size: 13px;
            color: #94a3b8;
            margin-top: 8px;
        }

        div[data-testid="stMetric"] {
            background-color: #161b22;
            border: 1px solid #30363d;
            padding: 14px;
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.18);
        }

        div[data-testid="stMetricLabel"] {
            color: #94a3b8;
        }

        div[data-testid="stMetricValue"] {
            color: #f8fafc;
        }

        div[data-testid="stMetricDelta"] {
            color: #22c55e;
        }

        h1, h2, h3, h4 {
            color: #f8fafc;
        }

        hr {
            border-color: #30363d;
        }

        .stDataFrame {
            background-color: #161b22;
        }

        p, li, span, div {
            color: inherit;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #ffffff;
            color: #111827;
        }

        section[data-testid="stSidebar"] {
            background-color: #f8fafc;
            border-right: 1px solid #e5e7eb;
        }

        .main-title {
            font-size: 34px;
            font-weight: 800;
            margin-bottom: 0px;
            color: #111827;
        }

        .sub-title {
            color: #666;
            font-size: 14px;
            margin-top: 0px;
        }

        .card {
            background-color: #f7f8fa;
            border-radius: 14px;
            padding: 18px;
            border: 1px solid #e6e8eb;
            height: 160px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        }

        .big-number {
            font-size: 28px;
            font-weight: 800;
            margin-top: 8px;
            color: #111827;
        }

        .small-note {
            font-size: 13px;
            color: #666;
            margin-top: 8px;
        }

        div[data-testid="stMetric"] {
            background-color: #f8fafc;
            border: 1px solid #e5e7eb;
            padding: 14px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# =========================
# 工具函数
# =========================

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
    """
    中国宏观数据尽量用 akshare 抓取。
    如果接口失败，则返回默认值，保证网页不崩。
    """
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
    """
    市场价格数据。
    yfinance 代码说明：
    ^HSI：恒生指数
    000001.SS：上证指数
    ^TNX：10Y 美债收益率，显示值约为实际收益率乘以 10，所以除以 10
    DX-Y.NYB：美元指数
    GC=F：COMEX 黄金期货，美元/盎司
    CNY=X：美元兑人民币
    """
    data = {}

    hsi, hsi_prev, hsi_hist = latest_close("^HSI")
    sh, sh_prev, sh_hist = latest_close("000001.SS")
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

    data["恒生指数"] = {
        "value": hsi if not pd.isna(hsi) else 26200,
        "prev": hsi_prev if not pd.isna(hsi_prev) else 26100,
        "hist": hsi_hist,
        "source": "yfinance"
    }

    data["上证指数"] = {
        "value": sh if not pd.isna(sh) else 3450,
        "prev": sh_prev if not pd.isna(sh_prev) else 3440,
        "hist": sh_hist,
        "source": "yfinance"
    }

    data["10Y美债"] = {
        "value": us10y if not pd.isna(us10y) else 4.43,
        "prev": us10y_prev if not pd.isna(us10y_prev) else 4.38,
        "hist": us10y_hist,
        "source": "yfinance"
    }

    data["美元指数"] = {
        "value": dxy if not pd.isna(dxy) else 99.2,
        "prev": dxy_prev if not pd.isna(dxy_prev) else 99.0,
        "hist": dxy_hist,
        "source": "yfinance"
    }

    data["黄金_人民币每克"] = {
        "value": gold_cny_gram,
        "prev": gold_cny_gram_prev,
        "hist": gold_hist,
        "source": "yfinance estimate"
    }

    data["美元人民币"] = {
        "value": usdcny if not pd.isna(usdcny) else 7.05,
        "prev": usdcny_prev if not pd.isna(usdcny_prev) else 7.04,
        "hist": usdcny_hist,
        "source": "yfinance"
    }

    return data


@st.cache_data(ttl=3600)
def get_us_macro():
    result = {}

    pmi, pmi_prev, pmi_hist = latest_fred("NAPM")
    result["ISM_PMI"] = {
        "value": pmi if not pd.isna(pmi) else 48.5,
        "prev": pmi_prev if not pd.isna(pmi_prev) else 48.8,
        "hist": pmi_hist,
        "source": "FRED NAPM"
    }

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

    result["CPI同比"] = {
        "value": cpi_yoy,
        "prev": cpi_yoy_prev,
        "hist": cpi_df,
        "source": "FRED CPIAUCSL"
    }

    fed, fed_prev, fed_hist = latest_fred("FEDFUNDS")
    result["联邦基金利率"] = {
        "value": fed if not pd.isna(fed) else 3.75,
        "prev": fed_prev if not pd.isna(fed_prev) else 3.75,
        "hist": fed_hist,
        "source": "FRED FEDFUNDS"
    }

    return result


def judge_us_season(us_macro):
    pmi = us_macro["ISM_PMI"]["value"]
    cpi = us_macro["CPI同比"]["value"]

    growth_up = pmi >= 50
    inflation_up = cpi >= 2.5

    if growth_up and not inflation_up:
        return "春", "增长↑ + 通胀↓", "股票、信用债", "green"
    elif growth_up and inflation_up:
        return "夏", "增长↑ + 通胀↑", "大宗商品、TIPS、资源股", "yellow"
    elif (not growth_up) and inflation_up:
        return "秋 / 滞胀", "增长↓ + 通胀↑", "黄金、资源、实物资产", "red"
    else:
        return "冬 / 衰退", "增长↓ + 通胀↓", "长债、现金、防御资产", "blue"


def judge_china_season(china_macro):
    social = china_macro["社融存量同比"]["value"]
    social_prev = china_macro["社融存量同比"]["prev"]
    pmi = china_macro["财新PMI"]["value"]

    credit_up = social >= social_prev
    growth_up = pmi >= 50

    if credit_up and growth_up:
        return "春", "信用扩张 + 增长修复", "A股、港股、科技、消费", "green"
    elif credit_up and not growth_up:
        return "结构春", "信用改善但增长未确认", "高股息、互联网龙头、黄金", "yellow"
    elif (not credit_up) and growth_up:
        return "弱夏", "增长尚可但信用转弱", "现金、红利、低估值资产", "yellow"
    else:
        return "冬", "信用收缩 + 增长承压", "黄金、现金、防御资产", "red"


def judge_hk_season(us_season, china_season):
    us_name = us_season[0]
    cn_name = china_season[0]

    if cn_name == "春" and us_name == "春":
        return "黄金春", "中国信用扩张 + 美国流动性改善", "港股进攻窗口，恒生科技、互联网、新消费弹性较大", "green"
    elif cn_name in ["春", "结构春"] and us_name in ["秋 / 滞胀", "冬 / 衰退"]:
        return "结构春", "中国偏暖 + 美国偏紧或放缓", "指数震荡，重点看高股息、互联网龙头、人民币黄金", "yellow"
    elif cn_name == "冬" and us_name in ["秋 / 滞胀", "冬 / 衰退"]:
        return "双杀冬", "中国信用收缩 + 美国分母压力", "降低权益仓位，提高黄金、现金、防御资产", "red"
    elif cn_name == "冬" and us_name == "春":
        return "流动性夏", "美国宽松但中国分子较弱", "成长股有估值反弹，但持续性取决于中国信用", "yellow"
    else:
        return "过渡期", "中美周期错位", "结构性机会强于指数机会，分批配置", "yellow"


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


def signal_badge(level):
    if level == "green":
        return "🟢"
    if level == "yellow":
        return "🟡"
    if level == "red":
        return "🔴"
    if level == "blue":
        return "🔵"
    return "⚪"


def render_card(title, main, desc, note, level="yellow"):
    badge = signal_badge(level)
    st.markdown(
        f"""
        <div class="card">
            <div style="font-size:14px;color:#94a3b8;">{title}</div>
            <div class="big-number">{badge} {main}</div>
            <div style="font-size:14px;margin-top:4px;">{desc}</div>
            <div class="small-note">{note}</div>
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
            height=360,
            margin=dict(l=20, r=20, t=50, b=20),
            hovermode="x unified",
            template="plotly_dark" if theme_mode == "🌙 夜间模式" else "plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.warning(f"图表生成失败：{e}")


def generate_alerts(china, us, market):
    alerts = []

    us10y = market["10Y美债"]["value"]
    dxy = market["美元指数"]["value"]
    social = china["社融存量同比"]["value"]
    cpi = us["CPI同比"]["value"]

    if us10y >= 4.5:
        alerts.append(("red", f"10Y 美债收益率达到 {us10y:.2f}%，接近或突破港股分母端警戒线。"))
    elif us10y <= 4.0:
        alerts.append(("green", f"10Y 美债收益率降至 {us10y:.2f}%，港股成长资产估值压力下降。"))

    if dxy >= 105:
        alerts.append(("red", f"美元指数达到 {dxy:.2f}，新兴市场和港股流动性压力上升。"))
    elif dxy <= 95:
        alerts.append(("green", f"美元指数降至 {dxy:.2f}，利好黄金、港股和非美资产。"))

    if social < 8:
        alerts.append(("red", f"社融存量同比为 {social:.2f}%，中国信用周期偏弱。"))
    elif social > 10:
        alerts.append(("green", f"社融存量同比为 {social:.2f}%，中国信用扩张信号较强。"))

    if cpi >= 3:
        alerts.append(("yellow", f"美国 CPI 同比为 {cpi:.2f}%，通胀粘性仍需警惕。"))

    if not alerts:
        alerts.append(("green", "核心指标暂无极端异动，维持当前观察框架。"))

    return alerts


# =========================
# 数据加载
# =========================

with st.spinner("正在获取实时数据，首次加载可能需要 20-60 秒..."):
    china_macro = get_china_macro_best_effort()
    us_macro = get_us_macro()
    market = get_market_data()

us_season = judge_us_season(us_macro)
china_season = judge_china_season(china_macro)
hk_season = judge_hk_season(us_season, china_season)
long_cycle = get_long_cycle_state(market, us_macro)
alerts = generate_alerts(china_macro, us_macro, market)


# =========================
# 顶部标题
# =========================

st.markdown('<div class="main-title">📊 投资雷达</div>', unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="sub-title">
    短周期 + 中周期 + 长周期一体化仪表盘｜
    更新时间：{now_cn().strftime("%Y-%m-%d %H:%M:%S")}｜
    自动刷新：{"开启" if auto_refresh else "关闭"}｜
    刷新频率：{refresh_interval}｜
    主题：{theme_mode}
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# =========================
# 页面标签
# =========================

tab_home, tab_short, tab_long, tab_allocation, tab_review = st.tabs(
    ["首页总览", "短周期仪表盘", "长周期仪表盘", "资产配置建议", "历史复盘"]
)


# =========================
# 首页
# =========================

with tab_home:
    st.subheader("今日核心判断")

    c1, c2, c3 = st.columns(3)

    with c1:
        render_card(
            "美国短周期",
            us_season[0],
            us_season[1],
            f"主导资产：{us_season[2]}",
            us_season[3]
        )

    with c2:
        render_card(
            "中国短周期",
            china_season[0],
            china_season[1],
            f"主导资产：{china_season[2]}",
            china_season[3]
        )

    with c3:
        render_card(
            "港股双周期",
            hk_season[0],
            hk_season[1],
            hk_season[2],
            hk_season[3]
        )

    st.subheader("长周期定位")

    l1, l2, l3, l4 = st.columns(4)
    l1.metric("债务大周期阶段", long_cycle["stage"])
    l2.metric("美国债务/GDP", f'{long_cycle["debt_gdp"]:.1f}%', "100% 已突破")
    l3.metric("利息支出/GDP", f'{long_cycle["interest_gdp"]:.1f}%', "高于疫情前")
    l4.metric("10Y 实际利率估算", f'{long_cycle["real_rate"]:.2f}%', "名义10Y - CPI")

    st.subheader("关键资产快照")

    m1, m2, m3, m4, m5, m6 = st.columns(6)

    market_items = [
        ("恒生指数", "恒生指数", ""),
        ("上证指数", "上证指数", ""),
        ("10Y美债", "10Y美债", "%"),
        ("美元指数", "美元指数", ""),
        ("人民币黄金", "黄金_人民币每克", " 元/克"),
        ("美元人民币", "美元人民币", "")
    ]

    cols = [m1, m2, m3, m4, m5, m6]

    for col, (label, key, suffix) in zip(cols, market_items):
        current = market[key]["value"]
        previous = market[key]["prev"]
        delta = current - previous
        col.metric(label, f"{current:.2f}{suffix}", f"{delta:+.2f}{suffix}")

    st.subheader("今日异动告警")

    for level, msg in alerts:
        if level == "red":
            st.error("🔴 " + msg)
        elif level == "yellow":
            st.warning("🟡 " + msg)
        else:
            st.success("🟢 " + msg)

    st.subheader("今日建议动作")

    st.markdown(
        f"""
        **港股策略：​** {hk_season[2]}

        **短周期策略：​** 当前美国为 **​{us_season[0]}​**，中国为 **​{china_season[0]}​**。这意味着投资上应重点观察中美周期是否从错位转向共振。

        **长周期策略：​** 美国债务周期已进入第五阶段初段，黄金、优质股权、资源类资产和货币多元化仍是战略底仓方向。

        **当前执行建议：​**
        - 港股不要一次性满仓，优先采用分批建仓。
        - 黄金建议作为长期底仓，而不是只做短线交易。
        - 如果 10Y 美债继续上破 4.5%，需要降低港股成长股仓位。
        - 如果中国社融继续回升，同时 10Y 美债跌破 4.0%，港股进攻窗口增强。
        """
    )


# =========================
# 短周期仪表盘
# =========================

with tab_short:
    st.subheader("中国短周期指标")

    c1, c2, c3, c4, c5 = st.columns(5)

    china_items = [
        ("社融存量同比", "社融存量同比", "%"),
        ("M1同比", "M1同比", "%"),
        ("M2同比", "M2同比", "%"),
        ("财新PMI", "财新PMI", ""),
        ("5Y LPR", "LPR_5Y", "%")
    ]

    for col, (label, key, suffix) in zip([c1, c2, c3, c4, c5], china_items):
        current = china_macro[key]["value"]
        previous = china_macro[key]["prev"]
        source = china_macro[key].get("source", "unknown")
        col.metric(label, f"{current:.2f}{suffix}", f"{current - previous:+.2f}{suffix}")
        col.caption(f"数据源：{source}")

    st.markdown("#### 中国周期解释")
    st.info(
        f"当前中国周期判定为 **​{china_season[0]}​**：{china_season[1]}。"
        f"核心逻辑是社融方向与 PMI 共同决定信用和增长的状态。"
    )

    st.subheader("美国短周期指标")

    u1, u2, u3, u4 = st.columns(4)

    us_items = [
        ("ISM PMI", "ISM_PMI", ""),
        ("CPI同比", "CPI同比", "%"),
        ("联邦基金利率", "联邦基金利率", "%"),
        ("10Y美债", "10Y美债", "%")
    ]

    for col, (label, key, suffix) in zip([u1, u2, u3, u4], us_items):
        if key in us_macro:
            current = us_macro[key]["value"]
            previous = us_macro[key]["prev"]
        else:
            current = market[key]["value"]
            previous = market[key]["prev"]

        col.metric(label, f"{current:.2f}{suffix}", f"{current - previous:+.2f}{suffix}")

    st.markdown("#### 美国周期解释")
    st.info(
        f"当前美国周期判定为 **​{us_season[0]}​**：{us_season[1]}。"
        f"核心逻辑是 ISM PMI 判断增长方向，CPI 判断通胀方向。"
    )

    st.subheader("关键走势图")

    chart_choice = st.selectbox(
        "选择查看指标",
        ["恒生指数", "上证指数", "10Y美债", "美元指数", "人民币黄金", "美元人民币"]
    )

    if chart_choice == "人民币黄金":
        make_line_chart(
            market["黄金_人民币每克"]["hist"],
            "COMEX 黄金走势（人民币每克为首页估算值，走势图为美元黄金期货）"
        )
    else:
        make_line_chart(market[chart_choice]["hist"], chart_choice)


# =========================
# 长周期仪表盘
# =========================

with tab_long:
    st.subheader("债务大周期三仪表盘")

    d1, d2, d3 = st.columns(3)
    d1.metric("美国债务/GDP", f'{long_cycle["debt_gdp"]:.1f}%', "第五阶段初段")
    d2.metric("利息支出/GDP", f'{long_cycle["interest_gdp"]:.1f}%', "财政压力上升")
    d3.metric("10Y实际利率", f'{long_cycle["real_rate"]:.2f}%', "仍需观察是否转负")

    st.warning(
        "长周期判断：美国处于债务大周期第五阶段初段。这个阶段不代表马上崩溃，"
        "但代表长期债券、单一法币和高估值资产的风险收益比正在变化。"
    )

    st.subheader("世界秩序 8 大实力指标")

    power_df = pd.DataFrame({
        "指标": ["教育", "创新技术", "成本竞争力", "军事", "贸易", "经济产出", "金融中心", "储备货币"],
        "美国": [0.84, 0.92, 0.55, 0.97, 0.74, 0.85, 0.96, 0.95],
        "中国": [0.65, 0.78, 0.91, 0.71, 0.95, 0.78, 0.55, 0.18],
        "印度": [0.45, 0.32, 0.62, 0.52, 0.31, 0.42, 0.21, 0.04],
    })

    fig = go.Figure()

    for country in ["美国", "中国", "印度"]:
        fig.add_trace(
            go.Scatterpolar(
                r=power_df[country],
                theta=power_df["指标"],
                fill="toself",
                name=country
            )
        )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=520,
        showlegend=True,
        template="plotly_dark" if theme_mode == "🌙 夜间模式" else "plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(power_df, use_container_width=True, hide_index=True)

    st.subheader("人民币国际化观察")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("SWIFT占比", "3.1%", "观察是否突破5%")
    r2.metric("CIPS日均规模", "9205亿", "观察持续性")
    r3.metric("央行黄金储备", "持续增持", "长期去单一货币")
    r4.metric("境外人民币资产", "10万亿+", "投融资功能增强")

    st.info(
        "长周期核心不是预测明年涨跌，而是决定战略底仓。"
        "当前最重要的长期配置原则是：货币多元化、黄金底仓、优质股权、减少对单一长期债权资产的依赖。"
    )


# =========================
# 资产配置建议
# =========================

with tab_allocation:
    st.subheader("当前建议配置")

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
            "中国资产离岸弹性",
            "本土信用周期受益",
            "长周期货币对冲",
            "美元流动性缓冲",
            "全球科技超额收益",
            "等待极端机会"
        ]
    })

    left, right = st.columns([1, 1])

    with left:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=allocation["资产类别"],
                    values=allocation["建议比例"],
                    hole=0.42
                )
            ]
        )
        fig.update_layout(
            height=460,
            template="plotly_dark" if theme_mode == "🌙 夜间模式" else "plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.dataframe(allocation, use_container_width=True, hide_index=True)

    st.subheader("触发条件 → 行动清单")

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

    st.dataframe(decision_df, use_container_width=True, hide_index=True)

    st.warning(
        "这不是自动交易信号，而是决策辅助。真正下单前仍需要结合估值、仓位、个人现金流和风险承受能力。"
    )


# =========================
# 历史复盘
# =========================

with tab_review:
    st.subheader("美国 2020-2025 四季复盘")

    us_history = pd.DataFrame({
        "年份": ["2020", "2021", "2022", "2023", "2024", "2025"],
        "增长": ["↓→↑", "↑↑", "↓", "↑", "↑", "↓"],
        "通胀": ["↓", "↓→↑", "↑↑", "↓", "↓但粘", "↓但粘"],
        "季节": ["冬→春", "春末段", "秋 / 滞胀", "秋→春", "春 + 长债压力", "软秋"],
        "主导资产": [
            "美债、黄金、科技股",
            "标普500、原油",
            "黄金、美元、商品",
            "七大科技股、纳指",
            "标普、黄金、比特币",
            "黄金、白银、资源"
        ]
    })

    st.dataframe(us_history, use_container_width=True, hide_index=True)

    st.subheader("中国与港股 2020-2025 复盘")

    cn_history = pd.DataFrame({
        "年份": ["2020", "2021", "2022", "2023", "2024", "2025"],
        "中国GDP": ["+2.3%", "+8.4%", "+3.0%", "+5.2%", "+5.0%", "+5.0%"],
        "社融同比": ["13.3%", "10.3%", "9.6%", "9.5%", "8.0%", "约9.0%"],
        "上证指数": ["+13.9%", "+4.8%", "-15.1%", "-3.7%", "+12.7%", "+18.4%"],
        "恒生指数": ["-3.4%", "-14.0%", "-15.5%", "-13.8%", "+17.7%", "+27.8%"]
    })

    st.dataframe(cn_history, use_container_width=True, hide_index=True)

    st.subheader("我的判断日记")

    note = st.text_area(
        "记录你本月对周期的判断、买卖动作和事后复盘：",
        height=180,
        placeholder="例如：2026年5月，我判断港股处于结构春，理由是中国信用修复但美债仍高位..."
    )

    if st.button("保存本次复盘记录"):
        st.success("当前简化版暂未接数据库。你可以先复制保存到本地，后续版本可接入 Supabase 或 SQLite。")


st.divider()
st.caption("免责声明：本网页仅用于个人研究和框架训练，不构成任何投资建议。投资有风险，决策需谨慎。")
