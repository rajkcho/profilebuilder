"""
AI Insights — generates comprehensive M&A analysis content:
  - Product Overview & Management Sentiment
  - Executive Summary bullets
  - M&A History (deals, valuations, rationale)
  - Industry Analysis & Risk Factors
  - SWOT Analysis
  - Growth Outlook
  - Capital Allocation Analysis

Uses OpenAI-compatible API via OPENAI_API_KEY env var.
Falls back to deterministic templates if no API key is set.
"""

import os
from dataclasses import dataclass
from data_engine import CompanyData, format_number, format_pct


# ── Helpers ─────────────────────────────────────────────────────

def _series_trend(series, cs="$", n=4):
    """Build a multi-year trend string from a pd.Series (most-recent first)."""
    if series is None or len(series) == 0:
        return "N/A"
    vals = series.dropna().head(n)
    parts = []
    for idx, v in vals.items():
        yr = idx.strftime("%Y") if hasattr(idx, "strftime") else str(idx)
        parts.append(f"{yr}: {format_number(v, currency_symbol=cs)}")
    return " → ".join(reversed(parts)) if parts else "N/A"


def _margin_trend(series, n=4):
    """Build a multi-year margin trend string (already in %)."""
    if series is None or len(series) == 0:
        return "N/A"
    vals = series.dropna().head(n)
    parts = []
    for idx, v in vals.items():
        yr = idx.strftime("%Y") if hasattr(idx, "strftime") else str(idx)
        parts.append(f"{yr}: {v:.1f}%")
    return " → ".join(reversed(parts)) if parts else "N/A"


def _peer_summary(cd: CompanyData) -> str:
    """One-line peer context."""
    if not cd.peer_data:
        return "No peer data available."
    names = [p.get("ticker", "") for p in cd.peer_data[:5]]
    return f"Peer group: {', '.join(names)}"


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

Multi-Year Trends:
- Revenue: {_series_trend(cd.revenue, cs)}
- Gross Margin: {_margin_trend(cd.gross_margin_series)}
- EBITDA Margin: {_margin_trend(cd.ebitda_margin)}
- Net Margin: {_margin_trend(cd.net_margin_series)}
- Free Cash Flow: {_series_trend(cd.free_cashflow_series, cs)}

Balance Sheet:
- Total Debt: {format_number(cd.total_debt_info, currency_symbol=cs) if cd.total_debt_info else 'N/A'}
- Total Cash: {format_number(cd.total_cash, currency_symbol=cs) if cd.total_cash else 'N/A'}

{_peer_summary(cd)}

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
- [geographic revenue mix and international exposure]
- [R&D intensity and innovation pipeline]

MGMT_SENTIMENT:
- [CEO background, tenure, and track record]
- [notable recent management actions — restructuring, capital allocation, strategy pivots]
- [shareholder alignment — buybacks, insider ownership, compensation structure]
- [board composition and governance quality]

EXECUTIVE_SUMMARY:
- [investment thesis in 2 sentences]
- [key competitive advantage / moat]
- [financial trajectory — is revenue/margin trend improving, stable, or deteriorating?]
- [free cash flow quality — strong, adequate, or weak relative to earnings]
- [primary risk factor with specific detail]
- [secondary risk — a less obvious but meaningful concern]
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
    cs = cd.currency_symbol
    peer_text = _peer_summary(cd)

    return f"""You are an industry analyst covering {cd.sector}. Provide industry context and risk analysis for {cd.name} ({cd.ticker}) in the {cd.industry} space.

Company context:
- Market Cap: {format_number(cd.market_cap, currency_symbol=cs)}
- Gross Margin: {format_pct(cd.gross_margins)} | Operating Margin: {format_pct(cd.operating_margins)}
- Revenue Growth: {f'{cd.revenue_growth:.1f}%' if cd.revenue_growth else 'N/A'}
- {peer_text}

INDUSTRY_ANALYSIS:
- [total addressable market (TAM) size and expected CAGR]
- [industry growth rate and current cycle phase]
- [key secular trends shaping the industry over 3-5 years]
- [competitive landscape — major players, market shares, fragmentation]
- [consolidation trends — is M&A activity increasing or decreasing?]
- [technology trends — AI, automation, digitization impact]
- [regulatory environment and recent policy changes]
- [supply chain dynamics and geographic concentration risks]

RISK_FACTORS:
- [HIGH] [company-specific operational or execution risk with evidence]
- [MEDIUM] [macro or industry-level risk — recession, rates, geopolitics]
- [MEDIUM] [financial or balance sheet risk — leverage, liquidity, refinancing]
- [HIGH/MEDIUM/LOW] [competitive disruption or technology risk]
- [MEDIUM] [regulatory or legal risk]
- [LOW/MEDIUM] [ESG or reputational risk]
"""


def _build_swot_prompt(cd: CompanyData) -> str:
    """Prompt for SWOT analysis."""
    cs = cd.currency_symbol

    return f"""You are a strategic analyst. Provide a SWOT analysis for {cd.name} ({cd.ticker}).

Company: {cd.name} ({cd.ticker})
Sector: {cd.sector} | Industry: {cd.industry}
Market Cap: {format_number(cd.market_cap, currency_symbol=cs)}
Revenue Growth: {f'{cd.revenue_growth:.1f}%' if cd.revenue_growth else 'N/A'}
Gross Margin: {format_pct(cd.gross_margins)} | Operating Margin: {format_pct(cd.operating_margins)}
ROE: {format_pct(cd.return_on_equity)} | D/E: {cd.debt_to_equity or 'N/A'}
FCF: {format_number(cd.free_cashflow_series.iloc[0], currency_symbol=cs) if cd.free_cashflow_series is not None and len(cd.free_cashflow_series) > 0 else 'N/A'}
Beta: {cd.beta or 'N/A'}
{_peer_summary(cd)}

Provide evidence-based SWOT in EXACT format (no extra commentary). Each bullet must cite specific data or facts.

STRENGTHS:
- [specific competitive advantage with evidence]
- [financial strength with data point]
- [market position or brand advantage]
- [operational efficiency or scale advantage]

WEAKNESSES:
- [specific internal limitation with evidence]
- [financial weakness with data point]
- [operational or strategic gap]

OPPORTUNITIES:
- [specific growth opportunity with market context]
- [expansion or new market opportunity]
- [strategic opportunity — M&A, partnership, new product]

THREATS:
- [specific competitive threat with context]
- [macro or regulatory threat]
- [technology disruption or market shift threat]
"""


def _build_growth_outlook_prompt(cd: CompanyData) -> str:
    """Prompt for growth outlook analysis."""
    cs = cd.currency_symbol

    return f"""You are a growth equity analyst. Provide a growth outlook for {cd.name} ({cd.ticker}).

Company: {cd.name} ({cd.ticker})
Sector: {cd.sector} | Industry: {cd.industry}
Revenue Trend: {_series_trend(cd.revenue, cs)}
Gross Margin Trend: {_margin_trend(cd.gross_margin_series)}
EBITDA Margin Trend: {_margin_trend(cd.ebitda_margin)}
Net Margin Trend: {_margin_trend(cd.net_margin_series)}
FCF Trend: {_series_trend(cd.free_cashflow_series, cs)}
Revenue Growth (YoY): {f'{cd.revenue_growth:.1f}%' if cd.revenue_growth else 'N/A'}
P/E: {cd.trailing_pe or 'N/A'} | Forward P/E: {cd.forward_pe or 'N/A'}

Provide growth outlook in EXACT format:

REVENUE_THESIS:
- [2-3 sentences on revenue growth drivers and trajectory over 2-3 years]

MARGIN_THESIS:
- [2-3 sentences on margin expansion/contraction outlook]

EARNINGS_PATH:
- [2-3 sentences on EPS trajectory and earnings quality]

KEY_CATALYSTS:
- [specific near-term catalyst with timeline]
- [medium-term catalyst with context]
- [long-term structural catalyst]

KEY_RISKS_TO_GROWTH:
- [most likely risk to growth thesis]
- [secondary growth risk]

GROWTH_RATING:
[one word: STRONG / MODERATE / WEAK]
"""


