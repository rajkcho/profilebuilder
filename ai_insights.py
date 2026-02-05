"""
AI Insights — generates comprehensive M&A analysis content:
  - Product Overview & Management Sentiment
  - Executive Summary bullets
  - M&A History (deals, valuations, rationale)
  - Industry Analysis & Risk Factors

Uses OpenAI-compatible API via OPENAI_API_KEY env var.
Falls back to deterministic templates if no API key is set.
"""

import os
from data_engine import CompanyData, format_number, format_pct


# ── Prompt Builders ──────────────────────────────────────────

def _summarize_recommendations(cd: CompanyData) -> str:
    """One-line summary of analyst recommendations."""
    if cd.recommendations_summary is not None and not cd.recommendations_summary.empty:
        try:
            row = cd.recommendations_summary.iloc[0]
            parts = []
            for col in ["strongBuy", "buy", "hold", "sell", "strongSell"]:
                if col in row.index:
                    parts.append(f"{col}: {int(row[col])}")
            if parts:
                return ", ".join(parts)
        except Exception:
            pass
    return "No analyst data available"


def _build_main_prompt(cd: CompanyData) -> str:
    """Comprehensive prompt for product overview, management, and executive summary."""
    officers_text = "\n".join(
        f"- {o.get('name', 'N/A')}: {o.get('title', 'N/A')}"
        for o in cd.officers[:6]
    ) or "No officer data available."

    news_text = "\n".join(
        f"- {n['title']} ({n['publisher']})" for n in cd.news[:8]
    ) or "No recent news available."

    cs = cd.currency_symbol

    # Latest financials
    rev_latest = format_number(cd.revenue.iloc[0], currency_symbol=cs) if cd.revenue is not None and len(cd.revenue) > 0 else "N/A"
    ebitda_latest = format_number(cd.ebitda.iloc[0], currency_symbol=cs) if cd.ebitda is not None and len(cd.ebitda) > 0 else "N/A"
    ni_latest = format_number(cd.net_income.iloc[0], currency_symbol=cs) if cd.net_income is not None and len(cd.net_income) > 0 else "N/A"
    fcf_latest = format_number(cd.free_cashflow_series.iloc[0], currency_symbol=cs) if cd.free_cashflow_series is not None and len(cd.free_cashflow_series) > 0 else "N/A"

    return f"""You are a senior M&A analyst at a bulge-bracket investment bank preparing a comprehensive tear sheet for {cd.name} ({cd.ticker}).

Company: {cd.name} ({cd.ticker})
Exchange: {cd.exchange}
Sector: {cd.sector} | Industry: {cd.industry}
Headquarters: {cd.city}, {cd.state}, {cd.country}
Employees: {cd.full_time_employees or 'N/A'}

Financial Snapshot:
- Market Cap: {format_number(cd.market_cap, currency_symbol=cs)}
- Enterprise Value: {format_number(cd.enterprise_value, currency_symbol=cs)}
- Current Price: {cs}{cd.current_price:.2f} ({cd.price_change_pct:+.2f}%) [{cd.currency_code}]
- Revenue (Latest Annual): {rev_latest}
- EBITDA (Latest Annual): {ebitda_latest}
- Net Income (Latest Annual): {ni_latest}
- Free Cash Flow: {fcf_latest}
- Gross Margin: {format_pct(cd.gross_margins)}
- Operating Margin: {format_pct(cd.operating_margins)}
- Net Margin: {format_pct(cd.profit_margins)}
- Revenue Growth (YoY): {f'{cd.revenue_growth:.1f}%' if cd.revenue_growth else 'N/A'}
- P/E: {cd.trailing_pe or 'N/A'} | Forward P/E: {cd.forward_pe or 'N/A'}
- EV/EBITDA: {cd.ev_to_ebitda or 'N/A'} | PEG: {cd.peg_ratio or 'N/A'}
- ROE: {format_pct(cd.return_on_equity)} | ROA: {format_pct(cd.return_on_assets)}
- D/E: {cd.debt_to_equity or 'N/A'} | Current Ratio: {cd.current_ratio or 'N/A'}

Key Officers:
{officers_text}

Analyst Consensus: {_summarize_recommendations(cd)}

Recent News:
{news_text}

Provide the following in EXACT format (no extra commentary):

PRODUCT_OVERVIEW:
- [what the company does, key products/services, revenue mix]
- [competitive positioning, moat, market share]
- [key growth drivers and catalysts]
- [headwinds, challenges, or disruption risks]

MGMT_SENTIMENT:
- [CEO background, tenure, and track record]
- [notable recent management actions — restructuring, capital allocation, strategy pivots]
- [shareholder alignment — buybacks, insider ownership, compensation structure]
- [board composition and governance quality]

EXECUTIVE_SUMMARY:
- [investment thesis in 2 sentences]
- [key competitive advantage / moat]
- [primary risk factor with specific detail]
- [valuation assessment — expensive, fair, or cheap relative to peers and history]
- [M&A attractiveness — is this company a likely acquirer, target, or neither, and why]
"""


