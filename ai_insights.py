"""
AI Insights — generates Product Overview, Management Sentiment,
and Executive Summary bullets from company data + news.

Uses OpenAI-compatible API via the OPENAI_API_KEY env var.
Falls back to a deterministic template if no API key is set.
"""

import os
from data_engine import CompanyData, format_number


def _build_prompt(cd: CompanyData) -> str:
    """Construct the LLM prompt from company data."""
    news_text = "\n".join(
        f"- {n['title']} ({n['publisher']})" for n in cd.news
    ) or "No recent news available."

    officers_text = "\n".join(
        f"- {o.get('name', 'N/A')}: {o.get('title', 'N/A')}"
        for o in cd.officers[:5]
    ) or "No officer data available."

    return f"""You are an M&A analyst preparing a tear sheet for {cd.name} ({cd.ticker}).

Company: {cd.name}
Sector: {cd.sector} | Industry: {cd.industry}
Market Cap: {format_number(cd.market_cap)}
Current Price: ${cd.current_price:.2f}
P/E Ratio: {cd.trailing_pe or 'N/A'}
Debt/Equity: {cd.debt_to_equity or 'N/A'}
Revenue Growth: {f'{cd.revenue_growth:.1f}%' if cd.revenue_growth else 'N/A'}
Deal Score: {cd.deal_score}/100

Key Officers:
{officers_text}

Recent News:
{news_text}

Provide the following in the EXACT format below (no extra text):

PRODUCT_OVERVIEW:
- [bullet 1: what the company does / key products]
- [bullet 2: competitive positioning]
- [bullet 3: growth drivers or headwinds]

MGMT_SENTIMENT:
- [bullet 1: CEO effectiveness / reputation]
- [bullet 2: recent management actions or commentary]
- [bullet 3: alignment with shareholder interests]

EXECUTIVE_SUMMARY:
- [bullet 1: investment thesis in one sentence]
- [bullet 2: key risk]
- [bullet 3: M&A attractiveness statement]
"""


def _parse_sections(text: str) -> dict:
    """Parse the structured LLM output into sections."""
    sections = {}
    current_key = None
    current_lines = []

    for line in text.strip().split("\n"):
        stripped = line.strip()
        if stripped.startswith("PRODUCT_OVERVIEW"):
            if current_key:
                sections[current_key] = "\n".join(current_lines)
            current_key = "product_overview"
            current_lines = []
        elif stripped.startswith("MGMT_SENTIMENT"):
            if current_key:
                sections[current_key] = "\n".join(current_lines)
            current_key = "mgmt_sentiment"
            current_lines = []
        elif stripped.startswith("EXECUTIVE_SUMMARY"):
            if current_key:
                sections[current_key] = "\n".join(current_lines)
            current_key = "executive_summary"
            current_lines = []
        elif stripped:
            current_lines.append(stripped)

    if current_key:
        sections[current_key] = "\n".join(current_lines)

    return sections


def _extract_bullets(text: str) -> list[str]:
    """Extract bullet points from a section of text."""
    bullets = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            bullets.append(line[2:].strip())
        elif line.startswith("* "):
            bullets.append(line[2:].strip())
        elif line:
            bullets.append(line)
    return bullets


def generate_insights_llm(cd: CompanyData) -> CompanyData:
    """Call the OpenAI API to generate insights. Requires OPENAI_API_KEY."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        prompt = _build_prompt(cd)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a senior M&A analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=800,
        )

        text = response.choices[0].message.content or ""
        sections = _parse_sections(text)

        cd.product_overview = sections.get("product_overview", "")
        cd.mgmt_sentiment = sections.get("mgmt_sentiment", "")
        cd.executive_summary_bullets = _extract_bullets(
            sections.get("executive_summary", "")
        )

    except Exception as e:
        print(f"LLM call failed ({e}), using fallback.")
        generate_insights_fallback(cd)

    return cd


def generate_insights_fallback(cd: CompanyData) -> CompanyData:
    """Deterministic fallback when no API key is available."""
    growth_desc = "growing" if (cd.revenue_growth or 0) > 0 else "contracting"
    de_desc = "manageable" if (cd.debt_to_equity or 0) < 150 else "elevated"

    cd.product_overview = (
        f"- {cd.name} operates in the {cd.industry} sector "
        f"within {cd.sector}\n"
        f"- Market capitalization of {format_number(cd.market_cap)} "
        f"with a {growth_desc} revenue trajectory\n"
        f"- Beta of {cd.beta or 'N/A'} indicates "
        f"{'above-average' if (cd.beta or 1) > 1 else 'below-average'} "
        f"market sensitivity"
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
        f"- Debt levels are {de_desc} "
        f"(D/E: {cd.debt_to_equity or 'N/A'})\n"
        f"- {'Dividend-paying' if cd.dividend_yield else 'Non-dividend'} "
        f"company suggesting "
        f"{'income-oriented' if cd.dividend_yield else 'growth-focused'} strategy"
    )

    score_label = (
        "Strong Buy" if cd.deal_score >= 70
        else "Moderate" if cd.deal_score >= 40
        else "Caution"
    )

    cd.executive_summary_bullets = [
        f"{cd.name} presents a {score_label.lower()} M&A opportunity "
        f"with a Deal Score of {cd.deal_score}/100",
        f"Key risk: {'high leverage' if (cd.debt_to_equity or 0) > 200 else 'revenue momentum'} "
        f"warrants further due diligence",
        f"Valuation at {cd.trailing_pe or 'N/A'}x P/E "
        f"{'below' if (cd.trailing_pe or 20) < 20 else 'above'} "
        f"historical averages",
    ]

    return cd


def generate_insights(cd: CompanyData) -> CompanyData:
    """Main entry point: try LLM first, fall back to deterministic."""
    if os.environ.get("OPENAI_API_KEY"):
        return generate_insights_llm(cd)
    return generate_insights_fallback(cd)
