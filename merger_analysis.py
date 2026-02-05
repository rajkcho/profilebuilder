"""
Merger Analysis Engine — computes pro forma financials, accretion/dilution,
football field valuation, sources & uses, and credit metrics for a
hypothetical acquirer + target combination.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List, Dict

from data_engine import CompanyData, format_number


# ══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════

@dataclass
class MergerAssumptions:
    """User-configurable deal assumptions (from sidebar sliders)."""
    offer_premium_pct: float = 30.0      # % premium to current price
    pct_cash: float = 50.0               # % of consideration in cash
    pct_stock: float = 50.0              # % of consideration in stock
    cost_synergies_pct: float = 10.0     # % of target SG&A
    revenue_synergies_pct: float = 2.0   # % of target revenue
    tax_rate: float = 25.0               # assumed marginal tax rate
    cost_of_debt: float = 5.0            # assumed new debt coupon rate
    transaction_fees_pct: float = 2.0    # advisory + legal fees as % of deal


@dataclass
class ProFormaData:
    """All computed merger metrics."""

    # ── Deal Terms ────────────────────────────────────────
    offer_price_per_share: float = 0.0
    purchase_price: float = 0.0            # total equity value paid
    cash_consideration: float = 0.0
    stock_consideration: float = 0.0
    new_shares_issued: float = 0.0
    transaction_fees: float = 0.0

    # Implied multiples
    implied_ev: float = 0.0
    implied_ev_ebitda: Optional[float] = None
    implied_ev_revenue: Optional[float] = None
    implied_pe: Optional[float] = None

    # ── Pro Forma Combined ────────────────────────────────
    pf_revenue: float = 0.0
    pf_ebitda: float = 0.0
    pf_net_income: float = 0.0
    pf_eps: float = 0.0
    pf_shares_outstanding: float = 0.0

    # Standalone for comparison
    acq_revenue: float = 0.0
    acq_ebitda: float = 0.0
    acq_net_income: float = 0.0
    acq_eps: float = 0.0
    acq_shares: float = 0.0
    tgt_revenue: float = 0.0
    tgt_ebitda: float = 0.0
    tgt_net_income: float = 0.0

    # ── Accretion / Dilution ──────────────────────────────
    accretion_dilution_pct: float = 0.0
    is_accretive: bool = False

    # ── Synergies ─────────────────────────────────────────
    cost_synergies: float = 0.0
    revenue_synergies: float = 0.0
    total_synergies: float = 0.0
    synergy_npv: float = 0.0              # NPV at 10% discount, perpetuity

    # ── Goodwill ──────────────────────────────────────────
    goodwill: float = 0.0
    target_book_value: float = 0.0

    # ── Credit Metrics ────────────────────────────────────
    pf_total_debt: float = 0.0
    pf_net_debt: float = 0.0
    pf_leverage_ratio: Optional[float] = None   # Debt / EBITDA
    pf_interest_coverage: Optional[float] = None # EBITDA / Interest
    incremental_interest: float = 0.0
    pf_total_interest: float = 0.0

    # ── Sources & Uses ────────────────────────────────────
    sources: Dict[str, float] = field(default_factory=dict)
    uses: Dict[str, float] = field(default_factory=dict)

    # ── Waterfall Steps (for accretion chart) ─────────────
    waterfall_steps: List[Dict] = field(default_factory=list)

    # ── Football Field ────────────────────────────────────
    football_field: Dict[str, Dict] = field(default_factory=dict)

    # ── Warnings ──────────────────────────────────────────
    currency_mismatch: bool = False
    warnings: List[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _latest_val(series: Optional[pd.Series], default: float = 0.0) -> float:
    """Get the most recent value from a pd.Series (iloc[0])."""
    if series is None or len(series) == 0:
        return default
    val = series.iloc[0]
    try:
        return float(val) if not pd.isna(val) else default
    except (TypeError, ValueError):
        return default


# ══════════════════════════════════════════════════════════════
# CORE: calculate_pro_forma
# ══════════════════════════════════════════════════════════════

def calculate_pro_forma(
    acq: CompanyData,
    tgt: CompanyData,
    assumptions: MergerAssumptions,
) -> ProFormaData:
    """Compute full pro forma merger analysis."""
    pf = ProFormaData()

    # ── Currency check ────────────────────────────────────
    if acq.currency_code != tgt.currency_code:
        pf.currency_mismatch = True
        pf.warnings.append(
            f"Currency mismatch: {acq.ticker} reports in {acq.currency_code}, "
            f"{tgt.ticker} reports in {tgt.currency_code}. "
            f"Proceeding with nominal values (no FX conversion)."
        )

    # ── Extract standalone financials ─────────────────────
    pf.acq_revenue = _latest_val(acq.revenue)
    pf.acq_ebitda = _latest_val(acq.ebitda)
    pf.acq_net_income = _latest_val(acq.net_income)
    pf.acq_shares = acq.shares_outstanding or 0
    pf.acq_eps = pf.acq_net_income / pf.acq_shares if pf.acq_shares else 0

    pf.tgt_revenue = _latest_val(tgt.revenue)
    pf.tgt_ebitda = _latest_val(tgt.ebitda)
    pf.tgt_net_income = _latest_val(tgt.net_income)

    # ── Deal Pricing ──────────────────────────────────────
    tgt_price = tgt.current_price or 0
    tgt_shares = tgt.shares_outstanding or 0

    pf.offer_price_per_share = tgt_price * (1 + assumptions.offer_premium_pct / 100)
    pf.purchase_price = pf.offer_price_per_share * tgt_shares

    # Consideration split
    pf.cash_consideration = pf.purchase_price * (assumptions.pct_cash / 100)
    pf.stock_consideration = pf.purchase_price * (assumptions.pct_stock / 100)

    # New shares issued to target shareholders
    acq_price = acq.current_price or 1
    pf.new_shares_issued = pf.stock_consideration / acq_price if acq_price else 0

    # Transaction fees
    pf.transaction_fees = pf.purchase_price * (assumptions.transaction_fees_pct / 100)

    # ── Implied Multiples ─────────────────────────────────
    # Implied EV = purchase price + target net debt
    tgt_total_debt = _latest_val(tgt.total_debt)
    tgt_cash = _latest_val(tgt.cash_and_equivalents)
    tgt_net_debt = tgt_total_debt - tgt_cash
    pf.implied_ev = pf.purchase_price + tgt_net_debt

    if pf.tgt_ebitda and pf.tgt_ebitda > 0:
        pf.implied_ev_ebitda = pf.implied_ev / pf.tgt_ebitda
    if pf.tgt_revenue and pf.tgt_revenue > 0:
        pf.implied_ev_revenue = pf.implied_ev / pf.tgt_revenue
    if pf.tgt_net_income and pf.tgt_net_income > 0:
        pf.implied_pe = pf.purchase_price / pf.tgt_net_income

    # ── Synergies ─────────────────────────────────────────
    tgt_sga = abs(_latest_val(tgt.sga_expense))
    if tgt_sga == 0:
        # Fallback: 5% of target revenue as synergy basis
        tgt_sga = pf.tgt_revenue * 0.05
        if tgt_sga > 0:
            pf.warnings.append(
                f"SG&A not available for {tgt.ticker}; using 5% of revenue as synergy basis."
            )

    pf.cost_synergies = tgt_sga * (assumptions.cost_synergies_pct / 100)
    pf.revenue_synergies = pf.tgt_revenue * (assumptions.revenue_synergies_pct / 100)
    pf.total_synergies = pf.cost_synergies + pf.revenue_synergies

    # Synergy NPV: perpetuity at 10% discount rate
    if pf.total_synergies > 0:
        pf.synergy_npv = pf.total_synergies / 0.10

    # ── Incremental Debt & Interest ───────────────────────
    new_debt = pf.cash_consideration + pf.transaction_fees
    pf.incremental_interest = new_debt * (assumptions.cost_of_debt / 100)

    # Existing interest expense (use absolute values — interest often stored as negative)
    acq_interest = abs(_latest_val(acq.interest_expense))
    tgt_interest = abs(_latest_val(tgt.interest_expense))
    pf.pf_total_interest = acq_interest + tgt_interest + pf.incremental_interest

    # ── Pro Forma Income Statement ────────────────────────
    pf.pf_revenue = pf.acq_revenue + pf.tgt_revenue + pf.revenue_synergies
    pf.pf_ebitda = pf.acq_ebitda + pf.tgt_ebitda + pf.total_synergies

    # Pro forma net income:
    # Combined NI + after-tax synergies - after-tax incremental interest
    tax_rate = assumptions.tax_rate / 100
    after_tax_synergies = pf.total_synergies * (1 - tax_rate)
    after_tax_incr_interest = pf.incremental_interest * (1 - tax_rate)
    pf.pf_net_income = (
        pf.acq_net_income + pf.tgt_net_income
        + after_tax_synergies - after_tax_incr_interest
    )

    # Pro forma shares & EPS
    pf.pf_shares_outstanding = pf.acq_shares + pf.new_shares_issued
    pf.pf_eps = pf.pf_net_income / pf.pf_shares_outstanding if pf.pf_shares_outstanding else 0

    # ── Accretion / Dilution ──────────────────────────────
    if pf.acq_eps and pf.acq_eps != 0:
        pf.accretion_dilution_pct = ((pf.pf_eps - pf.acq_eps) / abs(pf.acq_eps)) * 100
    pf.is_accretive = pf.accretion_dilution_pct > 0

    # ── Goodwill ──────────────────────────────────────────
    if tgt.book_value_per_share and tgt_shares:
        pf.target_book_value = tgt.book_value_per_share * tgt_shares
    else:
        # Fallback: use equity from balance sheet
        pf.target_book_value = _latest_val(tgt.total_equity)
    pf.goodwill = max(pf.purchase_price - pf.target_book_value, 0)

    # ── Credit Metrics ────────────────────────────────────
    acq_debt = _latest_val(acq.total_debt)
    pf.pf_total_debt = acq_debt + tgt_total_debt + new_debt

    acq_cash = _latest_val(acq.cash_and_equivalents)
    pf.pf_net_debt = pf.pf_total_debt - (acq_cash + tgt_cash)

    if pf.pf_ebitda and pf.pf_ebitda > 0:
        pf.pf_leverage_ratio = pf.pf_total_debt / pf.pf_ebitda
    if pf.pf_total_interest and pf.pf_total_interest > 0:
        pf.pf_interest_coverage = pf.pf_ebitda / pf.pf_total_interest

    # ── Sources & Uses ────────────────────────────────────
    pf.sources = {}
    if pf.cash_consideration > 0:
        pf.sources["New Debt"] = pf.cash_consideration + pf.transaction_fees
    if pf.stock_consideration > 0:
        pf.sources["New Equity (Stock)"] = pf.stock_consideration
    pf.sources["Total Sources"] = sum(v for k, v in pf.sources.items() if k != "Total Sources")

    pf.uses = {
        "Purchase Price (Equity)": pf.purchase_price,
        "Transaction Fees": pf.transaction_fees,
        "Total Uses": pf.purchase_price + pf.transaction_fees,
    }

    # ── Waterfall Steps ───────────────────────────────────
    pf.waterfall_steps = _build_waterfall_steps(pf, assumptions)

    # ── Validation warnings ───────────────────────────────
    if pf.acq_shares == 0:
        pf.warnings.append(f"Shares outstanding unavailable for {acq.ticker}.")
    if tgt_shares == 0:
        pf.warnings.append(f"Shares outstanding unavailable for {tgt.ticker}.")
    if pf.pf_leverage_ratio and pf.pf_leverage_ratio > 5:
        pf.warnings.append(
            f"Pro forma leverage is {pf.pf_leverage_ratio:.1f}x — this is very high."
        )

    return pf


def _build_waterfall_steps(pf: ProFormaData, assumptions: MergerAssumptions) -> List[Dict]:
    """Build waterfall chart steps for accretion/dilution analysis."""
    steps = []
    tax_rate = assumptions.tax_rate / 100

    # Start with acquirer standalone EPS
    steps.append({
        "label": f"Acquirer EPS",
        "value": pf.acq_eps,
        "type": "absolute",
    })

    # Target earnings contribution
    tgt_eps_contrib = pf.tgt_net_income / pf.pf_shares_outstanding if pf.pf_shares_outstanding else 0
    steps.append({
        "label": "Target Earnings",
        "value": tgt_eps_contrib,
        "type": "relative",
    })

    # Synergies (after tax)
    syn_eps = (pf.total_synergies * (1 - tax_rate)) / pf.pf_shares_outstanding if pf.pf_shares_outstanding else 0
    steps.append({
        "label": "Synergies",
        "value": syn_eps,
        "type": "relative",
    })

    # New interest expense (after tax, negative)
    int_eps = -(pf.incremental_interest * (1 - tax_rate)) / pf.pf_shares_outstanding if pf.pf_shares_outstanding else 0
    steps.append({
        "label": "New Interest",
        "value": int_eps,
        "type": "relative",
    })

    # Share dilution effect
    if pf.new_shares_issued > 0 and pf.acq_shares > 0:
        # The dilution from issuing shares: acquirer NI spread over more shares
        dilution = pf.acq_net_income / pf.acq_shares - pf.acq_net_income / pf.pf_shares_outstanding
        steps.append({
            "label": "Share Dilution",
            "value": -dilution,
            "type": "relative",
        })

    # Final pro forma EPS
    steps.append({
        "label": "Pro Forma EPS",
        "value": pf.pf_eps,
        "type": "total",
    })

    return steps


# ══════════════════════════════════════════════════════════════
# FOOTBALL FIELD VALUATION
# ══════════════════════════════════════════════════════════════

def build_football_field(
    acq: CompanyData,
    tgt: CompanyData,
    pro_forma: ProFormaData,
    precedent=None,
) -> Dict[str, Dict]:
    """Build valuation range data for a football field chart.

    Returns dict of {method_name: {"low": val, "high": val, "label": str}}.
    All values are total equity value (not per-share).
    """
    ff = {}
    tgt_shares = tgt.shares_outstanding or 0
    if tgt_shares == 0:
        return ff

    # 1. 52-Week Range
    if tgt.fifty_two_week_low and tgt.fifty_two_week_high:
        ff["52-Week Range"] = {
            "low": tgt.fifty_two_week_low * tgt_shares,
            "high": tgt.fifty_two_week_high * tgt_shares,
        }

    # 2. Analyst Price Targets
    if tgt.analyst_price_targets:
        apt = tgt.analyst_price_targets
        low_pt = apt.get("low")
        high_pt = apt.get("high")
        if low_pt and high_pt:
            ff["Analyst Targets"] = {
                "low": low_pt * tgt_shares,
                "high": high_pt * tgt_shares,
            }

    # 3. Peer EV/EBITDA Comps
    tgt_ebitda = _latest_val(tgt.ebitda)
    tgt_debt = _latest_val(tgt.total_debt)
    tgt_cash = _latest_val(tgt.cash_and_equivalents)
    tgt_net_debt = tgt_debt - tgt_cash

    if tgt.peer_data and tgt_ebitda > 0:
        peer_ev_ebitda = [
            p.get("ev_to_ebitda") for p in tgt.peer_data
            if p.get("ev_to_ebitda") is not None and p.get("ev_to_ebitda") > 0
        ]
        if peer_ev_ebitda:
            median_mult = float(np.median(peer_ev_ebitda))
            low_ev = tgt_ebitda * (median_mult * 0.8)
            high_ev = tgt_ebitda * (median_mult * 1.2)
            ff["EV/EBITDA Comps"] = {
                "low": low_ev - tgt_net_debt,
                "high": high_ev - tgt_net_debt,
            }

    # 4. Peer P/E Comps
    tgt_ni = _latest_val(tgt.net_income)
    if tgt.peer_data and tgt_ni > 0:
        peer_pe = [
            p.get("trailing_pe") for p in tgt.peer_data
            if p.get("trailing_pe") is not None and p.get("trailing_pe") > 0
        ]
        if peer_pe:
            median_pe = float(np.median(peer_pe))
            ff["P/E Comps"] = {
                "low": tgt_ni * (median_pe * 0.8),
                "high": tgt_ni * (median_pe * 1.2),
            }

    # 5. Simple DCF Range
    tgt_fcf = _latest_val(tgt.free_cashflow_series)
    if tgt_fcf > 0:
        # Gordon Growth: FCF * (1+g) / (WACC - g)
        # Low scenario: WACC=12%, g=2%  |  High: WACC=8%, g=4%
        dcf_low = tgt_fcf * 1.02 / (0.12 - 0.02) - tgt_net_debt
        dcf_high = tgt_fcf * 1.04 / (0.08 - 0.04) - tgt_net_debt
        if dcf_low > 0 and dcf_high > 0:
            ff["DCF (Perpetuity)"] = {
                "low": min(dcf_low, dcf_high),
                "high": max(dcf_low, dcf_high),
            }

    # 6. Precedent Transactions
    if precedent and getattr(precedent, "ev_ebitda_range", None) and tgt_ebitda > 0:
        low_mult, high_mult = precedent.ev_ebitda_range
        ff["Precedent Txns"] = {
            "low": tgt_ebitda * low_mult - tgt_net_debt,
            "high": tgt_ebitda * high_mult - tgt_net_debt,
        }

    # Store offer price for reference line
    ff["_offer_price"] = pro_forma.purchase_price

    return ff
