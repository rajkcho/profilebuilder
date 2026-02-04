"""
PPTX Generator — builds an 8-slide investment-banker-grade M&A profile.

Design standard: bulge-bracket pitch book quality — navy/gold/white palette,
Calibri throughout, tight grid alignment, professional header bands,
confidential footer, no wasted whitespace. Tables have navy headers with
white text, alternating row shading, right-aligned numbers.
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
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

from data_engine import CompanyData, format_number, format_pct, format_multiple

# ── Corporate Palette ────────────────────────────────────────
NAVY = RGBColor(0x0B, 0x1D, 0x3A)
DARK_BLUE = RGBColor(0x14, 0x2D, 0x5E)
ACCENT_BLUE = RGBColor(0x1E, 0x90, 0xFF)
GOLD = RGBColor(0xD4, 0xA5, 0x37)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF0, 0xF0, 0xF0)
MED_GRAY = RGBColor(0x99, 0x99, 0x99)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
RED = RGBColor(0xC6, 0x28, 0x28)
TEAL = RGBColor(0x00, 0x89, 0x7B)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


# ══════════════════════════════════════════════════════════════
# SHAPE HELPERS
# ══════════════════════════════════════════════════════════════

def _set_text(tf, text, font_size=12, bold=False, color=DARK_GRAY, alignment=PP_ALIGN.LEFT):
    tf.clear()
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = str(text)
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = "Calibri"
    p.alignment = alignment


def _add_textbox(slide, left, top, width, height, text,
                 font_size=12, bold=False, color=DARK_GRAY,
                 alignment=PP_ALIGN.LEFT, bg_color=None):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    _set_text(tf, text, font_size, bold, color, alignment)
    if bg_color:
        txBox.fill.solid()
        txBox.fill.fore_color.rgb = bg_color
    return txBox


def _add_para(text_frame, text, font_size=10, bold=False,
              color=DARK_GRAY, space_before=Pt(2), alignment=PP_ALIGN.LEFT):
    p = text_frame.add_paragraph()
    p.text = str(text)
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = "Calibri"
    p.space_before = space_before
    p.alignment = alignment
    return p


def _add_rect(slide, left, top, width, height, fill_color):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape


def _slide_header(slide, title_text):
    """Add the standard slide header: gold band + navy band + title."""
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.12), GOLD)
    _add_rect(slide, Inches(0), Inches(0.12), SLIDE_W, Inches(0.04), NAVY)
    _add_textbox(slide, Inches(0.5), Inches(0.3), Inches(12), Inches(0.5),
                 title_text, font_size=20, bold=True, color=NAVY)


def _slide_footer(slide, cd):
    """Add confidential footer bar."""
    _add_rect(slide, Inches(0), SLIDE_H - Inches(0.35), SLIDE_W, Inches(0.35), NAVY)
    _add_textbox(slide, Inches(0.5), SLIDE_H - Inches(0.32), Inches(8), Inches(0.25),
                 f"Confidential  |  {cd.name} ({cd.ticker})  |  {datetime.now().strftime('%B %d, %Y')}",
                 font_size=7, color=WHITE)
    _add_textbox(slide, SLIDE_W - Inches(2.5), SLIDE_H - Inches(0.32),
                 Inches(2.2), Inches(0.25),
                 "ProfileBuilder", font_size=7, bold=True, color=GOLD,
                 alignment=PP_ALIGN.RIGHT)


# ── Table Helper ─────────────────────────────────────────────

def _year_labels(series: Optional[pd.Series], count: int = 4) -> list[str]:
    """Extract year labels from a Series index."""
    if series is None:
        return ["—"] * count
    labels = []
    for col in series.index[:count]:
        if hasattr(col, "year"):
            labels.append(str(col.year))
        else:
            labels.append(str(col))
    while len(labels) < count:
        labels.append("—")
    return labels


def _add_styled_table(slide, headers, rows, left, top, width, height,
                      col_widths=None, num_cols_right_align=None):
    """Add a professionally formatted table with navy header row."""
    n_rows = len(rows) + 1  # +1 for header
    n_cols = len(headers)
    shape = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = shape.table

    if col_widths:
        for i, w in enumerate(col_widths):
            if i < n_cols:
                table.columns[i].width = w

    # Header row
    for c, hdr in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = str(hdr)
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(9)
            p.font.bold = True
            p.font.color.rgb = WHITE
            p.font.name = "Calibri"
            p.alignment = PP_ALIGN.CENTER
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY

    # Data rows
    right_align_start = num_cols_right_align or 1
    for r, row_data in enumerate(rows, start=1):
        for c, val in enumerate(row_data):
            cell = table.cell(r, c)
            cell.text = str(val)
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(8)
                p.font.name = "Calibri"
                p.font.bold = (c == 0)
                p.alignment = PP_ALIGN.RIGHT if c >= right_align_start else PP_ALIGN.LEFT
            # Alternating shading
            bg = LIGHT_GRAY if r % 2 == 0 else WHITE
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg

    return shape


def _series_vals(series: Optional[pd.Series], count: int = 4) -> list:
    """Extract up to `count` values from a Series."""
    if series is None:
        return [None] * count
    vals = list(series.values[:count])
    while len(vals) < count:
        vals.append(None)
    return vals


# ══════════════════════════════════════════════════════════════
# CHART RENDERERS (matplotlib → PNG → picture)
# ══════════════════════════════════════════════════════════════

def _render_5y_price_chart(cd: CompanyData) -> io.BytesIO:
    """5-year price chart with volume on secondary axis."""
    hist = cd.hist_5y if cd.hist_5y is not None and not cd.hist_5y.empty else cd.hist_1y
    fig, ax1 = plt.subplots(figsize=(7.5, 3.5))

    if hist is not None and not hist.empty:
        dates = hist.index
        prices = hist["Close"]

        ax1.fill_between(dates, prices, alpha=0.12, color="#1E90FF")
        ax1.plot(dates, prices, color="#1E90FF", linewidth=1.5)
        ax1.set_ylabel("Price ($)", fontsize=8, color="#333")
        ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.xticks(rotation=45, fontsize=7)
        plt.yticks(fontsize=7)

        if "Volume" in hist.columns:
            ax2 = ax1.twinx()
            ax2.bar(dates, hist["Volume"], alpha=0.15, color="#999", width=1)
            ax2.set_ylabel("Volume", fontsize=7, color="#999")
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(
                lambda x, _: f"{x/1e6:.0f}M" if x >= 1e6 else f"{x/1e3:.0f}K"
            ))
            ax2.tick_params(axis="y", labelsize=6, labelcolor="#999")

        ax1.set_title(f"{cd.ticker} — Price History", fontsize=10,
                      fontweight="bold", color="#0B1D3A", pad=8)
        ax1.grid(axis="y", alpha=0.2)
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
    else:
        ax1.text(0.5, 0.5, "Price data unavailable", ha="center", va="center",
                 fontsize=12, color="#999")
        ax1.axis("off")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _render_revenue_margin_chart(cd: CompanyData) -> io.BytesIO:
    """Dual-axis: revenue bars + margin lines."""
    fig, ax1 = plt.subplots(figsize=(6, 3))

    if cd.revenue is not None and not cd.revenue.empty:
        years = _year_labels(cd.revenue, 4)
        rev_vals = [float(v) / 1e9 if v is not None else 0 for v in _series_vals(cd.revenue, 4)]
        years.reverse()
        rev_vals.reverse()

        x = np.arange(len(years))
        bars = ax1.bar(x, rev_vals, color="#1E90FF", alpha=0.8, width=0.5)
        ax1.set_ylabel("Revenue ($B)", fontsize=8, color="#1E90FF")
        ax1.set_xticks(x)
        ax1.set_xticklabels(years, fontsize=7)
        ax1.tick_params(axis="y", labelsize=7, labelcolor="#1E90FF")

        # Margin line on secondary axis
        ax2 = ax1.twinx()
        margin_data = []
        has_margin = False
        if cd.gross_margin_series is not None:
            gm_vals = _series_vals(cd.gross_margin_series, 4)
            gm_vals.reverse()
            margin_data.append(("Gross", gm_vals, "#2E7D32"))
            has_margin = True
        if cd.operating_margin_series is not None:
            om_vals = _series_vals(cd.operating_margin_series, 4)
            om_vals.reverse()
            margin_data.append(("Operating", om_vals, "#D4A537"))
            has_margin = True

        if has_margin:
            for label, vals, clr in margin_data:
                clean = [float(v) if v is not None else 0 for v in vals]
                ax2.plot(x, clean, marker="o", markersize=4, color=clr,
                         linewidth=1.5, label=f"{label} %")
            ax2.set_ylabel("Margin (%)", fontsize=8)
            ax2.tick_params(axis="y", labelsize=7)
            ax2.legend(fontsize=6, loc="upper left")

        ax1.set_title("Revenue & Margins", fontsize=9, fontweight="bold",
                       color="#0B1D3A", pad=6)
        ax1.grid(axis="y", alpha=0.15)
        ax1.spines["top"].set_visible(False)
    else:
        ax1.text(0.5, 0.5, "Data unavailable", ha="center", va="center",
                 fontsize=10, color="#999")
        ax1.axis("off")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _render_cashflow_chart(cd: CompanyData) -> io.BytesIO:
    """Grouped bar chart: Operating CF vs Free CF."""
    fig, ax = plt.subplots(figsize=(5.5, 2.8))

    if cd.operating_cashflow_series is not None:
        years = _year_labels(cd.operating_cashflow_series, 4)
        ocf = [float(v) / 1e9 if v is not None else 0 for v in _series_vals(cd.operating_cashflow_series, 4)]
        fcf = [float(v) / 1e9 if v is not None else 0 for v in _series_vals(cd.free_cashflow_series, 4)]
        years.reverse(); ocf.reverse(); fcf.reverse()

        x = np.arange(len(years))
        w = 0.3
        ax.bar(x - w/2, ocf, w, label="Operating CF", color="#1E90FF", alpha=0.85)
        ax.bar(x + w/2, fcf, w, label="Free CF", color="#2E7D32", alpha=0.85)
        ax.set_xticks(x)
        ax.set_xticklabels(years, fontsize=7)
        ax.set_ylabel("$B", fontsize=8)
        ax.tick_params(axis="y", labelsize=7)
        ax.legend(fontsize=7)
        ax.set_title("Cash Flow Trends", fontsize=9, fontweight="bold",
                      color="#0B1D3A", pad=6)
        ax.grid(axis="y", alpha=0.15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    else:
        ax.text(0.5, 0.5, "Data unavailable", ha="center", va="center",
                fontsize=10, color="#999")
        ax.axis("off")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _render_recommendation_chart(cd: CompanyData) -> io.BytesIO:
    """Horizontal bar chart of analyst recommendations."""
    fig, ax = plt.subplots(figsize=(5, 2.2))

    if cd.recommendations_summary is not None and not cd.recommendations_summary.empty:
        try:
            row = cd.recommendations_summary.iloc[0]
            cats = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
            keys = ["strongBuy", "buy", "hold", "sell", "strongSell"]
            vals = [int(row.get(k, 0)) for k in keys]
            colors = ["#2E7D32", "#66BB6A", "#FFA726", "#EF5350", "#C62828"]

            y = np.arange(len(cats))
            ax.barh(y, vals, color=colors, height=0.6)
            ax.set_yticks(y)
            ax.set_yticklabels(cats, fontsize=7)
            ax.set_xlabel("# Analysts", fontsize=7)
            ax.tick_params(axis="x", labelsize=7)

            for i, v in enumerate(vals):
                if v > 0:
                    ax.text(v + 0.3, i, str(v), va="center", fontsize=7, color="#333")

            ax.set_title("Analyst Recommendations", fontsize=9, fontweight="bold",
                          color="#0B1D3A", pad=6)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.invert_yaxis()
        except Exception:
            ax.text(0.5, 0.5, "Data unavailable", ha="center", va="center",
                    fontsize=10, color="#999")
            ax.axis("off")
    else:
        ax.text(0.5, 0.5, "Analyst data unavailable", ha="center", va="center",
                fontsize=10, color="#999")
        ax.axis("off")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════
# NATIVE PPTX CHART (editable in PowerPoint)
# ══════════════════════════════════════════════════════════════

def _add_ebitda_margin_chart(slide, cd, left, top, width, height):
    """Native PPTX bar chart of EBITDA margins."""
    chart_data = CategoryChartData()
    if cd.ebitda_margin is not None and not cd.ebitda_margin.empty:
        cats = _year_labels(cd.ebitda_margin, 4)
        vals = [float(v) if v is not None else 0 for v in _series_vals(cd.ebitda_margin, 4)]
        cats.reverse(); vals.reverse()
        chart_data.categories = cats
        chart_data.add_series("EBITDA Margin (%)", vals)
    else:
        chart_data.categories = ["N/A"]
        chart_data.add_series("EBITDA Margin (%)", [0])

    frame = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED,
                                    left, top, width, height, chart_data)
    chart = frame.chart
    chart.has_legend = False
    plot = chart.plots[0]
    plot.gap_width = 80
    series = plot.series[0]
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = ACCENT_BLUE
    series.has_data_labels = True
    series.data_labels.font.size = Pt(8)
    series.data_labels.number_format = '0.0"%"'
    series.data_labels.label_position = XL_LABEL_POSITION.OUTSIDE_END
    chart.has_title = True
    chart.chart_title.text_frame.paragraphs[0].text = "EBITDA Margin"
    chart.chart_title.text_frame.paragraphs[0].font.size = Pt(9)
    chart.chart_title.text_frame.paragraphs[0].font.bold = True
    return frame


# ══════════════════════════════════════════════════════════════
# 8 SLIDE BUILDERS
# ══════════════════════════════════════════════════════════════

def _build_slide_1(prs, cd):
    """Slide 1 — Executive Summary."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _slide_header(slide, f"{cd.name}  ({cd.ticker})")

    # Sector / Industry / Exchange badge
    _add_textbox(slide, Inches(0.5), Inches(0.8), Inches(8), Inches(0.25),
                 f"{cd.exchange}  |  {cd.sector}  >  {cd.industry}",
                 font_size=9, color=MED_GRAY)

    # Price line
    chg_color = GREEN if cd.price_change >= 0 else RED
    _add_textbox(slide, Inches(0.5), Inches(1.1), Inches(6), Inches(0.35),
                 f"${cd.current_price:,.2f}   {cd.price_change:+.2f} ({cd.price_change_pct:+.2f}%)"
                 f"   |   Mkt Cap: {format_number(cd.market_cap)}"
                 f"   |   EV: {format_number(cd.enterprise_value)}",
                 font_size=13, bold=True, color=chg_color)

    # Business description (left column, truncated)
    desc = cd.long_business_summary or "Business description not available."
    if len(desc) > 600:
        desc = desc[:597] + "..."
    desc_box = _add_textbox(slide, Inches(0.5), Inches(1.7), Inches(6), Inches(2.2),
                            "Business Overview", font_size=11, bold=True, color=NAVY)
    tf = desc_box.text_frame
    _add_para(tf, desc, font_size=8, color=DARK_GRAY, space_before=Pt(4))

    # Key metrics mini-table (left, below desc)
    metrics_data = [
        ["P/E", f"{cd.trailing_pe:.1f}" if cd.trailing_pe else "N/A",
         "Fwd P/E", f"{cd.forward_pe:.1f}" if cd.forward_pe else "N/A"],
        ["EV/EBITDA", format_multiple(cd.ev_to_ebitda),
         "P/B", f"{cd.price_to_book:.2f}" if cd.price_to_book else "N/A"],
        ["Gross Margin", format_pct(cd.gross_margins),
         "Op. Margin", format_pct(cd.operating_margins)],
        ["ROE", format_pct(cd.return_on_equity),
         "D/E", f"{cd.debt_to_equity / 100:.2f}x" if cd.debt_to_equity else "N/A"],
        ["Revenue Growth", f"{cd.revenue_growth:+.1f}%" if cd.revenue_growth else "N/A",
         "Beta", f"{cd.beta:.2f}" if cd.beta else "N/A"],
        ["Div Yield", format_pct(cd.dividend_yield),
         "52W Range", f"${cd.fifty_two_week_low:,.0f}-${cd.fifty_two_week_high:,.0f}"],
    ]
    _add_styled_table(slide,
                      ["Metric", "Value", "Metric", "Value"],
                      metrics_data,
                      Inches(0.5), Inches(4.1), Inches(6), Inches(2.6),
                      col_widths=[Inches(1.3), Inches(1.2), Inches(1.3), Inches(1.2)])

    # Price chart (right)
    chart_buf = _render_5y_price_chart(cd)
    slide.shapes.add_picture(chart_buf, Inches(6.8), Inches(1.0),
                              Inches(6), Inches(3.5))

    # Executive summary bullets (right, below chart)
    if cd.executive_summary_bullets:
        sum_box = _add_textbox(slide, Inches(6.8), Inches(4.6), Inches(6), Inches(0.25),
                               "Investment Highlights", font_size=10, bold=True, color=NAVY)
        tf = sum_box.text_frame
        for b in cd.executive_summary_bullets[:5]:
            _add_para(tf, f"\u2022  {b}", font_size=8, color=DARK_GRAY, space_before=Pt(3))

    _slide_footer(slide, cd)


