# Orbital — M&A Intelligence Platform

A Streamlit-powered M&A intelligence platform that transforms stock tickers into comprehensive dashboards, valuation models, and professional PowerPoint presentations.

Combines live market data from Yahoo Finance, full financial statements, DCF valuation, peer benchmarking, and AI-generated strategic insights — replacing hours of manual analysis with a single click.

## Five Analysis Modes

### 1. Company Profile
Enter a ticker symbol and get:
- **60+ data points** from Yahoo Finance — financials, analyst estimates, ownership, ESG
- **M&A history** scraped from Wikipedia — acquisitions, dates, values
- **AI insights** — executive summary, industry analysis, risk factors
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

### 3. DCF Valuation (NEW)
Build a discounted cash flow model:
- **Customizable assumptions** — growth rate, WACC, terminal growth, projection years
- **Free cash flow projection** — multi-year FCF forecast
- **Terminal value** — Gordon Growth Model perpetuity calculation
- **Sensitivity analysis** — growth vs. WACC matrix with color coding
- **Value bridge** — enterprise value to equity value breakdown
- **Implied share price** — compare to current market price

### 4. Quick Compare (NEW)
Side-by-side company comparison:
- **Compare up to 10 companies** simultaneously
- **Key metrics table** — all valuation and profitability metrics
- **Radar chart** — visual multi-metric comparison
- **Price performance** — normalized 1Y price chart (adjustable period)
- **Valuation multiples** — P/E, EV/EBITDA, EV/Revenue comparison
- **Preset comparisons** — FAANG, Big Tech, Canadian Banks, etc.
- **CSV export** — download comparison data

### 5. Merger Analysis
Model a hypothetical acquisition:
- **Pro forma financials** — combined revenue, EBITDA, EPS
- **Accretion/dilution analysis** — impact on acquirer EPS
- **Football field valuation** — range of implied values
- **Sources & uses** — deal financing structure
- **AI-powered deal assessment** — strategic rationale, risks, verdict
- **Deal book PowerPoint** — professional M&A presentation

## New in v2.0

- **Watchlist system** — save favorite tickers with session persistence
- **Excel export** — multi-sheet workbook with Income Statement, Balance Sheet, Cash Flow, and Peer Data
- **DCF Valuation module** — full discounted cash flow analysis with sensitivity
- **Quick Compare mode** — compare up to 10 companies side-by-side
- **Sector screening** — quick picks by sector with popular tickers
- **Price performance charts** — normalized historical price comparison
- **Enhanced visualizations** — radar charts, sensitivity matrices, value bridges

## Quick Start

```bash
# Clone the repo
git clone https://github.com/rajkcho/profilebuilder.git
cd profilebuilder

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run main.py
```

### Enable AI Insights (Optional)

```bash
export OPENAI_API_KEY="sk-..."
streamlit run main.py
```

M&A deal history is scraped from Wikipedia and works without any API key. The OpenAI key enables richer industry analysis and risk factors via GPT-4o-mini.

## Project Structure

```
ProfileBuilder/
├── main.py                # Streamlit UI — 5-mode dashboard
├── data_engine.py         # yfinance data fetching, 60+ fields
├── comps_analysis.py      # Comparable company analysis engine
├── merger_analysis.py     # Pro forma merger calculations
├── ai_insights.py         # LLM-powered insights
├── pptx_generator.py      # PowerPoint builder
├── precedent_deals.py     # Precedent transaction analysis
├── alpha_vantage.py       # Alternative data source
├── create_template.py     # PPTX template generation
├── template_inspector.py  # Helper utility
├── requirements.txt       # Python dependencies
└── assets/
    └── template.pptx      # Blank slide template
```

## Tech Stack

- **Streamlit** — Data-dense web UI with tabs, expanders, interactive Plotly charts
- **python-pptx** — PowerPoint generation with styled tables and native charts
- **yfinance** — Real-time market data, financial statements, analyst estimates, ownership
- **openpyxl** — Excel export with multiple sheets
- **Matplotlib** — Static chart rendering for PPTX slides
- **Plotly** — Interactive price and analyst charts in the web UI
- **OpenAI** — Optional AI insights via GPT-4o-mini
- **NumPy/Pandas** — Financial calculations and data manipulation
- **ThreadPoolExecutor** — Parallel peer data fetching for fast comps

## Watchlist Feature

The watchlist persists during your session and appears in the sidebar:
- Click "Add to Watchlist" from any company profile
- Quick-view tickers with current prices and changes
- Remove tickers with one click

## Export Options

- **PowerPoint** — 8-slide professional tear sheet (Company Profile mode)
- **Excel** — Multi-sheet workbook with all financial data
- **CSV** — Quick summary export or comparison table
- **Deal Book** — 10-slide M&A presentation (Merger Analysis mode)

## License

MIT
