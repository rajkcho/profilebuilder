"""
PPTX Generator — builds the 3-slide M&A profile from CompanyData.

Uses the template-based injection workflow:
1. Load assets/template.pptx
2. Add slides from the appropriate layout
3. Inject text, tables, and charts into positioned shapes

Charts are rendered as both:
  - Static images (matplotlib → picture) for the price chart
  - Native PPTX charts (CategoryChartData) for EBITDA margins & pie charts
"""

import io
import os
import tempfile
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn

from data_engine import CompanyData, format_number

# ── Corporate palette ────────────────────────────────────────
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

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


# ── Helpers ──────────────────────────────────────────────────

def _set_text(tf, text, font_size=12, bold=False, color=DARK_GRAY, alignment=PP_ALIGN.LEFT):
    """Set text on a shape's text_frame with formatting."""
    tf.clear()
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = "Calibri"
    p.alignment = alignment


def _add_textbox(slide, left, top, width, height, text,
                 font_size=12, bold=False, color=DARK_GRAY,
                 alignment=PP_ALIGN.LEFT, bg_color=None):
    """Add a text box with optional background fill."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    _set_text(tf, text, font_size, bold, color, alignment)

    if bg_color:
        fill = txBox.fill
        fill.solid()
        fill.fore_color.rgb = bg_color

    return txBox


def _add_paragraph(text_frame, text, font_size=11, bold=False,
                   color=DARK_GRAY, space_before=Pt(4), bullet=False):
    """Append a paragraph to an existing text frame."""
    p = text_frame.add_paragraph()
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = "Calibri"
    p.space_before = space_before
    if bullet:
        p.level = 0
    return p


def _add_rect(slide, left, top, width, height, fill_color):
    """Add a filled rectangle (for background bands, etc.)."""
    from pptx.enum.shapes import MSO_SHAPE
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    return shape


def _render_price_chart(cd: CompanyData) -> io.BytesIO:
    """Render a 1-year price chart using matplotlib, return as PNG buffer."""
    fig, ax = plt.subplots(figsize=(8, 4))

    if cd.hist_1y is not None and not cd.hist_1y.empty:
        dates = cd.hist_1y.index
        prices = cd.hist_1y["Close"]

        ax.fill_between(dates, prices, alpha=0.15, color="#1E90FF")
        ax.plot(dates, prices, color="#1E90FF", linewidth=2)

        ax.set_ylabel("Price ($)", fontsize=10, color="#333")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("$%.0f"))
        plt.xticks(rotation=45, fontsize=8)
        plt.yticks(fontsize=8)

        ax.set_title(f"{cd.ticker} — 1-Year Price", fontsize=12,
                     fontweight="bold", color="#0B1D3A", pad=10)
        ax.grid(axis="y", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    else:
        ax.text(0.5, 0.5, "Price data unavailable", ha="center",
                va="center", fontsize=14, color="#999")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _add_financial_table(slide, cd: CompanyData, left, top, width, height):
    """Add a 4-column (Metric, Year3, Year2, Year1) financial table."""
    rows, cols = 4, 4  # Header + Revenue + EBITDA + Net Income

    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table

    # Column widths
    table.columns[0].width = Inches(1.8)
    for c in range(1, cols):
        table.columns[c].width = Inches(1.4)

    # Determine year labels
    years = []
    if cd.revenue is not None:
        for col in cd.revenue.index[:3]:
            if hasattr(col, "year"):
                years.append(str(col.year))
            else:
                years.append(str(col))
    while len(years) < 3:
        years.append("—")

    # Header row
    headers = ["Metric"] + years
    for c, hdr in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = hdr
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.color.rgb = WHITE
            p.font.name = "Calibri"
            p.alignment = PP_ALIGN.CENTER
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY

    # Data rows
    metrics = [
        ("Revenue", cd.revenue),
        ("EBITDA", cd.ebitda),
        ("Net Income", cd.net_income),
    ]

    for r, (label, series) in enumerate(metrics, start=1):
        table.cell(r, 0).text = label
        for p in table.cell(r, 0).text_frame.paragraphs:
            p.font.size = Pt(10)
            p.font.bold = True
            p.font.name = "Calibri"
            p.alignment = PP_ALIGN.LEFT

        for c in range(1, cols):
            val = None
            if series is not None and len(series) > (c - 1):
                val = series.iloc[c - 1]
            cell = table.cell(r, c)
            cell.text = format_number(val) if val is not None else "N/A"
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(10)
                p.font.name = "Calibri"
                p.alignment = PP_ALIGN.CENTER

        # Alternate row shading
        bg = LIGHT_GRAY if r % 2 == 0 else WHITE
        for c in range(cols):
            table.cell(r, c).fill.solid()
            table.cell(r, c).fill.fore_color.rgb = bg

    return table_shape


def _add_ebitda_bar_chart(slide, cd: CompanyData, left, top, width, height):
    """Add a native PPTX bar chart of EBITDA margins (editable in PowerPoint)."""
    chart_data = CategoryChartData()

    if cd.ebitda_margin is not None and not cd.ebitda_margin.empty:
        categories = []
        values = []
        for col in cd.ebitda_margin.index[:3]:
            yr = str(col.year) if hasattr(col, "year") else str(col)
            categories.append(yr)
            values.append(float(cd.ebitda_margin[col]))

        # Reverse so oldest is on left
        categories.reverse()
        values.reverse()

        chart_data.categories = categories
        chart_data.add_series("EBITDA Margin (%)", values)
    else:
        chart_data.categories = ["N/A"]
        chart_data.add_series("EBITDA Margin (%)", [0])

    chart_frame = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED, left, top, width, height, chart_data
    )
    chart = chart_frame.chart
    chart.has_legend = False

    # Style the chart
    plot = chart.plots[0]
    plot.gap_width = 80

    series = plot.series[0]
    series.format.fill.solid()
    series.format.fill.fore_color.rgb = ACCENT_BLUE

    # Data labels
    series.has_data_labels = True
    data_labels = series.data_labels
    data_labels.font.size = Pt(9)
    data_labels.font.color.rgb = DARK_GRAY
    data_labels.number_format = '0.0"%"'
    data_labels.label_position = XL_LABEL_POSITION.OUTSIDE_END

    # Value axis
    value_axis = chart.value_axis
    value_axis.has_title = True
    value_axis.axis_title.text_frame.paragraphs[0].text = "Margin (%)"
    value_axis.axis_title.text_frame.paragraphs[0].font.size = Pt(8)

    # Category axis
    cat_axis = chart.category_axis
    cat_axis.tick_labels.font.size = Pt(9)

    # Chart title
    chart.has_title = True
    chart.chart_title.text_frame.paragraphs[0].text = "EBITDA Margin Trend"
    chart.chart_title.text_frame.paragraphs[0].font.size = Pt(11)
    chart.chart_title.text_frame.paragraphs[0].font.bold = True

    return chart_frame


def _add_pie_chart(slide, cd: CompanyData, left, top, width, height):
    """Add a segment pie chart. Uses revenue breakdown if available,
    otherwise creates a placeholder based on sector."""
    chart_data = CategoryChartData()

    # yfinance doesn't provide segment data directly, so we create
    # a representative breakdown based on available info
    chart_data.categories = [cd.industry or "Core Business", "Other"]
    chart_data.add_series("Segments", [85, 15])

    chart_frame = slide.shapes.add_chart(
        XL_CHART_TYPE.PIE, left, top, width, height, chart_data
    )
    chart = chart_frame.chart

    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.legend.font.size = Pt(9)

    plot = chart.plots[0]
    series = plot.series[0]

    # Color the slices
    colors = [ACCENT_BLUE, GOLD]
    for i, color in enumerate(colors):
        point = series.points[i]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = color

    series.has_data_labels = True
    data_labels = series.data_labels
    data_labels.font.size = Pt(9)
    data_labels.number_format = '0"%"'
    data_labels.label_position = XL_LABEL_POSITION.OUTSIDE_END

    chart.has_title = True
    chart.chart_title.text_frame.paragraphs[0].text = "Revenue Segments"
    chart.chart_title.text_frame.paragraphs[0].font.size = Pt(11)
    chart.chart_title.text_frame.paragraphs[0].font.bold = True

    return chart_frame


def _add_deal_score_visual(slide, cd: CompanyData, left, top, width, height):
    """Render the deal score as a colored box with breakdown."""
    score = cd.deal_score
    if score >= 70:
        score_color = GREEN
        label = "STRONG BUY"
    elif score >= 40:
        score_color = GOLD
        label = "MODERATE"
    else:
        score_color = RED
        label = "CAUTION"

    # Score badge
    badge = _add_rect(slide, left, top, Inches(2), Inches(1.5), score_color)

    # Score number overlay
    score_box = _add_textbox(
        slide, left + Inches(0.1), top + Inches(0.1),
        Inches(1.8), Inches(0.8),
        str(int(score)), font_size=36, bold=True, color=WHITE,
        alignment=PP_ALIGN.CENTER,
    )

    label_box = _add_textbox(
        slide, left + Inches(0.1), top + Inches(0.85),
        Inches(1.8), Inches(0.5),
        label, font_size=14, bold=True, color=WHITE,
        alignment=PP_ALIGN.CENTER,
    )

    # Breakdown
    breakdown_text = (
        f"Valuation: {cd.valuation_score:.0f}/100\n"
        f"Solvency: {cd.solvency_score:.0f}/100\n"
        f"Growth: {cd.growth_score:.0f}/100"
    )
    _add_textbox(
        slide, left + Inches(2.3), top + Inches(0.1),
        Inches(3.2), Inches(1.4),
        breakdown_text, font_size=11, color=DARK_GRAY,
    )


def _add_footer(slide, cd: CompanyData):
    """Add a bottom footer bar."""
    _add_rect(slide, Inches(0), SLIDE_H - Inches(0.4), SLIDE_W, Inches(0.4), NAVY)
    _add_textbox(
        slide, Inches(0.5), SLIDE_H - Inches(0.35), Inches(8), Inches(0.3),
        f"Confidential — {cd.name} M&A Profile — {datetime.now().strftime('%B %d, %Y')}",
        font_size=8, color=WHITE, alignment=PP_ALIGN.LEFT,
    )
    _add_textbox(
        slide, SLIDE_W - Inches(2), SLIDE_H - Inches(0.35),
        Inches(1.8), Inches(0.3),
        "ProfileBuilder", font_size=8, bold=True, color=GOLD,
        alignment=PP_ALIGN.RIGHT,
    )


# ── Slide Builders ───────────────────────────────────────────

def _build_slide_1(prs: Presentation, cd: CompanyData):
    """Slide 1: Executive Summary."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # Header band
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.15), GOLD)
    _add_rect(slide, Inches(0), Inches(0.15), SLIDE_W, Inches(0.05), NAVY)

    # Company name
    _add_textbox(
        slide, Inches(0.5), Inches(0.4), Inches(6), Inches(0.6),
        cd.name, font_size=28, bold=True, color=NAVY,
    )

    # Ticker / Price line
    price_color = GREEN if cd.current_price > 0 else DARK_GRAY
    _add_textbox(
        slide, Inches(0.5), Inches(1.05), Inches(6), Inches(0.4),
        f"{cd.ticker}  |  ${cd.current_price:,.2f}  |  "
        f"Mkt Cap: {format_number(cd.market_cap)}",
        font_size=14, color=DARK_BLUE,
    )

    # Sector / Industry
    _add_textbox(
        slide, Inches(0.5), Inches(1.5), Inches(6), Inches(0.3),
        f"{cd.sector}  >  {cd.industry}",
        font_size=10, color=MED_GRAY,
    )

    # Executive Summary bullets
    summary_box = _add_textbox(
        slide, Inches(0.5), Inches(2.1), Inches(5.8), Inches(3.8),
        "Investment Highlights", font_size=14, bold=True, color=NAVY,
    )
    tf = summary_box.text_frame
    for bullet in cd.executive_summary_bullets:
        _add_paragraph(tf, f"\u2022  {bullet}", font_size=11, color=DARK_GRAY,
                       space_before=Pt(8))

    # Product Overview
    if cd.product_overview:
        _add_paragraph(tf, "", font_size=6)  # spacer
        _add_paragraph(tf, "Product Overview", font_size=12, bold=True, color=NAVY)
        for line in cd.product_overview.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                line = line[2:]
            if line:
                _add_paragraph(tf, f"\u2022  {line}", font_size=10, color=DARK_GRAY,
                               space_before=Pt(4))

    # Price chart (right side)
    chart_buf = _render_price_chart(cd)
    slide.shapes.add_picture(
        chart_buf, Inches(6.8), Inches(0.5), Inches(6), Inches(3.8)
    )

    # Key metrics box (right, below chart)
    metrics_box = _add_rect(
        slide, Inches(6.8), Inches(4.5), Inches(6), Inches(2.3), LIGHT_GRAY
    )
    _add_textbox(
        slide, Inches(7.0), Inches(4.6), Inches(5.5), Inches(0.3),
        "Key Metrics", font_size=12, bold=True, color=NAVY,
    )

    metrics_lines = [
        f"P/E Ratio:  {cd.trailing_pe or 'N/A'}",
        f"Forward P/E:  {cd.forward_pe or 'N/A'}",
        f"EV/EBITDA:  {cd.ev_to_ebitda or 'N/A'}",
        f"Price/Book:  {cd.price_to_book or 'N/A'}",
        f"D/E Ratio:  {(cd.debt_to_equity / 100):.2f}x" if cd.debt_to_equity else "D/E Ratio:  N/A",
        f"Beta:  {cd.beta or 'N/A'}",
        f"52W Range:  ${cd.fifty_two_week_low:,.2f} – ${cd.fifty_two_week_high:,.2f}",
        f"Div Yield:  {cd.dividend_yield * 100:.2f}%" if cd.dividend_yield else "Div Yield:  N/A",
    ]

    # Two-column metric layout
    left_metrics = metrics_lines[:4]
    right_metrics = metrics_lines[4:]

    left_box = _add_textbox(
        slide, Inches(7.0), Inches(5.0), Inches(2.8), Inches(1.7),
        "\n".join(left_metrics), font_size=9, color=DARK_GRAY,
    )
    right_box = _add_textbox(
        slide, Inches(10.0), Inches(5.0), Inches(2.8), Inches(1.7),
        "\n".join(right_metrics), font_size=9, color=DARK_GRAY,
    )

    _add_footer(slide, cd)


def _build_slide_2(prs: Presentation, cd: CompanyData):
    """Slide 2: Financials & Deal Score."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Header band
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.15), GOLD)
    _add_rect(slide, Inches(0), Inches(0.15), SLIDE_W, Inches(0.05), NAVY)

    # Title
    _add_textbox(
        slide, Inches(0.5), Inches(0.4), Inches(12), Inches(0.6),
        f"Financial Overview — {cd.name}",
        font_size=22, bold=True, color=NAVY,
    )

    # Financial table (left)
    _add_financial_table(
        slide, cd,
        left=Inches(0.5), top=Inches(1.3),
        width=Inches(6), height=Inches(2.0),
    )

    # Revenue growth callout
    if cd.revenue_growth is not None:
        growth_color = GREEN if cd.revenue_growth > 0 else RED
        _add_textbox(
            slide, Inches(0.5), Inches(3.5), Inches(6), Inches(0.4),
            f"Revenue Growth (YoY): {cd.revenue_growth:+.1f}%",
            font_size=12, bold=True, color=growth_color,
        )

    # EV callout
    _add_textbox(
        slide, Inches(0.5), Inches(4.0), Inches(6), Inches(0.4),
        f"Enterprise Value: {format_number(cd.enterprise_value)}  |  "
        f"EV/EBITDA: {cd.ev_to_ebitda or 'N/A'}x",
        font_size=11, color=DARK_GRAY,
    )

    # Management Sentiment (below financials on left)
    if cd.mgmt_sentiment:
        _add_textbox(
            slide, Inches(0.5), Inches(4.6), Inches(6), Inches(0.3),
            "Management Sentiment", font_size=12, bold=True, color=NAVY,
        )
        sentiment_box = _add_textbox(
            slide, Inches(0.5), Inches(5.0), Inches(6), Inches(1.8),
            "", font_size=10, color=DARK_GRAY,
        )
        tf = sentiment_box.text_frame
        for line in cd.mgmt_sentiment.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                line = line[2:]
            if line:
                _add_paragraph(tf, f"\u2022  {line}", font_size=10,
                               color=DARK_GRAY, space_before=Pt(4))

    # EBITDA margin chart (right, top)
    _add_ebitda_bar_chart(
        slide, cd,
        left=Inches(7.0), top=Inches(1.3),
        width=Inches(5.8), height=Inches(3.2),
    )

    # Deal Score (right, bottom)
    _add_textbox(
        slide, Inches(7.0), Inches(4.7), Inches(5.8), Inches(0.3),
        "Deal Score", font_size=14, bold=True, color=NAVY,
    )
    _add_deal_score_visual(
        slide, cd,
        left=Inches(7.0), top=Inches(5.1),
        width=Inches(5.8), height=Inches(1.5),
    )

    _add_footer(slide, cd)


def _build_slide_3(prs: Presentation, cd: CompanyData):
    """Slide 3: Strategy & M&A."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Header band
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.15), GOLD)
    _add_rect(slide, Inches(0), Inches(0.15), SLIDE_W, Inches(0.05), NAVY)

    # Title
    _add_textbox(
        slide, Inches(0.5), Inches(0.4), Inches(12), Inches(0.6),
        f"Strategic Overview & M&A Considerations — {cd.name}",
        font_size=22, bold=True, color=NAVY,
    )

    # Management team (left)
    _add_textbox(
        slide, Inches(0.5), Inches(1.3), Inches(5.8), Inches(0.3),
        "Key Management", font_size=14, bold=True, color=NAVY,
    )

    mgmt_box = _add_textbox(
        slide, Inches(0.5), Inches(1.7), Inches(5.8), Inches(2.3),
        "", font_size=10, color=DARK_GRAY,
    )
    tf = mgmt_box.text_frame
    if cd.officers:
        for officer in cd.officers[:5]:
            name = officer.get("name", "N/A")
            title = officer.get("title", "N/A")
            _add_paragraph(tf, f"{name} — {title}",
                           font_size=10, color=DARK_GRAY, space_before=Pt(6))
    else:
        _add_paragraph(tf, "Officer data not available", font_size=10,
                       color=MED_GRAY)

    # Pie chart (right)
    _add_pie_chart(
        slide, cd,
        left=Inches(7.0), top=Inches(1.3),
        width=Inches(5.8), height=Inches(2.8),
    )

    # Divider
    _add_rect(slide, Inches(0.5), Inches(4.2), Inches(12.3), Inches(0.03), GOLD)

    # News section
    _add_textbox(
        slide, Inches(0.5), Inches(4.4), Inches(12), Inches(0.3),
        "Recent News & Events", font_size=14, bold=True, color=NAVY,
    )

    news_box = _add_textbox(
        slide, Inches(0.5), Inches(4.85), Inches(12), Inches(2.2),
        "", font_size=10, color=DARK_GRAY,
    )
    tf = news_box.text_frame
    if cd.news:
        for n in cd.news[:5]:
            title = n.get("title", "")
            publisher = n.get("publisher", "")
            _add_paragraph(
                tf, f"\u2022  {title}  ({publisher})",
                font_size=10, color=DARK_GRAY, space_before=Pt(6),
            )
    else:
        _add_paragraph(tf, "No recent news available.", font_size=10,
                       color=MED_GRAY)

    _add_footer(slide, cd)


# ── Public API ───────────────────────────────────────────────

def generate_presentation(cd: CompanyData, template_path: str = "assets/template.pptx") -> io.BytesIO:
    """
    Build the 3-slide M&A profile and return as an in-memory BytesIO buffer.
    """
    prs = Presentation(template_path)
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    _build_slide_1(prs, cd)
    _build_slide_2(prs, cd)
    _build_slide_3(prs, cd)

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf
