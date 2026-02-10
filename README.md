<div align="center">

# 🛰️ ORBITAL — M&A Intelligence Platform

**Wall Street-grade financial analysis, powered by open data.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-6B5CE7?style=for-the-badge)](LICENSE)

A comprehensive M&A intelligence platform that combines company profiling, comparable analysis, DCF modeling, merger simulations, and advanced analytics into a single, beautifully designed Streamlit application.

![Orbital Screenshot](screenshot.png)

</div>

---

## ✨ Features

### 📊 6 Analysis Modes

| Mode | Description |
|------|-------------|
| **Company Profile** | Deep-dive single-company analysis with 200+ data points, financials, technicals, and AI commentary |
| **Comparable Analysis** | Multi-company comps with auto-calculated valuation multiples and percentile rankings |
| **DCF Valuation** | Full discounted cash flow model with WACC estimation, sensitivity tables, and scenario analysis |
| **Quick Compare** | Side-by-side comparison of up to 5 companies across key metrics |
| **Merger Analysis** | Accretion/dilution modeling, synergy estimation, pro-forma financials, and football field visualization |
| **VMS Screener** | Vertical market software screening with custom scoring and filtering |

### 🧮 Advanced Analytics

- **Monte Carlo Simulation** — Probabilistic price forecasting with configurable distributions and confidence intervals
- **LBO Model** — Leveraged buyout analysis with debt structuring, IRR waterfall, and exit scenario modeling
- **Sum-of-Parts (SOTP)** — Segment-level valuation with independent multiples and methodology per division
- **Dividend Discount Model (DDM)** — Multi-stage DDM with Gordon Growth terminal value
- **Piotroski F-Score** — 9-factor fundamental strength scoring
- **Altman Z-Score** — Bankruptcy risk probability assessment

### 📈 Technical Analysis

- **RSI** — Relative Strength Index with overbought/oversold signals
- **MACD** — Moving Average Convergence Divergence with signal line crossovers
- **Bollinger Bands** — Volatility-based price channels with squeeze detection
- **Support & Resistance** — Automated pivot point and level identification
- **Momentum Score** — Composite technical momentum indicator (0–100)

### 🤝 M&A Intelligence

- **Deal Book** — Exportable HTML deal book with branded cover page and full analysis
- **Precedent Transactions** — Comparable transaction multiples and premium analysis
- **Accretion/Dilution** — Pro-forma EPS impact modeling with synergy layering
- **Football Field** — Multi-methodology valuation range visualization

### 📤 Data Export

- **Excel** — Multi-sheet workbook with formatted financials, comps, and charts
- **PowerPoint** — 9-slide institutional-quality pitch deck with embedded visualizations
- **HTML Deal Book** — Standalone branded deal book for client distribution
- **CSV** — Raw data export for further analysis

### ⚠️ Risk & Quality

- **Risk Matrix** — Multi-factor risk scoring across market, credit, liquidity, and operational dimensions
- **Earnings Quality** — Accrual analysis, cash flow verification, and red flag detection
- **Covenant Monitor** — Debt covenant compliance tracking and headroom analysis
- **Insider Sentiment** — Insider transaction tracking and net sentiment scoring

### 🌐 Market Intelligence

- **Live Market Ticker** — Real-time index and commodity price marquee
- **Sector Heatmap** — S&P 500 sector performance visualization
- **News Feed** — Company and market news aggregation
- **Earnings Calendar** — Upcoming earnings dates and consensus estimates

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/orbital.git
cd orbital

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run main.py
```

The app will launch at [http://localhost:8501](http://localhost:8501).

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root (all keys are **optional**):

```env
# OpenAI — enables AI-powered commentary and insights
OPENAI_API_KEY=sk-...

# Alpha Vantage — enhances fundamental data coverage
ALPHA_VANTAGE_API_KEY=...
```

> **Note:** Orbital is fully functional without any API keys. AI commentary and some supplemental data sources are disabled when keys are not provided.

---

## 🏗️ Architecture

```
orbital/
├── main.py                  # Application entry point (~16,700 lines)
├── requirements.txt         # Python dependencies
├── .env                     # API keys (optional, not committed)
├── .streamlit/
│   └── config.toml          # Streamlit theme & server config
├── screenshot.png           # App screenshot for README
├── LICENSE                  # MIT License
└── README.md                # This file
```

The application is structured as a single-file Streamlit app with modular internal sections for each analysis mode. Key architectural patterns:

- **Session state management** for cross-component data sharing
- **Cached data fetching** via `@st.cache_data` for performance
- **Lazy computation** — heavy models (Monte Carlo, LBO, DCF) run on-demand
- **Responsive CSS** with custom dark theme and glassmorphism styling

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Streamlit, Custom CSS, HTML Components |
| **Visualization** | Plotly, Streamlit native charts |
| **Data** | yfinance, Alpha Vantage (optional) |
| **Modeling** | NumPy, Pandas |
| **Export** | python-pptx, openpyxl, native HTML |
| **AI** | OpenAI GPT (optional) |

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Guidelines

- Maintain the single-file architecture for `main.py`
- Follow existing code style and naming conventions
- Test with multiple tickers before submitting
- Update feature documentation if adding new analysis capabilities

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

**Built for analysts, by analysts.**

*ORBITAL — See the whole picture.*

</div>
