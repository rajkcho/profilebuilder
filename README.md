# Orbital — M&A Intelligence Platform

A Streamlit-powered M&A intelligence platform that transforms stock tickers into comprehensive dashboards, valuation models, and professional PowerPoint presentations.

Combines live market data from Yahoo Finance, full financial statements, DCF valuation, peer benchmarking, and AI-generated strategic insights — replacing hours of manual analysis with a single click.

## Five Analysis Modes

### 1. Company Profile
Enter a ticker symbol and get:
- **60+ data points** from Yahoo Finance — financials, analyst estimates, ownership, ESG
- **M&A history** scraped from Wikipedia — acquisitions, dates, values
- **AI insights** — executive summary, industry analysis, risk factors, SWOT
- **Technical analysis** — RSI, MACD, Bollinger Bands with live signals
- **Ownership overview** — institutional holders, major shareholders
- **Options overview** — put/call ratio, volume, open interest
- **Dividend analysis** — yield, payout ratio, history charts, ex-dates
- **Financial health scorecard** — Piotroski-inspired A-D grading
- **14-section dashboard** — Yahoo Finance-style UI with interactive charts
- **8-slide PowerPoint** — professional IB pitch book layout
- **Excel export** — multi-sheet workbook with all financial data

### 2. Comps Analysis
Run a full comparable company analysis:
- **Auto-discover peers** by sector, industry, and market cap
- **Trading multiples comparison** — EV/EBITDA, EV/Revenue, P/E, PEG
- **Percentile ranking** — see where your company sits vs peers
- **Implied valuation** — what the company would be worth at peer median multiples
- **Rule of 40** — SaaS metric for software companies
- **Exportable comps table** — all peers with key metrics

### 3. DCF Valuation
Build a discounted cash flow model:
- **Customizable assumptions** — growth rate, WACC, terminal growth, projection years
- **Free cash flow projection** — multi-year FCF forecast
- **Terminal value** — Gordon Growth Model perpetuity calculation
- **Sensitivity analysis** — 5x5 growth vs. WACC matrix with color coding
- **Value bridge** — enterprise value to equity value breakdown
- **Implied share price** — compare to current market price

### 4. Quick Compare
Side-by-side company comparison:
- **Compare up to 10 companies** simultaneously
- **Key metrics table** — all valuation and profitability metrics
- **Radar chart** — visual multi-metric comparison
- **Correlation matrix** — price correlation heatmap (1Y daily returns)
- **Price performance** — normalized price chart (adjustable period)
- **Valuation multiples** — P/E, EV/EBITDA, EV/Revenue comparison
- **Profitability comparison** — margins and ROE grouped bars
- **Preset comparisons** — FAANG, Big Tech, Canadian Banks, Semis, Healthcare, SaaS
- **CSV export** — download comparison data

### 5. Merger Analysis
Model a hypothetical acquisition:
- **Pro forma financials** — combined revenue, EBITDA, EPS
- **Accretion/dilution analysis** — impact on acquirer EPS with waterfall chart
- **Football field valuation** — multi-method range analysis
- **Sources & uses** — classic IB deal structure breakdown
- **AI deal intelligence** — strategic rationale, risk factors, deal grade
- **10-slide deal book** — professional PowerPoint export

## Home Dashboard
The splash page includes:
- **Market overview** — live indices (S&P 500, DJIA, NASDAQ, Russell 2000, TSX)
- **Market sentiment gauge** — fear/greed indicator based on SPY momentum
- **Top movers** — daily gainers and losers
- **Sector heatmap** — performance across 11 sector ETFs
- **Earnings calendar** — upcoming earnings for major companies
- **Market news feed** — recent headlines from Yahoo Finance
- **Search history** — quick-access buttons for recent lookups

## Watchlist
- Add/remove tickers from any analysis mode
- Live price and change display in sidebar
- **Notes per ticker** — jot down investment thesis
- Persistent within session

## Tech Stack
- **Streamlit** — UI framework
- **Plotly** — interactive charts
- **yfinance** — market data
- **OpenAI** (optional) — AI insights
- **python-pptx** — PowerPoint generation
- **openpyxl** — Excel export
- **Alpha Vantage** (optional) — earnings data

## Setup
```bash
pip install -r requirements.txt
streamlit run main.py
```

Optional environment variables:
```bash
OPENAI_API_KEY=sk-...      # AI insights
ALPHA_VANTAGE_KEY=...      # Earnings data
```

## Deployment
Hosted on Streamlit Cloud: [profilebuilder.streamlit.app](https://profilebuilder.streamlit.app)

## Version History
- **v4.4** — Percentile ranking, peer comparison bars, key takeaways, ESG scores, comps football field, scrolling market ticker, JSON export
- **v4.0** — Help tooltips, reverse DCF, Monte Carlo simulation, premium sensitivity, deal scorecard, contribution analysis, goodwill/PPA, synergy NPV
- **v3.5** — Enhanced M&A (implied multiples, contribution analysis, goodwill waterfall, synergy phase-in), sidebar redesign with emoji mode labels
- **v3.0** — Technical analysis, options, dividends, health scorecard, correlation matrix, sentiment gauge, sector heatmap, earnings calendar, news feed, watchlist notes, footer, print styles
- **v2.6** — Design improvements: sparklines, status badges, keyboard shortcuts, metric cards
- **v2.5** — Market overview with live indices, top movers on splash page
- **v2.4** — Market overview on splash page
- **v2.3** — Search history, market indices, sector screener
- **v2.2** — Splash pages for each mode, updated README
- **v2.1** — DCF sensitivity analysis, price performance charts
- **v2.0** — Watchlist, DCF, Quick Compare, Excel export, Merger Analysis
- **v1.0** — Company Profile, Comps Analysis, PowerPoint export
