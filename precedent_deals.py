"""
Precedent Transactions — fetches and parses comparable M&A deals from
EDGAR (DEFM14A / PREM14A filings) and FMP API.

Returns structured PrecedentData for use in football field valuation
and the precedent transactions UI table.
"""

import os
import re
import json
import urllib.request
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple

import pandas as pd
from io import StringIO


@dataclass
class PrecedentData:
    """Container for precedent transaction results."""
    deals: List[Dict] = field(default_factory=list)           # Individual deal rows
    ev_ebitda_range: Optional[Tuple[float, float]] = None     # (low, high) multiples
    ev_revenue_range: Optional[Tuple[float, float]] = None    # (low, high) multiples
    source: str = ""                                          # "EDGAR DEFM14A" or "FMP"
    source_url: str = ""


# ══════════════════════════════════════════════════════════════
# FMP DEAL FETCHER
# ══════════════════════════════════════════════════════════════

def fetch_fmp_deals(sector: str = "", limit: int = 50) -> List[Dict]:
    """Fetch recent M&A deals from Financial Modeling Prep API.
    Returns list of deal dicts, or [] if key missing / API fails.
    """
    key = os.environ.get("FMP_API_KEY", "").strip()
    if not key:
        return []

    url = (
        f"https://financialmodelingprep.com/stable/mergers-acquisitions-search"
        f"?apikey={key}&limit={limit}"
    )

    req = urllib.request.Request(url, headers={"User-Agent": "ProfileBuilder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"FMP deals fetch failed: {e}")
        return []

    if not isinstance(data, list):
        return []

    deals = []
    for d in data:
        try:
            deal = {
                "acquirer": d.get("companyName", d.get("acquirerName", "")),
                "target": d.get("targetedCompanyName", d.get("targetName", "")),
                "date": d.get("transactionDate", d.get("date", "")),
                "deal_value": _safe_float(d.get("dealSize", d.get("transactionAmount"))),
                "target_ticker": d.get("targetedCompanyTicker", d.get("symbol", "")),
            }
            if deal["acquirer"] or deal["target"]:
                deals.append(deal)
        except Exception:
            continue

    return deals


# ══════════════════════════════════════════════════════════════
# EDGAR DEFM14A PARSER
# ══════════════════════════════════════════════════════════════

def _score_table_headers(headers: List[str]) -> int:
    """Score a table's headers by keyword relevance for precedent multiples."""
    keywords = {
        "ev/ebitda": 3, "ev/revenue": 3, "enterprise value": 2,
        "ebitda": 2, "revenue": 1, "acquir": 2, "target": 2,
        "premium": 2, "multiple": 2, "ev / ebitda": 3, "ev / revenue": 3,
        "transaction": 1, "implied": 2, "consideration": 1,
    }
    score = 0
    combined = " ".join(str(h).lower() for h in headers)
    for kw, pts in keywords.items():
        if kw in combined:
            score += pts
    return score


def _extract_multiples_from_df(df: pd.DataFrame) -> Dict:
    """Extract EV/EBITDA and EV/Revenue multiples from a parsed table DataFrame."""
    result = {
        "ev_ebitda_values": [],
        "ev_revenue_values": [],
        "deals": [],
    }

    cols_lower = [str(c).lower() for c in df.columns]

    # Find multiple columns
    ebitda_col = None
    revenue_col = None
    for i, c in enumerate(cols_lower):
        if "ev/ebitda" in c or "ev / ebitda" in c or ("ebitda" in c and "ev" in c):
            ebitda_col = df.columns[i]
        elif "ev/revenue" in c or "ev / revenue" in c or ("revenue" in c and "ev" in c):
            revenue_col = df.columns[i]

    # Try to find acquirer/target name column
    name_col = None
    for i, c in enumerate(cols_lower):
        if any(kw in c for kw in ["target", "company", "acquir", "transaction"]):
            name_col = df.columns[i]
            break
    if name_col is None and len(df.columns) > 0:
        name_col = df.columns[0]

    # Date column
    date_col = None
    for i, c in enumerate(cols_lower):
        if any(kw in c for kw in ["date", "announced", "closed"]):
            date_col = df.columns[i]
            break

    summary_keywords = {"median", "mean", "average", "high", "low", "max", "min",
                        "25th", "75th", "percentile"}

    for _, row in df.iterrows():
        name_val = str(row.get(name_col, "")).strip().lower() if name_col else ""

        # Skip summary stat rows for deal extraction (but capture values)
        is_summary = any(kw in name_val for kw in summary_keywords)

        ev_ebitda = _safe_float(row.get(ebitda_col)) if ebitda_col else None
        ev_revenue = _safe_float(row.get(revenue_col)) if revenue_col else None

        if ev_ebitda is not None and 0 < ev_ebitda < 100:
            result["ev_ebitda_values"].append(ev_ebitda)
        if ev_revenue is not None and 0 < ev_revenue < 50:
            result["ev_revenue_values"].append(ev_revenue)

        if not is_summary and name_val and name_val != "nan":
            deal_row = {
                "name": str(row.get(name_col, "")).strip() if name_col else "",
                "date": str(row.get(date_col, "")).strip() if date_col else "",
                "ev_ebitda": ev_ebitda,
                "ev_revenue": ev_revenue,
            }
            result["deals"].append(deal_row)

    return result


def fetch_edgar_precedent_multiples(
    target_ticker: str, cik: str, sector: str
) -> Optional[Dict]:
    """Search EDGAR for DEFM14A/PREM14A filings and extract precedent multiples.

    Strategy:
    1. Try target company's own filings first (via CIK or ticker)
    2. Fall back to global DEFM14A search filtered by sector
    3. Parse HTML tables to find precedent transaction comparisons
    """
    try:
        from edgar import Company, get_filings
    except ImportError:
        print("edgartools not installed — skipping EDGAR precedent search")
        return None

    filing = None
    filing_url = ""

    # Strategy 1: Target company's own filings
    try:
        lookup = cik if cik else target_ticker
        company = Company(lookup)
        filings = company.get_filings(form=["DEFM14A", "PREM14A"])
        if filings and len(filings) > 0:
            filing = filings[0]
    except Exception as e:
        print(f"EDGAR company lookup failed for {target_ticker}: {e}")

    # Strategy 2: Global recent DEFM14A filings
    if filing is None:
        try:
            recent = get_filings(form="DEFM14A", filing_date="2022-01-01:")
            if recent and len(recent) > 0:
                # Just use the first few available filings
                for f in list(recent)[:5]:
                    try:
                        filing = f
                        break
                    except Exception:
                        continue
        except Exception as e:
            print(f"EDGAR global search failed: {e}")

    if filing is None:
        return None

    # Get the filing HTML
    try:
        html_content = filing.html()
        if not html_content:
            return None
        filing_url = getattr(filing, "filing_url", "") or str(getattr(filing, "url", ""))
    except Exception as e:
        print(f"EDGAR filing HTML fetch failed: {e}")
        return None

    # Parse tables with BeautifulSoup
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "lxml")
    except ImportError:
        print("beautifulsoup4/lxml not installed — skipping table parsing")
        return None

    tables = soup.find_all("table")
    if not tables:
        return None

    # Score each table and pick the best one
    best_score = 0
    best_table_html = None

    for table in tables:
        # Get header text
        headers = []
        first_row = table.find("tr")
        if first_row:
            for cell in first_row.find_all(["th", "td"]):
                headers.append(cell.get_text(strip=True))

        score = _score_table_headers(headers)
        if score > best_score:
            best_score = score
            best_table_html = str(table)

    if best_table_html is None or best_score < 4:
        return None

    # Parse the best table with pandas
    try:
        dfs = pd.read_html(StringIO(best_table_html))
        if not dfs:
            return None
        df = dfs[0]
        if len(df) < 2:
            return None
    except Exception:
        return None

    extracted = _extract_multiples_from_df(df)

    ev_ebitda_vals = extracted["ev_ebitda_values"]
    ev_revenue_vals = extracted["ev_revenue_values"]

    result = {
        "deals": extracted["deals"],
        "source_filing": filing_url,
    }

    if ev_ebitda_vals:
        result["ev_ebitda_low"] = min(ev_ebitda_vals)
        result["ev_ebitda_high"] = max(ev_ebitda_vals)
        result["ev_ebitda_median"] = float(pd.Series(ev_ebitda_vals).median())

    if ev_revenue_vals:
        result["ev_revenue_low"] = min(ev_revenue_vals)
        result["ev_revenue_high"] = max(ev_revenue_vals)
        result["ev_revenue_median"] = float(pd.Series(ev_revenue_vals).median())

    return result


# ══════════════════════════════════════════════════════════════
# FMP MULTIPLES COMPUTATION
# ══════════════════════════════════════════════════════════════

def _compute_fmp_multiples(deals: List[Dict]) -> Tuple[
    Optional[Tuple[float, float]], Optional[Tuple[float, float]]
]:
    """Compute EV/EBITDA and EV/Revenue ranges from FMP deal data.
    Uses yfinance to look up target financials for deals with tickers.
    """
    ev_ebitda_vals = []
    ev_revenue_vals = []

    import yfinance as yf

    for deal in deals[:10]:  # limit lookups
        ticker = deal.get("target_ticker", "")
        deal_value = deal.get("deal_value")
        if not ticker or not deal_value or deal_value <= 0:
            continue

        try:
            tk = yf.Ticker(ticker)
            info = tk.info or {}
            ebitda = info.get("ebitda")
            revenue = info.get("totalRevenue")

            if ebitda and ebitda > 0:
                mult = deal_value / ebitda
                if 0 < mult < 100:
                    ev_ebitda_vals.append(mult)
                    deal["ev_ebitda"] = round(mult, 1)

            if revenue and revenue > 0:
                mult = deal_value / revenue
                if 0 < mult < 50:
                    ev_revenue_vals.append(mult)
                    deal["ev_revenue"] = round(mult, 1)
        except Exception:
            continue

    ebitda_range = None
    revenue_range = None
    if ev_ebitda_vals:
        ebitda_range = (min(ev_ebitda_vals), max(ev_ebitda_vals))
    if ev_revenue_vals:
        revenue_range = (min(ev_revenue_vals), max(ev_revenue_vals))

    return ebitda_range, revenue_range


# ══════════════════════════════════════════════════════════════
# COMBINED ORCHESTRATOR
# ══════════════════════════════════════════════════════════════

def fetch_precedent_transactions(
    target_ticker: str, cik: str, sector: str
) -> PrecedentData:
    """Fetch precedent transaction data.

    Strategy:
    1. Try EDGAR first (richer data with real IB multiples)
    2. Fallback to FMP + yfinance-computed multiples
    """
    result = PrecedentData()

    # Try EDGAR
    try:
        edgar_data = fetch_edgar_precedent_multiples(target_ticker, cik, sector)
        if edgar_data and edgar_data.get("deals"):
            result.deals = edgar_data["deals"]
            result.source = "EDGAR DEFM14A"
            result.source_url = edgar_data.get("source_filing", "")

            if "ev_ebitda_low" in edgar_data and "ev_ebitda_high" in edgar_data:
                result.ev_ebitda_range = (
                    edgar_data["ev_ebitda_low"],
                    edgar_data["ev_ebitda_high"],
                )
            if "ev_revenue_low" in edgar_data and "ev_revenue_high" in edgar_data:
                result.ev_revenue_range = (
                    edgar_data["ev_revenue_low"],
                    edgar_data["ev_revenue_high"],
                )

            if result.deals:
                return result
    except Exception as e:
        print(f"EDGAR precedent fetch failed: {e}")

    # Fallback to FMP
    try:
        fmp_deals = fetch_fmp_deals(sector=sector)
        if fmp_deals:
            ebitda_range, revenue_range = _compute_fmp_multiples(fmp_deals)
            result.deals = [
                {
                    "name": f"{d.get('acquirer', '')} / {d.get('target', '')}",
                    "date": d.get("date", ""),
                    "ev_ebitda": d.get("ev_ebitda"),
                    "ev_revenue": d.get("ev_revenue"),
                    "deal_value": d.get("deal_value"),
                }
                for d in fmp_deals
                if d.get("acquirer") or d.get("target")
            ]
            result.ev_ebitda_range = ebitda_range
            result.ev_revenue_range = revenue_range
            result.source = "FMP"
    except Exception as e:
        print(f"FMP precedent fetch failed: {e}")

    return result


# ── Float helper ─────────────────────────────────────────────────

def _safe_float(val) -> Optional[float]:
    """Convert to float, return None on failure."""
    if val is None or val == "" or val == "None" or val == "N/A":
        return None
    try:
        # Remove common formatting: $, commas, x suffix
        cleaned = str(val).replace(",", "").replace("$", "").replace("x", "").strip()
        return float(cleaned)
    except (TypeError, ValueError):
        return None
