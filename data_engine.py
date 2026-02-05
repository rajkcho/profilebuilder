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

    # ── M&A Deal History (scraped) ─────────────────────────
    ma_deals: List[Dict] = field(default_factory=list)   # list of deal dicts
    ma_source: str = ""    # "wikipedia", "llm", or ""

    # ── Peer Comparison ────────────────────────────────────
    peer_data: List[Dict] = field(default_factory=list)  # list of peer metric dicts
    peer_tickers: List[str] = field(default_factory=list)

    # ── AI-Generated Content ──────────────────────────────
    product_overview: str = ""
    mgmt_sentiment: str = ""
    executive_summary_bullets: list = field(default_factory=list)
    ma_history: str = ""           # legacy markdown string (now built from ma_deals)
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

    # ── Logo (Clearbit) ──────────────────────────────────
    if cd.website:
        try:
            from urllib.parse import urlparse
            domain = urlparse(cd.website).netloc
            if domain.startswith("www."):
                domain = domain[4:]
            if domain:
                cd.logo_url = f"https://logo.clearbit.com/{domain}"
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
    """Human-readable large numbers: $1.2B, C$340.5M, etc."""
    if currency_symbol is not None:
        prefix = currency_symbol
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
