# M&A Profile Builder (Orbital)

A Streamlit-powered M&A intelligence platform that transforms a stock ticker into a comprehensive, Yahoo Finance-style dashboard, comparable company analysis, and investment-banker-grade PowerPoint tear sheets.

Combines live market data from Yahoo Finance, full financial statements, ownership analysis, peer benchmarking, and AI-generated strategic insights — replacing hours of manual tear sheet assembly with a single click.

## Three Analysis Modes

### 1. Company Profile
Enter a ticker symbol and get:
- **60+ data points** from Yahoo Finance — financials, analyst estimates, ownership, ESG
- **M&A history** scraped from Wikipedia — acquisitions, dates, values
- **AI insights** — executive summary, industry analysis, risk factors
- **14-section dashboard** — Yahoo Finance-style UI with interactive charts
- **8-slide PowerPoint** — professional IB pitch book layout

### 2. Comps Analysis (NEW)
Run a full comparable company analysis:
- **Auto-discover peers** by sector, industry, and market cap
- **Trading multiples comparison** — EV/EBITDA, EV/Revenue, P/E, PEG
- **Percentile ranking** — see where your company sits vs peers
- **Implied valuation** — what the company would be worth at peer median multiples
- **Rule of 40** — SaaS metric for software companies
- **Exportable comps table** — all peers with key metrics

### 3. Merger Analysis
Model a hypothetical acquisition:
- **Pro forma financials** — combined revenue, EBITDA, EPS
- **Accretion/dilution analysis** — impact on acquirer EPS
- **Football field valuation** — range of implied values
- **Sources & uses** — deal financing structure
- **AI-powered deal assessment** — strategic rationale, risks, verdict
- **Deal book PowerPoint** — professional M&A presentation

## The 8-Slide Tear Sheet (Company Profile)

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

## Comps Analysis Features

The comparable company analysis module provides:

- **Automatic peer discovery** — finds similar companies based on sector/industry
- **Market cap filtering** — peers sized appropriately to target
- **Key multiples**: EV/EBITDA, EV/Revenue, P/E, PEG, Price/Book
- **Profitability metrics**: Gross margin, EBITDA margin, ROE
- **Growth metrics**: Revenue growth, Rule of 40
- **Statistical summary**: Median, mean, percentile rankings
- **Implied valuation**: What target would be worth at peer multiples

Supports special handling for **SaaS/Software companies** with Rule of 40 analysis.

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
├── main.py                # Streamlit UI — 3-mode dashboard
├── data_engine.py         # yfinance data fetching, 60+ fields
├── comps_analysis.py      # Comparable company analysis engine (NEW)
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
- **Matplotlib** — Static chart rendering for PPTX slides
- **Plotly** — Interactive price and analyst charts in the web UI
- **OpenAI** — Optional AI insights via GPT-4o-mini
- **NumPy/Pandas** — Financial calculations and data manipulation
- **ThreadPoolExecutor** — Parallel peer data fetching for fast comps

## License

MIT
