"""
M&A Profile Builder — Streamlit Application

Professional-grade company research platform with polished UI.
Generates an 8-slide investment-banker-grade PowerPoint tear sheet.

Run:  streamlit run main.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os

from data_engine import (
    fetch_company_data, format_number, format_pct, format_multiple
)
from ai_insights import generate_insights
from pptx_generator import generate_presentation

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="M&A Profile Builder",
    page_icon="https://img.icons8.com/fluency/48/combo-chart.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
# COMPREHENSIVE CUSTOM CSS — Professional dark-navy theme
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── GLOBAL ──────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* ── SIDEBAR ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B1D3A 0%, #142D5E 100%);
    border-right: 3px solid #D4A537;
}
section[data-testid="stSidebar"] * {
    color: #E8ECF1 !important;
}
section[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(212,165,55,0.4);
    border-radius: 10px;
    color: #fff !important;
    font-weight: 600;
    font-size: 1.1rem;
    letter-spacing: 2px;
    text-align: center;
    padding: 0.7rem;
}
section[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
    border-color: #D4A537;
    box-shadow: 0 0 12px rgba(212,165,55,0.3);
}
section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #D4A537 0%, #F0C060 100%) !important;
    color: #0B1D3A !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.7rem 2rem !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(212,165,55,0.3);
}
section[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(212,165,55,0.4);
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(212,165,55,0.3) !important;
}

/* ── HEADER AREA ─────────────────────────────────────────── */
.hero-header {
    background: linear-gradient(135deg, #0B1D3A 0%, #1a3a6e 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    border-bottom: 4px solid #D4A537;
    box-shadow: 0 8px 32px rgba(11,29,58,0.15);
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-sub {
    font-size: 1rem;
    color: #8BA4C7;
    margin-top: 0.3rem;
    font-weight: 400;
}
.hero-tagline {
    display: inline-block;
    background: rgba(212,165,55,0.15);
    color: #D4A537;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* ── COMPANY HEADER CARD ─────────────────────────────────── */
.company-card {
    background: linear-gradient(135deg, #0B1D3A 0%, #142D5E 100%);
    border-radius: 16px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
    border-left: 5px solid #D4A537;
    box-shadow: 0 4px 20px rgba(11,29,58,0.12);
}
.company-name {
    font-size: 1.8rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.3px;
}
.company-meta {
    font-size: 0.85rem;
    color: #8BA4C7;
    margin-top: 0.25rem;
}
.company-meta span {
    color: #D4A537;
    font-weight: 600;
}
.price-tag {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
}
.price-up { color: #4CAF50; }
.price-down { color: #EF5350; }
.price-change {
    font-size: 0.85rem;
    font-weight: 600;
    padding: 0.15rem 0.5rem;
    border-radius: 6px;
    display: inline-block;
    margin-left: 0.5rem;
}
.change-up { background: rgba(76,175,80,0.15); color: #4CAF50; }
.change-down { background: rgba(239,83,80,0.15); color: #EF5350; }

/* ── SECTION STYLING ─────────────────────────────────────── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 2rem 0 0.8rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #E8ECF1;
}
.section-header h3 {
    font-size: 1.15rem;
    font-weight: 700;
    color: #0B1D3A;
    margin: 0;
}
.section-header .accent-bar {
    width: 4px;
    height: 22px;
    background: #D4A537;
    border-radius: 2px;
}
.section-divider { display: none; }

/* ── METRIC CARDS ────────────────────────────────────────── */
div[data-testid="stMetric"] {
    background: #FAFBFC;
    border: 1px solid #E8ECF1;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    transition: all 0.2s ease;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
div[data-testid="stMetric"]:hover {
    border-color: #D4A537;
    box-shadow: 0 4px 16px rgba(212,165,55,0.12);
    transform: translateY(-1px);
}
div[data-testid="stMetric"] label {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #7A8B9E !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: #0B1D3A !important;
}

/* ── KPI ROW (compact) ───────────────────────────────────── */
.kpi-row {
    display: flex;
    gap: 1rem;
    margin: 0.5rem 0;
}
.kpi-item {
    flex: 1;
    background: #FAFBFC;
    border: 1px solid #E8ECF1;
    border-radius: 10px;
    padding: 0.6rem 0.8rem;
    text-align: center;
}
.kpi-label {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    color: #7A8B9E;
    margin-bottom: 0.2rem;
}
.kpi-value {
    font-size: 1rem;
    font-weight: 700;
    color: #0B1D3A;
}

/* ── TABS ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #F0F2F6;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 0.5rem 1.2rem;
    color: #5A6C7F;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #0B1D3A;
    color: #ffffff;
    box-shadow: 0 2px 8px rgba(11,29,58,0.2);
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}
.stTabs [data-baseweb="tab-border"] {
    display: none;
}

/* ── EXPANDERS ───────────────────────────────────────────── */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: #0B1D3A !important;
    background: #FAFBFC;
    border: 1px solid #E8ECF1;
    border-radius: 10px;
}

/* ── DATAFRAMES ──────────────────────────────────────────── */
.stDataFrame {
    border: 1px solid #E8ECF1;
    border-radius: 10px;
    overflow: hidden;
}

/* ── DOWNLOAD BUTTON ─────────────────────────────────────── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #0B1D3A 0%, #1a3a6e 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.8rem 2rem !important;
    font-size: 1rem !important;
    width: 100% !important;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(11,29,58,0.2);
    letter-spacing: 0.3px;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(11,29,58,0.3);
}

/* ── NEWS CARDS ──────────────────────────────────────────── */
.news-item {
    padding: 0.65rem 0;
    border-bottom: 1px solid #F0F2F6;
    transition: background 0.15s;
}
.news-item:hover {
    background: #FAFBFC;
}
.news-title {
    font-weight: 600;
    color: #0B1D3A;
    font-size: 0.88rem;
    text-decoration: none;
}
.news-title:hover {
    color: #1E90FF;
}
.news-pub {
    font-size: 0.72rem;
    color: #7A8B9E;
    font-weight: 500;
}

/* ── ESG GAUGE CARDS ─────────────────────────────────────── */
.esg-card {
    background: linear-gradient(135deg, #FAFBFC 0%, #F0F4F8 100%);
    border: 1px solid #E0E7EF;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
}
.esg-score {
    font-size: 1.6rem;
    font-weight: 800;
    color: #0B1D3A;
}
.esg-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #7A8B9E;
    margin-top: 0.2rem;
}

/* ── BADGE / PILL ────────────────────────────────────────── */
.pill {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.pill-gold { background: rgba(212,165,55,0.15); color: #B8860B; }
.pill-blue { background: rgba(30,144,255,0.1); color: #1E90FF; }
.pill-navy { background: rgba(11,29,58,0.08); color: #0B1D3A; }

/* ── PLOTLY CHART CONTAINERS ─────────────────────────────── */
.stPlotlyChart {
    border: 1px solid #E8ECF1;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

/* ── LANDING PAGE ────────────────────────────────────────── */
.landing-card {
    background: #FAFBFC;
    border: 1px solid #E8ECF1;
    border-radius: 14px;
    padding: 1.5rem 2rem;
    margin: 0.5rem 0;
    transition: all 0.2s ease;
}
.landing-card:hover {
    border-color: #D4A537;
    box-shadow: 0 4px 16px rgba(212,165,55,0.1);
}
.landing-step {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin: 1rem 0;
}
.step-number {
    background: linear-gradient(135deg, #D4A537, #F0C060);
    color: #0B1D3A;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.85rem;
    flex-shrink: 0;
}
.step-text {
    color: #0B1D3A;
    font-size: 0.95rem;
    font-weight: 500;
    padding-top: 0.3rem;
}

/* ── SPINNER STYLING ─────────────────────────────────────── */
.stSpinner > div > div {
    border-top-color: #D4A537 !important;
}

/* ── SCROLLBAR ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #F0F2F6; border-radius: 10px; }
::-webkit-scrollbar-thumb { background: #C0C8D4; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #A0AAB8; }

/* ── RADIO BUTTONS (period selector) ─────────────────────── */
.stRadio > div {
    gap: 0.3rem;
}
.stRadio > div > label {
    background: #F0F2F6;
    border-radius: 8px;
    padding: 0.3rem 1rem;
    font-weight: 600;
    font-size: 0.8rem;
    border: 1px solid transparent;
    transition: all 0.15s;
}
.stRadio > div > label[data-checked="true"] {
    background: #0B1D3A;
    color: #ffffff;
}

/* ── HIDE STREAMLIT BRANDING ─────────────────────────────── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── HELPER: Section header with accent bar ──────────────────
def _section(title, icon=""):
    st.markdown(
        f'<div class="section-header">'
        f'<div class="accent-bar"></div>'
        f'<h3>{icon}  {title}</h3>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("")
    st.markdown(
        '<div style="text-align:center; padding: 1rem 0 0.5rem 0;">'
        '<div style="font-size:1.4rem; font-weight:800; letter-spacing:-0.5px;">M&A Profile</div>'
        '<div style="font-size:1.4rem; font-weight:800; color:#D4A537; margin-top:-0.3rem;">Builder</div>'
        '<div style="font-size:0.7rem; color:#8BA4C7; margin-top:0.3rem; letter-spacing:1.5px; text-transform:uppercase;">Investment Research Platform</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    ticker_input = st.text_input(
        "Stock Ticker", value="AAPL", max_chars=10,
        help="Enter a US stock ticker (e.g. AAPL, MSFT, TSLA, GOOGL)"
    ).strip().upper()

    generate_btn = st.button("Generate Profile", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; padding: 0.5rem 0;">'
        '<div style="font-size:0.65rem; color:#5A6C7F; letter-spacing:0.5px; line-height:1.8;">'
        'DATA: YAHOO FINANCE<br>'
        'M&A: WIKIPEDIA<br>'
        'CHARTS: PLOTLY<br>'
        'AI: OPENAI (OPT.)'
        '</div></div>',
        unsafe_allow_html=True,
    )

# ── Main Area ────────────────────────────────────────────────
st.markdown(
    '<div class="hero-header">'
    '<p class="hero-title">M&A Profile Builder</p>'
    '<p class="hero-sub">Comprehensive company research & 8-slide tear sheet generator</p>'
    '<span class="hero-tagline">Powered by Live Market Data</span>'
    '</div>',
    unsafe_allow_html=True,
)

if generate_btn and ticker_input:
    # ── Data Fetching ────────────────────────────────────
    with st.spinner(f"Fetching comprehensive data for {ticker_input}..."):
        try:
            cd = fetch_company_data(ticker_input)
        except Exception as e:
            st.error(f"Failed to fetch data for **{ticker_input}**: {e}")
            st.stop()

    with st.spinner("Generating AI insights..."):
        cd = generate_insights(cd)

    # ══════════════════════════════════════════════════════
    # 1. COMPANY HEADER CARD
    # ══════════════════════════════════════════════════════
    chg_class = "price-up" if cd.price_change >= 0 else "price-down"
    chg_badge = "change-up" if cd.price_change >= 0 else "change-down"
    arrow = "&#9650;" if cd.price_change >= 0 else "&#9660;"

    st.markdown(
        f'<div class="company-card">'
        f'<p class="company-name">{cd.name}</p>'
        f'<p class="company-meta"><span>{cd.ticker}</span> &nbsp;&middot;&nbsp; {cd.exchange} &nbsp;&middot;&nbsp; {cd.sector} &rarr; {cd.industry}</p>'
        f'<div style="display:flex; align-items:baseline; gap:1rem; margin-top:0.8rem;">'
        f'<p class="price-tag {chg_class}">${cd.current_price:,.2f}</p>'
        f'<span class="price-change {chg_badge}">{arrow} {cd.price_change:+.2f} ({cd.price_change_pct:+.2f}%)</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Quick KPI strip
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Market Cap", format_number(cd.market_cap))
    k2.metric("Enterprise Value", format_number(cd.enterprise_value))
    k3.metric("Volume", format_number(cd.volume, prefix="", decimals=0))
    k4.metric("Avg Volume", format_number(cd.avg_volume, prefix="", decimals=0))
    k5.metric("52W Low", f"${cd.fifty_two_week_low:,.2f}")
    k6.metric("52W High", f"${cd.fifty_two_week_high:,.2f}")

    # ══════════════════════════════════════════════════════
    # 2. BUSINESS OVERVIEW
    # ══════════════════════════════════════════════════════
    _section("Business Overview", "")
    with st.expander("Company Description", expanded=True):
        if cd.long_business_summary:
            st.markdown(f"<div style='line-height:1.7; color:#3A4A5C; font-size:0.9rem;'>{cd.long_business_summary}</div>", unsafe_allow_html=True)
        else:
            st.info("Business description not available.")
        st.markdown("")
        b1, b2, b3 = st.columns(3)
        with b1:
            st.markdown(
                f'<div class="kpi-item">'
                f'<div class="kpi-label">Employees</div>'
                f'<div class="kpi-value">{cd.full_time_employees:,}</div>'
                f'</div>' if cd.full_time_employees else
                '<div class="kpi-item"><div class="kpi-label">Employees</div><div class="kpi-value">N/A</div></div>',
                unsafe_allow_html=True,
            )
        with b2:
            hq = f"{cd.city}, {cd.state}" if cd.city else "N/A"
            if cd.country and cd.country != "United States":
                hq += f", {cd.country}"
            st.markdown(
                f'<div class="kpi-item">'
                f'<div class="kpi-label">Headquarters</div>'
                f'<div class="kpi-value">{hq}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with b3:
            web_display = cd.website.replace("https://", "").replace("http://", "").rstrip("/") if cd.website else "N/A"
            st.markdown(
                f'<div class="kpi-item">'
                f'<div class="kpi-label">Website</div>'
                f'<div class="kpi-value">{web_display}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════════════════
    # 3. KEY STATISTICS
    # ══════════════════════════════════════════════════════
    _section("Key Statistics", "")

    # Valuation row
    st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#7A8B9E; text-transform:uppercase; letter-spacing:1px; margin:0.5rem 0 0.3rem 0;'>Valuation</p>", unsafe_allow_html=True)
    v1, v2, v3, v4, v5 = st.columns(5)
    v1.metric("P/E (TTM)", f"{cd.trailing_pe:.1f}" if cd.trailing_pe else "N/A")
    v2.metric("Forward P/E", f"{cd.forward_pe:.1f}" if cd.forward_pe else "N/A")
    v3.metric("PEG Ratio", f"{cd.peg_ratio:.2f}" if cd.peg_ratio else "N/A")
    v4.metric("EV/EBITDA", format_multiple(cd.ev_to_ebitda))
    v5.metric("EV/Revenue", format_multiple(cd.ev_to_revenue))

    # Profitability row
    st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#7A8B9E; text-transform:uppercase; letter-spacing:1px; margin:0.8rem 0 0.3rem 0;'>Profitability</p>", unsafe_allow_html=True)
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Gross Margin", format_pct(cd.gross_margins))
    p2.metric("Op. Margin", format_pct(cd.operating_margins))
    p3.metric("Net Margin", format_pct(cd.profit_margins))
    p4.metric("ROE", format_pct(cd.return_on_equity))
    p5.metric("ROA", format_pct(cd.return_on_assets))

    # Financial health row
    st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#7A8B9E; text-transform:uppercase; letter-spacing:1px; margin:0.8rem 0 0.3rem 0;'>Financial Health</p>", unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns(5)
    f1.metric("P/S (TTM)", f"{cd.price_to_sales:.2f}" if cd.price_to_sales else "N/A")
    f2.metric("Price/Book", f"{cd.price_to_book:.2f}" if cd.price_to_book else "N/A")
    f3.metric("Current Ratio", f"{cd.current_ratio:.2f}" if cd.current_ratio else "N/A")
    f4.metric("D/E Ratio", f"{cd.debt_to_equity / 100:.2f}x" if cd.debt_to_equity else "N/A")
    f5.metric("Beta", f"{cd.beta:.2f}" if cd.beta else "N/A")

    # ══════════════════════════════════════════════════════
    # 4. PRICE CHART
    # ══════════════════════════════════════════════════════
    _section("Price History", "")

    period_choice = st.radio("Period", ["1Y", "3Y", "5Y"], horizontal=True, index=2, label_visibility="collapsed")

    hist = cd.hist_5y if cd.hist_5y is not None and not cd.hist_5y.empty else cd.hist_1y
    if hist is not None and not hist.empty:
        if period_choice == "1Y" and cd.hist_1y is not None:
            plot_hist = cd.hist_1y
        elif period_choice == "3Y" and hist is not None:
            plot_hist = hist.last("3Y") if hasattr(hist, "last") else hist.tail(756)
        else:
            plot_hist = hist

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=plot_hist.index, y=plot_hist["Close"],
            mode="lines", name="Close",
            line=dict(color="#1E90FF", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(30,144,255,0.05)",
        ))
        if "Volume" in plot_hist.columns:
            fig.add_trace(go.Bar(
                x=plot_hist.index, y=plot_hist["Volume"],
                name="Volume", yaxis="y2",
                marker_color="rgba(11,29,58,0.08)",
            ))
            fig.update_layout(
                yaxis2=dict(overlaying="y", side="right", showgrid=False,
                            title=dict(text="Volume", font=dict(size=10, color="#999")),
                            tickformat=".2s", tickfont=dict(size=8, color="#999")),
            )
        fig.update_layout(
            height=420,
            margin=dict(t=10, b=30, l=50, r=50),
            xaxis=dict(
                showgrid=False,
                tickfont=dict(size=9, color="#7A8B9E"),
                rangeslider=dict(visible=False),
            ),
            yaxis=dict(
                title=dict(text="Price ($)", font=dict(size=10, color="#7A8B9E")),
                gridcolor="rgba(0,0,0,0.04)",
                tickfont=dict(size=9, color="#7A8B9E"),
                tickprefix="$",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            hovermode="x unified",
            hoverlabel=dict(bgcolor="#0B1D3A", font_size=11, font_color="#fff"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Price history not available.")

    # ══════════════════════════════════════════════════════
    # 5. FINANCIAL STATEMENTS
    # ══════════════════════════════════════════════════════
    _section("Financial Statements", "")

    def _display_financial_df(df, label, quarterly=False):
        if df is not None and not df.empty:
            display_df = df.copy()
            fmt = "%b %Y" if quarterly else "%Y"
            new_cols = []
            for c in display_df.columns:
                col_str = c.strftime(fmt) if hasattr(c, "strftime") else str(c)
                base, n = col_str, 1
                while col_str in new_cols:
                    n += 1
                    col_str = f"{base} ({n})"
                new_cols.append(col_str)
            display_df.columns = new_cols
            st.dataframe(display_df, use_container_width=True, height=400)
        else:
            st.info(f"{label} not available.")

    fin_tab1, fin_tab2, fin_tab3, fin_tab4 = st.tabs([
        "Income Statement", "Balance Sheet", "Cash Flow", "Quarterly Income"
    ])
    with fin_tab1:
        _display_financial_df(cd.income_stmt, "Income Statement")
    with fin_tab2:
        _display_financial_df(cd.balance_sheet, "Balance Sheet")
    with fin_tab3:
        _display_financial_df(cd.cashflow, "Cash Flow Statement")
    with fin_tab4:
        _display_financial_df(cd.quarterly_income_stmt, "Quarterly Income Statement", quarterly=True)

    # ══════════════════════════════════════════════════════
    # 6. ANALYST CONSENSUS
    # ══════════════════════════════════════════════════════
    _section("Analyst Consensus", "")
    a1, a2 = st.columns([3, 2])

    with a1:
        if cd.recommendations_summary is not None and not cd.recommendations_summary.empty:
            try:
                row = cd.recommendations_summary.iloc[0]
                cats = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
                keys = ["strongBuy", "buy", "hold", "sell", "strongSell"]
                vals = [int(row.get(k, 0)) for k in keys]
                colors = ["#2E7D32", "#66BB6A", "#FFB74D", "#EF5350", "#B71C1C"]
                total = sum(vals)

                fig_rec = go.Figure(go.Bar(
                    x=vals, y=cats, orientation="h",
                    marker_color=colors,
                    text=[f"  {v} ({v/total*100:.0f}%)" if total > 0 else f"  {v}" for v in vals],
                    textposition="outside",
                    textfont=dict(size=11, color="#3A4A5C", family="Inter"),
                ))
                fig_rec.update_layout(
                    height=280,
                    margin=dict(t=40, b=20, l=110, r=60),
                    title=dict(
                        text="Analyst Recommendation Distribution",
                        font=dict(size=13, color="#0B1D3A", family="Inter"),
                    ),
                    xaxis=dict(
                        title=dict(text="# Analysts", font=dict(size=10)),
                        showgrid=True, gridcolor="rgba(0,0,0,0.04)",
                        tickfont=dict(size=9),
                    ),
                    yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#3A4A5C")),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    bargap=0.35,
                )
                st.plotly_chart(fig_rec, use_container_width=True)
            except Exception:
                st.info("Recommendation data not available.")
        else:
            st.info("Analyst recommendation data not available.")

    with a2:
        if cd.analyst_price_targets:
            pt = cd.analyst_price_targets
            st.markdown("")
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#0B1D3A; margin-bottom:0.5rem;'>Price Targets</p>", unsafe_allow_html=True)
            pt1, pt2 = st.columns(2)
            pt1.metric("Mean", f"${pt.get('mean', 0):,.2f}" if pt.get("mean") else "N/A")
            pt2.metric("Median", f"${pt.get('median', 0):,.2f}" if pt.get("median") else "N/A")
            pt3, pt4 = st.columns(2)
            pt3.metric("Low", f"${pt.get('low', 0):,.2f}" if pt.get("low") else "N/A")
            pt4.metric("High", f"${pt.get('high', 0):,.2f}" if pt.get("high") else "N/A")
            if pt.get("mean") and cd.current_price:
                upside = (pt["mean"] - cd.current_price) / cd.current_price * 100
                color = "#2E7D32" if upside >= 0 else "#EF5350"
                st.markdown(
                    f'<div style="text-align:center; margin-top:0.5rem; padding:0.5rem; '
                    f'background:{"rgba(46,125,50,0.08)" if upside >= 0 else "rgba(239,83,80,0.08)"}; '
                    f'border-radius:10px;">'
                    f'<span style="font-size:0.75rem; color:#7A8B9E; font-weight:600;">IMPLIED UPSIDE</span><br>'
                    f'<span style="font-size:1.3rem; font-weight:800; color:{color};">{upside:+.1f}%</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Price target data not available.")

    # ══════════════════════════════════════════════════════
    # 7. OWNERSHIP & INSIDERS
    # ══════════════════════════════════════════════════════
    _section("Ownership & Insiders", "")
    own_tab1, own_tab2, own_tab3 = st.tabs([
        "Major Holders", "Institutional Holders", "Insider Transactions"
    ])
    with own_tab1:
        if cd.major_holders is not None and not cd.major_holders.empty:
            st.dataframe(cd.major_holders, use_container_width=True, hide_index=True)
        else:
            st.info("Major holders data not available.")
    with own_tab2:
        if cd.institutional_holders is not None and not cd.institutional_holders.empty:
            st.dataframe(cd.institutional_holders.head(15), use_container_width=True, hide_index=True)
        else:
            st.info("Institutional holders data not available.")
    with own_tab3:
        if cd.insider_transactions is not None and not cd.insider_transactions.empty:
            st.dataframe(cd.insider_transactions.head(15), use_container_width=True, hide_index=True)
        else:
            st.info("Insider transaction data not available.")

    # ══════════════════════════════════════════════════════
    # 8. EARNINGS HISTORY
    # ══════════════════════════════════════════════════════
    _section("Earnings History", "")
    if cd.earnings_dates is not None and not cd.earnings_dates.empty:
        st.dataframe(cd.earnings_dates.head(8), use_container_width=True)
    else:
        st.info("Earnings data not available.")

    # ══════════════════════════════════════════════════════
    # 9. M&A HISTORY
    # ══════════════════════════════════════════════════════
    _section("M&A History", "")
    if cd.ma_deals:
        deal_count = len(cd.ma_deals)
        source_link = f' &middot; <a href="{cd.ma_source}" target="_blank" style="color:#1E90FF; text-decoration:none; font-weight:500;">View on Wikipedia &rarr;</a>' if cd.ma_source else ""
        st.markdown(
            f'<div style="margin-bottom:0.8rem;">'
            f'<span class="pill pill-gold">{deal_count} Acquisitions</span>'
            f'{source_link}'
            f'</div>',
            unsafe_allow_html=True,
        )
        ma_df = pd.DataFrame([
            {
                "Date": d.get("date", ""),
                "Target": d.get("company", ""),
                "Business": d.get("business", ""),
                "Country": d.get("country", ""),
                "Value (USD)": d.get("value", "Undisclosed"),
            }
            for d in cd.ma_deals[:30]
        ])
        st.dataframe(ma_df, use_container_width=True, hide_index=True, height=400)
        if deal_count > 30:
            st.caption(f"Showing 30 of {deal_count} deals.")
    elif cd.ma_history:
        st.markdown(cd.ma_history)
    else:
        st.info("No public M&A history found for this company.")

    # ══════════════════════════════════════════════════════
    # 10. MANAGEMENT
    # ══════════════════════════════════════════════════════
    _section("Management Team", "")

    mgmt_col1, mgmt_col2 = st.columns([3, 2])
    with mgmt_col1:
        if cd.officers:
            mgmt_data = []
            for o in cd.officers[:10]:
                mgmt_data.append({
                    "Name": o.get("name", "N/A"),
                    "Title": o.get("title", "N/A"),
                    "Age": o.get("age", ""),
                    "Total Pay": format_number(o.get("totalPay")) if o.get("totalPay") else "—",
                })
            st.dataframe(pd.DataFrame(mgmt_data), use_container_width=True, hide_index=True)
        else:
            st.info("Management data not available.")

    with mgmt_col2:
        if cd.mgmt_sentiment:
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#0B1D3A; margin-bottom:0.3rem;'>Management Assessment</p>", unsafe_allow_html=True)
            for line in cd.mgmt_sentiment.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"<div style='font-size:0.82rem; color:#3A4A5C; line-height:1.7; padding:0.15rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 11. NEWS
    # ══════════════════════════════════════════════════════
    _section("Recent News", "")
    if cd.news:
        for n in cd.news[:10]:
            title = n.get("title", "")
            publisher = n.get("publisher", "")
            link = n.get("link", "")
            if link:
                st.markdown(
                    f'<div class="news-item">'
                    f'<a href="{link}" target="_blank" class="news-title">{title}</a>'
                    f'<span class="news-pub"> &mdash; {publisher}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="news-item">'
                    f'<span class="news-title">{title}</span>'
                    f'<span class="news-pub"> &mdash; {publisher}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.info("No recent news available.")

    # ══════════════════════════════════════════════════════
    # 12. ESG SCORES
    # ══════════════════════════════════════════════════════
    _section("ESG Scores", "")
    if cd.esg_scores is not None and not cd.esg_scores.empty:
        e1, e2, e3, e4 = st.columns(4)
        esg_items = [
            (e1, "totalEsg", "Total ESG", "#0B1D3A"),
            (e2, "environmentScore", "Environment", "#2E7D32"),
            (e3, "socialScore", "Social", "#1E90FF"),
            (e4, "governanceScore", "Governance", "#D4A537"),
        ]
        for col_widget, key, label, color in esg_items:
            with col_widget:
                val = "N/A"
                if key in cd.esg_scores.index:
                    v = cd.esg_scores.loc[key]
                    if hasattr(v, "values"):
                        v = v.values[0]
                    val = f"{v}"
                st.markdown(
                    f'<div class="esg-card">'
                    f'<div class="esg-score" style="color:{color};">{val}</div>'
                    f'<div class="esg-label">{label}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.info("ESG data not available for this company.")

    # ══════════════════════════════════════════════════════
    # 13. AI INSIGHTS
    # ══════════════════════════════════════════════════════
    _section("AI-Generated Insights", "")
    ai_tab1, ai_tab2, ai_tab3, ai_tab4 = st.tabs([
        "Executive Summary", "Product Overview", "Industry Analysis", "Risk Factors"
    ])
    with ai_tab1:
        if cd.executive_summary_bullets:
            for b in cd.executive_summary_bullets:
                st.markdown(f"<div style='font-size:0.88rem; color:#3A4A5C; line-height:1.7; padding:0.2rem 0;'>&bull; {b}</div>", unsafe_allow_html=True)
        else:
            st.info("Executive summary not available.")
    with ai_tab2:
        if cd.product_overview:
            for line in cd.product_overview.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"<div style='font-size:0.88rem; color:#3A4A5C; line-height:1.7; padding:0.2rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)
        else:
            st.info("Product overview not available.")
    with ai_tab3:
        if cd.industry_analysis:
            for line in cd.industry_analysis.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"<div style='font-size:0.88rem; color:#3A4A5C; line-height:1.7; padding:0.2rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)
        else:
            st.info("Industry analysis not available.")
    with ai_tab4:
        if cd.risk_factors:
            for line in cd.risk_factors.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"<div style='font-size:0.88rem; color:#3A4A5C; line-height:1.7; padding:0.2rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)
        else:
            st.info("Risk factors not available.")

    # ══════════════════════════════════════════════════════
    # 14. DOWNLOAD PPTX
    # ══════════════════════════════════════════════════════
    st.markdown("")
    st.markdown("")
    _section("Download Tear Sheet", "")

    if not os.path.exists("assets/template.pptx"):
        with st.spinner("Creating template..."):
            from create_template import build
            build()

    with st.spinner("Building 8-slide PowerPoint presentation..."):
        pptx_buf = generate_presentation(cd)

    dl1, dl2, dl3 = st.columns([1, 2, 1])
    with dl2:
        st.download_button(
            label=f"Download {cd.ticker} M&A Profile  (8 slides)",
            data=pptx_buf,
            file_name=f"{cd.ticker}_MA_Profile.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )
        st.markdown(
            "<p style='text-align:center; font-size:0.72rem; color:#7A8B9E; margin-top:0.3rem;'>"
            "Professional IB-grade presentation &middot; Navy/Gold palette &middot; Editable charts"
            "</p>",
            unsafe_allow_html=True,
        )

elif generate_btn and not ticker_input:
    st.warning("Please enter a ticker symbol in the sidebar.")
else:
    # ══════════════════════════════════════════════════════
    # LANDING PAGE
    # ══════════════════════════════════════════════════════
    st.markdown("")

    l1, l2 = st.columns([1, 1])
    with l1:
        st.markdown(
            '<div class="landing-card">'
            '<p style="font-size:1.1rem; font-weight:700; color:#0B1D3A; margin-bottom:1rem;">How It Works</p>'
            '<div class="landing-step"><div class="step-number">1</div><div class="step-text">Enter a stock ticker in the sidebar</div></div>'
            '<div class="landing-step"><div class="step-number">2</div><div class="step-text">Click <b>Generate Profile</b> to pull 60+ live data points</div></div>'
            '<div class="landing-step"><div class="step-number">3</div><div class="step-text">Explore the interactive research dashboard</div></div>'
            '<div class="landing-step"><div class="step-number">4</div><div class="step-text">Download the 8-slide IB-grade PowerPoint</div></div>'
            '</div>',
            unsafe_allow_html=True,
        )

    with l2:
        st.markdown(
            '<div class="landing-card">'
            '<p style="font-size:1.1rem; font-weight:700; color:#0B1D3A; margin-bottom:1rem;">What\'s Inside</p>'
            '<div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.4rem;">'
            '<span class="pill pill-navy" style="text-align:center;">Price & Market Data</span>'
            '<span class="pill pill-navy" style="text-align:center;">Financial Statements</span>'
            '<span class="pill pill-navy" style="text-align:center;">Valuation Multiples</span>'
            '<span class="pill pill-navy" style="text-align:center;">Analyst Consensus</span>'
            '<span class="pill pill-gold" style="text-align:center;">M&A Deal History</span>'
            '<span class="pill pill-navy" style="text-align:center;">Ownership & Insiders</span>'
            '<span class="pill pill-navy" style="text-align:center;">Management Team</span>'
            '<span class="pill pill-navy" style="text-align:center;">ESG Scores</span>'
            '<span class="pill pill-blue" style="text-align:center;">AI Insights</span>'
            '<span class="pill pill-navy" style="text-align:center;">News & Events</span>'
            '</div>'
            '<p style="font-size:0.72rem; color:#7A8B9E; margin-top:0.8rem; text-align:center;">'
            'M&A history scraped from Wikipedia &mdash; no API key needed<br>'
            'Set <code>OPENAI_API_KEY</code> for enhanced AI insights'
            '</p>'
            '</div>',
            unsafe_allow_html=True,
        )
