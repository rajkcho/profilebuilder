# ProfileBuilder v7.1

**Wall Street–grade company analysis in a Streamlit app.** ProfileBuilder generates institutional-quality equity research profiles, comparable company analyses, DCF valuations, and M&A models — all from a single ticker input.

**New in v7.1:**
- 🎨 **Modern fintech aesthetic** — Clean blue/emerald/sky palette with professional gradients
- 📑 **Tab-based navigation** — Streamlined interface with organized analysis modes
- 🔍 **Ticker autocomplete** — Smart search with 3,000+ S&P companies
- ⚡ **13 analysis modes** — Expanded toolkit for comprehensive equity research
- ✨ **Enhanced animations** — Smooth transitions and loading states throughout

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
| **LBO Calculator** | Leveraged buyout model with returns analysis, credit metrics, and exit scenarios |
| **Options P/L** | Options profit/loss calculator with payoff diagrams and Greeks analysis |
| **Sector Rotation** | Sector-level analysis with rotation signals, relative strength, and macro overlay |
| **VMS Screener** | Vertical market software screener with Rule of 40, growth/margin scoring, and acquisition candidates |
| **Precedent Deals** | Precedent transaction analysis with deal multiples and premiums paid |
| **Beta Calculator** | Statistical risk analysis with beta calculation, correlation metrics, and volatility analysis |
| **Correlation Matrix** | Multi-asset correlation analysis with heatmaps and portfolio insights |
| **Monte Carlo Sim** | Advanced portfolio simulation with risk metrics and scenario analysis |

## ✨ Key Features

- **150+ data points** per company profile
- **Monte Carlo DCF** with 10,000-iteration simulation
- **Tab-based navigation** for intuitive workflow
- **Ticker autocomplete** with 3,000+ companies
- **Piotroski F-Score** and quality metrics
- **AI-powered insights** (OpenAI integration)
- **Excel export** with formatted, multi-tab workbooks
- **PowerPoint generation** for pitch decks and deal books
- **Precedent transaction** analysis for M&A
- **Pro forma merger modeling** with synergy & sensitivity analysis
- **Interactive Plotly charts** throughout
- **Modern fintech UI** with smooth animations

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
main.py               — Main Streamlit application (30,000+ lines)
data_engine.py        — Financial data fetching & processing
comps_analysis.py     — Comparable company analysis engine
merger_analysis.py    — M&A / pro forma modeling
ai_insights.py        — AI-powered insight generation
pptx_generator.py     — PowerPoint report generation
alpha_vantage.py      — Alpha Vantage API integration
create_template.py    — PowerPoint template generator
template_inspector.py — Template debugging utility
requirements.txt      — Python dependencies
.streamlit/config.toml— Streamlit theme configuration
assets/               — Static assets and resources
```

## 🎨 Design Philosophy

ProfileBuilder v7.1 embraces a **modern fintech aesthetic** inspired by professional trading terminals and institutional research platforms:

- **Color palette**: Blue (#2563EB), Emerald (#10B981), Sky (#60A5FA)
- **Typography**: Clean, readable fonts with proper hierarchy
- **Spacing**: Generous whitespace for improved readability
- **Animations**: Subtle transitions that enhance UX without distraction
- **Data density**: Information-rich displays balanced with visual clarity

## 📄 License

MIT

---

**Built for equity analysts, investment bankers, and portfolio managers who demand institutional-quality research tools.**
