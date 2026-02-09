"""
PPTX Generator — Goldman Sachs-style investment banking presentations.

Design: Clean, minimal, data-dense. Navy/white palette with gold accents.
Arial font throughout, tight grid alignment, professional formatting.
3-slide decks for both Company Profile and Merger Analysis.
"""

import io
from datetime import datetime
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

from data_engine import CompanyData, format_number, format_pct, format_multiple

# ══════════════════════════════════════════════════════════════
# GOLDMAN SACHS STYLE PALETTE
# ══════════════════════════════════════════════════════════════

NAVY = RGBColor(0x00, 0x32, 0x5B)  # Goldman dark blue
LIGHT_NAVY = RGBColor(0x00, 0x4B, 0x87)
GOLD = RGBColor(0xB5, 0x98, 0x5A)  # Goldman gold
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)
LIGHT_GRAY = RGBColor(0xF5, 0xF5, 0xF5)
MED_GRAY = RGBColor(0xE0, 0xE0, 0xE0)
DARK_GRAY = RGBColor(0x4A, 0x4A, 0x4A)
GREEN = RGBColor(0x00, 0x6B, 0x3F)
RED = RGBColor(0xA3, 0x1F, 0x34)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


# ══════════════════════════════════════════════════════════════
# CORE HELPERS
# ══════════════════════════════════════════════════════════════

def _set_cell_text(cell, text, font_size=9, bold=False, color=BLACK, align=PP_ALIGN.LEFT):
    """Set cell text with consistent formatting."""
    cell.text = str(text) if text is not None else "—"
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(font_size)
        p.font.bold = bold
        p.font.name = "Arial"
        p.font.color.rgb = color
        p.alignment = align
    cell.text_frame.paragraphs[0].space_before = Pt(2)
    cell.text_frame.paragraphs[0].space_after = Pt(2)


def _add_textbox(slide, left, top, width, height, text,
                 font_size=10, bold=False, color=BLACK, align=PP_ALIGN.LEFT):
    """Add a textbox with specified formatting."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = str(text) if text else ""
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.name = "Arial"
    p.font.color.rgb = color
    p.alignment = align
    return txBox


def _add_rect(slide, left, top, width, height, fill_color, line_color=None):
    """Add a rectangle shape."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
    else:
        shape.line.fill.background()
    return shape


def _gs_header(slide, title, subtitle=""):
    """Goldman Sachs style header - thin gold line, navy title."""
    # Gold accent line at very top
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.06), GOLD)
    # Title
    _add_textbox(slide, Inches(0.5), Inches(0.25), Inches(10), Inches(0.4),
                 title.upper(), font_size=14, bold=True, color=NAVY)
    if subtitle:
        _add_textbox(slide, Inches(0.5), Inches(0.55), Inches(10), Inches(0.25),
                     subtitle, font_size=9, color=DARK_GRAY)
    # Thin line under title
    _add_rect(slide, Inches(0.5), Inches(0.85), Inches(12.333), Inches(0.015), NAVY)


def _gs_footer(slide, left_text, right_text="ORBITAL"):
    """Goldman Sachs style footer - minimal, professional."""
    # Thin line above footer
    _add_rect(slide, Inches(0.5), SLIDE_H - Inches(0.5), Inches(12.333), Inches(0.01), MED_GRAY)
    # Left text (confidential + date)
    _add_textbox(slide, Inches(0.5), SLIDE_H - Inches(0.4), Inches(8), Inches(0.3),
                 f"CONFIDENTIAL  |  {left_text}  |  {datetime.now().strftime('%B %Y')}",
                 font_size=7, color=DARK_GRAY)
    # Right text (brand)
    _add_textbox(slide, Inches(10), SLIDE_H - Inches(0.4), Inches(2.833), Inches(0.3),
                 right_text, font_size=7, bold=True, color=NAVY, align=PP_ALIGN.RIGHT)


def _gs_section_title(slide, text, top):
    """Add a section title with gold underline."""
    _add_textbox(slide, Inches(0.5), top, Inches(5), Inches(0.3),
                 text.upper(), font_size=9, bold=True, color=NAVY)
    _add_rect(slide, Inches(0.5), top + Inches(0.25), Inches(1.5), Inches(0.02), GOLD)