def _build_capital_allocation_prompt(cd: CompanyData) -> str:
    """Prompt for capital allocation analysis."""
    cs = cd.currency_symbol

    div_text = f"Dividend Yield: {format_pct(cd.dividend_yield)}" if cd.dividend_yield else "No dividend"
    ma_text = f"{len(cd.ma_deals)} acquisitions on record" if cd.ma_deals else "Limited M&A activity"

    return f"""You are a capital allocation analyst. Evaluate capital allocation for {cd.name} ({cd.ticker}).

Company: {cd.name} ({cd.ticker})
FCF Trend: {_series_trend(cd.free_cashflow_series, cs)}
CapEx Trend: {_series_trend(cd.capital_expenditure, cs)}
Dividends Paid Trend: {_series_trend(cd.dividends_paid, cs)}
{div_text}
D/E: {cd.debt_to_equity or 'N/A'} | Total Debt: {format_number(cd.total_debt_info, currency_symbol=cs) if cd.total_debt_info else 'N/A'}
Total Cash: {format_number(cd.total_cash, currency_symbol=cs) if cd.total_cash else 'N/A'}
M&A Activity: {ma_text}

Provide capital allocation analysis in EXACT format:

STRATEGY_SUMMARY:
- [2-3 sentences on overall capital allocation philosophy]

CAPEX_ASSESSMENT:
- [2-3 sentences on capex intensity, trends, and adequacy]

SHAREHOLDER_RETURNS:
- [2-3 sentences on buybacks, dividends, and total shareholder return strategy]

MA_STRATEGY:
- [2-3 sentences on M&A approach, deal discipline, integration track record]

DEBT_MANAGEMENT:
- [2-3 sentences on leverage, maturity profile, credit quality]

CAPITAL_ALLOCATION_GRADE:
[one letter grade: A / B / C / D]
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
        # SWOT
        "STRENGTHS": "strengths",
        "WEAKNESSES": "weaknesses",
        "OPPORTUNITIES": "opportunities",
        "THREATS": "threats",
        # Growth outlook
        "REVENUE_THESIS": "revenue_thesis",
        "MARGIN_THESIS": "margin_thesis",
        "EARNINGS_PATH": "earnings_path",
        "KEY_CATALYSTS": "key_catalysts",
        "KEY_RISKS_TO_GROWTH": "key_risks_to_growth",
        "GROWTH_RATING": "growth_rating",
        # Capital allocation
        "STRATEGY_SUMMARY": "strategy_summary",
        "CAPEX_ASSESSMENT": "capex_assessment",
        "SHAREHOLDER_RETURNS": "shareholder_returns",
        "MA_STRATEGY": "ma_strategy",
        "DEBT_MANAGEMENT": "debt_management",
        "CAPITAL_ALLOCATION_GRADE": "capital_allocation_grade",
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
        text = _call_llm(_build_main_prompt(cd), max_tokens=3500)
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
        text = _call_llm(_build_industry_prompt(cd), max_tokens=2000)
        sections = _parse_sections(text)

        cd.industry_analysis = sections.get("industry_analysis", "")
        cd.risk_factors = sections.get("risk_factors", "")
    except Exception as e:
        print(f"Industry analysis LLM call failed ({e}), using fallback.")
        _fallback_industry(cd)
    return cd


def generate_swot_llm(cd: CompanyData) -> CompanyData:
    """Generate SWOT analysis via LLM."""
    try:
        text = _call_llm(_build_swot_prompt(cd), max_tokens=1500)
        sections = _parse_sections(text)

        cd.swot_analysis = {
            "strengths": _extract_bullets(sections.get("strengths", "")),
            "weaknesses": _extract_bullets(sections.get("weaknesses", "")),
            "opportunities": _extract_bullets(sections.get("opportunities", "")),
            "threats": _extract_bullets(sections.get("threats", "")),
        }
    except Exception as e:
        print(f"SWOT LLM call failed ({e}), using fallback.")
        _fallback_swot(cd)
    return cd


def generate_growth_and_capital_llm(cd: CompanyData) -> CompanyData:
    """Generate growth outlook and capital allocation analysis via LLM."""
    # Growth outlook
    try:
        text = _call_llm(_build_growth_outlook_prompt(cd), max_tokens=1500)
        sections = _parse_sections(text)

        cd.growth_outlook = {
            "revenue_thesis": sections.get("revenue_thesis", ""),
            "margin_thesis": sections.get("margin_thesis", ""),
            "earnings_path": sections.get("earnings_path", ""),
            "key_catalysts": _extract_bullets(sections.get("key_catalysts", "")),
            "key_risks_to_growth": _extract_bullets(sections.get("key_risks_to_growth", "")),
            "growth_rating": sections.get("growth_rating", "MODERATE").strip().upper(),
        }
    except Exception as e:
        print(f"Growth outlook LLM call failed ({e}), using fallback.")
        _fallback_growth_outlook(cd)

    # Capital allocation
    try:
        text = _call_llm(_build_capital_allocation_prompt(cd), max_tokens=1200)
        sections = _parse_sections(text)

        cd.capital_allocation_analysis = {
            "strategy_summary": sections.get("strategy_summary", ""),
            "capex_assessment": sections.get("capex_assessment", ""),
            "shareholder_returns": sections.get("shareholder_returns", ""),
            "ma_strategy": sections.get("ma_strategy", ""),
            "debt_management": sections.get("debt_management", ""),
            "capital_allocation_grade": sections.get("capital_allocation_grade", "B").strip().upper()[:1],
        }
    except Exception as e:
        print(f"Capital allocation LLM call failed ({e}), using fallback.")
        _fallback_capital_allocation(cd)

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
        f"{'above-average' if (cd.beta or 1) > 1 else 'below-average'} market sensitivity\n"
        f"- Revenue trend: {_series_trend(cd.revenue, cs)}\n"
        f"- R&D and innovation data not available in current dataset"
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

    fcf_str = format_number(cd.free_cashflow_series.iloc[0], currency_symbol=cs) if cd.free_cashflow_series is not None and len(cd.free_cashflow_series) > 0 else "N/A"

    cd.executive_summary_bullets = [
        f"{cd.name} is a {format_number(cd.market_cap, currency_symbol=cs)} market cap company "
        f"in the {cd.industry} space with "
        f"{'positive' if (cd.revenue_growth or 0) > 0 else 'negative'} revenue momentum",
        f"Trades at {cd.trailing_pe or 'N/A'}x trailing P/E and "
        f"{cd.ev_to_ebitda or 'N/A'}x EV/EBITDA",
        f"Revenue trajectory: {_series_trend(cd.revenue, cs)}",
        f"Free cash flow of {fcf_str} {'demonstrates strong cash generation' if fcf_str != 'N/A' else '(data not available)'}",
        f"Key risk: {'high leverage (D/E: ' + str(cd.debt_to_equity) + ')' if (cd.debt_to_equity or 0) > 200 else 'execution and competitive dynamics'}",
        f"Secondary risk: margin pressure in a {'competitive' if (cd.gross_margins or 0) < 0.4 else 'relatively protected'} market",
        f"Valuation {'appears stretched' if (cd.trailing_pe or 0) > 25 else 'is reasonable'} relative to growth profile",
        f"M&A profile: {'active acquirer with {0} deals on record'.format(len(cd.ma_deals)) if cd.ma_deals else 'limited public M&A activity'}",
    ]


def _fallback_industry(cd: CompanyData):
    """Deterministic fallback for industry analysis and risk factors."""
    cd.industry_analysis = (
        f"- {cd.industry} within the {cd.sector} sector\n"
        f"- Revenue growth of {cd.revenue_growth or 0:.1f}% vs industry trends\n"
        f"- Competitive dynamics driven by innovation and scale\n"
        f"- Regulatory environment varies by geography\n"
        f"- TAM data not available — industry sizing requires external research\n"
        f"- Consolidation trends depend on regulatory and capital market conditions\n"
        f"- Technology disruption (AI, automation) reshaping competitive dynamics\n"
        f"- Supply chain and geopolitical risks remain elevated"
    )
    cd.risk_factors = (
        f"- [HIGH] Execution risk in maintaining {format_pct(cd.gross_margins)} gross margins amid competitive pressure\n"
        f"- [MEDIUM] Macro sensitivity with beta of {cd.beta or 'N/A'} — vulnerable to economic slowdowns\n"
        f"- [MEDIUM] Balance sheet leverage at {cd.debt_to_equity or 'N/A'} D/E ratio\n"
        f"- [MEDIUM] Competitive and technology disruption risk in {cd.industry}\n"
        f"- [MEDIUM] Regulatory and compliance risk across operating jurisdictions\n"
        f"- [LOW] ESG and reputational risk — standard for {cd.sector} sector"
    )


def _fallback_swot(cd: CompanyData):
    """Deterministic fallback for SWOT analysis."""
    cs = cd.currency_symbol
    gm = (cd.gross_margins or 0) * 100
    de = cd.debt_to_equity or 0
    rg = cd.revenue_growth or 0
    beta = cd.beta or 1.0

    strengths = [
        f"Market capitalization of {format_number(cd.market_cap, currency_symbol=cs)} provides scale advantages",
        f"Gross margin of {gm:.1f}% {'above' if gm > 40 else 'in line with'} industry benchmarks",
    ]
    if (cd.return_on_equity or 0) > 0.15:
        strengths.append(f"Strong return on equity at {format_pct(cd.return_on_equity)}")
    if cd.free_cashflow_series is not None and len(cd.free_cashflow_series) > 0 and cd.free_cashflow_series.iloc[0] > 0:
        strengths.append(f"Positive free cash flow of {format_number(cd.free_cashflow_series.iloc[0], currency_symbol=cs)}")

    weaknesses = [
        f"{'Elevated' if de > 150 else 'Moderate'} leverage with D/E ratio of {de:.0f}",
    ]
    if rg < 0:
        weaknesses.append(f"Revenue declining at {rg:.1f}% YoY")
    elif rg < 5:
        weaknesses.append(f"Slow revenue growth at {rg:.1f}% YoY")
    if (cd.operating_margins or 0) < 0.1:
        weaknesses.append(f"Thin operating margins at {format_pct(cd.operating_margins)}")

    opportunities = [
        f"Expansion potential within the {cd.industry} market",
        f"M&A opportunities to accelerate growth and market share",
        f"International expansion could diversify revenue base",
    ]

    threats = [
        f"Competitive pressure from peers in {cd.industry}",
        f"{'Above-average' if beta > 1 else 'Moderate'} market sensitivity (beta: {beta:.2f})",
        f"Macroeconomic headwinds including interest rate uncertainty",
    ]

    cd.swot_analysis = {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "opportunities": opportunities,
        "threats": threats,
    }


def _fallback_growth_outlook(cd: CompanyData):
    """Deterministic fallback for growth outlook."""
    cs = cd.currency_symbol
    rg = cd.revenue_growth or 0
    pe = cd.trailing_pe or 0
    fpe = cd.forward_pe or 0

    if rg > 15:
        rating = "STRONG"
    elif rg > 5:
        rating = "MODERATE"
    else:
        rating = "WEAK"

    cd.growth_outlook = {
        "revenue_thesis": f"Revenue growth at {rg:.1f}% YoY. Trend: {_series_trend(cd.revenue, cs)}. {'Accelerating' if rg > 10 else 'Stable'} trajectory based on available data.",
        "margin_thesis": f"Gross margin trend: {_margin_trend(cd.gross_margin_series)}. Operating margin trend: {_margin_trend(cd.operating_margin_series)}. {'Expanding' if (cd.gross_margins or 0) > (cd.operating_margins or 0) else 'Stable'} margin profile.",
        "earnings_path": f"P/E of {pe:.1f}x trailing and {fpe:.1f}x forward suggests {'earnings growth expected' if fpe < pe and fpe > 0 else 'stable earnings outlook'}.",
        "key_catalysts": [
            f"Revenue acceleration from {cd.industry} market tailwinds",
            "Margin expansion through operational efficiency",
            "Long-term structural growth in addressable market",
        ],
        "key_risks_to_growth": [
            "Competitive pressure could compress margins",
            "Macroeconomic slowdown may reduce demand",
        ],
        "growth_rating": rating,
    }


def _fallback_capital_allocation(cd: CompanyData):
    """Deterministic fallback for capital allocation analysis."""
    cs = cd.currency_symbol
    fcf_str = format_number(cd.free_cashflow_series.iloc[0], currency_symbol=cs) if cd.free_cashflow_series is not None and len(cd.free_cashflow_series) > 0 else "N/A"
    div_yield = format_pct(cd.dividend_yield) if cd.dividend_yield else "No dividend"
    de = cd.debt_to_equity or 0
    ma_count = len(cd.ma_deals) if cd.ma_deals else 0

    if de < 50 and (cd.free_cashflow_series is not None and len(cd.free_cashflow_series) > 0 and cd.free_cashflow_series.iloc[0] > 0):
        grade = "A"
    elif de < 150:
        grade = "B"
    else:
        grade = "C"

    cd.capital_allocation_analysis = {
        "strategy_summary": f"FCF of {fcf_str} provides capital allocation flexibility. D/E ratio of {de:.0f} indicates {'conservative' if de < 100 else 'moderate'} leverage. {'Dividend-paying' if cd.dividend_yield else 'Growth-oriented'} capital return strategy.",
        "capex_assessment": f"Capital expenditure trend: {_series_trend(cd.capital_expenditure, cs)}. {'Investing for growth' if cd.capital_expenditure is not None and len(cd.capital_expenditure) > 0 else 'CapEx data limited'}.",
        "shareholder_returns": f"Dividend yield: {div_yield}. {'Payout ratio of ' + format_pct(cd.payout_ratio) + ' indicates sustainable dividend' if cd.payout_ratio else 'Shareholder return primarily through capital appreciation'}.",
        "ma_strategy": f"{'Active acquirer with ' + str(ma_count) + ' deals on record — strategic M&A is core to growth' if ma_count > 5 else 'Limited M&A activity — primarily organic growth strategy' if ma_count == 0 else str(ma_count) + ' deals on record — selective acquisition approach'}.",
        "debt_management": f"D/E ratio: {de:.0f}. {'Conservative balance sheet with ample capacity' if de < 50 else 'Moderate leverage — manageable but limited flexibility' if de < 150 else 'Elevated leverage — refinancing and deleveraging risk'}.",
        "capital_allocation_grade": grade,
    }


def generate_insights_fallback(cd: CompanyData) -> CompanyData:
    """Full deterministic fallback — no API key needed."""
    _fallback_main_insights(cd)
    # Use scraped Wikipedia data if available, otherwise show informative message
    if cd.ma_deals:
        cd.ma_history = _build_ma_history_from_deals(cd)
    else:
        cd.ma_history = _build_no_data_fallback(cd)
    _fallback_industry(cd)
    _fallback_swot(cd)
    _fallback_growth_outlook(cd)
    _fallback_capital_allocation(cd)
    return cd


# ── Public API ───────────────────────────────────────────────

def generate_insights(cd: CompanyData) -> CompanyData:
    """Main entry point: orchestrate all insight generation."""
    if os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY"):
        generate_insights_llm(cd)
        generate_ma_history_llm(cd)
        generate_industry_analysis_llm(cd)
        generate_swot_llm(cd)
        generate_growth_and_capital_llm(cd)
    else:
        generate_insights_fallback(cd)
    return cd


# ══════════════════════════════════════════════════════════════
# MERGER ANALYSIS INSIGHTS
# ══════════════════════════════════════════════════════════════

@dataclass
class MergerInsights:
    """AI-generated merger analysis content."""
    strategic_rationale: str = ""
    deal_risks: str = ""
    synergy_assessment: str = ""
    deal_verdict: str = ""
    deal_grade: str = "B"  # A/B/C/D/F


# ── Merger Prompt Builders ──────────────────────────────────

def _build_strategic_rationale_prompt(acq: CompanyData, tgt: CompanyData, pro_forma) -> str:
    cs_a = acq.currency_symbol
    cs_t = tgt.currency_symbol

    # Target standalone trading multiples
    tgt_trailing_pe = f"{tgt.trailing_pe:.1f}x" if tgt.trailing_pe else "N/A"
    tgt_forward_pe = f"{tgt.forward_pe:.1f}x" if tgt.forward_pe else "N/A"
    tgt_ev_ebitda = f"{tgt.ev_to_ebitda:.1f}x" if tgt.ev_to_ebitda else "N/A"

    # Implied deal multiples
    impl_ev_ebitda = f"{pro_forma.implied_ev_ebitda:.1f}x" if pro_forma.implied_ev_ebitda else "N/A"
    impl_pe = f"{pro_forma.implied_pe:.1f}x" if pro_forma.implied_pe else "N/A"

    # Target FCF
    tgt_fcf = "N/A"
    if tgt.free_cashflow_series is not None and len(tgt.free_cashflow_series) > 0:
        tgt_fcf = format_number(float(tgt.free_cashflow_series.iloc[0]), currency_symbol=cs_t)

    # Premium
    premium_pct = ((pro_forma.purchase_price / tgt.market_cap) - 1) * 100 if tgt.market_cap else 0

    return f"""You are a senior M&A advisor writing a strategic rationale memo for {acq.name} acquiring {tgt.name}.

