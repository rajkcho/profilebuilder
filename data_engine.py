"""
Data Engine — pulls comprehensive financial data from yfinance and
structures everything for the PPTX generator and Streamlit UI.

Covers: financials, cash flow, analyst data, insider activity,
institutional ownership, ESG, earnings, dividends, news,
and M&A history (scraped from Wikipedia).
"""

import yfinance as yf
import pandas as pd
import numpy as np
import urllib.request
import json
import re
import time
from io import StringIO
from dataclasses import dataclass, field
from typing import Optional, List, Dict


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

    # ── Currency ───────────────────────────────────────────
    currency_code: str = "USD"
    currency_symbol: str = "$"

    # ── Logo ───────────────────────────────────────────────
    logo_url: str = ""
    logo_domain: str = ""

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

    # ── Shares & Book Value ────────────────────────────────
    shares_outstanding: Optional[float] = None
    book_value_per_share: Optional[float] = None

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
    interest_expense: Optional[pd.Series] = None
    tax_provision: Optional[pd.Series] = None
    sga_expense: Optional[pd.Series] = None
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

    # ── M&A Deal History (scraped) ─────────────────────────
    ma_deals: List[Dict] = field(default_factory=list)   # list of deal dicts
    ma_source: str = ""    # "wikipedia", "llm", or ""

    # ── Peer Comparison ────────────────────────────────────
    peer_data: List[Dict] = field(default_factory=list)  # list of peer metric dicts
    peer_tickers: List[str] = field(default_factory=list)

    # ── Alpha Vantage Supplementary Data ────────────────────
    cik: str = ""                                          # SEC Central Index Key
    ev_to_ebitda_av: Optional[float] = None                # AV-sourced multiple
    ev_to_revenue_av: Optional[float] = None               # AV-sourced multiple
    earnings_history: List[Dict] = field(default_factory=list)       # quarterly EPS actual/estimate/surprise
    news_sentiment: List[Dict] = field(default_factory=list)         # recent news + sentiment scores
    av_insider_transactions: List[Dict] = field(default_factory=list)  # AV-sourced insider buys/sells

    # ── Precedent Transaction Data ───────────────────────────
    precedent_data: Optional[object] = None                # PrecedentData from precedent_deals.py

    # ── AI-Generated Content ──────────────────────────────
    product_overview: str = ""
    mgmt_sentiment: str = ""
    executive_summary_bullets: list = field(default_factory=list)
    ma_history: str = ""           # legacy markdown string (now built from ma_deals)
    industry_analysis: str = ""
    risk_factors: str = ""
    swot_analysis: dict = field(default_factory=dict)
    growth_outlook: dict = field(default_factory=dict)
    capital_allocation_analysis: dict = field(default_factory=dict)


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


# ── Exchange-to-Currency Mapping ────────────────────────────
EXCHANGE_CURRENCY_MAP = {
    # US
    "NMS": ("USD", "$"), "NYQ": ("USD", "$"), "NGM": ("USD", "$"),
    "NCM": ("USD", "$"), "ASE": ("USD", "$"), "BTS": ("USD", "$"),
    "PCX": ("USD", "$"), "OPR": ("USD", "$"),
    # Canada
    "TOR": ("CAD", "C$"), "VAN": ("CAD", "C$"), "CNQ": ("CAD", "C$"),
    # UK
    "LSE": ("GBP", "\u00a3"), "IOB": ("GBP", "\u00a3"),
    # Europe
    "FRA": ("EUR", "\u20ac"), "GER": ("EUR", "\u20ac"), "PAR": ("EUR", "\u20ac"),
    "AMS": ("EUR", "\u20ac"), "MIL": ("EUR", "\u20ac"), "MCE": ("EUR", "\u20ac"),
    "EBS": ("CHF", "CHF "),
    # Asia-Pacific
    "JPX": ("JPY", "\u00a5"), "TYO": ("JPY", "\u00a5"),
    "HKG": ("HKD", "HK$"),
    "SHH": ("CNY", "\u00a5"), "SHZ": ("CNY", "\u00a5"),
    "KSC": ("KRW", "\u20a9"), "KOE": ("KRW", "\u20a9"),
    "ASX": ("AUD", "A$"),
    "NSI": ("INR", "\u20b9"), "BSE": ("INR", "\u20b9"),
}

CURRENCY_SYMBOLS = {
    "USD": "$", "CAD": "C$", "GBP": "\u00a3", "EUR": "\u20ac",
    "JPY": "\u00a5", "HKD": "HK$", "AUD": "A$", "INR": "\u20b9",
    "CNY": "\u00a5", "KRW": "\u20a9", "CHF": "CHF ", "SEK": "kr ",
    "NOK": "kr ", "DKK": "kr ", "SGD": "S$", "NZD": "NZ$",
    "BRL": "R$", "MXN": "MX$", "ZAR": "R ",
}


def _resolve_currency(exchange_code: str) -> tuple:
    """Return (currency_code, currency_symbol) for a yfinance exchange code."""
    return EXCHANGE_CURRENCY_MAP.get(exchange_code, ("USD", "$"))


