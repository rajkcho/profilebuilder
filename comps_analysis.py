"""
Comparable Company Analysis Engine — finds peer companies and calculates
trading multiples for benchmarking valuation.

Provides:
- Auto-discovery of comparable companies by sector/industry
- Trading multiples calculation (EV/EBITDA, EV/Revenue, P/E, etc.)
- Peer ranking and percentile analysis
- Comps table generation for presentations
"""

import yfinance as yf
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


# ══════════════════════════════════════════════════════════════
# PEER UNIVERSE — curated lists by sector for reliable comps
# ══════════════════════════════════════════════════════════════

SECTOR_PEERS = {
    "Technology": [
        "AAPL", "MSFT", "GOOGL", "META", "NVDA", "ADBE", "CRM", "ORCL", "IBM", "INTC",
        "AMD", "QCOM", "TXN", "AVGO", "CSCO", "NOW", "SNOW", "PLTR", "DDOG", "NET",
        "ZS", "CRWD", "PANW", "FTNT", "OKTA", "MDB", "TEAM", "SHOP", "SQ", "PYPL"
    ],
    "Financial Services": [
        "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "V",
        "MA", "COF", "USB", "PNC", "TFC", "BK", "STT", "ICE", "CME", "SPGI"
    ],
    "Healthcare": [
        "JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "TMO", "ABT", "DHR", "BMY",
        "AMGN", "GILD", "CVS", "CI", "HUM", "ISRG", "MDT", "SYK", "BDX", "EW"
    ],
    "Consumer Cyclical": [
        "AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX", "LOW", "TJX", "TGT", "COST",
        "BKNG", "MAR", "HLT", "CMG", "DPZ", "YUM", "ROST", "LULU", "BBY", "ETSY"
    ],
    "Consumer Defensive": [
        "PG", "KO", "PEP", "WMT", "COST", "PM", "MO", "MDLZ", "CL", "KHC",
        "GIS", "K", "HSY", "SJM", "CPB", "CAG", "KR", "SYY", "ADM", "BG"
    ],
    "Industrials": [
        "HON", "UPS", "UNP", "CAT", "DE", "RTX", "BA", "LMT", "GE", "MMM",
        "ETN", "EMR", "ITW", "ROK", "PH", "CMI", "PCAR", "FAST", "GD", "NOC"
    ],
    "Energy": [
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "VLO", "PSX", "OXY", "DVN",
        "HAL", "BKR", "FANG", "HES", "PXD", "WMB", "KMI", "OKE", "TRGP", "ET"
    ],
    "Communication Services": [
        "GOOGL", "META", "NFLX", "DIS", "CMCSA", "VZ", "T", "TMUS", "CHTR", "EA",
        "TTWO", "ATVI", "RBLX", "SPOT", "WBD", "PARA", "FOX", "LYV", "OMC", "IPG"
    ],
    "Real Estate": [
        "PLD", "AMT", "EQIX", "CCI", "PSA", "SPG", "O", "WELL", "DLR", "AVB",
        "EQR", "VICI", "SBAC", "WY", "ARE", "VTR", "BXP", "HST", "KIM", "REG"
    ],
    "Utilities": [
        "NEE", "DUK", "SO", "D", "AEP", "SRE", "XEL", "PCG", "EXC", "ED",
        "WEC", "ES", "EIX", "DTE", "FE", "PPL", "AEE", "CMS", "AWK", "ETR"
    ],
    "Basic Materials": [
        "LIN", "APD", "SHW", "ECL", "NEM", "FCX", "DOW", "NUE", "VMC", "MLM",
        "PPG", "ALB", "DD", "EMN", "IFF", "CE", "CTVA", "CF", "MOS", "LYB"
    ]
}