ACQUIRER: {acq.name} ({acq.ticker})
- Sector: {acq.sector} | Industry: {acq.industry}
- Market Cap: {format_number(acq.market_cap, currency_symbol=cs_a)}
- Revenue: {format_number(pro_forma.acq_revenue, currency_symbol=cs_a)} | Revenue Growth: {f'{acq.revenue_growth:.1f}%' if acq.revenue_growth else 'N/A'}
- EBITDA: {format_number(pro_forma.acq_ebitda, currency_symbol=cs_a)}
- Margins: Gross {format_pct(acq.gross_margins)}, Operating {format_pct(acq.operating_margins)}

TARGET: {tgt.name} ({tgt.ticker})
- Sector: {tgt.sector} | Industry: {tgt.industry}
- Market Cap: {format_number(tgt.market_cap, currency_symbol=cs_t)}
- Revenue: {format_number(pro_forma.tgt_revenue, currency_symbol=cs_t)} | Revenue Growth: {f'{tgt.revenue_growth:.1f}%' if tgt.revenue_growth else 'N/A'}
- EBITDA: {format_number(pro_forma.tgt_ebitda, currency_symbol=cs_t)}
- Margins: Gross {format_pct(tgt.gross_margins)}, Operating {format_pct(tgt.operating_margins)}
- Free Cash Flow: {tgt_fcf}
- Standalone Trading Multiples: P/E {tgt_trailing_pe} (trailing), {tgt_forward_pe} (forward) | EV/EBITDA {tgt_ev_ebitda}

