"""
Data Engine — pulls comprehensive financial data from yfinance and
structures everything for the PPTX generator and Streamlit UI.

Covers: financials, cash flow, analyst data, insider activity,
institutional ownership, ESG, earnings, dividends, and news.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompanyData:
    """Comprehensive container for all company data."""

    # ── Identity ──────────────────────────────────────────
    ticker: str = ""
    name: str = ""
    sector: str = ""
    industry: str = ""
    exchange: str = ""
    website: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    long_business_summary: str = ""
    full_time_employees: Optional[int] = None

    # ── Price & Market ────────────────────────────────────
    current_price: float = 0.0
    previous_close: float = 0.0
    price_change: float = 0.0
    price_change_pct: float = 0.0
    market_cap: float = 0.0
    volume: float = 0.0
    avg_volume: float = 0.0
    fifty_two_week_high: float = 0.0
    fifty_two_week_low: float = 0.0
    fifty_day_average: float = 0.0
    two_hundred_day_average: float = 0.0
    beta: Optional[float] = None

    # ── Valuation Multiples ───────────────────────────────
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_sales: Optional[float] = None
    price_to_book: Optional[float] = None
    enterprise_value: Optional[float] = 0.0
    ev_to_ebitda: Optional[float] = None
    ev_to_revenue: Optional[float] = None

    # ── Profitability & Margins ───────────────────────────
    profit_margins: Optional[float] = None
    operating_margins: Optional[float] = None
    gross_margins: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None

    # ── Growth ────────────────────────────────────────────
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None

    # ── Leverage & Liquidity ──────────────────────────────
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    total_cash: Optional[float] = None
    total_debt_info: Optional[float] = None

    # ── Dividends ─────────────────────────────────────────
    dividend_yield: Optional[float] = None
    dividend_rate: Optional[float] = None
    payout_ratio: Optional[float] = None
    ex_dividend_date: Optional[str] = None

    # ── Officers ──────────────────────────────────────────
    officers: list = field(default_factory=list)

    # ── Financial Statements (Annual) ─────────────────────
    income_stmt: Optional[pd.DataFrame] = None
    balance_sheet: Optional[pd.DataFrame] = None
    cashflow: Optional[pd.DataFrame] = None

    # ── Financial Statements (Quarterly) ──────────────────
    quarterly_income_stmt: Optional[pd.DataFrame] = None
    quarterly_balance_sheet: Optional[pd.DataFrame] = None
    quarterly_cashflow: Optional[pd.DataFrame] = None

    # ── Derived Annual Series ─────────────────────────────
    revenue: Optional[pd.Series] = None
    cost_of_revenue: Optional[pd.Series] = None
    gross_profit: Optional[pd.Series] = None
    operating_income: Optional[pd.Series] = None
    ebitda: Optional[pd.Series] = None
    net_income: Optional[pd.Series] = None
    eps_basic: Optional[pd.Series] = None
    ebitda_margin: Optional[pd.Series] = None
    gross_margin_series: Optional[pd.Series] = None
    operating_margin_series: Optional[pd.Series] = None
    net_margin_series: Optional[pd.Series] = None

    # ── Balance Sheet Series ──────────────────────────────
    total_assets: Optional[pd.Series] = None
    total_liabilities: Optional[pd.Series] = None
    total_equity: Optional[pd.Series] = None
    total_debt: Optional[pd.Series] = None
    cash_and_equivalents: Optional[pd.Series] = None

    # ── Cash Flow Series ──────────────────────────────────
    operating_cashflow_series: Optional[pd.Series] = None
    capital_expenditure: Optional[pd.Series] = None
    free_cashflow_series: Optional[pd.Series] = None
    dividends_paid: Optional[pd.Series] = None

    # ── Price History ─────────────────────────────────────
    hist_1y: Optional[pd.DataFrame] = None
    hist_5y: Optional[pd.DataFrame] = None

    # ── Analyst Data ──────────────────────────────────────
    analyst_price_targets: Optional[dict] = None
    recommendations: Optional[pd.DataFrame] = None
    recommendations_summary: Optional[pd.DataFrame] = None

    # ── Insider Data ──────────────────────────────────────
    insider_transactions: Optional[pd.DataFrame] = None
    insider_purchases: Optional[pd.DataFrame] = None
    insider_roster: Optional[pd.DataFrame] = None

    # ── Institutional Ownership ───────────────────────────
    major_holders: Optional[pd.DataFrame] = None
    institutional_holders: Optional[pd.DataFrame] = None
    mutualfund_holders: Optional[pd.DataFrame] = None

    # ── Earnings ──────────────────────────────────────────
    earnings_dates: Optional[pd.DataFrame] = None

    # ── ESG ───────────────────────────────────────────────
    esg_scores: Optional[pd.DataFrame] = None

    # ── Dividends & Splits History ────────────────────────
    dividends_history: Optional[pd.Series] = None
    splits_history: Optional[pd.Series] = None

    # ── News ──────────────────────────────────────────────
    news: list = field(default_factory=list)

    # ── AI-Generated Content ──────────────────────────────
    product_overview: str = ""
    mgmt_sentiment: str = ""
    executive_summary_bullets: list = field(default_factory=list)
    ma_history: str = ""
    industry_analysis: str = ""
    risk_factors: str = ""


# ── Helpers ──────────────────────────────────────────────────

def _safe_get(info: dict, key: str, default=None):
    val = info.get(key, default)
    if val is None:
        return default
    return val


def _safe_series(df: pd.DataFrame, row_name: str) -> Optional[pd.Series]:
    """Safely extract a row from a DataFrame as a Series."""
    if df is None or df.empty:
        return None
    if row_name in df.index:
        return df.loc[row_name]
    return None


def fetch_company_data(ticker_str: str) -> CompanyData:
    """Pull all available data for a given ticker."""
    tk = yf.Ticker(ticker_str)
    info = tk.info or {}

    cd = CompanyData(ticker=ticker_str.upper())

    # ── Identity ─────────────────────────────────────────
    cd.name = _safe_get(info, "longName", _safe_get(info, "shortName", ticker_str.upper()))
    cd.sector = _safe_get(info, "sector", "N/A")
    cd.industry = _safe_get(info, "industry", "N/A")
    cd.exchange = _safe_get(info, "exchange", "")
    cd.website = _safe_get(info, "website", "")
    cd.city = _safe_get(info, "city", "")
    cd.state = _safe_get(info, "state", "")
    cd.country = _safe_get(info, "country", "")
    cd.long_business_summary = _safe_get(info, "longBusinessSummary", "")
    cd.full_time_employees = _safe_get(info, "fullTimeEmployees")

    # ── Price & Market ───────────────────────────────────
    cd.current_price = _safe_get(info, "currentPrice",
                                 _safe_get(info, "regularMarketPrice", 0.0))
    cd.previous_close = _safe_get(info, "previousClose", 0.0)
    if cd.current_price and cd.previous_close:
        cd.price_change = cd.current_price - cd.previous_close
        cd.price_change_pct = (cd.price_change / cd.previous_close) * 100 if cd.previous_close else 0
    cd.market_cap = _safe_get(info, "marketCap", 0)
    cd.volume = _safe_get(info, "volume", 0)
    cd.avg_volume = _safe_get(info, "averageVolume", 0)
    cd.fifty_two_week_high = _safe_get(info, "fiftyTwoWeekHigh", 0)
    cd.fifty_two_week_low = _safe_get(info, "fiftyTwoWeekLow", 0)
    cd.fifty_day_average = _safe_get(info, "fiftyDayAverage", 0.0)
    cd.two_hundred_day_average = _safe_get(info, "twoHundredDayAverage", 0.0)
    cd.beta = _safe_get(info, "beta")

    # ── Valuation Multiples ──────────────────────────────
    cd.trailing_pe = _safe_get(info, "trailingPE")
    cd.forward_pe = _safe_get(info, "forwardPE")
    cd.peg_ratio = _safe_get(info, "pegRatio")
    cd.price_to_sales = _safe_get(info, "priceToSalesTrailing12Months")
    cd.price_to_book = _safe_get(info, "priceToBook")
    cd.enterprise_value = _safe_get(info, "enterpriseValue", 0)
    cd.ev_to_ebitda = _safe_get(info, "enterpriseToEbitda")
    cd.ev_to_revenue = _safe_get(info, "enterpriseToRevenue")

    # ── Profitability & Margins ──────────────────────────
    cd.profit_margins = _safe_get(info, "profitMargins")
    cd.operating_margins = _safe_get(info, "operatingMargins")
    cd.gross_margins = _safe_get(info, "grossMargins")
    cd.return_on_assets = _safe_get(info, "returnOnAssets")
    cd.return_on_equity = _safe_get(info, "returnOnEquity")

    # ── Growth ───────────────────────────────────────────
    cd.earnings_growth = _safe_get(info, "earningsGrowth")

    # ── Leverage & Liquidity ─────────────────────────────
    cd.debt_to_equity = _safe_get(info, "debtToEquity")
    cd.current_ratio = _safe_get(info, "currentRatio")
    cd.total_cash = _safe_get(info, "totalCash")
    cd.total_debt_info = _safe_get(info, "totalDebt")

    # ── Dividends ────────────────────────────────────────
    cd.dividend_yield = _safe_get(info, "dividendYield")
    cd.dividend_rate = _safe_get(info, "dividendRate")
    cd.payout_ratio = _safe_get(info, "payoutRatio")
    cd.ex_dividend_date = _safe_get(info, "exDividendDate")

    # ── Officers ─────────────────────────────────────────
    cd.officers = _safe_get(info, "companyOfficers", [])

    # ── Income Statement (Annual) ────────────────────────
    try:
        inc = tk.income_stmt
        if inc is not None and not inc.empty:
            cd.income_stmt = inc
            cd.revenue = _safe_series(inc, "Total Revenue")
            cd.cost_of_revenue = _safe_series(inc, "Cost Of Revenue")
            cd.gross_profit = _safe_series(inc, "Gross Profit")
            cd.operating_income = _safe_series(inc, "Operating Income")
            cd.ebitda = _safe_series(inc, "EBITDA")
            cd.net_income = _safe_series(inc, "Net Income")
            cd.eps_basic = _safe_series(inc, "Basic EPS")

            # Margin series
            if cd.revenue is not None:
                if cd.ebitda is not None:
                    cd.ebitda_margin = (cd.ebitda / cd.revenue * 100).round(1)
                if cd.gross_profit is not None:
                    cd.gross_margin_series = (cd.gross_profit / cd.revenue * 100).round(1)
                if cd.operating_income is not None:
                    cd.operating_margin_series = (cd.operating_income / cd.revenue * 100).round(1)
                if cd.net_income is not None:
                    cd.net_margin_series = (cd.net_income / cd.revenue * 100).round(1)

            # Revenue growth (YoY)
            if cd.revenue is not None and len(cd.revenue) >= 2:
                vals = cd.revenue.dropna().values
                if len(vals) >= 2 and vals[1] != 0:
                    cd.revenue_growth = float((vals[0] - vals[1]) / abs(vals[1]) * 100)
    except Exception:
        pass

    # ── Balance Sheet (Annual) ───────────────────────────
    try:
        bs = tk.balance_sheet
        if bs is not None and not bs.empty:
            cd.balance_sheet = bs
            cd.total_assets = _safe_series(bs, "Total Assets")
            cd.total_liabilities = (
                _safe_series(bs, "Total Liabilities Net Minority Interest")
                or _safe_series(bs, "Total Liabilities")
            )
            cd.total_equity = (
                _safe_series(bs, "Stockholders Equity")
                or _safe_series(bs, "Total Stockholders Equity")
            )
            cd.total_debt = _safe_series(bs, "Total Debt")
            cd.cash_and_equivalents = (
                _safe_series(bs, "Cash And Cash Equivalents")
                or _safe_series(bs, "Cash Cash Equivalents And Short Term Investments")
            )
    except Exception:
        pass

    # ── Cash Flow (Annual) ───────────────────────────────
    try:
        cf = tk.cashflow
        if cf is not None and not cf.empty:
            cd.cashflow = cf
            cd.operating_cashflow_series = _safe_series(cf, "Operating Cash Flow")
            cd.capital_expenditure = _safe_series(cf, "Capital Expenditure")
            cd.dividends_paid = _safe_series(cf, "Common Stock Dividend Paid")
            # Free Cash Flow = Operating CF + CapEx (CapEx is negative)
            if cd.operating_cashflow_series is not None and cd.capital_expenditure is not None:
                cd.free_cashflow_series = cd.operating_cashflow_series + cd.capital_expenditure
    except Exception:
        pass

    # ── Quarterly Statements ─────────────────────────────
    try:
        cd.quarterly_income_stmt = tk.quarterly_income_stmt
    except Exception:
        pass
    try:
        cd.quarterly_balance_sheet = tk.quarterly_balance_sheet
    except Exception:
        pass
    try:
        cd.quarterly_cashflow = tk.quarterly_cashflow
    except Exception:
        pass

    # ── Price History ────────────────────────────────────
    try:
        cd.hist_1y = tk.history(period="1y")
    except Exception:
        pass
    try:
        cd.hist_5y = tk.history(period="5y")
    except Exception:
        pass

    # ── Analyst Data ─────────────────────────────────────
    try:
        targets = tk.analyst_price_targets
        if targets is not None and not targets.empty:
            cd.analyst_price_targets = {
                "current": _safe_get(dict(targets), "current"),
                "low": _safe_get(dict(targets), "low"),
                "high": _safe_get(dict(targets), "high"),
                "mean": _safe_get(dict(targets), "mean"),
                "median": _safe_get(dict(targets), "median"),
            }
    except Exception:
        pass

    try:
        cd.recommendations = tk.get_recommendations()
    except Exception:
        pass

    try:
        cd.recommendations_summary = tk.recommendations_summary
    except Exception:
        pass

    # ── Insider Data ─────────────────────────────────────
    try:
        cd.insider_transactions = tk.insider_transactions
    except Exception:
        pass
    try:
        cd.insider_purchases = tk.insider_purchases
    except Exception:
        pass
    try:
        cd.insider_roster = tk.insider_roster_holders
    except Exception:
        pass

    # ── Institutional Ownership ──────────────────────────
    try:
        cd.major_holders = tk.major_holders
    except Exception:
        pass
    try:
        cd.institutional_holders = tk.institutional_holders
    except Exception:
        pass
    try:
        cd.mutualfund_holders = tk.mutualfund_holders
    except Exception:
        pass

    # ── Earnings ─────────────────────────────────────────
    try:
        cd.earnings_dates = tk.get_earnings_dates(limit=8)
    except Exception:
        pass

    # ── ESG ──────────────────────────────────────────────
    try:
        cd.esg_scores = tk.sustainability
    except Exception:
        pass

    # ── Dividends & Splits ───────────────────────────────
    try:
        divs = tk.dividends
        if divs is not None and not divs.empty:
            cd.dividends_history = divs
    except Exception:
        pass
    try:
        splits = tk.splits
        if splits is not None and not splits.empty:
            cd.splits_history = splits
    except Exception:
        pass

    # ── News (fixed for both old and new yfinance formats) ──
    try:
        raw_news = tk.news or []
        parsed_news = []
        for n in raw_news[:10]:
            title = n.get("title", "")
            publisher = n.get("publisher", "")
            link = n.get("link", n.get("url", ""))
            pub_time = n.get("providerPublishTime", "")

            # yfinance >= 0.2.36 nests under 'content'
            if not title and "content" in n:
                content = n["content"]
                title = content.get("title", "")
                provider = content.get("provider", {})
                if isinstance(provider, dict):
                    publisher = provider.get("displayName", "")
                click_url = content.get("clickThroughUrl", {})
                if isinstance(click_url, dict):
                    link = click_url.get("url", "")
                pub_time = content.get("pubDate", "")

            if title:
                parsed_news.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "published": pub_time,
                })
        cd.news = parsed_news
    except Exception:
        cd.news = []

    return cd


# ── Formatting Helpers ───────────────────────────────────────

def format_number(val, prefix="$", suffix="", decimals=1) -> str:
    """Human-readable large numbers: $1.2B, $340.5M, etc."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    try:
        val = float(val)
    except (TypeError, ValueError):
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


def format_pct(val, decimals=1) -> str:
    """Format a decimal ratio as percentage: 0.35 → '35.0%'."""
    if val is None:
        return "N/A"
    try:
        return f"{float(val) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "N/A"


def format_ratio(val, decimals=2) -> str:
    """Format a ratio: 1.5 → '1.50x'."""
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.{decimals}f}x"
    except (TypeError, ValueError):
        return "N/A"


def format_multiple(val, decimals=1) -> str:
    """Format a multiple: 25.3 → '25.3x'."""
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.{decimals}f}x"
    except (TypeError, ValueError):
        return "N/A"