def _build_ma_history_prompt(cd: CompanyData) -> str:
    """Prompt for M&A history generation."""
    return f"""You are an M&A analyst. Provide a comprehensive M&A and strategic transaction history for {cd.name} ({cd.ticker}).

Company: {cd.name} ({cd.ticker})
Sector: {cd.sector} | Industry: {cd.industry}
Market Cap: {format_number(cd.market_cap, currency_symbol=cd.currency_symbol)}
Enterprise Value: {format_number(cd.enterprise_value, currency_symbol=cd.currency_symbol)}

List the most significant mergers, acquisitions, divestitures, and strategic transactions.
Include both deals BY the company and notable attempts TO acquire the company.
If the company has limited M&A history, state that clearly.

Use this EXACT format (no extra commentary):

MA_DEALS:
DEAL: [Target/Acquirer name]
YEAR: [Year]
VALUE: [Approximate deal value, or "Undisclosed"]
TYPE: [Acquisition / Divestiture / Merger / Failed Bid / Joint Venture]
RATIONALE: [1-2 sentence strategic rationale and outcome]
---
[Repeat for up to 8 most notable deals, most recent first]

MA_SUMMARY:
[3-4 sentences assessing the company's overall M&A strategy — is it an active acquirer, a roll-up story, primarily organic growth, a potential target? What is the strategic direction?]
"""


def _build_industry_prompt(cd: CompanyData) -> str:
    """Prompt for industry analysis and risk factors."""
    return f"""You are an industry analyst covering {cd.sector}. Provide industry context and risk analysis for {cd.name} ({cd.ticker}) in the {cd.industry} space.

INDUSTRY_ANALYSIS:
- [industry size, growth rate, and trajectory]
- [key secular trends shaping the industry]
- [competitive landscape — major players, fragmentation, consolidation trends]
- [regulatory environment and recent policy changes]

RISK_FACTORS:
- [company-specific operational or execution risk]
- [macro or industry-level risk]
- [financial or balance sheet risk]
- [competitive disruption or technology risk]
"""


# ── Response Parsing ─────────────────────────────────────────

def _parse_sections(text: str) -> dict:
    """Parse structured LLM output into named sections."""
    sections = {}
    current_key = None
    current_lines = []

    key_map = {
        "PRODUCT_OVERVIEW": "product_overview",
        "MGMT_SENTIMENT": "mgmt_sentiment",
        "EXECUTIVE_SUMMARY": "executive_summary",
        "MA_DEALS": "ma_deals",
        "MA_SUMMARY": "ma_summary",
        "INDUSTRY_ANALYSIS": "industry_analysis",
        "RISK_FACTORS": "risk_factors",
    }

    for line in text.strip().split("\n"):
        stripped = line.strip()
        # Check if this line starts a new section
        matched = False
        for marker, key in key_map.items():
            if stripped.startswith(marker):
                if current_key:
                    sections[current_key] = "\n".join(current_lines)
                current_key = key
                current_lines = []
                matched = True
                break
        if not matched and stripped:
            current_lines.append(stripped)

    if current_key:
        sections[current_key] = "\n".join(current_lines)

    return sections


def _extract_bullets(text: str) -> list[str]:
    """Extract bullet points from a section."""
    bullets = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            bullets.append(line[2:].strip())
        elif line.startswith("* "):
            bullets.append(line[2:].strip())
        elif line and not line.startswith("DEAL:") and not line.startswith("YEAR:"):
            bullets.append(line)
    return bullets


def _parse_ma_deals(text: str) -> str:
    """Parse MA_DEALS section into formatted markdown."""
    if not text:
        return ""
    lines = []
    current_deal = {}
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("DEAL:"):
            if current_deal:
                lines.append(_format_deal(current_deal))
                current_deal = {}
            current_deal["deal"] = line[5:].strip()
        elif line.startswith("YEAR:"):
            current_deal["year"] = line[5:].strip()
        elif line.startswith("VALUE:"):
            current_deal["value"] = line[6:].strip()
        elif line.startswith("TYPE:"):
            current_deal["type"] = line[5:].strip()
        elif line.startswith("RATIONALE:"):
            current_deal["rationale"] = line[10:].strip()
        elif line == "---":
            if current_deal:
                lines.append(_format_deal(current_deal))
                current_deal = {}
    if current_deal:
        lines.append(_format_deal(current_deal))
    return "\n\n".join(lines)