def _gs_table(slide, headers, rows, left, top, width, height, col_widths=None):
    """Professional Goldman-style table."""
    n_rows = len(rows) + 1
    n_cols = len(headers)
    shape = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = shape.table

    if col_widths:
        for i, w in enumerate(col_widths):
            if i < n_cols:
                table.columns[i].width = w

    # Header row - navy background
    for c, hdr in enumerate(headers):
        cell = table.cell(0, c)
        _set_cell_text(cell, hdr, font_size=8, bold=True, color=WHITE,
                       align=PP_ALIGN.CENTER if c > 0 else PP_ALIGN.LEFT)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY

    # Data rows
    for r, row_data in enumerate(rows, start=1):
        for c, val in enumerate(row_data):
            cell = table.cell(r, c)
            is_first_col = (c == 0)
            _set_cell_text(cell, val, font_size=8, bold=is_first_col,
                           color=DARK_GRAY, align=PP_ALIGN.LEFT if is_first_col else PP_ALIGN.RIGHT)
            # Alternating row colors
            cell.fill.solid()
            cell.fill.fore_color.rgb = LIGHT_GRAY if r % 2 == 0 else WHITE

    return shape


def _year_labels(series, count=4):
    """Extract year labels from a pandas Series."""
    if series is None or len(series) == 0:
        return ["—"] * count
    labels = []
    for idx in series.index[:count]:
        if hasattr(idx, "year"):
            labels.append(str(idx.year))
        else:
            labels.append(str(idx))
    while len(labels) < count:
        labels.append("—")
    return labels


def _series_vals(series, count=4, currency_symbol="$"):
    """Format series values for display."""
    if series is None or len(series) == 0:
        return ["—"] * count
    vals = []
    for v in list(series.values[:count]):
        if v is not None and not pd.isna(v):
            vals.append(format_number(v, currency_symbol=currency_symbol))
        else:
            vals.append("—")
    while len(vals) < count:
        vals.append("—")
    return vals


# ══════════════════════════════════════════════════════════════
# COMPANY PROFILE - 3 SLIDES
# ══════════════════════════════════════════════════════════════

def _company_slide_1(prs, cd: CompanyData):
    """Slide 1: Executive Summary - Company overview + key metrics."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    cs = cd.currency_symbol

    _gs_header(slide, f"{cd.name} ({cd.ticker})", f"{cd.sector} | {cd.industry}")
    _gs_footer(slide, cd.ticker)

    # Left column: Company Description
    _gs_section_title(slide, "Company Overview", Inches(1.0))

    _raw_desc = getattr(cd, 'description', None) or getattr(cd, 'long_business_summary', None) or ""
    if hasattr(_raw_desc, 'iloc'):
        _raw_desc = str(_raw_desc.iloc[0]) if len(_raw_desc) > 0 else ""
    _raw_desc = str(_raw_desc) if _raw_desc else ""
    desc = (_raw_desc[:600] + "...") if len(_raw_desc) > 600 else (_raw_desc or "Company description not available.")
    _add_textbox(slide, Inches(0.5), Inches(1.4), Inches(5.8), Inches(2.0),
                 desc, font_size=9, color=DARK_GRAY)

    # Key Statistics box
    _gs_section_title(slide, "Key Statistics", Inches(3.6))
    stats = [
        ["Market Cap", format_number(cd.market_cap, currency_symbol=cs)],
        ["Enterprise Value", format_number(cd.enterprise_value, currency_symbol=cs)],
        ["Revenue (LTM)", format_number(cd.revenue.iloc[0] if cd.revenue is not None and len(cd.revenue) > 0 else None, currency_symbol=cs)],
        ["EBITDA (LTM)", format_number(cd.ebitda.iloc[0] if cd.ebitda is not None and len(cd.ebitda) > 0 else None, currency_symbol=cs)],
        ["Employees", f"{cd.employees:,}" if cd.employees else "—"],
    ]
    _gs_table(slide, ["Metric", "Value"], stats,
              Inches(0.5), Inches(3.95), Inches(5.8), Inches(1.8),
              col_widths=[Inches(2.5), Inches(3.3)])

    # Right column: Valuation & Trading
    _gs_section_title(slide, "Valuation Metrics", Inches(1.0))

    valuation = [
        ["Current Price", f"{cs}{cd.current_price:,.2f}" if cd.current_price else "—"],
        ["52-Week Range", f"{cs}{cd.fifty_two_week_low:,.2f} - {cs}{cd.fifty_two_week_high:,.2f}" if cd.fifty_two_week_low and cd.fifty_two_week_high else "—"],
        ["P/E (TTM)", f"{cd.trailing_pe:.1f}x" if cd.trailing_pe else "—"],
        ["P/E (Forward)", f"{cd.forward_pe:.1f}x" if cd.forward_pe else "—"],
        ["EV/EBITDA", f"{cd.ev_to_ebitda:.1f}x" if cd.ev_to_ebitda else "—"],
        ["EV/Revenue", f"{cd.ev_to_revenue:.1f}x" if cd.ev_to_revenue else "—"],
        ["P/B", f"{cd.price_to_book:.1f}x" if cd.price_to_book else "—"],
        ["Dividend Yield", f"{cd.dividend_yield*100:.2f}%" if cd.dividend_yield else "—"],
    ]
    _gs_table(slide, ["Metric", "Value"], valuation,
              Inches(6.8), Inches(1.35), Inches(6), Inches(2.8),
              col_widths=[Inches(3), Inches(3)])

    # Trading Info
    _gs_section_title(slide, "Trading Information", Inches(4.4))
    trading = [
        ["Exchange", cd.exchange or "—"],
        ["Beta", f"{cd.beta:.2f}" if cd.beta else "—"],
        ["Avg Volume (3M)", f"{cd.average_volume/1e6:.1f}M" if cd.average_volume else "—"],
    ]
    _gs_table(slide, ["Metric", "Value"], trading,
              Inches(6.8), Inches(4.75), Inches(6), Inches(1.1),
              col_widths=[Inches(3), Inches(3)])


def _company_slide_2(prs, cd: CompanyData):
    """Slide 2: Financial Overview - P&L, Balance Sheet, Cash Flow."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    cs = cd.currency_symbol

    _gs_header(slide, "Financial Overview", f"{cd.name} ({cd.ticker})")
    _gs_footer(slide, cd.ticker)

    years = _year_labels(cd.revenue, 4)

    # Income Statement (top left)
    _gs_section_title(slide, "Income Statement", Inches(1.0))
    income_rows = [
        ["Revenue"] + _series_vals(cd.revenue, 4, cs),
        ["Gross Profit"] + _series_vals(cd.gross_profit, 4, cs),
        ["EBITDA"] + _series_vals(cd.ebitda, 4, cs),
        ["Net Income"] + _series_vals(cd.net_income, 4, cs),
    ]
    _gs_table(slide, [""] + years, income_rows,
              Inches(0.5), Inches(1.35), Inches(6), Inches(1.5),
              col_widths=[Inches(1.5)] + [Inches(1.125)] * 4)

    # Margins (top right)
    _gs_section_title(slide, "Profitability Margins", Inches(1.0))

    def _margin_vals(series, count=4):
        if series is None or len(series) == 0:
            return ["—"] * count
        vals = []
        for v in list(series.values[:count]):
            if v is not None and not pd.isna(v):
                vals.append(f"{v*100:.1f}%")
            else:
                vals.append("—")
        while len(vals) < count:
            vals.append("—")
        return vals

    margin_rows = [
        ["Gross Margin"] + _margin_vals(cd.gross_margin_series, 4),
        ["EBITDA Margin"] + _margin_vals(cd.ebitda_margin, 4),
        ["Net Margin"] + _margin_vals(cd.net_margin_series, 4),
    ]
    _gs_table(slide, [""] + years, margin_rows,
              Inches(6.8), Inches(1.35), Inches(6), Inches(1.2),
              col_widths=[Inches(1.5)] + [Inches(1.125)] * 4)

    # Balance Sheet (middle left)
    _gs_section_title(slide, "Balance Sheet", Inches(3.0))
    bs_years = _year_labels(cd.total_assets, 4)
    bs_rows = [
        ["Total Assets"] + _series_vals(cd.total_assets, 4, cs),
        ["Cash & Equivalents"] + _series_vals(cd.cash_and_equivalents, 4, cs),
        ["Total Debt"] + _series_vals(cd.total_debt, 4, cs),
        ["Total Equity"] + _series_vals(cd.total_equity, 4, cs),
    ]
    _gs_table(slide, [""] + bs_years, bs_rows,
              Inches(0.5), Inches(3.35), Inches(6), Inches(1.5),
              col_widths=[Inches(1.5)] + [Inches(1.125)] * 4)

    # Cash Flow (middle right)
    _gs_section_title(slide, "Cash Flow Statement", Inches(3.0))
    cf_years = _year_labels(cd.operating_cashflow_series, 4)
    cf_rows = [
        ["Operating CF"] + _series_vals(cd.operating_cashflow_series, 4, cs),
        ["Capital Expenditures"] + _series_vals(cd.capital_expenditure, 4, cs),
        ["Free Cash Flow"] + _series_vals(cd.free_cashflow_series, 4, cs),
    ]
    _gs_table(slide, [""] + cf_years, cf_rows,
              Inches(6.8), Inches(3.35), Inches(6), Inches(1.2),
              col_widths=[Inches(1.5)] + [Inches(1.125)] * 4)

    # Credit Metrics (bottom)
    _gs_section_title(slide, "Credit Metrics", Inches(5.0))

    debt_ebitda = "—"
    if cd.total_debt is not None and len(cd.total_debt) > 0 and cd.ebitda is not None and len(cd.ebitda) > 0:
        d = cd.total_debt.iloc[0]
        e = cd.ebitda.iloc[0]
        if d and e and e != 0:
            debt_ebitda = f"{d/e:.1f}x"

    credit_rows = [
        ["Debt / EBITDA", debt_ebitda],
        ["Net Debt / EBITDA", f"{cd.net_debt_to_ebitda:.1f}x" if cd.net_debt_to_ebitda else "—"],
        ["Interest Coverage", f"{cd.interest_coverage:.1f}x" if cd.interest_coverage else "—"],
    ]
    _gs_table(slide, ["Metric", "Value"], credit_rows,
              Inches(0.5), Inches(5.35), Inches(4), Inches(1.1),
              col_widths=[Inches(2), Inches(2)])


