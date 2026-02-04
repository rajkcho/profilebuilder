# M&A Profile Builder

A Streamlit-powered tool that transforms a stock ticker into a professional 3-page landscape M&A tear sheet (PowerPoint), combining live market data, financial analysis, and AI-generated strategic insights.

Built with 15+ years of M&A advisory experience distilled into an automated workflow — replacing hours of manual tear sheet assembly with a single click.

## What It Does

Enter a ticker symbol, and the app:

1. **Pulls live data** from Yahoo Finance — 3 years of income statements, balance sheets, price history, and news
2. **Computes a Deal Score** (1–100) weighing valuation (40%), solvency (30%), and revenue growth (30%)
3. **Generates AI insights** — product overview, management sentiment, and executive summary (via OpenAI, with a deterministic fallback)
4. **Builds a 3-slide PowerPoint** using the template-based injection pattern from python-pptx

### The 3-Page Profile

| Slide | Contents |
|-------|----------|
| **Executive Summary** | Company name, ticker, price, 1-year price chart, key metrics, investment highlights |
| **Financials & Deal Score** | 3-year revenue/EBITDA/net income table, EBITDA margin bar chart (native PPTX), deal score gauge |
| **Strategy & M&A** | Management team, product segment pie chart (native PPTX), recent news headlines |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/rajkcho/profilebuilder.git
cd profilebuilder

# Install dependencies
pip install -r requirements.txt

# Generate the PowerPoint template
python create_template.py

# Run the app
streamlit run main.py
```

### Optional: Enable AI Insights

```bash
export OPENAI_API_KEY="sk-..."
streamlit run main.py
```

Without the API key, the app uses a deterministic fallback that produces structured bullets from the financial data.

## Project Structure

```
ProfileBuilder/
├── main.py               # Streamlit UI — sidebar, gauge, metrics, download
├── data_engine.py         # yfinance data fetching + Deal Score algorithm
├── ai_insights.py         # LLM-powered insights with fallback
├── pptx_generator.py      # 3-slide PowerPoint builder
├── create_template.py     # One-time template generation script
├── template_inspector.py  # Helper to print placeholder idx mapping
├── requirements.txt       # Python dependencies
├── .gitignore
└── assets/
    └── template.pptx      # Branded slide template
```

## Deal Score Algorithm

The proprietary Deal Score rates M&A attractiveness from 1 to 100:

- **Valuation (40%)** — Trailing P/E mapped to a 0–100 scale (lower P/E = higher score)
- **Solvency (30%)** — Debt-to-Equity ratio (lower leverage = higher score)
- **Growth (30%)** — Year-over-year revenue growth (higher growth = higher score)

The Risk Appetite slider (1–10) in the sidebar adjusts the final interpretation threshold.

## Template Workflow

This project follows the **Template-Based Injection** pattern:

1. `create_template.py` generates `assets/template.pptx` with indexed placeholders
2. `template_inspector.py` lets you verify the placeholder idx mapping
3. `pptx_generator.py` loads the template and injects data into positioned shapes
4. Native PPTX charts (`CategoryChartData`) produce editable bar and pie charts

## Tech Stack

- **Streamlit** — Web UI with sidebar controls and interactive Plotly charts
- **python-pptx** — PowerPoint generation with native chart support
- **yfinance** — Real-time market data and financial statements
- **Matplotlib** — Static price chart rendering
- **Plotly** — Interactive deal score gauge in the web UI
- **OpenAI** — Optional AI-powered insights (GPT-4o-mini)

## License

MIT
