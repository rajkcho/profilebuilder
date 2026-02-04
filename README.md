# M&A Profile Builder

A Streamlit-powered company research platform that transforms a stock ticker into a comprehensive, Yahoo Finance-style dashboard and an 8-slide investment-banker-grade PowerPoint tear sheet.

Combines live market data from Yahoo Finance, full financial statements, ownership analysis, and AI-generated strategic insights — replacing hours of manual tear sheet assembly with a single click.

## What It Does

Enter a ticker symbol, and the app:

1. **Pulls 60+ data points** from Yahoo Finance — 4 years of income statements, balance sheets, cash flow, quarterly data, analyst estimates, insider transactions, institutional ownership, ESG scores, earnings history, and 5-year price history
2. **Scrapes M&A history** from Wikipedia — acquisition targets, dates, deal values, and business descriptions (no API key needed)
3. **Generates AI insights** — product overview, management assessment, executive summary, industry analysis, and risk factors (via OpenAI, with deterministic fallback)
3. **Displays a 14-section dashboard** — Yahoo Finance-style data-dense UI with interactive charts, sortable tables, and collapsible sections
4. **Builds an 8-slide PowerPoint** — professional IB pitch book layout with navy/gold/white palette, styled tables, and embedded charts

### The 8-Slide Tear Sheet

| Slide | Contents |
|-------|----------|
| **Executive Summary** | Company header, business description, key metrics table, 5-year price chart |
| **Financial Analysis** | 4-year income statement table, revenue & margin dual-axis chart, profitability ratios |
| **Balance Sheet & Cash Flow** | Balance sheet highlights, cash flow table, leverage ratios, CF trend chart |
| **Valuation & Analyst** | Valuation multiples table, analyst recommendation bar chart, price target summary |
| **Ownership & Insiders** | Major holders, top 10 institutional holders table, insider transactions |
| **M&A History** | Wikipedia-scraped deal table with dates, targets, values (up to 15 deals) |
| **Management & Governance** | Executives table with compensation, ESG scores, governance highlights |
| **News & Market Context** | 10 news headlines, industry analysis, risk factors |

### The Dashboard

14 interactive sections covering:
- Company header with live price, market cap, volume, 52-week range
- Business overview with employees, HQ, and website
- 15-metric key statistics grid (P/E, PEG, margins, ROE, beta, etc.)
- Tabbed financial statements (annual & quarterly)
- 5-year interactive price chart with volume bars (1Y/3Y/5Y toggle)
- Analyst consensus with recommendation distribution and price targets
- Ownership & insider transaction tables
- Earnings history
- M&A deal history scraped from Wikipedia (dates, targets, values, business descriptions)
- Management team table
- Recent news with links
- ESG scores
- Collapsible AI insights (executive summary, product overview, industry, risks)
- One-click PowerPoint download

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

M&A deal history is scraped from Wikipedia and works without any API key. The OpenAI key enables richer industry analysis and risk factors via GPT-4o-mini. Without it, deterministic insights are generated from financial data.

## Project Structure

```
ProfileBuilder/
├── main.py               # Streamlit UI — 14-section Yahoo Finance-style dashboard
├── data_engine.py         # yfinance data fetching, 60+ fields, CompanyData model
├── ai_insights.py         # LLM-powered insights: M&A history, industry, risks
├── pptx_generator.py      # 8-slide IB-grade PowerPoint builder
├── create_template.py     # One-time template generation (landscape 13.3" × 7.5")
├── template_inspector.py  # Helper to print placeholder idx mapping
├── requirements.txt       # Python dependencies
├── .gitignore
└── assets/
    └── template.pptx      # Blank slide template (auto-generated)
```

## Tech Stack

- **Streamlit** — Data-dense web UI with tabs, expanders, interactive Plotly charts
- **python-pptx** — PowerPoint generation with styled tables and native charts
- **yfinance** — Real-time market data, financial statements, analyst estimates, ownership
- **Matplotlib** — Static chart rendering for PPTX slides (price, revenue, cash flow)
- **Plotly** — Interactive price and analyst charts in the web UI
- **OpenAI** — Optional AI insights via GPT-4o-mini (M&A history, industry analysis)

## License

MIT