def _build_slide_2(prs, cd):
    """Slide 2 — Financial Analysis (Income Statement)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _slide_header(slide, f"Financial Analysis — {cd.name}")

    years = _year_labels(cd.revenue, 4)
    def _fmtv(v): return format_number(v) if v is not None else "N/A"

    rows = [
        ["Revenue"] + [_fmtv(v) for v in _series_vals(cd.revenue, 4)],
        ["Cost of Revenue"] + [_fmtv(v) for v in _series_vals(cd.cost_of_revenue, 4)],
        ["Gross Profit"] + [_fmtv(v) for v in _series_vals(cd.gross_profit, 4)],
        ["Operating Income"] + [_fmtv(v) for v in _series_vals(cd.operating_income, 4)],
        ["EBITDA"] + [_fmtv(v) for v in _series_vals(cd.ebitda, 4)],
        ["Net Income"] + [_fmtv(v) for v in _series_vals(cd.net_income, 4)],
        ["Basic EPS"] + [f"${float(v):.2f}" if v is not None else "N/A"
                         for v in _series_vals(cd.eps_basic, 4)],
    ]
    _add_styled_table(slide, ["($ in millions)"] + years, rows,
                      Inches(0.5), Inches(1.0), Inches(6.2), Inches(3.2),
                      col_widths=[Inches(1.5)] + [Inches(1.15)] * 4)

    # Margin summary box
    _add_textbox(slide, Inches(0.5), Inches(4.4), Inches(6.2), Inches(0.25),
                 "Profitability Ratios (TTM)", font_size=10, bold=True, color=NAVY)
    ratios_text = (
        f"Gross Margin: {format_pct(cd.gross_margins)}    "
        f"Operating Margin: {format_pct(cd.operating_margins)}    "
        f"Net Margin: {format_pct(cd.profit_margins)}    "
        f"ROE: {format_pct(cd.return_on_equity)}    "
        f"ROA: {format_pct(cd.return_on_assets)}"
    )
    _add_textbox(slide, Inches(0.5), Inches(4.7), Inches(6.2), Inches(0.5),
                 ratios_text, font_size=8, color=DARK_GRAY)

    # Revenue & margin chart (right)
    chart_buf = _render_revenue_margin_chart(cd)
    slide.shapes.add_picture(chart_buf, Inches(7.0), Inches(1.0),
                              Inches(5.8), Inches(3.0))

    # EBITDA margin native chart (right, below)
    _add_ebitda_margin_chart(slide, cd,
                             Inches(7.0), Inches(4.2), Inches(5.8), Inches(2.5))

    _slide_footer(slide, cd)


def _build_slide_3(prs, cd):
    """Slide 3 — Balance Sheet & Cash Flow."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _slide_header(slide, f"Balance Sheet & Cash Flow — {cd.name}")

    years = _year_labels(cd.total_assets, 4)
    def _fmtv(v): return format_number(v) if v is not None else "N/A"

    # Balance Sheet table
    bs_rows = [
        ["Total Assets"] + [_fmtv(v) for v in _series_vals(cd.total_assets, 4)],
        ["Total Liabilities"] + [_fmtv(v) for v in _series_vals(cd.total_liabilities, 4)],
        ["Stockholders' Equity"] + [_fmtv(v) for v in _series_vals(cd.total_equity, 4)],
        ["Total Debt"] + [_fmtv(v) for v in _series_vals(cd.total_debt, 4)],
        ["Cash & Equivalents"] + [_fmtv(v) for v in _series_vals(cd.cash_and_equivalents, 4)],
    ]
    _add_textbox(slide, Inches(0.5), Inches(0.9), Inches(6.2), Inches(0.25),
                 "Balance Sheet Highlights", font_size=10, bold=True, color=NAVY)
    _add_styled_table(slide, ["($ in millions)"] + years, bs_rows,
                      Inches(0.5), Inches(1.2), Inches(6.2), Inches(2.2),
                      col_widths=[Inches(1.5)] + [Inches(1.15)] * 4)

    # Cash Flow table
    cf_years = _year_labels(cd.operating_cashflow_series, 4)
    cf_rows = [
        ["Operating Cash Flow"] + [_fmtv(v) for v in _series_vals(cd.operating_cashflow_series, 4)],
        ["Capital Expenditure"] + [_fmtv(v) for v in _series_vals(cd.capital_expenditure, 4)],
        ["Free Cash Flow"] + [_fmtv(v) for v in _series_vals(cd.free_cashflow_series, 4)],
        ["Dividends Paid"] + [_fmtv(v) for v in _series_vals(cd.dividends_paid, 4)],
    ]
    _add_textbox(slide, Inches(0.5), Inches(3.7), Inches(6.2), Inches(0.25),
                 "Cash Flow Summary", font_size=10, bold=True, color=NAVY)
    _add_styled_table(slide, ["($ in millions)"] + cf_years, cf_rows,
                      Inches(0.5), Inches(4.0), Inches(6.2), Inches(1.8),
                      col_widths=[Inches(1.5)] + [Inches(1.15)] * 4)

    # Leverage ratios
    _add_textbox(slide, Inches(0.5), Inches(6.0), Inches(6.2), Inches(0.25),
                 f"D/E: {cd.debt_to_equity / 100:.2f}x" if cd.debt_to_equity else "D/E: N/A"
                 + f"     Current Ratio: {cd.current_ratio:.2f}" if cd.current_ratio else ""
                 + f"     Net Cash: {format_number(cd.total_cash)}",
                 font_size=8, color=DARK_GRAY)

    # Cash flow chart (right)
    chart_buf = _render_cashflow_chart(cd)
    slide.shapes.add_picture(chart_buf, Inches(7.0), Inches(1.0),
                              Inches(5.8), Inches(2.8))

    # Supplementary: Net Debt callout
    net_debt = None
    if cd.total_debt is not None and cd.cash_and_equivalents is not None:
        try:
            net_debt = float(cd.total_debt.iloc[0]) - float(cd.cash_and_equivalents.iloc[0])
        except Exception:
            pass
    if net_debt is not None:
        _add_textbox(slide, Inches(7.0), Inches(4.0), Inches(5.8), Inches(0.3),
                     f"Net Debt: {format_number(net_debt)}   |   "
                     f"Total Cash: {format_number(cd.total_cash)}   |   "
                     f"Total Debt: {format_number(cd.total_debt_info)}",
                     font_size=9, bold=True, color=NAVY)

    _slide_footer(slide, cd)