DEAL TERMS:
- Purchase Price: {format_number(pro_forma.purchase_price, currency_symbol=cs_a)} at {cs_a}{pro_forma.offer_price_per_share:.2f}/share
- Offer Premium: {premium_pct:.0f}%
- Implied EV/EBITDA: {impl_ev_ebitda} (vs target trading at {tgt_ev_ebitda})
- Implied P/E: {impl_pe} (vs target trading at {tgt_trailing_pe})
- Pro Forma Combined Revenue: {format_number(pro_forma.pf_revenue, currency_symbol=cs_a)}
- Pro Forma Combined EBITDA: {format_number(pro_forma.pf_ebitda, currency_symbol=cs_a)} (incl. synergies)

Provide EXACTLY in this format (use the tag labels in brackets at the start of each bullet):

STRATEGIC_RATIONALE:
- [DEAL LOGIC] 2-3 sentences: What is the acquirer actually buying — revenue base, IP/technology, customer relationships, geographic access, or cost takeout? Name the specific strategic thesis (horizontal consolidation, vertical integration, capability acquisition, geographic expansion, or diversification). State whether this is offensive (growth-driven) or defensive (market-share protection).
- [FINANCIAL MERIT] Evaluate the price paid: compare implied EV/EBITDA and P/E to the target's standalone trading multiples. Is the acquirer overpaying, paying fair value, or getting a bargain after synergies? What does the premium imply about the acquirer's confidence in synergy capture?
- [STRATEGIC FIT] How complementary are the two businesses? Assess overlap vs. adjacency. Where specifically do cost and revenue synergies come from — headcount, facilities, procurement, cross-selling, or bundling?
- [COMPETITIVE POSITIONING] How does the combined entity rank in its market? Does this deal create a category leader, close a gap to a larger rival, or merely add scale without strategic differentiation?
"""


def _build_deal_risks_prompt(acq: CompanyData, tgt: CompanyData, pro_forma, assumptions=None) -> str:
    cs_a = acq.currency_symbol

    # Goodwill metrics
    goodwill_pct = (pro_forma.goodwill / pro_forma.purchase_price * 100) if pro_forma.purchase_price else 0

    # Deal size relative to acquirer
    deal_size_pct = (pro_forma.purchase_price / acq.market_cap * 100) if acq.market_cap else 0

    # Cash/stock mix
    pct_cash = assumptions.pct_cash if assumptions else 50
    pct_stock = assumptions.pct_stock if assumptions else 50
    premium = assumptions.offer_premium_pct if assumptions else 0

    return f"""You are an M&A risk analyst writing a risk assessment memo for {acq.name} acquiring {tgt.name}.