def _company_slide_3(prs, cd: CompanyData):
    """Slide 3: Peer Comparison & Analyst Views."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    cs = cd.currency_symbol

    _gs_header(slide, "Valuation & Peer Comparison", f"{cd.name} ({cd.ticker})")
    _gs_footer(slide, cd.ticker)

    # Peer Comparison Table
    _gs_section_title(slide, "Comparable Company Analysis", Inches(1.0))

    peer_headers = ["Company", "Price", "Mkt Cap", "EV/EBITDA", "P/E", "EV/Rev"]
    peer_rows = []

    # Add target company first
    peer_rows.append([
        f"{cd.ticker} (Target)",
        f"{cs}{cd.current_price:.2f}" if cd.current_price else "—",
        format_number(cd.market_cap, currency_symbol=cs) if cd.market_cap else "—",
        f"{cd.ev_to_ebitda:.1f}x" if cd.ev_to_ebitda else "—",
        f"{cd.trailing_pe:.1f}x" if cd.trailing_pe else "—",
        f"{cd.ev_to_revenue:.1f}x" if cd.ev_to_revenue else "—",
    ])

    # Add peers
    if cd.peer_data:
        for peer in cd.peer_data[:6]:
            peer_rows.append([
                peer.get("ticker", "—"),
                f"{cs}{peer.get('price', 0):.2f}" if peer.get("price") else "—",
                format_number(peer.get("market_cap"), currency_symbol=cs) if peer.get("market_cap") else "—",
                f"{peer.get('ev_ebitda', 0):.1f}x" if peer.get("ev_ebitda") else "—",
                f"{peer.get('pe_ratio', 0):.1f}x" if peer.get("pe_ratio") else "—",
                f"{peer.get('ev_revenue', 0):.1f}x" if peer.get("ev_revenue") else "—",
            ])

    _gs_table(slide, peer_headers, peer_rows,
              Inches(0.5), Inches(1.35), Inches(12.333), Inches(2.5),
              col_widths=[Inches(2.5), Inches(1.5), Inches(2.2), Inches(2), Inches(2), Inches(2.133)])

    # Analyst Price Targets (bottom left)
    _gs_section_title(slide, "Analyst Price Targets", Inches(4.2))

    if cd.analyst_price_targets:
        targets = cd.analyst_price_targets
        target_rows = [
            ["Current Price", f"{cs}{cd.current_price:.2f}" if cd.current_price else "—"],
            ["Low Target", f"{cs}{targets.get('low', 0):.2f}" if targets.get('low') else "—"],
            ["Mean Target", f"{cs}{targets.get('mean', 0):.2f}" if targets.get('mean') else "—"],
            ["High Target", f"{cs}{targets.get('high', 0):.2f}" if targets.get('high') else "—"],
        ]
        if targets.get('mean') and cd.current_price:
            upside = ((targets['mean'] / cd.current_price) - 1) * 100
            target_rows.append(["Implied Upside", f"{upside:+.1f}%"])
    else:
        target_rows = [["No analyst data available", "—"]]

    _gs_table(slide, ["Metric", "Value"], target_rows,
              Inches(0.5), Inches(4.55), Inches(5), Inches(1.8),
              col_widths=[Inches(2.5), Inches(2.5)])

    # Analyst Recommendations (bottom right)
    _gs_section_title(slide, "Analyst Recommendations", Inches(4.2))

    if cd.analyst_recommendations:
        rec = cd.analyst_recommendations
        rec_rows = [
            ["Strong Buy", str(rec.get('strongBuy', 0))],
            ["Buy", str(rec.get('buy', 0))],
            ["Hold", str(rec.get('hold', 0))],
            ["Sell", str(rec.get('sell', 0))],
            ["Strong Sell", str(rec.get('strongSell', 0))],
        ]
    else:
        rec_rows = [["No recommendation data available", "—"]]

    _gs_table(slide, ["Rating", "# Analysts"], rec_rows,
              Inches(6.8), Inches(4.55), Inches(5.533), Inches(1.8),
              col_widths=[Inches(2.8), Inches(2.733)])


def generate_presentation(cd: CompanyData, template_path: str = "assets/template.pptx") -> io.BytesIO:
    """Build the 3-slide Goldman Sachs-style company profile."""
    prs = Presentation(template_path)
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    _company_slide_1(prs, cd)  # Executive Summary
    _company_slide_2(prs, cd)  # Financial Overview
    _company_slide_3(prs, cd)  # Peer Comparison

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════
# MERGER DEAL BOOK - 3 SLIDES
# ══════════════════════════════════════════════════════════════

def _deal_slide_1(prs, acq, tgt, pf, assumptions):
    """Slide 1: Transaction Overview."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    cs = acq.currency_symbol

    _gs_header(slide, "Transaction Overview", f"{acq.name} to acquire {tgt.name}")
    _gs_footer(slide, f"{acq.ticker} + {tgt.ticker}")

    # Key Transaction Terms (left)
    _gs_section_title(slide, "Key Transaction Terms", Inches(1.0))

    terms = [
        ["Purchase Price", format_number(pf.purchase_price, currency_symbol=cs)],
        ["Offer Premium", f"{assumptions.offer_premium_pct:.0f}%"],
        ["Offer Price / Share", f"{cs}{pf.offer_price_per_share:.2f}" if pf.offer_price_per_share else "—"],
        ["Implied EV/EBITDA", f"{pf.implied_ev_ebitda:.1f}x" if pf.implied_ev_ebitda else "—"],
        ["Implied P/E", f"{pf.implied_pe:.1f}x" if pf.implied_pe else "—"],
        ["Transaction Fees", format_number(pf.transaction_fees, currency_symbol=cs)],
    ]
    _gs_table(slide, ["Metric", "Value"], terms,
              Inches(0.5), Inches(1.35), Inches(5.5), Inches(2.2),
              col_widths=[Inches(2.5), Inches(3)])

    # Consideration Mix (left bottom)
    _gs_section_title(slide, "Consideration Structure", Inches(3.8))

    consideration = [
        ["Cash Consideration", format_number(pf.cash_consideration, currency_symbol=cs), f"{assumptions.pct_cash:.0f}%"],
        ["Stock Consideration", format_number(pf.stock_consideration, currency_symbol=cs), f"{assumptions.pct_stock:.0f}%"],
        ["New Shares Issued", f"{pf.new_shares_issued/1e6:.1f}M", "—"],
        ["Total Consideration", format_number(pf.purchase_price, currency_symbol=cs), "100%"],
    ]
    _gs_table(slide, ["Component", "Amount", "% of Total"], consideration,
              Inches(0.5), Inches(4.15), Inches(5.5), Inches(1.5),
              col_widths=[Inches(2.2), Inches(2.0), Inches(1.3)])

    # Company Comparison (right)
    _gs_section_title(slide, "Company Comparison", Inches(1.0))

    comparison = [
        ["Market Cap", format_number(acq.market_cap, currency_symbol=cs), format_number(tgt.market_cap, currency_symbol=cs)],
        ["Enterprise Value", format_number(acq.enterprise_value, currency_symbol=cs), format_number(tgt.enterprise_value, currency_symbol=cs)],
        ["Revenue (LTM)", format_number(pf.acq_revenue, currency_symbol=cs), format_number(pf.tgt_revenue, currency_symbol=cs)],
        ["EBITDA (LTM)", format_number(pf.acq_ebitda, currency_symbol=cs), format_number(pf.tgt_ebitda, currency_symbol=cs)],
        ["Net Income", format_number(pf.acq_net_income, currency_symbol=cs), format_number(pf.tgt_net_income, currency_symbol=cs)],
        ["EV/EBITDA", f"{acq.ev_to_ebitda:.1f}x" if acq.ev_to_ebitda else "—", f"{tgt.ev_to_ebitda:.1f}x" if tgt.ev_to_ebitda else "—"],
    ]
    _gs_table(slide, ["Metric", acq.ticker, tgt.ticker], comparison,
              Inches(6.8), Inches(1.35), Inches(6), Inches(2.2),
              col_widths=[Inches(2.2), Inches(1.9), Inches(1.9)])

    # Deal Rationale (right bottom)
    _gs_section_title(slide, "Strategic Rationale", Inches(3.8))

    rationale = [
        ["Cost Synergies", format_number(pf.cost_synergies, currency_symbol=cs)],
        ["Revenue Synergies", format_number(pf.revenue_synergies, currency_symbol=cs)],
        ["Total Synergies", format_number(pf.total_synergies, currency_symbol=cs)],
        ["Synergies % of Target Rev", f"{pf.total_synergies/pf.tgt_revenue*100:.1f}%" if pf.tgt_revenue else "—"],
    ]
    _gs_table(slide, ["Metric", "Value"], rationale,
              Inches(6.8), Inches(4.15), Inches(6), Inches(1.5),
              col_widths=[Inches(3.5), Inches(2.5)])