def _build_slide_4(prs, cd):
    """Slide 4 — Valuation & Analyst Sentiment."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _slide_header(slide, f"Valuation & Analyst Sentiment — {cd.name}")

    # Valuation table
    val_rows = [
        ["Trailing P/E", f"{cd.trailing_pe:.1f}" if cd.trailing_pe else "N/A"],
        ["Forward P/E", f"{cd.forward_pe:.1f}" if cd.forward_pe else "N/A"],
        ["PEG Ratio", f"{cd.peg_ratio:.2f}" if cd.peg_ratio else "N/A"],
        ["P/S (TTM)", f"{cd.price_to_sales:.2f}" if cd.price_to_sales else "N/A"],
        ["Price/Book", f"{cd.price_to_book:.2f}" if cd.price_to_book else "N/A"],
        ["EV/EBITDA", format_multiple(cd.ev_to_ebitda)],
        ["EV/Revenue", format_multiple(cd.ev_to_revenue)],
    ]
    _add_textbox(slide, Inches(0.5), Inches(0.9), Inches(4), Inches(0.25),
                 "Valuation Multiples", font_size=10, bold=True, color=NAVY)
    _add_styled_table(slide, ["Multiple", "Value"], val_rows,
                      Inches(0.5), Inches(1.2), Inches(4), Inches(3.0),
                      col_widths=[Inches(2), Inches(2)])

    # Price targets
    if cd.analyst_price_targets:
        _add_textbox(slide, Inches(0.5), Inches(4.5), Inches(4), Inches(0.25),
                     "Analyst Price Targets", font_size=10, bold=True, color=NAVY)
        pt = cd.analyst_price_targets
        pt_rows = [
            ["Current Price", f"${cd.current_price:,.2f}"],
            ["Mean Target", f"${pt.get('mean', 0):,.2f}" if pt.get("mean") else "N/A"],
            ["Median Target", f"${pt.get('median', 0):,.2f}" if pt.get("median") else "N/A"],
            ["Low Target", f"${pt.get('low', 0):,.2f}" if pt.get("low") else "N/A"],
            ["High Target", f"${pt.get('high', 0):,.2f}" if pt.get("high") else "N/A"],
        ]
        # Upside/downside
        if pt.get("mean") and cd.current_price:
            upside = (pt["mean"] - cd.current_price) / cd.current_price * 100
            pt_rows.append(["Implied Upside", f"{upside:+.1f}%"])
        _add_styled_table(slide, ["", "Price"], pt_rows,
                          Inches(0.5), Inches(4.8), Inches(4), Inches(2.2),
                          col_widths=[Inches(2), Inches(2)])

    # Recommendation chart (right)
    chart_buf = _render_recommendation_chart(cd)
    slide.shapes.add_picture(chart_buf, Inches(5.0), Inches(1.0),
                              Inches(5.5), Inches(2.5))

    # Earnings surprise (right, below chart)
    if cd.earnings_dates is not None and not cd.earnings_dates.empty:
        _add_textbox(slide, Inches(5.0), Inches(3.7), Inches(7.5), Inches(0.25),
                     "Recent Earnings", font_size=10, bold=True, color=NAVY)
        try:
            ed = cd.earnings_dates.head(6).copy()
            earn_headers = list(ed.columns[:4])
            earn_rows = []
            for _, row in ed.iterrows():
                earn_rows.append([str(v)[:12] for v in row.values[:4]])
            if earn_rows:
                _add_styled_table(slide, earn_headers, earn_rows,
                                  Inches(5.0), Inches(4.0), Inches(7.5), Inches(2.8))
        except Exception:
            pass

    _slide_footer(slide, cd)


def _build_slide_5(prs, cd):
    """Slide 5 — Ownership & Insider Activity."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _slide_header(slide, f"Ownership & Insider Activity — {cd.name}")

    # Major holders summary
    _add_textbox(slide, Inches(0.5), Inches(0.9), Inches(5.5), Inches(0.25),
                 "Ownership Breakdown", font_size=10, bold=True, color=NAVY)
    if cd.major_holders is not None and not cd.major_holders.empty:
        mh_rows = []
        for _, row in cd.major_holders.iterrows():
            vals = [str(v) for v in row.values]
            mh_rows.append(vals)
        headers = list(cd.major_holders.columns) if len(cd.major_holders.columns) > 1 else ["Metric", "Value"]
        _add_styled_table(slide, headers, mh_rows,
                          Inches(0.5), Inches(1.2), Inches(5.5), Inches(1.5))
    else:
        _add_textbox(slide, Inches(0.5), Inches(1.2), Inches(5.5), Inches(0.3),
                     "Major holders data not available", font_size=9, color=MED_GRAY)

    # Institutional holders (right)
    _add_textbox(slide, Inches(6.5), Inches(0.9), Inches(6.3), Inches(0.25),
                 "Top Institutional Holders", font_size=10, bold=True, color=NAVY)
    if cd.institutional_holders is not None and not cd.institutional_holders.empty:
        ih = cd.institutional_holders.head(10)
        ih_headers = ["Holder", "Shares", "% Out", "Value"]
        ih_rows = []
        for _, row in ih.iterrows():
            holder = str(row.get("Holder", ""))[:30]
            shares = format_number(row.get("Shares", 0), prefix="", decimals=0)
            pct = f"{row.get('% Out', 0) * 100:.2f}%" if row.get("% Out") else "N/A"
            value = format_number(row.get("Value", 0))
            ih_rows.append([holder, shares, pct, value])
        _add_styled_table(slide, ih_headers, ih_rows,
                          Inches(6.5), Inches(1.2), Inches(6.3), Inches(3.0),
                          col_widths=[Inches(2.2), Inches(1.2), Inches(1.0), Inches(1.2)])

    # Insider transactions (bottom)
    _add_textbox(slide, Inches(0.5), Inches(4.5), Inches(12.3), Inches(0.25),
                 "Recent Insider Transactions", font_size=10, bold=True, color=NAVY)
    if cd.insider_transactions is not None and not cd.insider_transactions.empty:
        it = cd.insider_transactions.head(8)
        it_headers = list(it.columns[:5])
        it_rows = []
        for _, row in it.iterrows():
            it_rows.append([str(v)[:25] for v in row.values[:5]])
        _add_styled_table(slide, it_headers, it_rows,
                          Inches(0.5), Inches(4.8), Inches(12.3), Inches(2.0))
    else:
        _add_textbox(slide, Inches(0.5), Inches(4.8), Inches(12), Inches(0.3),
                     "Insider transaction data not available", font_size=9, color=MED_GRAY)

    _slide_footer(slide, cd)


def _build_slide_6(prs, cd):
    """Slide 6 — M&A History & Strategic Transactions."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _slide_header(slide, f"M&A History — {cd.name}")

    if cd.ma_deals:
        # Show deal count and source
        source_label = ""
        if cd.ma_source:
            source_label = f"   (Source: Wikipedia — {len(cd.ma_deals)} deals on record)"
        _add_textbox(slide, Inches(0.5), Inches(0.9), Inches(12), Inches(0.25),
                     f"Acquisition History{source_label}",
                     font_size=10, bold=True, color=NAVY)

        # Build deal table — show up to 15 most recent deals
        shown = cd.ma_deals[:15]
        deal_rows = []
        for d in shown:
            date = d.get("date", "")[:20]
            company = d.get("company", "")[:30]
            business = d.get("business", "")[:35]
            country = d.get("country", "")[:15]
            value = d.get("value", "Undisclosed")[:20]
            deal_rows.append([date, company, business, country, value])

        _add_styled_table(
            slide,
            ["Date", "Target", "Business", "Country", "Value (USD)"],
            deal_rows,
            Inches(0.5), Inches(1.2), Inches(12.3), Inches(5.0),
            col_widths=[Inches(1.8), Inches(3.0), Inches(3.5), Inches(1.5), Inches(2.0)],
            num_cols_right_align=4,
        )

        if len(cd.ma_deals) > 15:
            _add_textbox(slide, Inches(0.5), Inches(6.3), Inches(12), Inches(0.3),
                         f"Showing 15 of {len(cd.ma_deals)} acquisitions. Full list available on Wikipedia.",
                         font_size=7, color=MED_GRAY)

    else:
        # No scraped deals — show ma_history text (LLM-generated or fallback)
        _add_textbox(slide, Inches(0.5), Inches(0.9), Inches(12), Inches(0.25),
                     "Mergers, Acquisitions & Strategic Transactions",
                     font_size=10, bold=True, color=NAVY)

        ma_text = cd.ma_history or "No public M&A history found for this company."
        clean_text = ma_text.replace("**", "").replace("*", "")

        content_box = _add_textbox(slide, Inches(0.5), Inches(1.3), Inches(12), Inches(5.0),
                                   "", font_size=9, color=DARK_GRAY)
        tf = content_box.text_frame
        for line in clean_text.split("\n"):
            line = line.strip()
            if not line:
                _add_para(tf, "", font_size=4)
            else:
                _add_para(tf, line, font_size=8, color=DARK_GRAY, space_before=Pt(2))

    _slide_footer(slide, cd)


def _build_slide_7(prs, cd):
    """Slide 7 — Management & Governance."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _slide_header(slide, f"Management & Governance — {cd.name}")

    # Executives table
    _add_textbox(slide, Inches(0.5), Inches(0.9), Inches(6), Inches(0.25),
                 "Key Executives", font_size=10, bold=True, color=NAVY)
    if cd.officers:
        exec_rows = []
        for o in cd.officers[:8]:
            name = o.get("name", "N/A")
            title = o.get("title", "N/A")
            age = str(o.get("age", "")) if o.get("age") else ""
            pay = format_number(o.get("totalPay", None)) if o.get("totalPay") else ""
            exec_rows.append([name, title, age, pay])
        _add_styled_table(slide, ["Name", "Title", "Age", "Compensation"], exec_rows,
                          Inches(0.5), Inches(1.2), Inches(6.2), Inches(3.0),
                          col_widths=[Inches(1.8), Inches(2.2), Inches(0.6), Inches(1.2)])
    else:
        _add_textbox(slide, Inches(0.5), Inches(1.2), Inches(6), Inches(0.3),
                     "Executive data not available", font_size=9, color=MED_GRAY)

    # Management sentiment (right)
    if cd.mgmt_sentiment:
        _add_textbox(slide, Inches(7.0), Inches(0.9), Inches(5.8), Inches(0.25),
                     "Management Assessment", font_size=10, bold=True, color=NAVY)
        sent_box = _add_textbox(slide, Inches(7.0), Inches(1.2), Inches(5.8), Inches(3.0),
                                "", font_size=9, color=DARK_GRAY)
        tf = sent_box.text_frame
        for line in cd.mgmt_sentiment.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                line = line[2:]
            if line:
                _add_para(tf, f"\u2022  {line}", font_size=8, color=DARK_GRAY, space_before=Pt(4))

    # ESG Scores (bottom)
    _add_rect(slide, Inches(0.5), Inches(4.5), Inches(12.3), Inches(0.03), GOLD)
    _add_textbox(slide, Inches(0.5), Inches(4.7), Inches(12), Inches(0.25),
                 "ESG & Sustainability", font_size=10, bold=True, color=NAVY)
    if cd.esg_scores is not None and not cd.esg_scores.empty:
        esg_text_parts = []
        for key in ["totalEsg", "environmentScore", "socialScore", "governanceScore"]:
            if key in cd.esg_scores.index:
                val = cd.esg_scores.loc[key]
                if hasattr(val, "values"):
                    val = val.values[0]
                label = key.replace("Score", "").replace("total", "Total ")
                esg_text_parts.append(f"{label}: {val}")
        esg_text = "     ".join(esg_text_parts) if esg_text_parts else "ESG data available — see detail in appendix"
        _add_textbox(slide, Inches(0.5), Inches(5.0), Inches(12), Inches(0.4),
                     esg_text, font_size=9, color=DARK_GRAY)
    else:
        _add_textbox(slide, Inches(0.5), Inches(5.0), Inches(12), Inches(0.3),
                     "ESG data not available for this company", font_size=9, color=MED_GRAY)

    # Company info footer
    info_parts = []
    if cd.city:
        hq = f"{cd.city}"
        if cd.state:
            hq += f", {cd.state}"
        if cd.country:
            hq += f", {cd.country}"
        info_parts.append(f"HQ: {hq}")
    if cd.full_time_employees:
        info_parts.append(f"Employees: {cd.full_time_employees:,}")
    if cd.website:
        info_parts.append(f"Web: {cd.website}")
    if info_parts:
        _add_textbox(slide, Inches(0.5), Inches(5.6), Inches(12), Inches(0.4),
                     "   |   ".join(info_parts), font_size=8, color=MED_GRAY)

    _slide_footer(slide, cd)