def _format_deal(deal: dict) -> str:
    """Format a single M&A deal entry."""
    name = deal.get("deal", "Unknown")
    year = deal.get("year", "")
    value = deal.get("value", "Undisclosed")
    dtype = deal.get("type", "")
    rationale = deal.get("rationale", "")
    return (
        f"**{name}** ({year}) — {dtype}\n"
        f"  Value: {value}\n"
        f"  {rationale}"
    )


# ── LLM Generators ──────────────────────────────────────────

def _call_llm(prompt: str, system_msg: str = "You are a senior M&A analyst.",
              max_tokens: int = 1500) -> str:
    """Make an LLM API call via OpenAI or OpenRouter and return the response text."""
    from openai import OpenAI

    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if openrouter_key:
        client = OpenAI(
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
        )
        model = "gpt-4o-mini"
    elif openai_key:
        client = OpenAI(api_key=openai_key)
        model = "gpt-4o-mini"
    else:
        raise RuntimeError("No API key set")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def generate_insights_llm(cd: CompanyData) -> CompanyData:
    """Generate product overview, management sentiment, and executive summary via LLM."""
    try:
        text = _call_llm(_build_main_prompt(cd), max_tokens=2000)
        sections = _parse_sections(text)

        cd.product_overview = sections.get("product_overview", "")
        cd.mgmt_sentiment = sections.get("mgmt_sentiment", "")
        cd.executive_summary_bullets = _extract_bullets(
            sections.get("executive_summary", "")
        )
    except Exception as e:
        print(f"Main insights LLM call failed ({e}), using fallback.")
        _fallback_main_insights(cd)
    return cd


def generate_ma_history_llm(cd: CompanyData) -> CompanyData:
    """Generate M&A history — uses scraped Wikipedia data as primary source,
    falls back to LLM only when no scraped data is available."""

    # If we already have scraped deals from Wikipedia, build ma_history from them
    if cd.ma_deals:
        cd.ma_history = _build_ma_history_from_deals(cd)
        return cd

    # No scraped data — try LLM
    try:
        text = _call_llm(_build_ma_history_prompt(cd), max_tokens=2000)
        sections = _parse_sections(text)

        deals_text = sections.get("ma_deals", "")
        summary_text = sections.get("ma_summary", "")

        formatted_deals = _parse_ma_deals(deals_text)
        cd.ma_history = formatted_deals
        if summary_text:
            cd.ma_history += f"\n\n**M&A Strategy Assessment:**\n{summary_text}"
    except Exception as e:
        print(f"M&A history LLM call failed ({e}), using fallback.")
        cd.ma_history = _build_no_data_fallback(cd)
    return cd


def _build_ma_history_from_deals(cd: CompanyData) -> str:
    """Build formatted markdown M&A history from scraped deal data."""
    deals = cd.ma_deals
    total = len(deals)

    # Show up to 20 most recent deals with values, then a summary
    shown_deals = deals[:20]

    lines = [f"**{total} acquisitions on record** *(Source: [Wikipedia]({cd.ma_source}))*\n"]
    lines.append("| Date | Target | Business | Value |")
    lines.append("|------|--------|----------|-------|")
    for d in shown_deals:
        date = d.get("date", "")
        company = d.get("company", "")
        business = d.get("business", "")[:60]
        value = d.get("value", "Undisclosed")
        lines.append(f"| {date} | {company} | {business} | {value} |")

    if total > 20:
        lines.append(f"\n*...and {total - 20} more deals. See full list on Wikipedia.*")

    return "\n".join(lines)


def _build_no_data_fallback(cd: CompanyData) -> str:
    """Fallback when no M&A data is available from any source."""
    return (
        f"No public M&A history found for {cd.name}. "
        f"This company may have limited acquisition activity, "
        f"or its deal history may not be documented on Wikipedia."
    )


def generate_industry_analysis_llm(cd: CompanyData) -> CompanyData:
    """Generate industry analysis and risk factors via LLM."""
    try:
        text = _call_llm(_build_industry_prompt(cd), max_tokens=1200)
        sections = _parse_sections(text)

        cd.industry_analysis = sections.get("industry_analysis", "")
        cd.risk_factors = sections.get("risk_factors", "")
    except Exception as e:
        print(f"Industry analysis LLM call failed ({e}), using fallback.")
        _fallback_industry(cd)
    return cd


# ── Deterministic Fallbacks ──────────────────────────────────

def _fallback_main_insights(cd: CompanyData):
    """Deterministic fallback for main insights."""
    cs = cd.currency_symbol
    growth_desc = "growing" if (cd.revenue_growth or 0) > 0 else "contracting"
    de_desc = "manageable" if (cd.debt_to_equity or 0) < 150 else "elevated"

    cd.product_overview = (
        f"- {cd.name} operates in the {cd.industry} sector within {cd.sector}\n"
        f"- Market capitalization of {format_number(cd.market_cap, currency_symbol=cs)} with a "
        f"{growth_desc} revenue trajectory ({cd.revenue_growth or 0:+.1f}% YoY)\n"
        f"- Gross margin of {format_pct(cd.gross_margins)}, "
        f"operating margin of {format_pct(cd.operating_margins)}\n"
        f"- Beta of {cd.beta or 'N/A'} indicates "
        f"{'above-average' if (cd.beta or 1) > 1 else 'below-average'} market sensitivity"
    )

    ceo_name = "Management team"
    if cd.officers:
        ceo = next(
            (o for o in cd.officers if "CEO" in o.get("title", "").upper()),
            cd.officers[0],
        )
        ceo_name = ceo.get("name", "Management team")

    cd.mgmt_sentiment = (
        f"- Led by {ceo_name}\n"
        f"- Debt levels are {de_desc} (D/E: {cd.debt_to_equity or 'N/A'})\n"
        f"- Return on Equity: {format_pct(cd.return_on_equity)}, "
        f"Return on Assets: {format_pct(cd.return_on_assets)}\n"
        f"- {'Dividend-paying' if cd.dividend_yield else 'Non-dividend'} company "
        f"({'yield: ' + format_pct(cd.dividend_yield) if cd.dividend_yield else 'growth-focused strategy'})"
    )

    cd.executive_summary_bullets = [
        f"{cd.name} is a {format_number(cd.market_cap, currency_symbol=cs)} market cap company "
        f"in the {cd.industry} space with "
        f"{'positive' if (cd.revenue_growth or 0) > 0 else 'negative'} revenue momentum",
        f"Trades at {cd.trailing_pe or 'N/A'}x trailing P/E and "
        f"{cd.ev_to_ebitda or 'N/A'}x EV/EBITDA",
        f"Key risk: {'high leverage (D/E: ' + str(cd.debt_to_equity) + ')' if (cd.debt_to_equity or 0) > 200 else 'execution and competitive dynamics'}",
        f"Free cash flow of {format_number(cd.free_cashflow_series.iloc[0], currency_symbol=cs) if cd.free_cashflow_series is not None and len(cd.free_cashflow_series) > 0 else 'N/A'} supports capital return capacity",
        f"Valuation {'appears stretched' if (cd.trailing_pe or 0) > 25 else 'is reasonable'} relative to growth profile",
    ]


def _fallback_industry(cd: CompanyData):
    """Deterministic fallback for industry analysis and risk factors."""
    cd.industry_analysis = (
        f"- {cd.industry} within the {cd.sector} sector\n"
        f"- Revenue growth of {cd.revenue_growth or 0:.1f}% vs industry trends\n"
        f"- Competitive dynamics driven by innovation and scale\n"
        f"- Regulatory environment varies by geography"
    )
    cd.risk_factors = (
        f"- Execution risk in maintaining {format_pct(cd.gross_margins)} gross margins\n"
        f"- Macro sensitivity with beta of {cd.beta or 'N/A'}\n"
        f"- Balance sheet leverage at {cd.debt_to_equity or 'N/A'} D/E ratio\n"
        f"- Competitive and technology disruption risk in {cd.industry}"
    )


def generate_insights_fallback(cd: CompanyData) -> CompanyData:
    """Full deterministic fallback — no API key needed."""
    _fallback_main_insights(cd)
    # Use scraped Wikipedia data if available, otherwise show informative message
    if cd.ma_deals:
        cd.ma_history = _build_ma_history_from_deals(cd)
    else:
        cd.ma_history = _build_no_data_fallback(cd)
    _fallback_industry(cd)
    return cd


# ── Public API ───────────────────────────────────────────────

def generate_insights(cd: CompanyData) -> CompanyData:
    """Main entry point: orchestrate all insight generation."""
    if os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY"):
        generate_insights_llm(cd)
        generate_ma_history_llm(cd)
        generate_industry_analysis_llm(cd)
    else:
        generate_insights_fallback(cd)
    return cd