def _deal_slide_2(prs, acq, tgt, pf, assumptions):
    """Slide 2: Financial Impact - Pro Forma & Accretion/Dilution."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    cs = acq.currency_symbol
    tax_r = assumptions.tax_rate / 100

    _gs_header(slide, "Financial Impact Analysis", f"{acq.ticker} + {tgt.ticker}")
    _gs_footer(slide, f"{acq.ticker} + {tgt.ticker}")

    # Pro Forma P&L (left)
    _gs_section_title(slide, "Pro Forma Income Statement", Inches(1.0))

    ats = pf.total_synergies * (1 - tax_r)
    ati = pf.incremental_interest * (1 - tax_r)

    pf_rows = [
        ["Revenue", format_number(pf.acq_revenue, currency_symbol=cs), format_number(pf.tgt_revenue, currency_symbol=cs), format_number(pf.revenue_synergies, currency_symbol=cs), format_number(pf.pf_revenue, currency_symbol=cs)],
        ["EBITDA", format_number(pf.acq_ebitda, currency_symbol=cs), format_number(pf.tgt_ebitda, currency_symbol=cs), format_number(pf.total_synergies, currency_symbol=cs), format_number(pf.pf_ebitda, currency_symbol=cs)],
        ["Net Income", format_number(pf.acq_net_income, currency_symbol=cs), format_number(pf.tgt_net_income, currency_symbol=cs), format_number(ats - ati, currency_symbol=cs), format_number(pf.pf_net_income, currency_symbol=cs)],
        ["Shares (M)", f"{pf.acq_shares/1e6:.0f}" if pf.acq_shares else "—", "—", f"+{pf.new_shares_issued/1e6:.0f}" if pf.new_shares_issued else "—", f"{pf.pf_shares_outstanding/1e6:.0f}" if pf.pf_shares_outstanding else "—"],
        ["EPS", f"{cs}{pf.acq_eps:.2f}" if pf.acq_eps else "—", "—", "—", f"{cs}{pf.pf_eps:.2f}" if pf.pf_eps else "—"],
    ]
    _gs_table(slide, ["", acq.ticker, tgt.ticker, "Adj.", "Pro Forma"], pf_rows,
              Inches(0.5), Inches(1.35), Inches(7.5), Inches(1.9),
              col_widths=[Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.5)])

    # Accretion/Dilution Summary (left bottom)
    _gs_section_title(slide, "Accretion / Dilution", Inches(3.5))

    acc_color = GREEN if pf.is_accretive else RED
    acc_word = "ACCRETIVE" if pf.is_accretive else "DILUTIVE"

    # Big impact number
    _add_textbox(slide, Inches(0.5), Inches(3.85), Inches(3), Inches(0.6),
                 f"{pf.accretion_dilution_pct:+.1f}%", font_size=28, bold=True, color=acc_color)
    _add_textbox(slide, Inches(0.5), Inches(4.4), Inches(3), Inches(0.3),
                 acc_word, font_size=12, bold=True, color=acc_color)

    # EPS bridge table
    eps_rows = [
        ["Standalone EPS", f"{cs}{pf.acq_eps:.2f}" if pf.acq_eps else "—"],
        ["Pro Forma EPS", f"{cs}{pf.pf_eps:.2f}" if pf.pf_eps else "—"],
        ["EPS Change", f"{cs}{pf.pf_eps - pf.acq_eps:.2f}" if pf.acq_eps and pf.pf_eps else "—"],
    ]
    _gs_table(slide, ["Metric", "Value"], eps_rows,
              Inches(3.8), Inches(3.85), Inches(3.7), Inches(1.1),
              col_widths=[Inches(2), Inches(1.7)])

    # Sources & Uses (right)
    _gs_section_title(slide, "Sources of Funds", Inches(1.0))

    sources_rows = [[k, format_number(v, currency_symbol=cs)] for k, v in pf.sources.items()]
    _gs_table(slide, ["Source", "Amount"], sources_rows,
              Inches(8.5), Inches(1.35), Inches(4.333), Inches(1.5),
              col_widths=[Inches(2.5), Inches(1.833)])

    _gs_section_title(slide, "Uses of Funds", Inches(3.0))

    uses_rows = [[k, format_number(v, currency_symbol=cs)] for k, v in pf.uses.items()]
    _gs_table(slide, ["Use", "Amount"], uses_rows,
              Inches(8.5), Inches(3.35), Inches(4.333), Inches(1.5),
              col_widths=[Inches(2.5), Inches(1.833)])

    # Credit Metrics (bottom right)
    _gs_section_title(slide, "Pro Forma Credit Profile", Inches(5.0))

    credit_rows = [
        ["PF Debt / EBITDA", f"{pf.pf_leverage_ratio:.1f}x" if pf.pf_leverage_ratio else "—"],
        ["PF Interest Coverage", f"{pf.pf_interest_coverage:.1f}x" if pf.pf_interest_coverage else "—"],
        ["PF Total Debt", format_number(pf.pf_total_debt, currency_symbol=cs)],
    ]
    _gs_table(slide, ["Metric", "Value"], credit_rows,
              Inches(8.5), Inches(5.35), Inches(4.333), Inches(1.1),
              col_widths=[Inches(2.5), Inches(1.833)])


def _deal_slide_3(prs, acq, tgt, pf, assumptions, football_field):
    """Slide 3: Valuation Analysis - Football Field."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    cs = acq.currency_symbol

    _gs_header(slide, "Valuation Analysis", f"{tgt.name} ({tgt.ticker})")
    _gs_footer(slide, f"{acq.ticker} + {tgt.ticker}")

    # Football Field Table
    _gs_section_title(slide, "Valuation Summary (Football Field)", Inches(1.0))

    offer_price = football_field.get("_offer_price", 0) if football_field else 0
    methods = {k: v for k, v in football_field.items() if not k.startswith("_")} if football_field else {}

    def _fmt_val(v):
        if v is None:
            return "—"
        if abs(v) >= 1e9:
            return f"{cs}{v/1e9:.1f}B"
        elif abs(v) >= 1e6:
            return f"{cs}{v/1e6:.0f}M"
        else:
            return f"{cs}{v:,.0f}"

    ff_rows = []
    for method, vals in methods.items():
        low = vals.get("low", 0)
        high = vals.get("high", 0)
        mid = (low + high) / 2 if low and high else 0
        ff_rows.append([method, _fmt_val(low), _fmt_val(mid), _fmt_val(high)])

    if ff_rows:
        _gs_table(slide, ["Methodology", "Low", "Midpoint", "High"], ff_rows,
                  Inches(0.5), Inches(1.35), Inches(7), Inches(2.2),
                  col_widths=[Inches(2.5), Inches(1.5), Inches(1.5), Inches(1.5)])
    else:
        _add_textbox(slide, Inches(0.5), Inches(1.35), Inches(7), Inches(0.5),
                     "Insufficient data for valuation analysis", font_size=10, color=DARK_GRAY)

    # Offer Price Comparison
    _gs_section_title(slide, "Offer Analysis", Inches(3.8))

    offer_rows = [
        ["Offer Price / Share", f"{cs}{pf.offer_price_per_share:.2f}" if pf.offer_price_per_share else "—"],
        ["Current Price", f"{cs}{tgt.current_price:.2f}" if tgt.current_price else "—"],
        ["Offer Premium", f"{assumptions.offer_premium_pct:.0f}%"],
        ["52-Week High", f"{cs}{tgt.fifty_two_week_high:.2f}" if tgt.fifty_two_week_high else "—"],
        ["52-Week Low", f"{cs}{tgt.fifty_two_week_low:.2f}" if tgt.fifty_two_week_low else "—"],
    ]
    _gs_table(slide, ["Metric", "Value"], offer_rows,
              Inches(0.5), Inches(4.15), Inches(5), Inches(1.8),
              col_widths=[Inches(2.5), Inches(2.5)])

    # Implied Multiples (right side)
    _gs_section_title(slide, "Implied Transaction Multiples", Inches(1.0))

    multiples = [
        ["Implied EV / Revenue", f"{pf.purchase_price / pf.tgt_revenue:.1f}x" if pf.tgt_revenue else "—"],
        ["Implied EV / EBITDA", f"{pf.implied_ev_ebitda:.1f}x" if pf.implied_ev_ebitda else "—"],
        ["Implied P / E", f"{pf.implied_pe:.1f}x" if pf.implied_pe else "—"],
    ]
    _gs_table(slide, ["Multiple", "Value"], multiples,
              Inches(8), Inches(1.35), Inches(4.833), Inches(1.2),
              col_widths=[Inches(2.8), Inches(2.033)])

    # Transaction Assumptions
    _gs_section_title(slide, "Transaction Assumptions", Inches(2.8))

    assump_rows = [
        ["Cost of Debt", f"{assumptions.cost_of_debt:.1f}%"],
        ["Tax Rate", f"{assumptions.tax_rate:.1f}%"],
        ["Cost Synergies (% of Target SG&A)", f"{assumptions.cost_synergies_pct:.1f}%"],
        ["Revenue Synergies (% of Target Rev)", f"{assumptions.revenue_synergies_pct:.1f}%"],
        ["Transaction Fees (% of Deal)", f"{assumptions.transaction_fees_pct:.1f}%"],
    ]
    _gs_table(slide, ["Assumption", "Value"], assump_rows,
              Inches(8), Inches(3.15), Inches(4.833), Inches(1.9),
              col_widths=[Inches(3.3), Inches(1.533)])


def generate_deal_book(acq_cd, tgt_cd, pro_forma, merger_insights, assumptions,
                       template_path: str = "assets/template.pptx") -> io.BytesIO:
    """Build the 3-slide Goldman Sachs-style deal book."""
    prs = Presentation(template_path)
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    _deal_slide_1(prs, acq_cd, tgt_cd, pro_forma, assumptions)  # Transaction Overview
    _deal_slide_2(prs, acq_cd, tgt_cd, pro_forma, assumptions)  # Financial Impact
    _deal_slide_3(prs, acq_cd, tgt_cd, pro_forma, assumptions, pro_forma.football_field)  # Valuation

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf
