# ProfileBuilder v5.8

**Wall Street–grade company analysis in a Streamlit app.** ProfileBuilder generates institutional-quality equity research profiles, comparable company analyses, DCF valuations, and M&A models — all from a single ticker input.

![ProfileBuilder Screenshot](docs/screenshot.png)
<!-- Replace with actual screenshot -->

---

## 🎯 Analysis Modes

| Mode | Description |
|------|-------------|
| **Company Profile** | Full equity research profile with 150+ data points, financial statements, key ratios, ownership, and AI-generated insights |
| **Comps Analysis** | Comparable company analysis with automatic peer discovery, trading multiples, and relative valuation |
| **DCF Valuation** | Discounted cash flow model with Monte Carlo simulation, sensitivity tables, and football field chart |
| **Quick Compare** | Side-by-side comparison of up to 5 companies across key financial metrics |
| **Merger Analysis** | Full M&A model with pro forma financials, accretion/dilution analysis, synergy modeling, and deal structure |
| **Options P/L** | Options profit/loss calculator with payoff diagrams and Greeks analysis |
| **Sector Rotation** | Sector-level analysis with rotation signals, relative strength, and macro overlay |
| **VMS Screener** | Vertical market software screener with Rule of 40, growth/margin scoring, and acquisition candidates |

## ✨ Key Features

- **150+ data points** per company profile
- **Monte Carlo DCF** with 10,000-iteration simulation
- **LBO / Leveraged Buyout** calculator
- **Piotroski F-Score** and quality metrics
- **AI-powered insights** (OpenAI integration)
- **Excel export** with formatted, multi-tab workbooks
- **PowerPoint generation** for pitch decks and deal books
- **Precedent transaction** analysis for M&A
- **Pro forma merger modeling** with synergy & sensitivity analysis
- **Interactive Plotly charts** throughout

## 🛠 Tech Stack

- **Python 3.10+**
- **Streamlit** — UI framework
- **Plotly** — interactive charting
- **yfinance** — market data
- **pandas / NumPy** — data processing
- **openpyxl** — Excel export
- **python-pptx** — PowerPoint generation
- **matplotlib** — supplementary charts

## 🚀 Getting Started

```bash
# Clone
git clone https://github.com/rajkcho/profilebuilder.git
cd profilebuilder

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run main.py
```

The app opens at `http://localhost:8501`.

### Optional: AI Insights

Set your OpenAI API key for AI-generated analysis:

```bash
echo "OPENAI_API_KEY=sk-..." > .env
```

## 📁 Project Structure

```
main.py               — Main Streamlit application (19,100+ lines)
data_engine.py        — Financial data fetching & processing
comps_analysis.py     — Comparable company analysis engine
merger_analysis.py    — M&A / pro forma modeling
precedent_deals.py    — Precedent transaction scraping
ai_insights.py        — AI-powered insight generation
pptx_generator.py     — PowerPoint report generation
requirements.txt      — Python dependencies
```

## 📄 License

MIT