# Software/SaaS specific peers (for VMS screening)
SOFTWARE_SAAS_PEERS = [
    "CRM", "NOW", "ADBE", "ORCL", "SAP", "INTU", "TEAM", "DDOG", "SNOW", "MDB",
    "NET", "ZS", "CRWD", "OKTA", "HUBS", "VEEV", "CDNS", "SNPS", "ANSS", "PTC",
    "SSNC", "CSGP", "TYL", "GWRE", "PCTY", "PAYC", "MANH", "COUP", "BILL", "DOCN",
    "ESTC", "CFLT", "DT", "MNDY", "PATH", "ZI", "APP", "BRZE", "GTLB", "IOT"
]


@dataclass
class CompanyComps:
    """Trading multiples for a single company."""
    ticker: str = ""
    name: str = ""
    sector: str = ""
    industry: str = ""
    market_cap: float = 0.0
    enterprise_value: float = 0.0
    
    # Revenue & Profitability
    revenue_ltm: float = 0.0
    ebitda_ltm: float = 0.0
    net_income_ltm: float = 0.0
    gross_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None
    net_margin: Optional[float] = None
    
    # Growth
    revenue_growth: Optional[float] = None
    
    # Valuation Multiples
    ev_revenue: Optional[float] = None
    ev_ebitda: Optional[float] = None
    pe_ratio: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_sales: Optional[float] = None
    price_to_book: Optional[float] = None
    
    # Other metrics
    roe: Optional[float] = None
    roic: Optional[float] = None
    debt_to_ebitda: Optional[float] = None
    
    # Rule of 40 (SaaS metric)
    rule_of_40: Optional[float] = None
    
    # Fetch status
    valid: bool = True
    error: str = ""


@dataclass
class CompsAnalysis:
    """Complete comparable company analysis results."""
    target_ticker: str = ""
    target_name: str = ""
    target_sector: str = ""
    target_industry: str = ""
    
    # Target company metrics (for comparison)
    target_comps: Optional[CompanyComps] = None
    
    # Peer companies
    peers: List[CompanyComps] = field(default_factory=list)
    
    # Summary statistics
    median_ev_revenue: Optional[float] = None
    median_ev_ebitda: Optional[float] = None
    median_pe: Optional[float] = None
    mean_ev_revenue: Optional[float] = None
    mean_ev_ebitda: Optional[float] = None
    mean_pe: Optional[float] = None
    
    # Implied valuations
    implied_ev_from_revenue: Optional[float] = None
    implied_ev_from_ebitda: Optional[float] = None
    implied_price_from_pe: Optional[float] = None
    
    # Percentile rankings (where target sits vs peers)
    percentile_ev_revenue: Optional[float] = None
    percentile_ev_ebitda: Optional[float] = None
    percentile_pe: Optional[float] = None
    percentile_growth: Optional[float] = None


def fetch_company_multiples(ticker: str) -> CompanyComps:
    """Fetch trading multiples for a single company."""
    comps = CompanyComps(ticker=ticker)
    
    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        
        if not info or info.get("regularMarketPrice") is None:
            comps.valid = False
            comps.error = "No data available"
            return comps
        
        # Basic info
        comps.name = info.get("shortName") or info.get("longName") or ticker
        comps.sector = info.get("sector", "")
        comps.industry = info.get("industry", "")
        comps.market_cap = info.get("marketCap") or 0
        comps.enterprise_value = info.get("enterpriseValue") or 0
        
        # Valuation multiples (directly from yfinance)
        comps.ev_revenue = info.get("enterpriseToRevenue")
        comps.ev_ebitda = info.get("enterpriseToEbitda")
        comps.pe_ratio = info.get("trailingPE")
        comps.peg_ratio = info.get("pegRatio")
        comps.price_to_sales = info.get("priceToSalesTrailing12Months")
        comps.price_to_book = info.get("priceToBook")
        
        # Profitability
        comps.gross_margin = info.get("grossMargins")
        comps.ebitda_margin = info.get("ebitdaMargins")
        comps.net_margin = info.get("profitMargins")
        comps.roe = info.get("returnOnEquity")
        
        # Revenue & EBITDA
        comps.revenue_ltm = info.get("totalRevenue") or 0
        comps.ebitda_ltm = info.get("ebitda") or 0
        comps.net_income_ltm = info.get("netIncomeToCommon") or 0
        
        # Growth
        comps.revenue_growth = info.get("revenueGrowth")
        
        # Rule of 40 (revenue growth + EBITDA margin)
        if comps.revenue_growth is not None and comps.ebitda_margin is not None:
            comps.rule_of_40 = (comps.revenue_growth * 100) + (comps.ebitda_margin * 100)
        
        # Leverage
        total_debt = info.get("totalDebt") or 0
        if comps.ebitda_ltm and comps.ebitda_ltm > 0:
            comps.debt_to_ebitda = total_debt / comps.ebitda_ltm
        
        comps.valid = True
        
    except Exception as e:
        comps.valid = False
        comps.error = str(e)
    
    return comps


