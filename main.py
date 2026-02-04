"""
M&A Profile Builder — Streamlit Application

Transforms a stock ticker into a professional 3-page landscape
M&A tear sheet (PowerPoint) with live market data, AI-generated
insights, and a proprietary Deal Score.

Run:  streamlit run main.py
"""

import streamlit as st
import plotly.graph_objects as go
import os

from data_engine import fetch_company_data, format_number
from ai_insights import generate_insights
from pptx_generator import generate_presentation

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="M&A Profile Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0B1D3A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        border-left: 4px solid #1E90FF;
    }
    .score-high { color: #2E7D32; }
    .score-mid  { color: #D4A537; }
    .score-low  { color: #C62828; }
    .stDownloadButton > button {
        background-color: #0B1D3A;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.6rem 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### M&A Profile Builder")
    st.markdown("---")

    ticker_input = st.text_input(
        "Stock Ticker",
        value="AAPL",
        max_chars=10,
        help="Enter a US stock ticker (e.g. AAPL, MSFT, TSLA)",
    ).strip().upper()

    risk_appetite = st.slider(
        "Risk Appetite",
        min_value=1,
        max_value=10,
        value=5,
        help="1 = Conservative, 10 = Aggressive. Adjusts the Deal Score interpretation.",
    )

    generate_btn = st.button("Generate Profile", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown(
        "<small>Data: Yahoo Finance<br>"
        "Charts: Matplotlib + python-pptx<br>"
        "AI: OpenAI (optional)</small>",
        unsafe_allow_html=True,
    )

# ── Main Area ────────────────────────────────────────────────
st.markdown('<p class="main-header">M&A Profile Builder</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">'
    "Enter a ticker in the sidebar to generate a professional tear sheet."
    "</p>",
    unsafe_allow_html=True,
)

if generate_btn and ticker_input:
    with st.spinner(f"Fetching data for {ticker_input}..."):
        try:
            cd = fetch_company_data(ticker_input)
        except Exception as e:
            st.error(f"Failed to fetch data for **{ticker_input}**: {e}")
            st.stop()

    with st.spinner("Generating AI insights..."):
        cd = generate_insights(cd)

    # ── Company Header ───────────────────────────────────────
    col_name, col_price = st.columns([3, 1])
    with col_name:
        st.markdown(f"## {cd.name}")
        st.markdown(f"**{cd.ticker}**  |  {cd.sector} > {cd.industry}")
    with col_price:
        st.metric(
            "Current Price",
            f"${cd.current_price:,.2f}",
            delta=f"52W: ${cd.fifty_two_week_low:,.0f}–${cd.fifty_two_week_high:,.0f}",
        )

    st.markdown("---")

    # ── Deal Score Gauge ─────────────────────────────────────
    col_gauge, col_outlook = st.columns([1, 2])

    with col_gauge:
        st.markdown("### Deal Score")

        # Adjust interpretation based on risk appetite
        adjusted = cd.deal_score + (risk_appetite - 5) * 2
        adjusted = max(0, min(100, adjusted))

        if adjusted >= 70:
            color = "#2E7D32"
            label = "STRONG BUY"
        elif adjusted >= 40:
            color = "#D4A537"
            label = "MODERATE"
        else:
            color = "#C62828"
            label = "CAUTION"

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=adjusted,
            title={"text": label, "font": {"size": 18, "color": color}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 40], "color": "#FFEBEE"},
                    {"range": [40, 70], "color": "#FFF8E1"},
                    {"range": [70, 100], "color": "#E8F5E9"},
                ],
                "threshold": {
                    "line": {"color": "#0B1D3A", "width": 3},
                    "thickness": 0.8,
                    "value": cd.deal_score,
                },
            },
        ))
        fig_gauge.update_layout(
            height=280, margin=dict(t=40, b=20, l=30, r=30),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Score breakdown
        st.markdown(
            f"**Valuation:** {cd.valuation_score:.0f}/100  \n"
            f"**Solvency:** {cd.solvency_score:.0f}/100  \n"
            f"**Growth:** {cd.growth_score:.0f}/100"
        )

    with col_outlook:
        st.markdown("### Strategic Outlook")

        if cd.executive_summary_bullets:
            for bullet in cd.executive_summary_bullets:
                st.markdown(f"- {bullet}")

        st.markdown("#### Management Sentiment")
        if cd.mgmt_sentiment:
            for line in cd.mgmt_sentiment.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"- {line}")

    st.markdown("---")

    # ── Key Metrics Row ──────────────────────────────────────
    st.markdown("### Key Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Market Cap", format_number(cd.market_cap))
    m2.metric("P/E Ratio", f"{cd.trailing_pe:.1f}" if cd.trailing_pe else "N/A")
    m3.metric("EV/EBITDA", f"{cd.ev_to_ebitda:.1f}x" if cd.ev_to_ebitda else "N/A")
    m4.metric(
        "Revenue Growth",
        f"{cd.revenue_growth:+.1f}%" if cd.revenue_growth is not None else "N/A",
    )

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Enterprise Value", format_number(cd.enterprise_value))
    m6.metric("D/E Ratio", f"{cd.debt_to_equity / 100:.2f}x" if cd.debt_to_equity else "N/A")
    m7.metric("Beta", f"{cd.beta:.2f}" if cd.beta else "N/A")
    m8.metric("Div Yield", f"{cd.dividend_yield * 100:.2f}%" if cd.dividend_yield else "N/A")

    st.markdown("---")

    # ── Price Chart (interactive) ────────────────────────────
    st.markdown("### 1-Year Price History")
    if cd.hist_1y is not None and not cd.hist_1y.empty:
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(
            x=cd.hist_1y.index, y=cd.hist_1y["Close"],
            mode="lines", name="Close",
            line=dict(color="#1E90FF", width=2),
            fill="tozeroy", fillcolor="rgba(30,144,255,0.08)",
        ))
        fig_price.update_layout(
            height=350,
            margin=dict(t=20, b=40, l=50, r=20),
            xaxis_title="", yaxis_title="Price ($)",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
        )
        st.plotly_chart(fig_price, use_container_width=True)
    else:
        st.info("Price history not available.")

    st.markdown("---")

    # ── Recent News ──────────────────────────────────────────
    st.markdown("### Recent News")
    if cd.news:
        for n in cd.news:
            st.markdown(f"- **{n['title']}** — *{n['publisher']}*")
    else:
        st.info("No recent news available.")

    st.markdown("---")

    # ── Generate PPTX ────────────────────────────────────────
    st.markdown("### Download Tear Sheet")

    # Ensure template exists
    if not os.path.exists("assets/template.pptx"):
        with st.spinner("Creating template..."):
            from create_template import build
            build()

    with st.spinner("Building PowerPoint presentation..."):
        pptx_buf = generate_presentation(cd)

    st.download_button(
        label=f"Download {cd.ticker} M&A Profile (.pptx)",
        data=pptx_buf,
        file_name=f"{cd.ticker}_MA_Profile.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        use_container_width=True,
    )

elif generate_btn and not ticker_input:
    st.warning("Please enter a ticker symbol in the sidebar.")
else:
    # Landing state
    st.markdown(
        """
        ### How It Works

        1. **Enter a ticker** in the sidebar (e.g., AAPL, MSFT, TSLA)
        2. **Adjust risk appetite** to calibrate the Deal Score
        3. **Click Generate** to pull live data and AI insights
        4. **Download** the 3-page PowerPoint tear sheet

        The generated profile includes:
        - **Executive Summary** with price chart and key metrics
        - **Financial Overview** with 3-year trends and EBITDA margins
        - **Strategic Analysis** with management team and recent news

        ---
        *Set an `OPENAI_API_KEY` environment variable to enable AI-powered
        insights. Without it, the app uses a deterministic fallback.*
        """
    )
