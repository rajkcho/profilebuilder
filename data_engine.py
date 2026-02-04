"""
Data Engine — pulls financial data from yfinance, computes the Deal Score,
and structures everything for the PPTX generator and Streamlit UI.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompanyData:
    """Container for all data needed by the presentation and UI."""

    ticker: str = ""
    name: str = ""
    sector: str = ""
    industry: str = ""
    current_price: float = 0.0
    market_cap: float = 0.0
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    trailing_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    debt_to_equity: Optional[float] = None
    enterprise_value: Optional[float] = 0.0
    ev_to_ebitda: Optional[float] = None
    beta: Optional[float] = None
    dividend_yield: Optional[float] = None
    fifty_two_week_high: float = 0.0
    fifty_two_week_low: float = 0.0
    avg_volume: float = 0.0

    # Officers
    officers: list = field(default_factory=list)

    # Financials — DataFrames
    income_stmt: Optional[pd.DataFrame] = None
    balance_sheet: Optional[pd.DataFrame] = None

    # Derived annual series (most recent 3 years)
    revenue: Optional[pd.Series] = None
    ebitda: Optional[pd.Series] = None
    net_income: Optional[pd.Series] = None
    ebitda_margin: Optional[pd.Series] = None
    total_debt: Optional[pd.Series] = None
    total_equity: Optional[pd.Series] = None

    # Revenue growth (YoY latest)
    revenue_growth: Optional[float] = None

    # Historical price (1-year daily)
    hist_1y: Optional[pd.DataFrame] = None

    # News headlines
    news: list = field(default_factory=list)

    # Deal score components
    deal_score: float = 0.0
    valuation_score: float = 0.0
    solvency_score: float = 0.0
    growth_score: float = 0.0

    # Summary text (set by AI module)
    product_overview: str = ""
    mgmt_sentiment: str = ""
    executive_summary_bullets: list = field(default_factory=list)


def _safe_get(info: dict, key: str, default=None):
    val = info.get(key, default)
    if val is None:
        return default
    return val


def fetch_company_data(ticker_str: str) -> CompanyData:
    """Pull all data for a given ticker and return a CompanyData object."""
    tk = yf.Ticker(ticker_str)
    info = tk.info or {}

    cd = CompanyData(ticker=ticker_str.upper())
    cd.name = _safe_get(info, "longName", _safe_get(info, "shortName", ticker_str.upper()))
    cd.sector = _safe_get(info, "sector", "N/A")
    cd.industry = _safe_get(info, "industry", "N/A")
    cd.current_price = _safe_get(info, "currentPrice",
                                 _safe_get(info, "regularMarketPrice", 0.0))
    cd.market_cap = _safe_get(info, "marketCap", 0)
    cd.pe_ratio = _safe_get(info, "trailingPE")
    cd.forward_pe = _safe_get(info, "forwardPE")
    cd.trailing_pe = _safe_get(info, "trailingPE")
    cd.price_to_book = _safe_get(info, "priceToBook")
    cd.debt_to_equity = _safe_get(info, "debtToEquity")
    cd.enterprise_value = _safe_get(info, "enterpriseValue", 0)
    cd.ev_to_ebitda = _safe_get(info, "enterpriseToEbitda")
    cd.beta = _safe_get(info, "beta")
    cd.dividend_yield = _safe_get(info, "dividendYield")
    cd.fifty_two_week_high = _safe_get(info, "fiftyTwoWeekHigh", 0)
    cd.fifty_two_week_low = _safe_get(info, "fiftyTwoWeekLow", 0)
    cd.avg_volume = _safe_get(info, "averageVolume", 0)

    # Officers
    cd.officers = _safe_get(info, "companyOfficers", [])

    # --- Income Statement (annual, 3 years) ---
    try:
        inc = tk.income_stmt
        if inc is not None and not inc.empty:
            cd.income_stmt = inc
            cd.revenue = inc.loc["Total Revenue"] if "Total Revenue" in inc.index else None
            cd.net_income = inc.loc["Net Income"] if "Net Income" in inc.index else None
            cd.ebitda = inc.loc["EBITDA"] if "EBITDA" in inc.index else None

            if cd.revenue is not None and cd.ebitda is not None:
                cd.ebitda_margin = (cd.ebitda / cd.revenue * 100).round(1)

            if cd.revenue is not None and len(cd.revenue) >= 2:
                vals = cd.revenue.dropna().values
                if len(vals) >= 2 and vals[1] != 0:
                    cd.revenue_growth = float((vals[0] - vals[1]) / abs(vals[1]) * 100)
    except Exception:
        pass

    # --- Balance Sheet ---
    try:
        bs = tk.balance_sheet
        if bs is not None and not bs.empty:
            cd.balance_sheet = bs
            cd.total_debt = bs.loc["Total Debt"] if "Total Debt" in bs.index else None
            cd.total_equity = (
                bs.loc["Stockholders Equity"]
                if "Stockholders Equity" in bs.index
                else bs.loc.get("Total Stockholders Equity")
            )
    except Exception:
        pass

    # --- Historical price (1 year) ---
    try:
        cd.hist_1y = tk.history(period="1y")
    except Exception:
        pass

    # --- News ---
    try:
        raw_news = tk.news or []
        cd.news = [
            {
                "title": n.get("title", ""),
                "publisher": n.get("publisher", ""),
                "link": n.get("link", ""),
            }
            for n in raw_news[:5]
        ]
    except Exception:
        cd.news = []

    # --- Compute Deal Score ---
    cd.deal_score, cd.valuation_score, cd.solvency_score, cd.growth_score = (
        compute_deal_score(cd)
    )

    return cd


def compute_deal_score(cd: CompanyData) -> tuple[float, float, float, float]:
    """
    Deal Score (1-100):
      40% Valuation  — P/E relative to sector (lower = better)
      30% Solvency   — Debt/Equity (lower = better)
      30% Growth     — Revenue growth (higher = better)
    """
    # --- Valuation (40%) ---
    pe = cd.trailing_pe
    if pe is not None and pe > 0:
        # Score: PE < 10 → 100, PE > 50 → 0, linear between
        val_raw = max(0, min(100, (50 - pe) / 40 * 100))
    else:
        val_raw = 50  # neutral if unavailable

    # --- Solvency (30%) ---
    de = cd.debt_to_equity
    if de is not None:
        # D/E as percentage from yfinance (e.g. 150 means 1.5x)
        de_ratio = de / 100.0
        # Score: D/E < 0.3 → 100, D/E > 3.0 → 0
        sol_raw = max(0, min(100, (3.0 - de_ratio) / 2.7 * 100))
    else:
        sol_raw = 50

    # --- Growth (30%) ---
    rg = cd.revenue_growth
    if rg is not None:
        # Score: growth > 30% → 100, growth < -10% → 0
        gro_raw = max(0, min(100, (rg + 10) / 40 * 100))
    else:
        gro_raw = 50

    total = round(val_raw * 0.4 + sol_raw * 0.3 + gro_raw * 0.3, 1)
    return total, round(val_raw, 1), round(sol_raw, 1), round(gro_raw, 1)


def format_number(val, prefix="$", suffix="", decimals=1) -> str:
    """Human-readable large numbers: $1.2B, $340.5M, etc."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}{prefix}{abs_val/1e12:.{decimals}f}T{suffix}"
    if abs_val >= 1e9:
        return f"{sign}{prefix}{abs_val/1e9:.{decimals}f}B{suffix}"
    if abs_val >= 1e6:
        return f"{sign}{prefix}{abs_val/1e6:.{decimals}f}M{suffix}"
    if abs_val >= 1e3:
        return f"{sign}{prefix}{abs_val/1e3:.{decimals}f}K{suffix}"
    return f"{sign}{prefix}{abs_val:.{decimals}f}{suffix}"