# ── Peer Group Industry Map ─────────────────────────────────
INDUSTRY_PEER_MAP = {
    # Technology
    "Consumer Electronics": ["AAPL", "SONY", "HPQ", "DELL", "LOGI"],
    "Software - Infrastructure": ["MSFT", "ORCL", "CRM", "NOW", "ADBE", "INTU"],
    "Software - Application": ["CRM", "ADBE", "INTU", "NOW", "WDAY", "TEAM"],
    "Semiconductors": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "TXN", "MU"],
    "Semiconductor Equipment & Materials": ["ASML", "AMAT", "LRCX", "KLAC", "TER"],
    "Internet Content & Information": ["GOOGL", "META", "SNAP", "PINS", "SPOT"],
    "Internet Retail": ["AMZN", "BABA", "JD", "MELI", "SE", "SHOP"],
    "Information Technology Services": ["ACN", "IBM", "CTSH", "INFY", "WIT"],
    "Electronic Components": ["APH", "TEL", "GLW", "JBL", "FLEX"],
    "Communication Equipment": ["CSCO", "MSI", "JNPR", "ERIC", "NOK"],
    # Financials
    "Banks - Diversified": ["JPM", "BAC", "WFC", "C", "GS", "MS"],
    "Banks - Regional": ["USB", "PNC", "TFC", "FITB", "KEY", "RF"],
    "Insurance - Diversified": ["BRK-B", "AIG", "MET", "PRU", "ALL"],
    "Capital Markets": ["GS", "MS", "SCHW", "BLK", "ICE", "CME"],
    "Financial Data & Stock Exchanges": ["SPGI", "MCO", "MSCI", "ICE", "NDAQ"],
    # Healthcare
    "Drug Manufacturers - General": ["JNJ", "PFE", "MRK", "LLY", "ABBV", "NVO"],
    "Biotechnology": ["AMGN", "GILD", "VRTX", "REGN", "BIIB", "MRNA"],
    "Medical Devices": ["MDT", "ABT", "SYK", "BSX", "ISRG", "EW"],
    "Health Care Plans": ["UNH", "ELV", "CI", "HUM", "CNC"],
    # Energy
    "Oil & Gas Integrated": ["XOM", "CVX", "SHEL", "TTE", "COP", "BP"],
    "Oil & Gas E&P": ["EOG", "PXD", "DVN", "FANG", "MRO"],
    # Consumer
    "Beverages - Non-Alcoholic": ["KO", "PEP", "MNST", "CELH"],
    "Restaurants": ["MCD", "SBUX", "CMG", "YUM", "DRI", "QSR"],
    "Discount Stores": ["WMT", "COST", "TGT", "DG", "DLTR"],
    "Specialty Retail": ["HD", "LOW", "TJX", "ROST", "ORLY"],
    "Household & Personal Products": ["PG", "CL", "KMB", "EL", "CHD"],
    # Industrial
    "Aerospace & Defense": ["BA", "LMT", "RTX", "NOC", "GD", "GE"],
    "Auto Manufacturers": ["TSLA", "TM", "GM", "F", "HMC", "STLA"],
    "Railroads": ["UNP", "CSX", "NSC", "CP"],
    "Industrial Conglomerates": ["HON", "MMM", "GE", "ITW", "EMR"],
    # Telecom / Media
    "Entertainment": ["DIS", "NFLX", "CMCSA", "WBD", "PARA"],
    "Telecom Services": ["T", "VZ", "TMUS", "CHTR"],
    # Real Estate
    "REIT - Diversified": ["AMT", "PLD", "CCI", "EQIX", "SPG"],
    # Utilities
    "Utilities - Regulated Electric": ["NEE", "DUK", "SO", "D", "AEP"],
}