def find_peer_companies(
    ticker: str,
    sector: str = "",
    industry: str = "",
    market_cap: float = 0,
    max_peers: int = 10,
    include_saas: bool = False
) -> List[str]:
    """
    Find comparable companies based on sector, industry, and market cap.
    Returns list of ticker symbols.
    """
    peers = []
    
    # Get sector-based peers
    sector_key = None
    for key in SECTOR_PEERS:
        if key.lower() in sector.lower() or sector.lower() in key.lower():
            sector_key = key
            break
    
    if sector_key:
        peers.extend(SECTOR_PEERS[sector_key])
    
    # Add SaaS peers for software companies
    if include_saas or "software" in industry.lower() or "saas" in industry.lower():
        peers.extend(SOFTWARE_SAAS_PEERS)
    
    # Remove the target company itself
    peers = [p for p in peers if p.upper() != ticker.upper()]
    
    # Remove duplicates
    peers = list(dict.fromkeys(peers))
    
    # Limit to max_peers (will filter by market cap later)
    return peers[:max_peers * 3]  # Fetch more, filter later


def run_comps_analysis(
    ticker: str,
    max_peers: int = 10,
    min_market_cap: float = 0,
    max_market_cap: float = float('inf'),
    include_saas: bool = False,
    progress_callback=None
) -> CompsAnalysis:
    """
    Run full comparable company analysis.
    
    Args:
        ticker: Target company ticker
        max_peers: Maximum number of peer companies to include
        min_market_cap: Minimum market cap filter (in dollars)
        max_market_cap: Maximum market cap filter (in dollars)
        include_saas: Include SaaS-specific peers
        progress_callback: Optional callback for progress updates
    
    Returns:
        CompsAnalysis with target and peer data
    """
    analysis = CompsAnalysis(target_ticker=ticker)
    
    # Fetch target company data first
    if progress_callback:
        progress_callback(0.1, "Fetching target company data...")
    
    target_comps = fetch_company_multiples(ticker)
    analysis.target_comps = target_comps
    analysis.target_name = target_comps.name
    analysis.target_sector = target_comps.sector
    analysis.target_industry = target_comps.industry
    
    if not target_comps.valid:
        return analysis
    
    # Find peer companies
    if progress_callback:
        progress_callback(0.2, "Identifying peer companies...")
    
    peer_tickers = find_peer_companies(
        ticker=ticker,
        sector=target_comps.sector,
        industry=target_comps.industry,
        market_cap=target_comps.market_cap,
        max_peers=max_peers * 2,
        include_saas=include_saas
    )
    
    # Fetch peer data in parallel
    if progress_callback:
        progress_callback(0.3, f"Fetching data for {len(peer_tickers)} potential peers...")
    
    peer_results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_company_multiples, t): t for t in peer_tickers}
        completed = 0
        for future in as_completed(futures):
            completed += 1
            if progress_callback:
                progress_callback(0.3 + (0.5 * completed / len(futures)), 
                                f"Fetched {completed}/{len(peer_tickers)} peers...")
            try:
                result = future.result()
                if result.valid and result.market_cap > 0:
                    peer_results.append(result)
            except:
                pass
    
    # Filter by market cap range
    if target_comps.market_cap > 0:
        mc = target_comps.market_cap
        if min_market_cap == 0:
            min_market_cap = mc * 0.2  # Default: 20% of target
        if max_market_cap == float('inf'):
            max_market_cap = mc * 5.0  # Default: 5x target
    
    filtered_peers = [
        p for p in peer_results 
        if min_market_cap <= p.market_cap <= max_market_cap
    ]
    
    # Sort by market cap proximity to target
    if target_comps.market_cap > 0:
        filtered_peers.sort(key=lambda p: abs(p.market_cap - target_comps.market_cap))
    
    # Take top max_peers
    analysis.peers = filtered_peers[:max_peers]
    
    # Calculate summary statistics
    if progress_callback:
        progress_callback(0.9, "Calculating statistics...")
    
    if analysis.peers:
        ev_revenues = [p.ev_revenue for p in analysis.peers if p.ev_revenue and p.ev_revenue > 0]
        ev_ebitdas = [p.ev_ebitda for p in analysis.peers if p.ev_ebitda and p.ev_ebitda > 0]
        pes = [p.pe_ratio for p in analysis.peers if p.pe_ratio and p.pe_ratio > 0]
        
        if ev_revenues:
            analysis.median_ev_revenue = np.median(ev_revenues)
            analysis.mean_ev_revenue = np.mean(ev_revenues)
            if target_comps.revenue_ltm and target_comps.revenue_ltm > 0:
                analysis.implied_ev_from_revenue = analysis.median_ev_revenue * target_comps.revenue_ltm
        
        if ev_ebitdas:
            analysis.median_ev_ebitda = np.median(ev_ebitdas)
            analysis.mean_ev_ebitda = np.mean(ev_ebitdas)
            if target_comps.ebitda_ltm and target_comps.ebitda_ltm > 0:
                analysis.implied_ev_from_ebitda = analysis.median_ev_ebitda * target_comps.ebitda_ltm
        
        if pes:
            analysis.median_pe = np.median(pes)
            analysis.mean_pe = np.mean(pes)
        
        # Calculate percentile rankings
        if target_comps.ev_revenue and ev_revenues:
            analysis.percentile_ev_revenue = (
                sum(1 for x in ev_revenues if x < target_comps.ev_revenue) / len(ev_revenues) * 100
            )
        
        if target_comps.ev_ebitda and ev_ebitdas:
            analysis.percentile_ev_ebitda = (
                sum(1 for x in ev_ebitdas if x < target_comps.ev_ebitda) / len(ev_ebitdas) * 100
            )
        
        if target_comps.pe_ratio and pes:
            analysis.percentile_pe = (
                sum(1 for x in pes if x < target_comps.pe_ratio) / len(pes) * 100
            )
    
    if progress_callback:
        progress_callback(1.0, "Complete!")
    
    return analysis


