# Orbital (ProfileBuilder) v7.0

**Modern M&A intelligence platform with institutional-grade analytics.** Orbital delivers professional equity research, comparable company analysis, DCF valuation, and comprehensive M&A functionality — all with a clean, modern fintech interface inspired by Linear, Vercel, and Stripe.

![ProfileBuilder Screenshot](docs/screenshot.png)
<!-- Replace with actual screenshot -->

---

## 🎯 Analysis Modes

| Mode | Description |
|------|-------------|
| **📊 Company Profile** | Full equity research profile with 150+ data points, financial statements, key ratios, ownership, and AI insights |
| **📈 Comps Analysis** | Comparable company analysis with automatic peer discovery, trading multiples, and relative valuation |
| **💹 DCF Valuation** | Discounted cash flow model with Monte Carlo simulation, sensitivity tables, and football field chart |
| **⚖️ Quick Compare** | Side-by-side comparison of up to 5 companies across key financial metrics |
| **🤝 Merger Analysis** | Full M&A model with pro forma financials, accretion/dilution analysis, synergy modeling, and deal structure |
| **📋 Due Diligence** | ✨ NEW - Comprehensive DD tracker with 40+ checkpoints across 6 categories (Financial, Legal, Commercial, Ops, IT, HR) |
| **🔗 Synergy Model** | ✨ NEW - Revenue and cost synergy estimation with waterfall bridge chart and run-rate calculations |
| **📅 Integration Plan** | ✨ NEW - 100-day post-merger integration roadmap with milestones, phases, and Gantt timeline |
| **💼 Deal Structure** | ✨ NEW - Stock vs cash vs mixed consideration optimizer with pros/cons and tax implications |
| **📊 Fairness Opinion** | ✨ NEW - Valuation football field across DCF, comps, precedent transactions with fair/unfair determination |
| **🔍 VMS Screener** | Vertical market software screener with Rule of 40, growth/margin scoring, and acquisition candidates |
| **📊 Options P/L** | Options profit/loss calculator with payoff diagrams and Greeks analysis |
| **🔄 Sector Rotation** | Sector-level analysis with rotation signals, relative strength, and macro overlay |

## ✨ What's New in v7.0

**🎨 Complete Visual Redesign**
- Modern fintech aesthetic inspired by Linear, Vercel, Stripe, and Bloomberg
- Glass-morphism cards with backdrop blur effects
- Electric blue (#2563EB) and emerald (#10B981) accent colors
- Clean typography with Inter font family
- Purposeful animations (fade-ins, hover lifts, shimmer effects)
- Replaced 80s space/neon theme with professional design system

**🤝 5 New M&A Analysis Modes**
- Due Diligence Tracker with comprehensive checklists
- Synergy Model with waterfall visualization
- 100-Day Integration Planning
- Deal Structure Optimizer (cash/stock/mixed)
- Fairness Opinion Generator with football field

**📊 Enhanced PPTX Output**
- McKinsey-level slide quality
- 7-slide company profile deck (vs. 3 previously)
- Professional formatting with page numbers and watermarks
- Football field valuation charts
- ESG, LBO, and management effectiveness slides

## ✨ Core Features

- **150+ data points** per company profile
- **Monte Carlo DCF** with 10,000-iteration simulation
- **LBO / Leveraged Buyout** calculator
- **Piotroski F-Score** and quality metrics
- **AI-powered insights** (OpenAI integration)
- **Excel export** with formatted, multi-tab workbooks
- **PowerPoint generation** for pitch decks and deal books (7 slides)
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