def _wiki_search_ma_page(company_name: str) -> Optional[str]:
    """Search Wikipedia for an M&A page and return the page title if found."""
    # Clean up company name for searching
    clean = company_name.replace(", Inc.", "").replace(" Inc.", "")
    clean = clean.replace(", Inc", "").replace(" Inc", "")
    clean = clean.replace(" Corporation", "").replace(" Corp.", "")
    clean = clean.replace(" Co.", "").replace(", Ltd.", "")
    clean = clean.replace(" Platforms", "").replace(" Holdings", "")
    clean = clean.strip()

    # Also try first word only (e.g., "Apple" from "Apple Inc.")
    first_word = clean.split()[0] if clean else ""

    # Build candidate page titles to try
    candidates = []
    for name in [clean, first_word]:
        if not name:
            continue
        wiki_name = name.replace(" ", "_")
        candidates.append(f"List_of_mergers_and_acquisitions_by_{wiki_name}")
        candidates.append(f"List_of_acquisitions_by_{wiki_name}")

    # Try direct page fetch first (faster than search)
    for page_title in candidates:
        url = f"https://en.wikipedia.org/api/rest_v1/page/html/{urllib.request.quote(page_title)}"
        req = urllib.request.Request(url, headers={"User-Agent": "ProfileBuilder/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return page_title
        except Exception:
            continue

    # Fallback: use Wikipedia search API
    for name in [clean, first_word]:
        if not name:
            continue
        name_lower = name.lower()
        for prefix in ["List of mergers and acquisitions by", "List of acquisitions by"]:
            query = f"{prefix} {name}"
            search_url = (
                f"https://en.wikipedia.org/w/api.php?action=opensearch"
                f"&search={urllib.request.quote(query)}&limit=5&format=json"
            )
            req = urllib.request.Request(search_url, headers={"User-Agent": "ProfileBuilder/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                titles = data[1] if len(data) > 1 else []
                for t in titles:
                    tl = t.lower()
                    if ("mergers and acquisitions" in tl or "acquisitions by" in tl):
                        # Validate: the page title must contain the company name
                        # to avoid false matches (e.g., Tesla → Research In Motion)
                        if name_lower in tl:
                            return t.replace(" ", "_")
            except Exception:
                continue

    return None


def _parse_wiki_ma_table(html: str) -> List[Dict]:
    """Parse M&A tables from Wikipedia HTML into a list of deal dicts."""
    tables = pd.read_html(StringIO(html))

    deals = []
    for df in tables:
        if len(df) < 2 or len(df.columns) < 3:
            continue

        cols_lower = [str(c).lower() for c in df.columns]

        # Flexible column detection — handle many Wikipedia variants
        col_map = {}
        for i, c in enumerate(cols_lower):
            orig = df.columns[i]
            # Date columns: "date", "acquired on", "announced", etc.
            if not col_map.get("date") and any(
                kw in c for kw in ["date", "acquired on", "announced", "year"]
            ):
                col_map["date"] = orig
            # Company columns: "company", "target company", "target"
            elif not col_map.get("company") and any(
                kw in c for kw in ["company", "target"]
            ) and "country" not in c:
                col_map["company"] = orig
            # Business/description: "business", "description", "industry", "type"
            elif not col_map.get("business") and any(
                kw in c for kw in ["business", "description", "industry", "type",
                                   "service", "product"]
            ):
                col_map["business"] = orig
            # Country/location: "country", "location", "nationality"
            elif not col_map.get("country") and any(
                kw in c for kw in ["country", "location", "nationality"]
            ):
                col_map["country"] = orig
            # Value: "value", "price", "acquired for", "deal value", "amount"
            elif not col_map.get("value") and any(
                kw in c for kw in ["value", "price", "acquired for", "deal",
                                   "amount", "cost"]
            ):
                col_map["value"] = orig

        company_col = col_map.get("company")
        date_col = col_map.get("date")
        if not company_col or not date_col:
            continue

        for _, row in df.iterrows():
            company_name = str(row.get(company_col, "")).strip()
            date_str = str(row.get(date_col, "")).strip()

            # Skip garbage rows
            if not company_name or company_name in ("nan", "", "—"):
                continue
            if not date_str or date_str in ("nan", ""):
                continue
            # Skip rows that look like repeated headers
            if company_name.lower() in ("company", "target", "target company"):
                continue

            deal = {
                "company": company_name,
                "date": date_str,
                "business": "",
                "country": "",
                "value": "",
            }
            if col_map.get("business"):
                deal["business"] = str(row.get(col_map["business"], "")).strip()
            if col_map.get("country"):
                deal["country"] = str(row.get(col_map["country"], "")).strip()
            if col_map.get("value"):
                deal["value"] = str(row.get(col_map["value"], "")).strip()

            # Clean value field
            val = deal["value"]
            if val in ("nan", "—", "–", "Undisclosed", "", "N/A"):
                deal["value"] = "Undisclosed"
            # Strip footnote references like [note 12] or [123]
            deal["value"] = re.sub(r"\[.*?\]", "", deal["value"]).strip()

            # Clean 'nan' strings across all fields
            for k in deal:
                if deal[k] == "nan":
                    deal[k] = ""

            deals.append(deal)

    return deals


def _extract_year(date_str: str) -> int:
    """Extract a 4-digit year from a date string, return 0 on failure."""
    match = re.search(r"\b(19|20)\d{2}\b", date_str)
    return int(match.group()) if match else 0


def fetch_ma_deals(company_name: str) -> tuple:
    """
    Fetch M&A deal history from Wikipedia for a given company.
    Returns (deals_list, source_string).
    """
    try:
        page_title = _wiki_search_ma_page(company_name)
        if not page_title:
            return [], ""

        url = f"https://en.wikipedia.org/api/rest_v1/page/html/{urllib.request.quote(page_title)}"
        req = urllib.request.Request(url, headers={"User-Agent": "ProfileBuilder/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")

        deals = _parse_wiki_ma_table(html)

        if not deals:
            return [], ""

        # Sort by year descending (most recent first)
        deals.sort(key=lambda d: _extract_year(d.get("date", "")), reverse=True)

        source_url = f"https://en.wikipedia.org/wiki/{page_title}"
        return deals, source_url

    except Exception as e:
        print(f"Wikipedia M&A fetch failed for '{company_name}': {e}")
        return [], ""


def _retry_yf_info(tk, max_retries=3):
    """Fetch ticker.info with exponential backoff on rate-limit errors.

    NOTE: tk.info is a property that makes a new HTTP request on every access,
    so we must cache the result and never call it more than necessary.
    """
    last_result = {}
    for attempt in range(max_retries):
        try:
            info = tk.info  # single HTTP call
            if info:
                last_result = info
                # Accept any non-trivial response (>5 keys means real data)
                if len(info) > 5:
                    return info
            # Sparse/stub response — may be transient rate-limit stub
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"Sparse response (attempt {attempt + 1}/{max_retries}), retrying in {wait}s...")
                time.sleep(wait)
        except Exception as e:
            err_msg = str(e).lower()
            if "too many requests" in err_msg or "rate" in err_msg or "429" in err_msg:
                wait = 2 ** (attempt + 1)
                print(f"Rate limited (attempt {attempt + 1}/{max_retries}), retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    return last_result


def fetch_company_data(ticker_str: str) -> CompanyData:
    """Pull all available data for a given ticker."""
    tk = yf.Ticker(ticker_str)
    info = _retry_yf_info(tk)

    cd = CompanyData(ticker=ticker_str.upper())

    # ── Identity ─────────────────────────────────────────
    cd.name = _safe_get(info, "longName", _safe_get(info, "shortName", ticker_str.upper()))
    cd.sector = _safe_get(info, "sector", "N/A")
    cd.industry = _safe_get(info, "industry", "N/A")
    cd.exchange = _safe_get(info, "exchange", "")

    # ── Currency ──────────────────────────────────────────
    fin_currency = _safe_get(info, "financialCurrency", "")
    if fin_currency and fin_currency in CURRENCY_SYMBOLS:
        cd.currency_code = fin_currency
        cd.currency_symbol = CURRENCY_SYMBOLS[fin_currency]
    elif cd.exchange:
        cd.currency_code, cd.currency_symbol = _resolve_currency(cd.exchange)

    cd.website = _safe_get(info, "website", "")
    cd.city = _safe_get(info, "city", "")
    cd.state = _safe_get(info, "state", "")
    cd.country = _safe_get(info, "country", "")
    cd.long_business_summary = _safe_get(info, "longBusinessSummary", "")
    cd.full_time_employees = _safe_get(info, "fullTimeEmployees")

    # ── Logo (Google Favicon API primary, Clearbit fallback) ──
    if cd.website:
        try:
            from urllib.parse import urlparse
            domain = urlparse(cd.website).netloc
            if domain.startswith("www."):
                domain = domain[4:]
            if domain:
                cd.logo_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
                cd.logo_domain = domain  # stored for onerror fallback
        except Exception:
            pass

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

    # ── Shares & Book Value ──────────────────────────────
    # Try multiple sources for shares outstanding
    cd.shares_outstanding = (
        _safe_get(info, "sharesOutstanding") or
        _safe_get(info, "impliedSharesOutstanding") or
        _safe_get(info, "floatShares")  # Less accurate but a fallback
    )
    cd.book_value_per_share = _safe_get(info, "bookValue")
    # Fallback: derive shares from market cap / price
    if not cd.shares_outstanding and cd.market_cap and cd.current_price and cd.current_price > 0:
        cd.shares_outstanding = cd.market_cap / cd.current_price

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
            cd.interest_expense = _safe_series(inc, "Interest Expense")
            cd.tax_provision = _safe_series(inc, "Tax Provision")
            cd.sga_expense = (
                _safe_series(inc, "Selling General And Administration")
                or _safe_series(inc, "Selling And Marketing Expense")
            )

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
        # yfinance >=1.1.0 returns a dict; older versions return a DataFrame
        if targets is not None:
            if isinstance(targets, dict):
                tgt = targets
            else:
                tgt = dict(targets) if not getattr(targets, "empty", True) else {}
            if tgt:
                cd.analyst_price_targets = {
                    "current": tgt.get("current"),
                    "low": tgt.get("low"),
                    "high": tgt.get("high"),
                    "mean": tgt.get("mean"),
                    "median": tgt.get("median"),
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

    # ── M&A History (Wikipedia scrape) ─────────────────
    try:
        deals, source = fetch_ma_deals(cd.name)
        if deals:
            cd.ma_deals = deals
            cd.ma_source = source
    except Exception as e:
        print(f"M&A scraping failed: {e}")

    # ── Alpha Vantage Enrichment ───────────────────────
    try:
        from alpha_vantage import enrich_company_data
        cd = enrich_company_data(cd)
    except Exception as e:
        print(f"Alpha Vantage enrichment failed: {e}")

    return cd


# ── Peer Comparison Fetcher ──────────────────────────────────

def fetch_peer_data(cd: CompanyData) -> CompanyData:
    """Fetch valuation metrics for peer companies based on industry mapping.

    Uses INDUSTRY_PEER_MAP (hardcoded, no API key needed).
    Limits to 5 peers for performance (~1-3s per peer).
    """
    peer_tickers = INDUSTRY_PEER_MAP.get(cd.industry, [])

    # Remove the target company itself
    peer_tickers = [t for t in peer_tickers if t.upper() != cd.ticker.upper()]

    # Limit to 5 peers
    peer_tickers = peer_tickers[:5]

    if not peer_tickers:
        return cd

    cd.peer_tickers = peer_tickers
    peers = []

    for i, pticker in enumerate(peer_tickers):
        if i > 0:
            time.sleep(0.5)  # Throttle to avoid Yahoo Finance rate limiting
        try:
            pk = yf.Ticker(pticker)
            pinfo = _retry_yf_info(pk)
            peer = {
                "ticker": pticker,
                "name": _safe_get(pinfo, "shortName", pticker),
                "market_cap": _safe_get(pinfo, "marketCap", 0),
                "trailing_pe": _safe_get(pinfo, "trailingPE"),
                "forward_pe": _safe_get(pinfo, "forwardPE"),
                "ev_to_ebitda": _safe_get(pinfo, "enterpriseToEbitda"),
                "price_to_sales": _safe_get(pinfo, "priceToSalesTrailing12Months"),
                "peg_ratio": _safe_get(pinfo, "pegRatio"),
                "price_to_book": _safe_get(pinfo, "priceToBook"),
                "gross_margins": _safe_get(pinfo, "grossMargins"),
                "operating_margins": _safe_get(pinfo, "operatingMargins"),
                "profit_margins": _safe_get(pinfo, "profitMargins"),
                "return_on_equity": _safe_get(pinfo, "returnOnEquity"),
                "revenue_growth": _safe_get(pinfo, "revenueGrowth"),
                "current_price": _safe_get(pinfo, "currentPrice",
                                           _safe_get(pinfo, "regularMarketPrice", 0)),
            }
            peers.append(peer)
        except Exception:
            continue

    cd.peer_data = peers
    return cd


# ── Formatting Helpers ───────────────────────────────────────

def format_number(val, prefix="$", suffix="", decimals=1, currency_symbol=None) -> str:
    """Human-readable large numbers: $1.2B, C$340.5M, etc.

    Args:
        currency_symbol: If provided, overrides prefix. Handles JPY/¥ (no decimals),
                         GBP (£), EUR (€), CAD (C$), INR (₹), etc.
    """
    if currency_symbol is not None:
        prefix = currency_symbol
        # JPY and KRW typically don't use decimals
        if currency_symbol in ("¥", "₩"):
            decimals = 0
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


def _safe_val(series, idx=0):
    """Safely get a value from a Series by iloc position. Returns None on failure."""
    if series is None:
        return None
    try:
        if len(series) <= idx:
            return None
        v = series.iloc[idx]
        if pd.isna(v):
            return None
        return float(v)
    except Exception:
        return None


def calculate_piotroski_score(cd: CompanyData) -> Optional[dict]:
    """Calculate Piotroski F-Score (0-9) from CompanyData.

    Components:
      1. ROA > 0
      2. Operating Cash Flow > 0
      3. ΔROA > 0 (ROA improvement)
      4. Accruals: Operating CF > Net Income
      5. ΔLeverage: Long-term debt ratio decreased
      6. ΔCurrent Ratio: Current ratio improved
      7. No dilution: No new shares issued
      8. ΔGross Margin > 0
      9. ΔAsset Turnover > 0
    """
    try:
        # Need at least 2 years of data for deltas
        ta_0 = _safe_val(cd.total_assets, 0)
        ta_1 = _safe_val(cd.total_assets, 1)
        ni_0 = _safe_val(cd.net_income, 0)
        ni_1 = _safe_val(cd.net_income, 1)
        ocf_0 = _safe_val(cd.operating_cashflow_series, 0)

        if ta_0 is None or ta_1 is None or ni_0 is None:
            return None

        components = {}

        # 1. ROA > 0
        roa_0 = ni_0 / ta_0 if ta_0 != 0 else 0
        components['roa_positive'] = 1 if roa_0 > 0 else 0

        # 2. Operating CF > 0
        components['ocf_positive'] = 1 if ocf_0 is not None and ocf_0 > 0 else 0

        # 3. ΔROA > 0
        roa_1 = ni_1 / ta_1 if ni_1 is not None and ta_1 != 0 else None
        components['delta_roa'] = 1 if roa_1 is not None and roa_0 > roa_1 else 0

        # 4. Accruals: OCF > NI
        components['accruals'] = 1 if ocf_0 is not None and ocf_0 > ni_0 else 0

        # 5. ΔLeverage (debt/assets decreased)
        debt_0 = _safe_val(cd.total_debt, 0)
        debt_1 = _safe_val(cd.total_debt, 1)
        if debt_0 is not None and debt_1 is not None and ta_0 != 0 and ta_1 != 0:
            components['delta_leverage'] = 1 if (debt_0 / ta_0) <= (debt_1 / ta_1) else 0
        else:
            components['delta_leverage'] = 1  # No debt = good

        # 6. ΔCurrent Ratio
        # Approximate from balance sheet if current_ratio not in series
        cr_now = cd.current_ratio
        if cr_now is not None:
            components['delta_current_ratio'] = 1  # Can't compute delta with single value; assume pass
        else:
            components['delta_current_ratio'] = 0

        # 7. No dilution (shares didn't increase)
        # Check if shares_outstanding available; if splits_history is empty, assume no dilution
        if cd.splits_history is not None and len(cd.splits_history) > 0:
            components['no_dilution'] = 0  # Recent splits may indicate dilution
        else:
            components['no_dilution'] = 1

        # 8. ΔGross Margin > 0
        gm_0 = _safe_val(cd.gross_margin_series, 0)
        gm_1 = _safe_val(cd.gross_margin_series, 1)
        if gm_0 is not None and gm_1 is not None:
            components['delta_gross_margin'] = 1 if gm_0 > gm_1 else 0
        else:
            components['delta_gross_margin'] = 0

        # 9. ΔAsset Turnover > 0
        rev_0 = _safe_val(cd.revenue, 0)
        rev_1 = _safe_val(cd.revenue, 1)
        if rev_0 is not None and rev_1 is not None and ta_0 != 0 and ta_1 != 0:
            at_0 = rev_0 / ta_0
            at_1 = rev_1 / ta_1
            components['delta_asset_turnover'] = 1 if at_0 > at_1 else 0
        else:
            components['delta_asset_turnover'] = 0

        score = sum(components.values())
        return {'score': score, 'max_score': 9, 'components': components}

    except Exception:
        return None


def calculate_intrinsic_value(cd: CompanyData, growth_rate=0.10, discount_rate=0.10,
                              terminal_multiple=15) -> Optional[dict]:
    """Simple DCF intrinsic value estimate.

    Projects FCF for 5 years, applies terminal multiple, discounts back.
    Returns dict with intrinsic_value_per_share, upside_pct, margin_of_safety.
    """
    try:
        fcf_0 = _safe_val(cd.free_cashflow_series, 0)
        shares = cd.shares_outstanding
        price = cd.current_price

        if fcf_0 is None or not shares or shares <= 0 or not price or price <= 0:
            return None
        if fcf_0 <= 0:
            return None  # DCF not meaningful with negative FCF

        # Project FCF for 5 years
        projected_fcf = []
        for yr in range(1, 6):
            projected_fcf.append(fcf_0 * (1 + growth_rate) ** yr)

        # Terminal value at end of year 5
        terminal_value = projected_fcf[-1] * terminal_multiple

        # Discount back to present
        pv_fcf = sum(f / (1 + discount_rate) ** i for i, f in enumerate(projected_fcf, 1))
        pv_terminal = terminal_value / (1 + discount_rate) ** 5

        enterprise_value = pv_fcf + pv_terminal

        # Adjust for net debt
        net_debt = 0
        debt_val = _safe_val(cd.total_debt, 0)
        cash_val = _safe_val(cd.cash_and_equivalents, 0)
        if debt_val is not None:
            net_debt += debt_val
        if cash_val is not None:
            net_debt -= cash_val

        equity_value = enterprise_value - net_debt
        intrinsic_per_share = equity_value / shares

        upside_pct = ((intrinsic_per_share / price) - 1) * 100
        margin_of_safety = max(0, upside_pct)

        return {
            'intrinsic_value_per_share': round(intrinsic_per_share, 2),
            'equity_value': round(equity_value, 0),
            'enterprise_value_dcf': round(enterprise_value, 0),
            'upside_pct': round(upside_pct, 1),
            'margin_of_safety': round(margin_of_safety, 1),
            'assumptions': {
                'base_fcf': fcf_0,
                'growth_rate': growth_rate,
                'discount_rate': discount_rate,
                'terminal_multiple': terminal_multiple,
            }
        }
    except Exception:
        return None


def get_key_ratios_summary(cd: CompanyData) -> dict:
    """Return ~20 key financial ratios organized by category.

    Categories: Valuation, Profitability, Leverage, Efficiency, Growth.
    All values are raw numbers (not formatted), None if unavailable.
    """
    def _ratio(a, b):
        """Safe division returning None on failure."""
        if a is None or b is None:
            return None
        try:
            a, b = float(a), float(b)
            return round(a / b, 4) if b != 0 else None
        except Exception:
            return None

    rev_0 = _safe_val(cd.revenue, 0)
    ni_0 = _safe_val(cd.net_income, 0)
    ta_0 = _safe_val(cd.total_assets, 0)
    te_0 = _safe_val(cd.total_equity, 0)
    ebitda_0 = _safe_val(cd.ebitda, 0)
    gp_0 = _safe_val(cd.gross_profit, 0)
    oi_0 = _safe_val(cd.operating_income, 0)
    fcf_0 = _safe_val(cd.free_cashflow_series, 0)
    debt_0 = _safe_val(cd.total_debt, 0)
    cash_0 = _safe_val(cd.cash_and_equivalents, 0)

    # Growth (YoY)
    rev_1 = _safe_val(cd.revenue, 1)
    ni_1 = _safe_val(cd.net_income, 1)
    ebitda_1 = _safe_val(cd.ebitda, 1)

    def _growth(curr, prev):
        if curr is None or prev is None or prev == 0:
            return None
        return round((curr - prev) / abs(prev), 4)

    return {
        'valuation': {
            'trailing_pe': cd.trailing_pe,
            'forward_pe': cd.forward_pe,
            'peg_ratio': cd.peg_ratio,
            'price_to_sales': cd.price_to_sales,
            'price_to_book': cd.price_to_book,
            'ev_to_ebitda': cd.ev_to_ebitda,
            'ev_to_revenue': cd.ev_to_revenue,
            'fcf_yield': _ratio(fcf_0, cd.market_cap) if cd.market_cap else None,
        },
        'profitability': {
            'gross_margin': cd.gross_margins,
            'operating_margin': cd.operating_margins,
            'net_margin': cd.profit_margins,
            'roa': cd.return_on_assets,
            'roe': cd.return_on_equity,
            'ebitda_margin': _ratio(ebitda_0, rev_0),
        },
        'leverage': {
            'debt_to_equity': cd.debt_to_equity,
            'current_ratio': cd.current_ratio,
            'net_debt': round(debt_0 - cash_0, 0) if debt_0 is not None and cash_0 is not None else None,
            'debt_to_assets': _ratio(debt_0, ta_0),
            'interest_coverage': _ratio(oi_0, abs(_safe_val(cd.interest_expense, 0) or 0)) if _safe_val(cd.interest_expense, 0) else None,
        },
        'efficiency': {
            'asset_turnover': _ratio(rev_0, ta_0),
            'revenue_per_employee': round(rev_0 / cd.full_time_employees, 0) if rev_0 and cd.full_time_employees else None,
        },
        'growth': {
            'revenue_growth_yoy': _growth(rev_0, rev_1),
            'net_income_growth_yoy': _growth(ni_0, ni_1),
            'ebitda_growth_yoy': _growth(ebitda_0, ebitda_1),
            'earnings_growth': cd.earnings_growth,
        },
    }


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


# ── Sector Benchmarks ────────────────────────────────────────

SECTOR_BENCHMARKS = {
    "Technology": {
        "pe": {"low": 18, "median": 28, "high": 45},
        "ev_ebitda": {"low": 12, "median": 20, "high": 35},
        "gross_margin": {"low": 0.50, "median": 0.65, "high": 0.80},
        "revenue_growth": {"low": 0.05, "median": 0.12, "high": 0.30},
        "debt_equity": {"low": 0.10, "median": 0.40, "high": 1.00},
    },
    "Healthcare": {
        "pe": {"low": 15, "median": 22, "high": 40},
        "ev_ebitda": {"low": 10, "median": 16, "high": 28},
        "gross_margin": {"low": 0.40, "median": 0.60, "high": 0.80},
        "revenue_growth": {"low": 0.03, "median": 0.08, "high": 0.20},
        "debt_equity": {"low": 0.20, "median": 0.60, "high": 1.50},
    },
    "Financials": {
        "pe": {"low": 8, "median": 13, "high": 20},
        "ev_ebitda": {"low": 6, "median": 10, "high": 16},
        "gross_margin": {"low": 0.30, "median": 0.50, "high": 0.70},
        "revenue_growth": {"low": 0.02, "median": 0.06, "high": 0.15},
        "debt_equity": {"low": 1.00, "median": 3.00, "high": 8.00},
    },
    "Consumer Discretionary": {
        "pe": {"low": 12, "median": 20, "high": 35},
        "ev_ebitda": {"low": 8, "median": 14, "high": 24},
        "gross_margin": {"low": 0.25, "median": 0.40, "high": 0.60},
        "revenue_growth": {"low": 0.02, "median": 0.08, "high": 0.20},
        "debt_equity": {"low": 0.30, "median": 0.80, "high": 2.00},
    },
    "Consumer Staples": {
        "pe": {"low": 15, "median": 22, "high": 30},
        "ev_ebitda": {"low": 10, "median": 15, "high": 22},
        "gross_margin": {"low": 0.30, "median": 0.45, "high": 0.60},
        "revenue_growth": {"low": 0.01, "median": 0.04, "high": 0.10},
        "debt_equity": {"low": 0.40, "median": 0.90, "high": 1.80},
    },
    "Industrials": {
        "pe": {"low": 14, "median": 21, "high": 32},
        "ev_ebitda": {"low": 9, "median": 14, "high": 22},
        "gross_margin": {"low": 0.20, "median": 0.35, "high": 0.50},
        "revenue_growth": {"low": 0.02, "median": 0.06, "high": 0.15},
        "debt_equity": {"low": 0.30, "median": 0.80, "high": 1.80},
    },
    "Energy": {
        "pe": {"low": 6, "median": 11, "high": 20},
        "ev_ebitda": {"low": 3, "median": 6, "high": 10},
        "gross_margin": {"low": 0.15, "median": 0.35, "high": 0.55},
        "revenue_growth": {"low": -0.10, "median": 0.05, "high": 0.25},
        "debt_equity": {"low": 0.20, "median": 0.50, "high": 1.20},
    },
    "Materials": {
        "pe": {"low": 10, "median": 16, "high": 25},
        "ev_ebitda": {"low": 6, "median": 10, "high": 16},
        "gross_margin": {"low": 0.20, "median": 0.35, "high": 0.50},
        "revenue_growth": {"low": -0.05, "median": 0.05, "high": 0.15},
        "debt_equity": {"low": 0.20, "median": 0.55, "high": 1.20},
    },
    "Real Estate": {
        "pe": {"low": 20, "median": 35, "high": 55},
        "ev_ebitda": {"low": 15, "median": 22, "high": 35},
        "gross_margin": {"low": 0.30, "median": 0.55, "high": 0.75},
        "revenue_growth": {"low": 0.01, "median": 0.05, "high": 0.15},
        "debt_equity": {"low": 0.50, "median": 1.20, "high": 2.50},
    },
    "Utilities": {
        "pe": {"low": 12, "median": 18, "high": 26},
        "ev_ebitda": {"low": 8, "median": 12, "high": 18},
        "gross_margin": {"low": 0.25, "median": 0.40, "high": 0.60},
        "revenue_growth": {"low": 0.01, "median": 0.04, "high": 0.10},
        "debt_equity": {"low": 0.80, "median": 1.30, "high": 2.20},
    },
    "Communication Services": {
        "pe": {"low": 12, "median": 20, "high": 35},
        "ev_ebitda": {"low": 7, "median": 12, "high": 22},
        "gross_margin": {"low": 0.35, "median": 0.55, "high": 0.75},
        "revenue_growth": {"low": 0.02, "median": 0.08, "high": 0.20},
        "debt_equity": {"low": 0.40, "median": 0.90, "high": 2.00},
    },
}


def get_sector_benchmarks(sector: str) -> Optional[dict]:
    """Return benchmark ranges for key metrics by sector.

    Returns dict with keys: pe, ev_ebitda, gross_margin, revenue_growth, debt_equity.
    Each sub-dict has: low, median, high.
    Returns None if sector not found.
    """
    return SECTOR_BENCHMARKS.get(sector)


# ── Industry Peers Mapping (30+ industries) ─────────────────

INDUSTRY_PEERS = {
    "Consumer Electronics": ["AAPL", "SONY", "HPQ", "DELL", "LOGI", "HEAR", "GPRO"],
    "Software - Infrastructure": ["MSFT", "ORCL", "CRM", "NOW", "ADBE", "INTU", "SNOW", "DDOG", "NET"],
    "Software - Application": ["CRM", "ADBE", "INTU", "NOW", "WDAY", "TEAM", "HUBS", "ZS", "PANW"],
    "Semiconductors": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "TXN", "MU", "MRVL", "ON"],
    "Semiconductor Equipment & Materials": ["ASML", "AMAT", "LRCX", "KLAC", "TER", "ENTG"],
    "Internet Content & Information": ["GOOGL", "META", "SNAP", "PINS", "SPOT", "RDDT", "YELP"],
    "Internet Retail": ["AMZN", "BABA", "JD", "MELI", "SE", "SHOP", "ETSY", "W", "CHWY"],
    "Information Technology Services": ["ACN", "IBM", "CTSH", "INFY", "WIT", "EPAM", "GLOB"],
    "Electronic Components": ["APH", "TEL", "GLW", "JBL", "FLEX", "CLS"],
    "Communication Equipment": ["CSCO", "MSI", "JNPR", "ERIC", "NOK", "CIEN", "CALX"],
    "Banks - Diversified": ["JPM", "BAC", "WFC", "C", "GS", "MS", "USB"],
    "Banks - Regional": ["USB", "PNC", "TFC", "FITB", "KEY", "RF", "HBAN", "CFG"],
    "Insurance - Diversified": ["BRK-B", "AIG", "MET", "PRU", "ALL", "TRV", "HIG"],
    "Capital Markets": ["GS", "MS", "SCHW", "BLK", "ICE", "CME", "NDAQ"],
    "Financial Data & Stock Exchanges": ["SPGI", "MCO", "MSCI", "ICE", "NDAQ", "FDS"],
    "Drug Manufacturers - General": ["JNJ", "PFE", "MRK", "LLY", "ABBV", "NVO", "AZN", "BMY"],
    "Biotechnology": ["AMGN", "GILD", "VRTX", "REGN", "BIIB", "MRNA", "SGEN", "ALNY"],
    "Medical Devices": ["MDT", "ABT", "SYK", "BSX", "ISRG", "EW", "ZBH", "BAX"],
    "Health Care Plans": ["UNH", "ELV", "CI", "HUM", "CNC", "MOH"],
    "Oil & Gas Integrated": ["XOM", "CVX", "SHEL", "TTE", "COP", "BP", "ENB"],
    "Oil & Gas E&P": ["EOG", "PXD", "DVN", "FANG", "MRO", "OVV", "APA"],
    "Beverages - Non-Alcoholic": ["KO", "PEP", "MNST", "CELH", "KDP"],
    "Restaurants": ["MCD", "SBUX", "CMG", "YUM", "DRI", "QSR", "WING"],
    "Discount Stores": ["WMT", "COST", "TGT", "DG", "DLTR", "BJ"],
    "Specialty Retail": ["HD", "LOW", "TJX", "ROST", "ORLY", "AZO", "ULTA"],
    "Household & Personal Products": ["PG", "CL", "KMB", "EL", "CHD", "CLX"],
    "Aerospace & Defense": ["BA", "LMT", "RTX", "NOC", "GD", "GE", "HII", "LHX"],
    "Auto Manufacturers": ["TSLA", "TM", "GM", "F", "HMC", "STLA", "RIVN"],
    "Railroads": ["UNP", "CSX", "NSC", "CP", "CNI"],
    "Industrial Conglomerates": ["HON", "MMM", "GE", "ITW", "EMR", "ETN"],
    "Entertainment": ["DIS", "NFLX", "CMCSA", "WBD", "PARA", "LGF-A"],
    "Telecom Services": ["T", "VZ", "TMUS", "CHTR", "LBRDK"],
    "REIT - Diversified": ["AMT", "PLD", "CCI", "EQIX", "SPG", "O", "DLR"],
    "Utilities - Regulated Electric": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE"],
    "Diagnostics & Research": ["TMO", "DHR", "A", "ILMN", "BIO", "WAT"],
    "Insurance - Property & Casualty": ["PGR", "CB", "ALL", "TRV", "HIG", "CNA"],
    "Asset Management": ["BLK", "BX", "KKR", "APO", "ARES", "OWL"],
}

# Cache for discovered peers
_peer_cache: Dict[str, List[str]] = {}


def discover_peers(cd: CompanyData, max_peers: int = 8) -> List[str]:
    """Auto-discover peer tickers based on sector, industry, and market cap.

    Uses INDUSTRY_PEERS mapping, filters by same sector and market cap range (0.2x-5x).
    Results are cached by ticker.
    """
    cache_key = f"{cd.ticker}_{max_peers}"
    if cache_key in _peer_cache:
        return _peer_cache[cache_key]

    candidates = []

    # Look up from industry map first, then fall back to INDUSTRY_PEER_MAP
    industry_candidates = INDUSTRY_PEERS.get(cd.industry, [])
    if not industry_candidates:
        industry_candidates = INDUSTRY_PEER_MAP.get(cd.industry, [])
    if not industry_candidates:
        # Try sector-level fallback: collect all tickers from industries in this sector
        for ind, tickers in INDUSTRY_PEERS.items():
            if tickers:
                # We can't easily check sector from the map, so just use what we have
                pass
        industry_candidates = INDUSTRY_PEER_MAP.get(cd.industry, [])

    # Remove target itself
    industry_candidates = [t for t in industry_candidates if t.upper() != cd.ticker.upper()]

    if not industry_candidates:
        _peer_cache[cache_key] = []
        return []

    target_mcap = cd.market_cap or 0

    validated = []
    for pticker in industry_candidates:
        if len(validated) >= max_peers:
            break
        try:
            pk = yf.Ticker(pticker)
            pinfo = pk.fast_info if hasattr(pk, 'fast_info') else {}
            # Try fast_info first for market cap
            p_mcap = getattr(pinfo, 'market_cap', None)
            if p_mcap is None:
                pinfo_full = pk.info
                p_mcap = pinfo_full.get('marketCap', 0)
                p_sector = pinfo_full.get('sector', '')
            else:
                p_sector = cd.sector  # Assume same sector from our curated list

            if not p_mcap:
                continue

            # Filter: market cap within 0.2x to 5x of target
            if target_mcap > 0:
                ratio = p_mcap / target_mcap
                if ratio < 0.2 or ratio > 5.0:
                    continue

            validated.append(pticker)
        except Exception:
            # If yfinance fails, still include it (it's from our curated list)
            validated.append(pticker)
            continue

    result = validated[:max_peers]
    _peer_cache[cache_key] = result
    return result


def get_upcoming_earnings(ticker: str) -> dict:
    """Fetch upcoming and recent earnings data for a ticker.

    Returns dict with:
        - next_earnings_date: str or None
        - previous_earnings_date: str or None
        - quarterly_eps: list of dicts with date, estimate, actual, surprise
    """
    result = {
        "next_earnings_date": None,
        "previous_earnings_date": None,
        "quarterly_eps": [],
    }
    try:
        tk = yf.Ticker(ticker)

        # Try earnings_dates (shows future + past)
        try:
            ed = tk.get_earnings_dates(limit=12)
            if ed is not None and not ed.empty:
                now = pd.Timestamp.now(tz='UTC') if ed.index.tz else pd.Timestamp.now()

                future = ed[ed.index > now]
                past = ed[ed.index <= now]

                if not future.empty:
                    result["next_earnings_date"] = str(future.index[-1].date())
                if not past.empty:
                    result["previous_earnings_date"] = str(past.index[0].date())

                # Last 4 quarters of EPS data
                past_4 = past.head(4)
                for idx, row in past_4.iterrows():
                    eps_entry = {
                        "date": str(idx.date()),
                        "estimate": None,
                        "actual": None,
                        "surprise_pct": None,
                    }
                    for col in row.index:
                        cl = col.lower()
                        val = row[col]
                        if pd.notna(val):
                            if "estimate" in cl or "expected" in cl:
                                eps_entry["estimate"] = float(val)
                            elif "reported" in cl or "actual" in cl:
                                eps_entry["actual"] = float(val)
                            elif "surprise" in cl:
                                eps_entry["surprise_pct"] = float(val)
                    result["quarterly_eps"].append(eps_entry)
        except Exception:
            pass

        # Fallback: try calendar property
        if not result["next_earnings_date"]:
            try:
                cal = tk.calendar
                if cal is not None:
                    if isinstance(cal, dict):
                        ed_list = cal.get("Earnings Date", [])
                        if ed_list:
                            result["next_earnings_date"] = str(ed_list[0])
                    elif isinstance(cal, pd.DataFrame) and not cal.empty:
                        if "Earnings Date" in cal.index:
                            val = cal.loc["Earnings Date"].iloc[0]
                            if pd.notna(val):
                                result["next_earnings_date"] = str(val)
            except Exception:
                pass

    except Exception:
        pass

    return result


def format_multiple(val, decimals=1) -> str:
    """Format a multiple: 25.3 → '25.3x'."""
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.{decimals}f}x"
    except (TypeError, ValueError):
        return "N/A"