DEAL METRICS:
- Purchase Price: {format_number(pro_forma.purchase_price, currency_symbol=cs_a)} ({deal_size_pct:.0f}% of acquirer market cap)
- Offer Premium: {premium:.0f}%
- Consideration Mix: {pct_cash:.0f}% cash / {pct_stock:.0f}% stock
- Goodwill Created: {format_number(pro_forma.goodwill, currency_symbol=cs_a)} ({goodwill_pct:.0f}% of purchase price)
- Pro Forma Net Debt: {format_number(pro_forma.pf_net_debt, currency_symbol=cs_a)}
- Pro Forma Leverage: {f'{pro_forma.pf_leverage_ratio:.1f}x' if pro_forma.pf_leverage_ratio else 'N/A'} Debt/EBITDA
- Pro Forma Interest: {format_number(pro_forma.pf_total_interest, currency_symbol=cs_a)} annual
- Interest Coverage: {f'{pro_forma.pf_interest_coverage:.1f}x' if pro_forma.pf_interest_coverage else 'N/A'}
- EPS Impact: {pro_forma.accretion_dilution_pct:+.1f}% ({'accretive' if pro_forma.is_accretive else 'dilutive'})

COMPANY CONTEXT:
- Acquirer: {acq.sector} / {acq.industry} | Revenue Growth: {f'{acq.revenue_growth:.1f}%' if acq.revenue_growth else 'N/A'}
- Target: {tgt.sector} / {tgt.industry} | Revenue Growth: {f'{tgt.revenue_growth:.1f}%' if tgt.revenue_growth else 'N/A'}
- Same industry: {acq.industry == tgt.industry}

Provide EXACTLY in this format (use the tag labels in brackets at the start of each bullet). Anchor every risk in specific numbers from above:

DEAL_RISKS:
- [VALUATION] Is the acquirer overpaying? Evaluate the {premium:.0f}% premium. Goodwill of {goodwill_pct:.0f}% of purchase price — what happens if synergies fall 50% short? Would impairment risk be material?
- [FINANCIAL] Pro forma leverage of {f'{pro_forma.pf_leverage_ratio:.1f}x' if pro_forma.pf_leverage_ratio else 'N/A'} — evaluate balance sheet stress. Can the combined entity service {format_number(pro_forma.pf_total_interest, currency_symbol=cs_a)} in annual interest from {format_number(pro_forma.pf_ebitda, currency_symbol=cs_a)} EBITDA? Deleveraging timeline? Rating migration risk?
- [INTEGRATION] Given the {'same' if acq.industry == tgt.industry else 'different'} industry overlap, assess operational integration complexity — systems, culture, talent retention, customer churn risk.
- [EXECUTION] This deal is {deal_size_pct:.0f}% of the acquirer's market cap — evaluate management bandwidth. Timeline risk if regulatory review extends to 12-18 months?
- [MARKET] Deal is {pro_forma.accretion_dilution_pct:+.1f}% {'accretive' if pro_forma.is_accretive else 'dilutive'} to EPS. How will the market react given the {pct_cash:.0f}/{pct_stock:.0f} cash/stock mix? Macro sensitivity?
"""


def _build_synergy_assessment_prompt(acq: CompanyData, tgt: CompanyData, pro_forma, assumptions) -> str:
    cs_a = acq.currency_symbol
    return f"""You are an M&A synergy analyst evaluating the {acq.name} + {tgt.name} combination.

Cost Synergies: {format_number(pro_forma.cost_synergies, currency_symbol=cs_a)} ({assumptions.cost_synergies_pct:.0f}% of target SG&A)
Revenue Synergies: {format_number(pro_forma.revenue_synergies, currency_symbol=cs_a)} ({assumptions.revenue_synergies_pct:.0f}% of target revenue)
Total Synergies: {format_number(pro_forma.total_synergies, currency_symbol=cs_a)}
Synergy NPV: {format_number(pro_forma.synergy_npv, currency_symbol=cs_a)}

Acquirer operates in: {acq.industry} | Target operates in: {tgt.industry}
Same sector: {acq.sector == tgt.sector}

Provide in EXACT format:

SYNERGY_ASSESSMENT:
- [realism of cost synergy assumptions — are they achievable? typical range is 5-15% of target SG&A]
- [realism of revenue synergy assumptions — harder to achieve, typical realization rate 30-50%]
- [expected timeline — when would synergies be fully realized? typically 2-3 years]
- [risks to synergy realization — what could prevent achieving these numbers?]
"""


def _build_deal_verdict_prompt(acq: CompanyData, tgt: CompanyData, pro_forma, assumptions) -> str:
    cs_a = acq.currency_symbol

    # Goodwill and synergy coverage
    goodwill_pct = (pro_forma.goodwill / pro_forma.purchase_price * 100) if pro_forma.purchase_price else 0
    synergy_covers_goodwill = "yes" if pro_forma.synergy_npv >= pro_forma.goodwill else "no"

    # Interest coverage
    int_cov = f"{pro_forma.pf_interest_coverage:.1f}x" if pro_forma.pf_interest_coverage else "N/A"

    # Target standalone growth
    tgt_growth = f"{tgt.revenue_growth:.1f}%" if tgt.revenue_growth else "N/A"

    return f"""You are an M&A committee advisor rendering a final verdict on {acq.name} acquiring {tgt.name}. Write like a real M&A committee memo — be direct, quantitative, and take a clear position.

KEY DEAL FACTS:
- Purchase Price: {format_number(pro_forma.purchase_price, currency_symbol=cs_a)}
- Premium: {assumptions.offer_premium_pct:.0f}%
- Mix: {assumptions.pct_cash:.0f}% cash / {assumptions.pct_stock:.0f}% stock
- EPS Impact: {pro_forma.accretion_dilution_pct:+.1f}% ({'accretive' if pro_forma.is_accretive else 'dilutive'})
- Pro Forma Leverage: {f'{pro_forma.pf_leverage_ratio:.1f}x' if pro_forma.pf_leverage_ratio else 'N/A'}
- Interest Coverage: {int_cov}
- Implied EV/EBITDA: {f'{pro_forma.implied_ev_ebitda:.1f}x' if pro_forma.implied_ev_ebitda else 'N/A'}
- Total Synergies: {format_number(pro_forma.total_synergies, currency_symbol=cs_a)}
- Synergy NPV: {format_number(pro_forma.synergy_npv, currency_symbol=cs_a)}
- Goodwill: {format_number(pro_forma.goodwill, currency_symbol=cs_a)} ({goodwill_pct:.0f}% of purchase price)
- Synergy NPV covers goodwill: {synergy_covers_goodwill}
- Combined Revenue: {format_number(pro_forma.pf_revenue, currency_symbol=cs_a)}
- Combined EBITDA: {format_number(pro_forma.pf_ebitda, currency_symbol=cs_a)}
- Target Standalone Growth: {tgt_growth}
- Same industry: {acq.industry == tgt.industry}

Provide EXACTLY in this format (use the tag labels in brackets at the start of each bullet). Be specific and quantitative in every section:

DEAL_VERDICT:
- [OVERALL] 2-3 sentences: Render a clear judgment — is this deal value-creative or value-destructive for the acquirer's shareholders? Anchor in the numbers: the {pro_forma.accretion_dilution_pct:+.1f}% EPS impact, the {assumptions.offer_premium_pct:.0f}% premium, and whether synergy NPV ({format_number(pro_forma.synergy_npv, currency_symbol=cs_a)}) justifies the goodwill ({format_number(pro_forma.goodwill, currency_symbol=cs_a)}). State a clear recommendation: proceed, proceed with reservations, or walk away.
- [BULL CASE] 1-2 sentences: What has to go right — be specific and quantified. Reference actual synergy and EPS numbers.
- [BEAR CASE] 1-2 sentences: What could go wrong — be specific and quantified. Reference what happens if synergies miss by 50% and leverage implications.
- [KEY CONDITION] 1 sentence: The single most critical factor that determines whether this deal succeeds or fails.

DEAL_GRADE:
[A/B/C/D/F with 1-line justification. A = value-creative with manageable risk, B = strategically sound but some concerns, C = marginal, D = significant value concerns, F = value-destructive]
"""


# ── Merger Response Parsing ─────────────────────────────────

def _parse_merger_sections(text: str) -> dict:
    """Parse merger LLM output into named sections."""
    sections = {}
    current_key = None
    current_lines = []

    key_map = {
        "STRATEGIC_RATIONALE": "strategic_rationale",
        "DEAL_RISKS": "deal_risks",
        "SYNERGY_ASSESSMENT": "synergy_assessment",
        "DEAL_VERDICT": "deal_verdict",
        "DEAL_GRADE": "deal_grade",
    }

    for line in text.strip().split("\n"):
        stripped = line.strip()
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


# ── Merger Deterministic Fallbacks ──────────────────────────

def _fallback_merger_insights(acq, tgt, pro_forma, assumptions) -> MergerInsights:
    """Build deterministic merger insights with finance-grade analysis."""
    cs = acq.currency_symbol
    same_sector = acq.sector == tgt.sector
    same_industry = acq.industry == tgt.industry

    # ── Derived metrics used across sections ──────────────
    leverage = pro_forma.pf_leverage_ratio or 0
    int_cov = pro_forma.pf_interest_coverage or 0
    goodwill_pct = (pro_forma.goodwill / pro_forma.purchase_price * 100) if pro_forma.purchase_price else 0
    deal_size_pct = (pro_forma.purchase_price / acq.market_cap * 100) if acq.market_cap else 0
    premium = assumptions.offer_premium_pct

    # Target standalone trading multiples
    tgt_ev_ebitda = tgt.ev_to_ebitda
    impl_ev_ebitda = pro_forma.implied_ev_ebitda

    # Combined operating margin vs standalone
    pf_op_margin = (pro_forma.pf_ebitda / pro_forma.pf_revenue * 100) if pro_forma.pf_revenue else 0
    acq_op_margin = (acq.operating_margins or 0) * 100
    tgt_op_margin = (tgt.operating_margins or 0) * 100

    # Synergy NPV coverage of goodwill
    synergy_coverage = (pro_forma.synergy_npv / pro_forma.goodwill) if pro_forma.goodwill else 0

    # FCF for deleveraging estimate
    acq_fcf = 0
    if acq.free_cashflow_series is not None and len(acq.free_cashflow_series) > 0:
        acq_fcf = float(acq.free_cashflow_series.iloc[0])
    tgt_fcf = 0
    if tgt.free_cashflow_series is not None and len(tgt.free_cashflow_series) > 0:
        tgt_fcf = float(tgt.free_cashflow_series.iloc[0])
    combined_fcf = acq_fcf + tgt_fcf

    # Half synergies scenario for bear case
    half_synergies = pro_forma.total_synergies * 0.5

    # ── Strategic Rationale ───────────────────────────────
    if same_industry:
        deal_type = "horizontal consolidation"
        thesis = "offensive scale play" if (acq.market_cap or 0) > (tgt.market_cap or 0) * 3 else "transformative horizontal merger"
        synergy_source = "headcount rationalization, overlapping facilities, and procurement leverage"
    elif same_sector:
        deal_type = "adjacent capability acquisition"
        thesis = "capability-driven expansion within the sector"
        synergy_source = "shared infrastructure, cross-selling to combined customer base, and bundled offerings"
    else:
        deal_type = "diversification play"
        thesis = "defensive diversification away from core market"
        synergy_source = "corporate overhead reduction and limited operational overlap"

    # Valuation comparison
    val_comparison = ""
    if impl_ev_ebitda and tgt_ev_ebitda:
        val_premium = ((impl_ev_ebitda / tgt_ev_ebitda) - 1) * 100
        val_comparison = (
            f"The acquirer is paying {impl_ev_ebitda:.1f}x EV/EBITDA vs the target's standalone trading multiple "
            f"of {tgt_ev_ebitda:.1f}x, a {val_premium:.0f}% premium to market multiples."
        )
    elif impl_ev_ebitda:
        val_comparison = f"Implied EV/EBITDA of {impl_ev_ebitda:.1f}x on the deal."

    # Goodwill characterization
    gw_label = "modest" if goodwill_pct < 40 else "significant" if goodwill_pct < 70 else "substantial"

    strategic = (
        f"- [DEAL LOGIC] This deal represents {deal_type} — a {thesis}. {acq.name} "
        f"({format_number(acq.market_cap, currency_symbol=cs)} market cap) is acquiring {tgt.name}'s "
        f"{format_number(pro_forma.tgt_revenue, currency_symbol=cs)} revenue base at a {premium:.0f}% premium "
        f"for {format_number(pro_forma.purchase_price, currency_symbol=cs)}. "
        f"The strategic thesis is {'growth-driven' if (tgt.revenue_growth or 0) > (acq.revenue_growth or 0) else 'cost-driven consolidation'}.\n"
        f"- [FINANCIAL MERIT] {val_comparison} "
        f"Goodwill of {format_number(pro_forma.goodwill, currency_symbol=cs)} represents {goodwill_pct:.0f}% "
        f"of the purchase price, indicating {gw_label} premium to book value. "
        f"Synergy NPV of {format_number(pro_forma.synergy_npv, currency_symbol=cs)} covers "
        f"{synergy_coverage:.1f}x the goodwill created — "
        f"{'suggesting the premium is well-supported by synergy economics' if synergy_coverage >= 1.0 else 'raising questions about whether the premium paid can be recovered through synergies alone'}.\n"
        f"- [STRATEGIC FIT] Combined operating margin of {pf_op_margin:.1f}% vs acquirer's "
        f"{acq_op_margin:.1f}% and target's {tgt_op_margin:.1f}%. "
        f"Primary synergy sources: {synergy_source}. "
        f"Cost synergies of {format_number(pro_forma.cost_synergies, currency_symbol=cs)} "
        f"({assumptions.cost_synergies_pct:.0f}% of target SG&A) are the primary value driver.\n"
        f"- [COMPETITIVE POSITIONING] The combined entity would have "
        f"{format_number(pro_forma.pf_revenue, currency_symbol=cs)} in revenue and "
        f"{format_number(pro_forma.pf_ebitda, currency_symbol=cs)} in EBITDA. "
        f"{'This creates meaningful scale in a common market' if same_industry else 'This broadens the revenue mix' if same_sector else 'This diversifies into an unrelated market, without clear competitive synergy'}."
    )

    # ── Deal Risks (graduated severity) ───────────────────

    # VALUATION risk
    if premium > 50:
        val_severity = "Aggressive"
        val_detail = f"The {premium:.0f}% premium is well above the 25-35% typical range for strategic transactions"
    elif premium > 40:
        val_severity = "Elevated"
        val_detail = f"The {premium:.0f}% premium is above the 25-35% norm"
    elif premium > 25:
        val_severity = "Moderate"
        val_detail = f"The {premium:.0f}% premium is within the typical range"
    else:
        val_severity = "Low"
        val_detail = f"The {premium:.0f}% premium is below the sector average"

    gw_risk = f"Goodwill of {goodwill_pct:.0f}% of purchase price represents {'material impairment risk' if goodwill_pct > 60 else 'manageable impairment exposure' if goodwill_pct > 40 else 'limited goodwill risk'}"
    if synergy_coverage < 0.5:
        gw_risk += "; synergy NPV covers less than half the goodwill — significant risk if synergies disappoint"
    elif synergy_coverage < 1.0:
        gw_risk += f"; synergy NPV covers only {synergy_coverage:.1f}x the goodwill"

    # FINANCIAL risk
    if leverage >= 5:
        lev_label = "Distressed-level"
        lev_detail = "severely constrained strategic flexibility and high credit risk"
    elif leverage >= 4:
        lev_label = "Concerning"
        lev_detail = "meaningful credit risk with limited financial flexibility"
    elif leverage >= 3:
        lev_label = "Elevated"
        lev_detail = "above-average leverage that will require disciplined deleveraging"
    elif leverage >= 2:
        lev_label = "Manageable"
        lev_detail = "investment-grade-consistent leverage"
    else:
        lev_label = "Comfortable"
        lev_detail = "conservative leverage leaving ample capacity"

    if int_cov > 5:
        cov_label = "strong coverage cushion"
    elif int_cov > 3:
        cov_label = "adequate coverage"
    elif int_cov > 2:
        cov_label = "tight coverage — limited margin of safety"
    else:
        cov_label = "unsustainable coverage — cash flow stress likely"

    # Deleveraging timeline estimate
    delev_str = ""
    if combined_fcf > 0 and pro_forma.pf_net_debt > 0 and pro_forma.pf_ebitda > 0:
        target_debt = 2.5 * pro_forma.pf_ebitda
        excess_debt = pro_forma.pf_net_debt - target_debt
        if excess_debt > 0:
            years_to_delever = excess_debt / (combined_fcf * 0.5)
            delev_str = f" Estimated ~{years_to_delever:.1f} years to delever to 2.5x at 50% FCF allocation."
        else:
            delev_str = " Already below 2.5x target — no deleveraging needed."

    # INTEGRATION risk
    if same_industry:
        integ_detail = (
            f"Same-industry deal reduces business model risk but increases integration complexity "
            f"from overlapping functions — expect headcount redundancies, systems consolidation, "
            f"and potential customer churn during transition."
        )
    elif same_sector:
        integ_detail = (
            f"Adjacent-sector combination has moderate integration complexity — shared support functions "
            f"but different operating models and customer bases require careful coordination."
        )
    else:
        integ_detail = (
            f"Cross-sector diversification minimizes operational overlap but maximizes cultural integration risk "
            f"— fundamentally different business processes, metrics, and talent requirements."
        )

    # EXECUTION risk
    if deal_size_pct > 50:
        exec_label = "transformative acquisition with significant execution risk"
        exec_detail = f"At {deal_size_pct:.0f}% of acquirer market cap, this is a bet-the-company deal requiring flawless execution"
    elif deal_size_pct > 10:
        exec_label = "material bolt-on with meaningful execution demands"
        exec_detail = f"At {deal_size_pct:.0f}% of acquirer market cap, management bandwidth will be substantially consumed"
    else:
        exec_label = "tuck-in with manageable complexity"
        exec_detail = f"At {deal_size_pct:.0f}% of acquirer market cap, execution risk is contained"

    # MARKET risk
    if assumptions.pct_stock > 60:
        mix_risk = f"The {assumptions.pct_stock:.0f}% stock consideration exposes the deal to acquirer share price volatility and creates dilution risk"
    elif assumptions.pct_stock > 30:
        mix_risk = f"The {assumptions.pct_cash:.0f}/{assumptions.pct_stock:.0f} cash/stock mix balances dilution against leverage"
    else:
        mix_risk = f"The heavily cash-funded structure ({assumptions.pct_cash:.0f}%) limits dilution but adds balance sheet risk"

    # Check if accretion relies on synergies
    accretion_ex_syn = pro_forma.accretion_dilution_pct  # approximate — full strip would need recalc
    market_detail = (
        f"Deal is {pro_forma.accretion_dilution_pct:+.1f}% "
        f"{'accretive' if pro_forma.is_accretive else 'dilutive'} to EPS. "
        f"{mix_risk}."
    )

    risks = (
        f"- [VALUATION] {val_severity} valuation risk. {val_detail}. {gw_risk}.\n"
        f"- [FINANCIAL] {lev_label} — pro forma leverage of {leverage:.1f}x implies {lev_detail}. "
        f"Interest coverage at {int_cov:.1f}x represents {cov_label}.{delev_str}\n"
        f"- [INTEGRATION] {integ_detail}\n"
        f"- [EXECUTION] This is a {exec_label}. {exec_detail}.\n"
        f"- [MARKET] {market_detail}"
    )

    # ── Synergy Assessment (unchanged) ────────────────────
    synergy = (
        f"- Cost synergies of {format_number(pro_forma.cost_synergies, currency_symbol=cs)} "
        f"({assumptions.cost_synergies_pct:.0f}% of target SG&A) are "
        f"{'conservative and achievable' if assumptions.cost_synergies_pct <= 15 else 'aggressive and may be challenging to realize'}.\n"
        f"- Revenue synergies of {format_number(pro_forma.revenue_synergies, currency_symbol=cs)} "
        f"({assumptions.revenue_synergies_pct:.0f}% of target revenue) are "
        f"{'realistic' if assumptions.revenue_synergies_pct <= 3 else 'optimistic — revenue synergies typically harder to achieve'}.\n"
        f"- Expected timeline: full synergy realization in 2-3 years post-close.\n"
        f"- Synergy NPV of {format_number(pro_forma.synergy_npv, currency_symbol=cs)} "
        f"{'partially offsets' if pro_forma.synergy_npv < pro_forma.goodwill else 'exceeds'} "
        f"goodwill of {format_number(pro_forma.goodwill, currency_symbol=cs)}."
    )

    # ── Deal Verdict & Grade (weighted multi-factor) ──────

    # Accretion/Dilution (25 pts)
    ad = pro_forma.accretion_dilution_pct
    if ad > 5:
        pts_ad = 25
    elif ad > 2:
        pts_ad = 20
    elif ad > 0:
        pts_ad = 15
    elif ad > -2:
        pts_ad = 8
    else:
        pts_ad = 0

    # Leverage (20 pts)
    if leverage < 2.5:
        pts_lev = 20
    elif leverage < 3.5:
        pts_lev = 15
    elif leverage < 4.5:
        pts_lev = 8
    else:
        pts_lev = 0

    # Premium vs Synergy Coverage (20 pts)
    if synergy_coverage > 1.5:
        pts_syn = 20
    elif synergy_coverage > 1.0:
        pts_syn = 15
    elif synergy_coverage > 0.5:
        pts_syn = 8
    else:
        pts_syn = 0

    # Strategic Fit (15 pts)
    if same_industry:
        pts_fit = 15
    elif same_sector:
        pts_fit = 10
    else:
        pts_fit = 3

    # Premium Reasonableness (10 pts)
    if premium < 25:
        pts_prem = 10
    elif premium <= 35:
        pts_prem = 8
    elif premium <= 50:
        pts_prem = 4
    else:
        pts_prem = 0

    # Interest Coverage (10 pts)
    if int_cov > 5:
        pts_cov = 10
    elif int_cov > 3:
        pts_cov = 7
    elif int_cov > 2:
        pts_cov = 3
    else:
        pts_cov = 0

    total_score = pts_ad + pts_lev + pts_syn + pts_fit + pts_prem + pts_cov

    if total_score >= 80:
        grade = "A"
    elif total_score >= 60:
        grade = "B"
    elif total_score >= 40:
        grade = "C"
    elif total_score >= 20:
        grade = "D"
    else:
        grade = "F"

    # Recommendation
    if grade in ("A", "B"):
        recommendation = "proceed" if grade == "A" else "proceed with reservations"
    elif grade == "C":
        recommendation = "marginal — renegotiate terms or walk away"
    else:
        recommendation = "walk away"

    # Value creative/destructive
    value_judgment = "value-creative" if pro_forma.is_accretive and synergy_coverage >= 0.8 else \
                     "marginally accretive but premium-heavy" if pro_forma.is_accretive else \
                     "value-destructive"

    # Quantified bull case
    upside_synergies = pro_forma.total_synergies * 1.25
    upside_eps_est = pro_forma.pf_eps * 1.02 if pro_forma.pf_eps else 0  # rough approximation

    # Quantified bear case
    bear_syn = pro_forma.total_synergies * 0.5
    bear_leverage = leverage * 1.15  # integration costs add ~15% to debt load

    # Key condition
    if pts_lev <= 8:
        key_condition = "Successful deleveraging to below 3.5x within 24 months is the make-or-break condition."
    elif pts_syn <= 8:
        key_condition = "Realizing at least 75% of announced synergies within the first 2 years is the critical success factor."
    elif pts_ad == 0:
        key_condition = "Achieving EPS accretion by Year 2 is essential to justify the premium paid."
    elif not same_sector:
        key_condition = "Management's ability to operate a diversified business without losing focus on the core is the key risk."
    else:
        key_condition = "Speed of integration execution — the faster synergies are captured, the more value is created for shareholders."

    # Score breakdown for transparency
    score_detail = f"Score: {total_score}/100 (Accretion {pts_ad}/25, Leverage {pts_lev}/20, Synergy Coverage {pts_syn}/20, Strategic Fit {pts_fit}/15, Premium {pts_prem}/10, Coverage {pts_cov}/10)"

    verdict = (
        f"- [OVERALL] This deal is {value_judgment} for {acq.name} shareholders. "
        f"The {pro_forma.accretion_dilution_pct:+.1f}% EPS impact and {premium:.0f}% premium are "
        f"{'supported' if synergy_coverage >= 1.0 else 'not fully justified'} by synergy NPV of "
        f"{format_number(pro_forma.synergy_npv, currency_symbol=cs)} against goodwill of "
        f"{format_number(pro_forma.goodwill, currency_symbol=cs)} ({synergy_coverage:.1f}x coverage). "
        f"Recommendation: {recommendation}. {score_detail}.\n"
        f"- [BULL CASE] If cost synergies reach {format_number(upside_synergies, currency_symbol=cs)} "
        f"(25% above base case) and revenue synergies fully materialize, "
        f"the combined entity generates {format_number(pro_forma.pf_ebitda, currency_symbol=cs)} EBITDA "
        f"with improving margins — accelerating deleveraging and driving re-rating potential.\n"
        f"- [BEAR CASE] If only 50% of synergies ({format_number(bear_syn, currency_symbol=cs)}) materialize "
        f"and integration costs exceed plan, pro forma leverage could reach ~{bear_leverage:.1f}x "
        f"with {'meaningful dilution to EPS' if not pro_forma.is_accretive else 'accretion narrowing to breakeven'} "
        f"— risking credit downgrade and shareholder value erosion.\n"
        f"- [KEY CONDITION] {key_condition}"
    )

    return MergerInsights(
        strategic_rationale=strategic,
        deal_risks=risks,
        synergy_assessment=synergy,
        deal_verdict=verdict,
        deal_grade=grade,
    )


# ── Merger Insights Orchestrator ────────────────────────────

def generate_merger_insights(acq, tgt, pro_forma, assumptions) -> MergerInsights:
    """Generate AI-powered merger insights, with deterministic fallback."""
    if not (os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        return _fallback_merger_insights(acq, tgt, pro_forma, assumptions)

    insights = MergerInsights()

    # Strategic Rationale
    try:
        text = _call_llm(_build_strategic_rationale_prompt(acq, tgt, pro_forma), max_tokens=1500)
        sections = _parse_merger_sections(text)
        insights.strategic_rationale = sections.get("strategic_rationale", "")
    except Exception as e:
        print(f"Merger strategic rationale LLM failed ({e})")

    # Deal Risks
    try:
        text = _call_llm(_build_deal_risks_prompt(acq, tgt, pro_forma, assumptions), max_tokens=1500)
        sections = _parse_merger_sections(text)
        insights.deal_risks = sections.get("deal_risks", "")
    except Exception as e:
        print(f"Merger deal risks LLM failed ({e})")

    # Synergy Assessment
    try:
        text = _call_llm(_build_synergy_assessment_prompt(acq, tgt, pro_forma, assumptions), max_tokens=1200)
        sections = _parse_merger_sections(text)
        insights.synergy_assessment = sections.get("synergy_assessment", "")
    except Exception as e:
        print(f"Merger synergy assessment LLM failed ({e})")

    # Deal Verdict
    try:
        text = _call_llm(_build_deal_verdict_prompt(acq, tgt, pro_forma, assumptions), max_tokens=1200)
        sections = _parse_merger_sections(text)
        insights.deal_verdict = sections.get("deal_verdict", "")
        grade_text = sections.get("deal_grade", "B").strip().upper()
        if grade_text and grade_text[0] in "ABCDF":
            insights.deal_grade = grade_text[0]
    except Exception as e:
        print(f"Merger deal verdict LLM failed ({e})")

    # If any section is empty, fill from fallback
    fallback = _fallback_merger_insights(acq, tgt, pro_forma, assumptions)
    if not insights.strategic_rationale:
        insights.strategic_rationale = fallback.strategic_rationale
    if not insights.deal_risks:
        insights.deal_risks = fallback.deal_risks
    if not insights.synergy_assessment:
        insights.synergy_assessment = fallback.synergy_assessment
    if not insights.deal_verdict:
        insights.deal_verdict = fallback.deal_verdict
        insights.deal_grade = fallback.deal_grade

    return insights