def generate_comps_table(analysis: CompsAnalysis) -> pd.DataFrame:
    """Generate a formatted comps table as DataFrame."""
    if not analysis.peers:
        return pd.DataFrame()
    
    data = []
    
    # Add target company first
    if analysis.target_comps:
        tc = analysis.target_comps
        data.append({
            "Company": f"**{tc.name}** (Target)",
            "Ticker": tc.ticker,
            "Market Cap": tc.market_cap,
            "EV": tc.enterprise_value,
            "Revenue": tc.revenue_ltm,
            "EBITDA": tc.ebitda_ltm,
            "EV/Rev": tc.ev_revenue,
            "EV/EBITDA": tc.ev_ebitda,
            "P/E": tc.pe_ratio,
            "Rev Growth": tc.revenue_growth,
            "EBITDA Margin": tc.ebitda_margin,
            "Rule of 40": tc.rule_of_40,
        })
    
    # Add peers
    for p in analysis.peers:
        data.append({
            "Company": p.name,
            "Ticker": p.ticker,
            "Market Cap": p.market_cap,
            "EV": p.enterprise_value,
            "Revenue": p.revenue_ltm,
            "EBITDA": p.ebitda_ltm,
            "EV/Rev": p.ev_revenue,
            "EV/EBITDA": p.ev_ebitda,
            "P/E": p.pe_ratio,
            "Rev Growth": p.revenue_growth,
            "EBITDA Margin": p.ebitda_margin,
            "Rule of 40": p.rule_of_40,
        })
    
    # Helper for safe stats
    def _safe_median(vals):
        v = [x for x in vals if x is not None and not (isinstance(x, float) and np.isnan(x))]
        return np.median(v) if v else None

    def _safe_mean(vals):
        v = [x for x in vals if x is not None and not (isinstance(x, float) and np.isnan(x))]
        return np.mean(v) if v else None

    _peer_vals = lambda attr: [getattr(p, attr) for p in analysis.peers]

    # Add Median summary row
    data.append({
        "Company": "📊 Peer Median",
        "Ticker": "",
        "Market Cap": _safe_median(_peer_vals("market_cap")),
        "EV": _safe_median([p.enterprise_value for p in analysis.peers]),
        "Revenue": _safe_median([p.revenue_ltm for p in analysis.peers]),
        "EBITDA": _safe_median([p.ebitda_ltm for p in analysis.peers]),
        "EV/Rev": analysis.median_ev_revenue,
        "EV/EBITDA": analysis.median_ev_ebitda,
        "P/E": analysis.median_pe,
        "Rev Growth": _safe_median(_peer_vals("revenue_growth")),
        "EBITDA Margin": _safe_median(_peer_vals("ebitda_margin")),
        "Rule of 40": _safe_median(_peer_vals("rule_of_40")),
    })

    # Add Mean summary row
    data.append({
        "Company": "📈 Peer Mean",
        "Ticker": "",
        "Market Cap": _safe_mean(_peer_vals("market_cap")),
        "EV": _safe_mean([p.enterprise_value for p in analysis.peers]),
        "Revenue": _safe_mean([p.revenue_ltm for p in analysis.peers]),
        "EBITDA": _safe_mean([p.ebitda_ltm for p in analysis.peers]),
        "EV/Rev": _safe_mean([p.ev_revenue for p in analysis.peers]),
        "EV/EBITDA": _safe_mean([p.ev_ebitda for p in analysis.peers]),
        "P/E": _safe_mean([p.pe_ratio for p in analysis.peers]),
        "Rev Growth": _safe_mean(_peer_vals("revenue_growth")),
        "EBITDA Margin": _safe_mean(_peer_vals("ebitda_margin")),
        "Rule of 40": _safe_mean(_peer_vals("rule_of_40")),
    })

    return pd.DataFrame(data)


def format_comps_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Format comps table for display with proper formatting."""
    display_df = df.copy()
    
    def fmt_millions(x):
        if pd.isna(x) or x == 0:
            return "—"
        if abs(x) >= 1e12:
            return f"${x/1e12:.1f}T"
        if abs(x) >= 1e9:
            return f"${x/1e9:.1f}B"
        if abs(x) >= 1e6:
            return f"${x/1e6:.0f}M"
        return f"${x:,.0f}"
    
    def fmt_multiple(x):
        if pd.isna(x) or x == 0:
            return "—"
        return f"{x:.1f}x"
    
    def fmt_percent(x):
        if pd.isna(x):
            return "—"
        return f"{x*100:.1f}%"
    
    def fmt_r40(x):
        if pd.isna(x):
            return "—"
        return f"{x:.0f}"
    
    for col in ["Market Cap", "EV", "Revenue", "EBITDA"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(fmt_millions)
    
    for col in ["EV/Rev", "EV/EBITDA", "P/E"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(fmt_multiple)
    
    for col in ["Rev Growth", "EBITDA Margin"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(fmt_percent)
    
    if "Rule of 40" in display_df.columns:
        display_df["Rule of 40"] = display_df["Rule of 40"].apply(fmt_r40)
    
    return display_df
