"""
Alpha Vantage API wrapper — supplementary data for company profiles
and merger analysis.  All functions gracefully return None/[] when
the API key is missing or the call fails.
"""

import os
import json
import urllib.request
from typing import Optional, Dict, List


AV_BASE = "https://www.alphavantage.co/query"


# ── Core helper ──────────────────────────────────────────────────

def _av_get(function: str, symbol: str = "", **extra_params) -> Optional[Dict]:
    """Call Alpha Vantage API.  Returns parsed JSON or None."""
    key = os.environ.get("ALPHAVANTAGE_API_KEY", "").strip()
    if not key:
        return None
    params = {"function": function, "apikey": key}
    if symbol:
        params["symbol"] = symbol
    params.update(extra_params)

    qs = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
    url = f"{AV_BASE}?{qs}"

    req = urllib.request.Request(url, headers={"User-Agent": "ProfileBuilder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        # AV returns {"Note": ...} or {"Information": ...} on rate-limit/errors
        if "Note" in data or "Information" in data or "Error Message" in data:
            return None
        return data
    except Exception:
        return None


# ── Endpoint wrappers ────────────────────────────────────────────

def fetch_company_overview(ticker: str) -> Optional[Dict]:
    """OVERVIEW — ~50 fields: CIK, EBITDA, margins, Beta, AnalystTargetPrice, etc."""
    return _av_get("OVERVIEW", symbol=ticker)


def fetch_income_statement(ticker: str) -> Optional[Dict]:
    """INCOME_STATEMENT — annual + quarterly reports."""
    return _av_get("INCOME_STATEMENT", symbol=ticker)


def fetch_balance_sheet(ticker: str) -> Optional[Dict]:
    """BALANCE_SHEET — annual + quarterly reports."""
    return _av_get("BALANCE_SHEET", symbol=ticker)


def fetch_cash_flow(ticker: str) -> Optional[Dict]:
    """CASH_FLOW — annual + quarterly reports."""
    return _av_get("CASH_FLOW", symbol=ticker)


def fetch_earnings(ticker: str) -> List[Dict]:
    """EARNINGS — quarterly EPS actual vs estimate + surprise %.
    Returns list of dicts sorted most-recent-first."""
    data = _av_get("EARNINGS", symbol=ticker)
    if not data:
        return []
    quarterly = data.get("quarterlyEarnings", [])
    result = []
    for q in quarterly[:12]:  # last 12 quarters
        try:
            result.append({
                "date": q.get("fiscalDateEnding", ""),
                "reported_date": q.get("reportedDate", ""),
                "estimated_eps": _safe_float(q.get("estimatedEPS")),
                "actual_eps": _safe_float(q.get("reportedEPS")),
                "surprise": _safe_float(q.get("surprise")),
                "surprise_pct": _safe_float(q.get("surprisePercentage")),
            })
        except Exception:
            continue
    return result


def fetch_news_sentiment(ticker: str) -> List[Dict]:
    """NEWS_SENTIMENT — recent articles with sentiment scores."""
    data = _av_get("NEWS_SENTIMENT", tickers=ticker, limit="15")
    if not data:
        return []
    feed = data.get("feed", [])
    result = []
    for article in feed[:15]:
        try:
            # Find ticker-specific sentiment
            ticker_sentiment = {}
            for ts in article.get("ticker_sentiment", []):
                if ts.get("ticker", "").upper() == ticker.upper():
                    ticker_sentiment = ts
                    break

            result.append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "source": article.get("source", ""),
                "published": article.get("time_published", "")[:10],
                "overall_sentiment": article.get("overall_sentiment_label", "Neutral"),
                "overall_score": _safe_float(article.get("overall_sentiment_score")),
                "relevance": _safe_float(ticker_sentiment.get("relevance_score")),
                "ticker_sentiment": ticker_sentiment.get("ticker_sentiment_label", ""),
                "ticker_score": _safe_float(ticker_sentiment.get("ticker_sentiment_score")),
            })
        except Exception:
            continue
    return result


def fetch_insider_transactions(ticker: str) -> List[Dict]:
    """INSIDER_TRANSACTIONS — insider buy/sell with dates, shares, values."""
    data = _av_get("INSIDER_TRANSACTIONS", symbol=ticker)
    if not data:
        return []
    txns = data.get("data", [])
    result = []
    for t in txns[:30]:  # last 30 transactions
        try:
            shares = _safe_float(t.get("shares"))
            value = _safe_float(t.get("value"))
            result.append({
                "date": t.get("transaction_date", ""),
                "insider": t.get("full_name", ""),
                "title": t.get("executive_title", ""),
                "type": t.get("acquisition_or_disposal", ""),  # A = acquisition, D = disposal
                "shares": shares,
                "value": value,
                "security_type": t.get("security_type", ""),
            })
        except Exception:
            continue
    return result


# ── Float helper ─────────────────────────────────────────────────

def _safe_float(val) -> Optional[float]:
    """Convert to float, return None on failure."""
    if val is None or val == "" or val == "None":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


# ── Data enrichment ──────────────────────────────────────────────

def enrich_company_data(cd) -> object:
    """Supplement CompanyData with Alpha Vantage fields.

    Strategy: yfinance is primary; Alpha Vantage fills gaps + adds new data.
    """
    overview = fetch_company_overview(cd.ticker)
    if overview:
        # CIK (needed for EDGAR)
        if not getattr(cd, "cik", ""):
            cd.cik = overview.get("CIK", "")

        # Fill gaps
        if cd.beta is None:
            cd.beta = _safe_float(overview.get("Beta"))

        if cd.ev_to_ebitda is None:
            cd.ev_to_ebitda = _safe_float(overview.get("EVToEBITDA"))

        if cd.ev_to_revenue is None:
            cd.ev_to_revenue = _safe_float(overview.get("EVToRevenue"))

        # Store AV-sourced multiples separately
        cd.ev_to_ebitda_av = _safe_float(overview.get("EVToEBITDA"))
        cd.ev_to_revenue_av = _safe_float(overview.get("EVToRevenue"))

        # Analyst target if missing
        if cd.analyst_price_targets is None:
            av_target = _safe_float(overview.get("AnalystTargetPrice"))
            if av_target:
                cd.analyst_price_targets = {
                    "current": cd.current_price,
                    "low": av_target * 0.85,
                    "high": av_target * 1.15,
                    "mean": av_target,
                    "median": av_target,
                }

    # Earnings history
    cd.earnings_history = fetch_earnings(cd.ticker)

    # News sentiment
    cd.news_sentiment = fetch_news_sentiment(cd.ticker)

    # Insider transactions (AV-sourced, stored separately)
    cd.av_insider_transactions = fetch_insider_transactions(cd.ticker)

    return cd