def _build_slide_8(prs, cd):
    """Slide 8 — News & Market Context."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _slide_header(slide, f"News & Market Context — {cd.name}")

    # News (left)
    _add_textbox(slide, Inches(0.5), Inches(0.9), Inches(6.2), Inches(0.25),
                 "Recent News & Events", font_size=10, bold=True, color=NAVY)
    news_box = _add_textbox(slide, Inches(0.5), Inches(1.2), Inches(6.2), Inches(3.0),
                            "", font_size=8, color=DARK_GRAY)
    tf = news_box.text_frame
    if cd.news:
        for n in cd.news[:10]:
            title = n.get("title", "")
            pub = n.get("publisher", "")
            _add_para(tf, f"\u2022  {title}  ({pub})",
                      font_size=8, color=DARK_GRAY, space_before=Pt(4))
    else:
        _add_para(tf, "No recent news available.", font_size=9, color=MED_GRAY)

    # Industry Analysis (right top)
    _add_textbox(slide, Inches(7.0), Inches(0.9), Inches(5.8), Inches(0.25),
                 "Industry Analysis", font_size=10, bold=True, color=NAVY)
    ind_box = _add_textbox(slide, Inches(7.0), Inches(1.2), Inches(5.8), Inches(2.2),
                           "", font_size=8, color=DARK_GRAY)
    tf2 = ind_box.text_frame
    if cd.industry_analysis:
        for line in cd.industry_analysis.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                line = line[2:]
            if line:
                _add_para(tf2, f"\u2022  {line}", font_size=8, color=DARK_GRAY, space_before=Pt(3))

    # Divider
    _add_rect(slide, Inches(0.5), Inches(4.4), Inches(12.3), Inches(0.03), GOLD)

    # Risk Factors (full width, bottom)
    _add_textbox(slide, Inches(0.5), Inches(4.6), Inches(12), Inches(0.25),
                 "Key Risk Factors", font_size=10, bold=True, color=NAVY)
    risk_box = _add_textbox(slide, Inches(0.5), Inches(4.9), Inches(12), Inches(1.8),
                            "", font_size=8, color=DARK_GRAY)
    tf3 = risk_box.text_frame
    if cd.risk_factors:
        for line in cd.risk_factors.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                line = line[2:]
            if line:
                _add_para(tf3, f"\u2022  {line}", font_size=8, color=DARK_GRAY, space_before=Pt(3))

    _slide_footer(slide, cd)


# ══════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════

def generate_presentation(cd: CompanyData, template_path: str = "assets/template.pptx") -> io.BytesIO:
    """Build the 8-slide M&A profile and return as an in-memory BytesIO buffer."""
    prs = Presentation(template_path)
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    _build_slide_1(prs, cd)   # Executive Summary
    _build_slide_2(prs, cd)   # Financial Analysis
    _build_slide_3(prs, cd)   # Balance Sheet & Cash Flow
    _build_slide_4(prs, cd)   # Valuation & Analyst Sentiment
    _build_slide_5(prs, cd)   # Ownership & Insider Activity
    _build_slide_6(prs, cd)   # M&A History
    _build_slide_7(prs, cd)   # Management & Governance
    _build_slide_8(prs, cd)   # News & Market Context

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf
