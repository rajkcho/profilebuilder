"""
M&A Profile Builder — Streamlit Application

Yahoo Finance / Perplexity-style comprehensive company research platform.
Generates an 8-slide investment-banker-grade PowerPoint tear sheet.

Run:  streamlit run main.py
"""

import streamlit as st
import plotly.graph_objects as go
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
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: 700; color: #0B1D3A; margin-bottom: 0; }
    .sub-header { font-size: 0.9rem; color: #666; margin-bottom: 1rem; }
    .price-up { color: #2E7D32; font-weight: 700; }
    .price-down { color: #C62828; font-weight: 700; }
    .stat-label { font-size: 0.7rem; color: #888; text-transform: uppercase; }
    .stat-value { font-size: 1rem; font-weight: 600; color: #0B1D3A; }
    .section-divider { border-top: 2px solid #D4A537; margin: 1.5rem 0 1rem 0; }
    div[data-testid="stMetric"] { background: #f8f9fa; border-radius: 8px; padding: 0.5rem; }
    .stDownloadButton > button {
        background-color: #0B1D3A; color: white; font-weight: 600;
        border-radius: 8px; padding: 0.6rem 2rem; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### M&A Profile Builder")
    st.markdown("---")
    ticker_input = st.text_input(
        "Stock Ticker", value="AAPL", max_chars=10,
        help="Enter a US stock ticker (e.g. AAPL, MSFT, TSLA, GOOGL)"
    ).strip().upper()

    generate_btn = st.button("Generate Profile", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown(
        "<small>Data: Yahoo Finance<br>"
        "Charts: Plotly + Matplotlib<br>"
        "PPTX: python-pptx<br>"
        "AI: OpenAI (optional)</small>",
        unsafe_allow_html=True,
    )

# ── Main Area ────────────────────────────────────────────────
st.markdown('<p class="main-header">M&A Profile Builder</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Comprehensive company research & 8-slide tear sheet generator</p>',
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
    # 1. COMPANY HEADER BAR
    # ══════════════════════════════════════════════════════
    c1, c2, c3, c4, c5 = st.columns([4, 2, 2, 2, 2])
    with c1:
        st.markdown(f"## {cd.name}")
        st.markdown(f"**{cd.ticker}**  |  {cd.exchange}  |  {cd.sector} > {cd.industry}")
    with c2:
        color = "normal" if cd.price_change >= 0 else "inverse"
        st.metric("Price", f"${cd.current_price:,.2f}",
                  f"{cd.price_change:+.2f} ({cd.price_change_pct:+.2f}%)")
    with c3:
        st.metric("Market Cap", format_number(cd.market_cap))
    with c4:
        st.metric("Volume", format_number(cd.volume, prefix="", decimals=0))
    with c5:
        st.metric("52W Range", f"${cd.fifty_two_week_low:,.0f} - ${cd.fifty_two_week_high:,.0f}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 2. BUSINESS OVERVIEW
    # ══════════════════════════════════════════════════════
    with st.expander("Business Overview", expanded=True):
        if cd.long_business_summary:
            st.write(cd.long_business_summary)
        else:
            st.info("Business description not available.")
        b1, b2, b3 = st.columns(3)
        b1.markdown(f"**Employees:** {cd.full_time_employees:,}" if cd.full_time_employees else "**Employees:** N/A")
        hq = f"{cd.city}, {cd.state}, {cd.country}" if cd.city else "N/A"
        b2.markdown(f"**Headquarters:** {hq}")
        b3.markdown(f"**Website:** [{cd.website}]({cd.website})" if cd.website else "**Website:** N/A")

    # ══════════════════════════════════════════════════════
    # 3. KEY STATISTICS PANEL
    # ══════════════════════════════════════════════════════
    st.markdown("### Key Statistics")
    r1c1, r1c2, r1c3, r1c4, r1c5 = st.columns(5)
    r1c1.metric("P/E (TTM)", f"{cd.trailing_pe:.1f}" if cd.trailing_pe else "N/A")
    r1c2.metric("Forward P/E", f"{cd.forward_pe:.1f}" if cd.forward_pe else "N/A")
    r1c3.metric("PEG Ratio", f"{cd.peg_ratio:.2f}" if cd.peg_ratio else "N/A")
    r1c4.metric("P/S (TTM)", f"{cd.price_to_sales:.2f}" if cd.price_to_sales else "N/A")
    r1c5.metric("Price/Book", f"{cd.price_to_book:.2f}" if cd.price_to_book else "N/A")

    r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns(5)
    r2c1.metric("EV/EBITDA", format_multiple(cd.ev_to_ebitda))
    r2c2.metric("EV/Revenue", format_multiple(cd.ev_to_revenue))
    r2c3.metric("Gross Margin", format_pct(cd.gross_margins))
    r2c4.metric("Op. Margin", format_pct(cd.operating_margins))
    r2c5.metric("Net Margin", format_pct(cd.profit_margins))

    r3c1, r3c2, r3c3, r3c4, r3c5 = st.columns(5)
    r3c1.metric("ROE", format_pct(cd.return_on_equity))
    r3c2.metric("ROA", format_pct(cd.return_on_assets))
    r3c3.metric("Current Ratio", f"{cd.current_ratio:.2f}" if cd.current_ratio else "N/A")
    r3c4.metric("D/E Ratio", f"{cd.debt_to_equity / 100:.2f}x" if cd.debt_to_equity else "N/A")
    r3c5.metric("Beta", f"{cd.beta:.2f}" if cd.beta else "N/A")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 4. FINANCIAL STATEMENTS (Tabbed)
    # ══════════════════════════════════════════════════════
    st.markdown("### Financial Statements")

    def _display_financial_df(df, label, quarterly=False):
        if df is not None and not df.empty:
            display_df = df.copy()
            # Format column headers — use quarter format for quarterly data
            fmt = "%b %Y" if quarterly else "%Y"
            new_cols = []
            for c in display_df.columns:
                col_str = c.strftime(fmt) if hasattr(c, "strftime") else str(c)
                # Deduplicate: append suffix if already seen
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

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 5. PRICE CHART (5-Year)
    # ══════════════════════════════════════════════════════
    st.markdown("### Price History")
    period_choice = st.radio("Period", ["1Y", "3Y", "5Y"], horizontal=True, index=2)

    hist = cd.hist_5y if cd.hist_5y is not None and not cd.hist_5y.empty else cd.hist_1y
    if hist is not None and not hist.empty:
        # Filter by period
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
            line=dict(color="#1E90FF", width=2),
            fill="tozeroy", fillcolor="rgba(30,144,255,0.06)",
        ))
        if "Volume" in plot_hist.columns:
            fig.add_trace(go.Bar(
                x=plot_hist.index, y=plot_hist["Volume"],
                name="Volume", yaxis="y2",
                marker_color="rgba(153,153,153,0.3)",
            ))
            fig.update_layout(
                yaxis2=dict(overlaying="y", side="right", showgrid=False,
                            title="Volume", tickformat=".2s"),
            )
        fig.update_layout(
            height=400, margin=dict(t=20, b=40, l=50, r=50),
            xaxis_title="", yaxis_title="Price ($)",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Price history not available.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 6. ANALYST CONSENSUS
    # ══════════════════════════════════════════════════════
    st.markdown("### Analyst Consensus")
    a1, a2 = st.columns([1, 1])

    with a1:
        if cd.recommendations_summary is not None and not cd.recommendations_summary.empty:
            try:
                row = cd.recommendations_summary.iloc[0]
                cats = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
                keys = ["strongBuy", "buy", "hold", "sell", "strongSell"]
                vals = [int(row.get(k, 0)) for k in keys]
                colors = ["#2E7D32", "#66BB6A", "#FFA726", "#EF5350", "#C62828"]

                fig_rec = go.Figure(go.Bar(
                    x=vals, y=cats, orientation="h",
                    marker_color=colors, text=vals, textposition="outside",
                ))
                fig_rec.update_layout(
                    height=250, margin=dict(t=30, b=20, l=100, r=40),
                    title="Recommendation Distribution",
                    xaxis_title="# Analysts",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_rec, use_container_width=True)
            except Exception:
                st.info("Recommendation data not available.")
        else:
            st.info("Analyst recommendation data not available.")

    with a2:
        if cd.analyst_price_targets:
            pt = cd.analyst_price_targets
            st.markdown("**Price Targets**")
            pt1, pt2 = st.columns(2)
            pt1.metric("Mean Target", f"${pt.get('mean', 0):,.2f}" if pt.get("mean") else "N/A")
            pt2.metric("Median Target", f"${pt.get('median', 0):,.2f}" if pt.get("median") else "N/A")
            pt3, pt4 = st.columns(2)
            pt3.metric("Low", f"${pt.get('low', 0):,.2f}" if pt.get("low") else "N/A")
            pt4.metric("High", f"${pt.get('high', 0):,.2f}" if pt.get("high") else "N/A")
            if pt.get("mean") and cd.current_price:
                upside = (pt["mean"] - cd.current_price) / cd.current_price * 100
                st.markdown(f"**Implied Upside/Downside:** {upside:+.1f}%")
        else:
            st.info("Price target data not available.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 7. OWNERSHIP & INSIDERS
    # ══════════════════════════════════════════════════════
    st.markdown("### Ownership & Insiders")
    own_tab1, own_tab2, own_tab3 = st.tabs([
        "Major Holders", "Institutional Holders", "Insider Transactions"
    ])
    with own_tab1:
        if cd.major_holders is not None and not cd.major_holders.empty:
            st.dataframe(cd.major_holders, use_container_width=True)
        else:
            st.info("Major holders data not available.")
    with own_tab2:
        if cd.institutional_holders is not None and not cd.institutional_holders.empty:
            st.dataframe(cd.institutional_holders.head(15), use_container_width=True)
        else:
            st.info("Institutional holders data not available.")
    with own_tab3:
        if cd.insider_transactions is not None and not cd.insider_transactions.empty:
            st.dataframe(cd.insider_transactions.head(15), use_container_width=True)
        else:
            st.info("Insider transaction data not available.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 8. EARNINGS
    # ══════════════════════════════════════════════════════
    st.markdown("### Earnings History")
    if cd.earnings_dates is not None and not cd.earnings_dates.empty:
        st.dataframe(cd.earnings_dates.head(8), use_container_width=True)
    else:
        st.info("Earnings data not available.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 9. M&A HISTORY
    # ══════════════════════════════════════════════════════
    st.markdown("### M&A History")
    if cd.ma_history:
        st.markdown(cd.ma_history)
    else:
        st.info("M&A history not available. Set OPENAI_API_KEY for AI-generated deal history.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 10. MANAGEMENT
    # ══════════════════════════════════════════════════════
    st.markdown("### Management Team")
    if cd.officers:
        mgmt_data = []
        for o in cd.officers[:10]:
            mgmt_data.append({
                "Name": o.get("name", "N/A"),
                "Title": o.get("title", "N/A"),
                "Age": o.get("age", ""),
                "Compensation": format_number(o.get("totalPay")) if o.get("totalPay") else "",
            })
        st.dataframe(pd.DataFrame(mgmt_data), use_container_width=True, hide_index=True)
    else:
        st.info("Management data not available.")

    if cd.mgmt_sentiment:
        with st.expander("Management Assessment"):
            for line in cd.mgmt_sentiment.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"- {line}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 11. NEWS
    # ══════════════════════════════════════════════════════
    st.markdown("### Recent News")
    if cd.news:
        for n in cd.news[:10]:
            title = n.get("title", "")
            publisher = n.get("publisher", "")
            link = n.get("link", "")
            if link:
                st.markdown(f"- [{title}]({link}) — *{publisher}*")
            else:
                st.markdown(f"- **{title}** — *{publisher}*")
    else:
        st.info("No recent news available.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 12. ESG
    # ══════════════════════════════════════════════════════
    st.markdown("### ESG Scores")
    if cd.esg_scores is not None and not cd.esg_scores.empty:
        e1, e2, e3, e4 = st.columns(4)
        for col_widget, key, label in [
            (e1, "totalEsg", "Total ESG"),
            (e2, "environmentScore", "Environment"),
            (e3, "socialScore", "Social"),
            (e4, "governanceScore", "Governance"),
        ]:
            if key in cd.esg_scores.index:
                val = cd.esg_scores.loc[key]
                if hasattr(val, "values"):
                    val = val.values[0]
                col_widget.metric(label, f"{val}")
            else:
                col_widget.metric(label, "N/A")
    else:
        st.info("ESG data not available for this company.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 13. AI INSIGHTS (Collapsible)
    # ══════════════════════════════════════════════════════
    with st.expander("AI-Generated Insights"):
        if cd.executive_summary_bullets:
            st.markdown("**Executive Summary**")
            for b in cd.executive_summary_bullets:
                st.markdown(f"- {b}")

        if cd.product_overview:
            st.markdown("**Product Overview**")
            for line in cd.product_overview.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"- {line}")

        if cd.industry_analysis:
            st.markdown("**Industry Analysis**")
            for line in cd.industry_analysis.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"- {line}")

        if cd.risk_factors:
            st.markdown("**Risk Factors**")
            for line in cd.risk_factors.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"- {line}")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 14. DOWNLOAD PPTX
    # ══════════════════════════════════════════════════════
    st.markdown("### Download Tear Sheet")

    if not os.path.exists("assets/template.pptx"):
        with st.spinner("Creating template..."):
            from create_template import build
            build()

    with st.spinner("Building 8-slide PowerPoint presentation..."):
        pptx_buf = generate_presentation(cd)

    st.download_button(
        label=f"Download {cd.ticker} M&A Profile (8 slides)",
        data=pptx_buf,
        file_name=f"{cd.ticker}_MA_Profile.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        use_container_width=True,
    )

elif generate_btn and not ticker_input:
    st.warning("Please enter a ticker symbol in the sidebar.")
else:
    # Landing state
    st.markdown("""
### How It Works

1. **Enter a ticker** in the sidebar (e.g., AAPL, MSFT, TSLA)
2. **Click Generate** to pull comprehensive live data and AI insights
3. **Explore** the Yahoo Finance-style dashboard with 14 data sections
4. **Download** the 8-slide investment-banker-grade PowerPoint tear sheet

### What's Included

| Section | Data |
|---------|------|
| **Executive Summary** | Price, market cap, business description, key metrics chart |
| **Financial Analysis** | 4-year income statement, revenue & margin trends |
| **Balance Sheet & Cash Flow** | Assets, liabilities, equity, operating & free cash flow |
| **Valuation & Analyst** | P/E, PEG, EV/EBITDA, price targets, recommendation distribution |
| **Ownership & Insiders** | Institutional holders, insider transactions |
| **M&A History** | AI-generated deal history with valuations (requires API key) |
| **Management & Governance** | Officers, compensation, ESG scores |
| **News & Market Context** | Recent headlines, industry analysis, risk factors |

---
*Set `OPENAI_API_KEY` for AI-powered M&A history, industry analysis, and risk factors.
Without it, deterministic insights are generated from financial data.*
    """)
