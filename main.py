"""
M&A Profile Builder — Streamlit Application

Professional-grade company research platform with Sky.money-inspired UI.
Generates an 8-slide investment-banker-grade PowerPoint tear sheet.

Run:  streamlit run main.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os
import random
import time
from dotenv import load_dotenv

load_dotenv()

from data_engine import (
    fetch_company_data, fetch_peer_data,
    format_number, format_pct, format_multiple
)
from ai_insights import generate_insights, generate_merger_insights
from pptx_generator import generate_presentation, generate_deal_book
from merger_analysis import MergerAssumptions, calculate_pro_forma, build_football_field
import yfinance as yf

# ── Quick Ticker Lookup (for sidebar previews) ───────────────
@st.cache_data(ttl=300, show_spinner=False)
def _quick_ticker_lookup(ticker: str) -> dict:
    """Lightweight ticker lookup for sidebar preview cards."""
    if not ticker or len(ticker) < 1:
        return {}
    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        name = info.get("shortName") or info.get("longName") or ticker
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        currency = info.get("currency", "USD")
        market_cap = info.get("marketCap")
        change_pct = info.get("regularMarketChangePercent")
        # Logo URL
        website = info.get("website", "")
        domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0] if website else ""
        logo_url = f"https://logo.clearbit.com/{domain}" if domain else ""
        return {
            "name": name,
            "price": price,
            "currency": currency,
            "market_cap": market_cap,
            "change_pct": change_pct,
            "logo_url": logo_url,
            "valid": True,
        }
    except Exception:
        return {"valid": False}

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="M&A Profile Builder",
    page_icon="https://img.icons8.com/fluency/48/combo-chart.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Generate star box-shadow strings (deterministic seed) ──────
random.seed(42)
def _gen_stars(count, spread=2000):
    return ", ".join(f"{random.randint(0,spread)}px {random.randint(0,spread)}px #FFF" for _ in range(count))
_STARS1 = _gen_stars(80)
_STARS2 = _gen_stars(50)
_STARS3 = _gen_stars(30)

# ── Chart visual helpers ──────────────────────────────────
_CHART_LAYOUT_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter"),
    hoverlabel=dict(
        bgcolor="rgba(11,14,26,0.95)",
        bordercolor="rgba(107,92,231,0.4)",
        font=dict(size=11, color="#fff", family="Inter"),
    ),
    hovermode="x unified",
)

def _apply_space_grid(fig, show_x_grid=False, show_y_grid=True):
    """Apply purple-tinted dot grid for space-coordinate look."""
    if show_y_grid:
        fig.update_yaxes(gridcolor="rgba(107,92,231,0.08)", griddash="dot")
    if show_x_grid:
        fig.update_xaxes(gridcolor="rgba(107,92,231,0.08)", griddash="dot")

def _glow_line_traces(fig, x, y, color, name, width=2.5, glow_width=8, yaxis=None):
    """Add a neon glow effect: wide transparent underlay + sharp main line."""
    # Parse hex color to rgba for glow
    glow_color = color
    if color.startswith("#") and len(color) == 7:
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        glow_color = f"rgba({r},{g},{b},0.15)"
    # Glow underlay
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines", name=name,
        line=dict(color=glow_color, width=glow_width),
        showlegend=False, hoverinfo="skip",
        yaxis=yaxis,
    ))
    # Main line
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="lines+markers", name=name,
        line=dict(color=color, width=width),
        marker=dict(size=7, line=dict(color="#fff", width=1.5)),
        yaxis=yaxis,
    ))

# ── Global animated starfield (visible on ALL pages) ──────────
st.markdown(
    '<div class="global-starfield">'
    '<div class="global-star-1">&#8203;</div>'
    '<div class="global-star-2">&#8203;</div>'
    '<div class="global-star-3">&#8203;</div>'
    '<div class="global-nebula">&#8203;</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════
# COMPREHENSIVE CUSTOM CSS — Immersive space theme
# ══════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
/* ── GLOBAL ──────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

[data-testid="stApp"] {{
    background: linear-gradient(170deg, #020515, #0B0E1A, #151933, #1a1040) !important;
}}

.block-container {{
    padding-top: 0 !important;
    padding-bottom: 2rem;
    max-width: 1400px;
    position: relative;
    z-index: 1;
}}

/* ── GLOBAL STARFIELD (fixed behind all content) ──────── */
.global-starfield {{
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    z-index: 0; pointer-events: none; overflow: hidden;
}}
.global-star-1 {{
    position: absolute; top: 0; left: 0; width: 1px; height: 1px;
    box-shadow: {_STARS1};
    opacity: 0.4;
    animation: starDrift1 150s linear infinite;
}}
.global-star-1::after {{
    content: ''; position: absolute; top: 2000px; left: 0;
    width: 1px; height: 1px;
    box-shadow: {_STARS1};
}}
.global-star-2 {{
    position: absolute; top: 0; left: 0; width: 1.5px; height: 1.5px;
    box-shadow: {_STARS2};
    opacity: 0.5;
    animation: starDrift2 100s linear infinite;
}}
.global-star-2::after {{
    content: ''; position: absolute; top: 2000px; left: 0;
    width: 1.5px; height: 1.5px;
    box-shadow: {_STARS2};
}}
.global-star-3 {{
    position: absolute; top: 0; left: 0; width: 2px; height: 2px;
    box-shadow: {_STARS3};
    opacity: 0.6;
    animation: starDrift3 75s linear infinite;
}}
.global-star-3::after {{
    content: ''; position: absolute; top: 2000px; left: 0;
    width: 2px; height: 2px;
    box-shadow: {_STARS3};
}}
.global-nebula {{
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background:
        radial-gradient(ellipse at 30% 40%, rgba(107,92,231,0.06) 0%, transparent 50%),
        radial-gradient(ellipse at 70% 60%, rgba(232,99,139,0.04) 0%, transparent 50%);
    animation: nebulaPulse 30s ease-in-out infinite;
}}

/* ── GLOBAL TEXT OVERRIDES FOR NATIVE STREAMLIT ELEMENTS ─ */
[data-testid="stAppViewContainer"] {{ color: #E0DCF5; }}
[data-testid="stAlert"] {{ background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; color: #E0DCF5 !important; }}
[data-testid="stAlert"] p {{ color: #E0DCF5 !important; }}
[data-testid="stExpanderDetails"] {{ background: rgba(255,255,255,0.02) !important; }}

/* ── ANIMATIONS (15+ keyframes) ────────────────────────── */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(30px) scale(0.98); }}
    to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}
@keyframes fadeInScale {{
    from {{ opacity: 0; transform: scale(0.9); }}
    to {{ opacity: 1; transform: scale(1); }}
}}
@keyframes starDrift1 {{
    from {{ transform: translateY(0); }}
    to {{ transform: translateY(-2000px); }}
}}
@keyframes starDrift2 {{
    from {{ transform: translateY(0); }}
    to {{ transform: translateY(-2000px); }}
}}
@keyframes starDrift3 {{
    from {{ transform: translateY(0); }}
    to {{ transform: translateY(-2000px); }}
}}
@keyframes shootingStar {{
    0% {{ transform: translate(0, 0) rotate(-45deg); opacity: 0; }}
    5% {{ opacity: 1; }}
    40% {{ opacity: 1; }}
    100% {{ transform: translate(-600px, 600px) rotate(-45deg); opacity: 0; }}
}}
@keyframes nebulaPulse {{
    0%, 100% {{ opacity: 0.4; transform: scale(1); }}
    50% {{ opacity: 0.7; transform: scale(1.05); }}
}}
@keyframes float1 {{
    0%, 100% {{ transform: translate(0, 0); }}
    25% {{ transform: translate(15px, -20px); }}
    50% {{ transform: translate(-10px, -35px); }}
    75% {{ transform: translate(-20px, -10px); }}
}}
@keyframes float2 {{
    0%, 100% {{ transform: translate(0, 0); }}
    25% {{ transform: translate(-20px, 15px); }}
    50% {{ transform: translate(10px, 25px); }}
    75% {{ transform: translate(25px, -15px); }}
}}
@keyframes float3 {{
    0%, 100% {{ transform: translate(0, 0); }}
    33% {{ transform: translate(20px, -25px); }}
    66% {{ transform: translate(-15px, 20px); }}
}}
@keyframes float4 {{
    0%, 100% {{ transform: translate(0, 0); }}
    20% {{ transform: translate(-15px, -10px); }}
    40% {{ transform: translate(10px, -30px); }}
    60% {{ transform: translate(25px, -5px); }}
    80% {{ transform: translate(-5px, 15px); }}
}}
@keyframes titleGlow {{
    0%, 100% {{ opacity: 0.3; transform: scale(1); }}
    50% {{ opacity: 0.6; transform: scale(1.1); }}
}}
@keyframes gradientShift {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}
@keyframes shimmerLine {{
    0% {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
}}
@keyframes gentlePulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.8; }}
}}
@keyframes glowPulse {{
    0%, 100% {{ box-shadow: 0 0 5px rgba(107,92,231,0.3); }}
    50% {{ box-shadow: 0 0 15px rgba(107,92,231,0.6); }}
}}
@keyframes twinkle {{
    0%, 100% {{ opacity: 0.3; }}
    50% {{ opacity: 1; }}
}}
@keyframes pulse-glow {{
    0%, 100% {{ opacity: 0.6; }}
    50% {{ opacity: 1; }}
}}
@keyframes shimmer {{
    0% {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
}}
@keyframes borderGlow {{
    0%, 100% {{ border-color: rgba(107,92,231,0.3); }}
    50% {{ border-color: rgba(155,138,255,0.6); }}
}}
@keyframes rocketLaunch {{
    0% {{ transform: translateY(0) scale(1); opacity: 1; }}
    60% {{ transform: translateY(-120px) scale(0.9); opacity: 0.8; }}
    100% {{ transform: translateY(-300px) scale(0.6); opacity: 0; }}
}}
@keyframes flameFlicker {{
    0%, 100% {{ transform: scaleY(1) scaleX(1); opacity: 0.9; }}
    25% {{ transform: scaleY(1.3) scaleX(0.85); opacity: 1; }}
    50% {{ transform: scaleY(0.8) scaleX(1.15); opacity: 0.85; }}
    75% {{ transform: scaleY(1.15) scaleX(0.9); opacity: 1; }}
}}
@keyframes exhaustTrail {{
    0% {{ opacity: 0.6; transform: translateY(0); }}
    100% {{ opacity: 0; transform: translateY(40px); }}
}}
@keyframes missionPulse {{
    0%, 100% {{ box-shadow: 0 0 8px rgba(107,92,231,0.2); }}
    50% {{ box-shadow: 0 0 20px rgba(107,92,231,0.5), 0 0 40px rgba(107,92,231,0.15); }}
}}
@keyframes checkPop {{
    0% {{ transform: scale(0); }}
    60% {{ transform: scale(1.25); }}
    100% {{ transform: scale(1); }}
}}
@keyframes progressGlow {{
    0% {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
}}
@keyframes spin {{
    from {{ transform: rotate(0deg); }}
    to {{ transform: rotate(360deg); }}
}}
@keyframes slideInLeft {{
    from {{ opacity: 0; transform: translateX(-20px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes slideInRight {{
    from {{ opacity: 0; transform: translateX(20px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes countUp {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes borderShimmer {{
    0% {{ background-position: 0% 0%; }}
    100% {{ background-position: 100% 100%; }}
}}
@keyframes cardReveal {{
    from {{ opacity: 0; transform: translateY(15px) scale(0.98); }}
    to {{ opacity: 1; transform: none; }}
}}
@keyframes pulseRing {{
    0% {{ transform: scale(1); opacity: 0.6; }}
    100% {{ transform: scale(1.5); opacity: 0; }}
}}
@keyframes sb-fill {{
    from {{ max-width: 0; }}
    to {{ max-width: 100%; }}
}}
@keyframes sb-btn-pulse {{
    0%, 100% {{ box-shadow: 0 4px 20px rgba(107,92,231,0.3); }}
    50% {{ box-shadow: 0 4px 30px rgba(107,92,231,0.55); }}
}}
@keyframes orbBreath1 {{
    0%, 100% {{ filter: blur(80px) hue-rotate(0deg); }}
    50% {{ filter: blur(80px) hue-rotate(30deg); }}
}}
@keyframes orbBreath4 {{
    0%, 100% {{ filter: blur(90px) hue-rotate(0deg); }}
    50% {{ filter: blur(90px) hue-rotate(30deg); }}
}}
@keyframes bounceIn {{
    0%   {{ opacity: 0; transform: scale(0.85) translateY(30px); }}
    50%  {{ opacity: 1; transform: scale(1.03) translateY(-5px); }}
    70%  {{ transform: scale(0.98) translateY(2px); }}
    100% {{ opacity: 1; transform: scale(1) translateY(0); }}
}}
@keyframes slideUpBounce {{
    0%   {{ opacity: 0; transform: translateY(40px); }}
    60%  {{ opacity: 1; transform: translateY(-8px); }}
    80%  {{ transform: translateY(3px); }}
    100% {{ transform: translateY(0); }}
}}
@keyframes chartGlow {{
    0%, 100% {{ box-shadow: 0 2px 15px rgba(107,92,231,0.15); }}
    50%      {{ box-shadow: 0 8px 35px rgba(107,92,231,0.3); }}
}}
/* Elastic bounce for chart containers — chartscss.org inspired */
@keyframes chartBounceIn {{
    0%   {{ transform: scale(0.92) translateY(20px); opacity: 0; }}
    40%  {{ transform: scale(1.03) translateY(-4px); opacity: 1; }}
    60%  {{ transform: scaleY(0.97) scaleX(1.02); }}
    80%  {{ transform: scaleY(1.01) scaleX(0.99); }}
    100% {{ transform: scale(1); }}
}}
/* Glow pulse on chart data */
@keyframes dataGlowPulse {{
    0%, 100% {{ box-shadow: none; }}
    50%      {{ box-shadow: 0 0 4px 0 rgba(107,92,231,0.4), 0 0 20px 5px rgba(107,92,231,0.15); }}
}}
/* Scanner keyframes (profile loading) */
@keyframes scannerSweep {{
    0%, 100% {{ transform: rotate(-15deg); }}
    50%      {{ transform: rotate(15deg); }}
}}
@keyframes scannerLock {{
    0%   {{ transform: scale(1); filter: drop-shadow(0 0 12px rgba(6,182,212,0.5)); }}
    50%  {{ transform: scale(1.15); filter: drop-shadow(0 0 25px rgba(16,185,129,0.7)); }}
    100% {{ transform: scale(1); filter: drop-shadow(0 0 15px rgba(16,185,129,0.5)); }}
}}
@keyframes scannerBeamSweep {{
    0%   {{ transform: scaleX(0.3) rotate(-20deg); opacity: 0.3; }}
    50%  {{ transform: scaleX(1) rotate(0deg); opacity: 0.8; }}
    100% {{ transform: scaleX(0.3) rotate(20deg); opacity: 0.3; }}
}}
@keyframes scannerRingPulse {{
    0%   {{ transform: translate(-50%, -50%) scale(1); opacity: 0.4; }}
    100% {{ transform: translate(-50%, -50%) scale(2); opacity: 0; }}
}}
@keyframes scannerPhasePulse {{
    0%, 100% {{ box-shadow: 0 0 8px rgba(6,182,212,0.2); }}
    50%      {{ box-shadow: 0 0 20px rgba(6,182,212,0.5), 0 0 40px rgba(6,182,212,0.15); }}
}}

/* ── SIDEBAR ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0B0E1A 0%, #10132A 50%, #151933 100%);
    border-right: 1px solid rgba(107,92,231,0.2);
    box-shadow: 4px 0 30px rgba(107,92,231,0.08);
    min-width: 340px !important;
}}
section[data-testid="stSidebar"] > div:first-child {{
    padding: 1rem 1.5rem !important;
}}
section[data-testid="stSidebar"] * {{
    color: #C8C3E3 !important;
}}
/* Hide default radio labels */
section[data-testid="stSidebar"] .stRadio > label {{
    display: none !important;
}}
section[data-testid="stSidebar"] .stRadio > div {{
    flex-direction: row !important;
    gap: 0 !important;
    background: rgba(107,92,231,0.1);
    border-radius: 14px;
    padding: 4px;
    border: 1px solid rgba(107,92,231,0.2);
}}
section[data-testid="stSidebar"] .stRadio > div > label {{
    flex: 1 !important;
    margin: 0 !important;
    padding: 0.6rem 0.8rem !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
    cursor: pointer !important;
    background: transparent !important;
}}
section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {{
    background: linear-gradient(135deg, #6B5CE7 0%, #9B8AFF 100%) !important;
    box-shadow: 0 4px 15px rgba(107,92,231,0.4) !important;
}}
section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] span,
section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] p {{
    color: #fff !important;
}}
section[data-testid="stSidebar"] .stTextInput > div > div > input {{
    background: rgba(107,92,231,0.08);
    border: 1px solid rgba(107,92,231,0.3);
    border-radius: 12px;
    color: #fff !important;
    font-weight: 700;
    font-size: 1.2rem;
    letter-spacing: 3px;
    text-align: center;
    padding: 0.9rem;
    text-transform: uppercase;
}}
section[data-testid="stSidebar"] .stTextInput > div > div > input:focus {{
    border-color: #6B5CE7;
    box-shadow: 0 0 20px rgba(107,92,231,0.4);
}}
section[data-testid="stSidebar"] .stTextInput > div > div > input::placeholder {{
    color: #6B5CE7 !important;
    opacity: 0.5;
    letter-spacing: 1px;
    font-size: 0.85rem;
}}
section[data-testid="stSidebar"] .stButton > button {{
    background: linear-gradient(135deg, #6B5CE7 0%, #9B8AFF 100%) !important;
    color: #fff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.9rem 2rem !important;
    font-size: 1rem !important;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 20px rgba(107,92,231,0.3);
    animation: sb-btn-pulse 2s ease-in-out infinite;
    margin-top: 0.5rem !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(107,92,231,0.5);
}}
section[data-testid="stSidebar"] hr {{
    border-color: rgba(107,92,231,0.2) !important;
}}
/* Company preview card */
.sb-company-card {{
    background: linear-gradient(135deg, rgba(107,92,231,0.12), rgba(232,99,139,0.05));
    border: 1px solid rgba(107,92,231,0.25);
    border-radius: 16px;
    padding: 0.9rem 1rem;
    margin: 0.6rem 0;
    display: flex;
    align-items: center;
    gap: 0.9rem;
    animation: cardReveal 0.5s ease-out;
    transition: all 0.3s ease;
}}
.sb-company-card:hover {{
    border-color: rgba(107,92,231,0.5);
    box-shadow: 0 4px 20px rgba(107,92,231,0.2);
    transform: translateY(-2px);
}}
.sb-company-logo {{
    width: 44px;
    height: 44px;
    border-radius: 10px;
    background: #fff;
    padding: 4px;
    object-fit: contain;
    flex-shrink: 0;
}}
.sb-company-info {{
    flex: 1;
    min-width: 0;
}}
.sb-company-name {{
    font-size: 0.9rem;
    font-weight: 700;
    color: #fff !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin: 0;
    line-height: 1.3;
}}
.sb-company-ticker {{
    font-size: 0.7rem;
    color: #9B8AFF !important;
    font-weight: 600;
    letter-spacing: 1px;
}}
.sb-company-price {{
    text-align: right;
    flex-shrink: 0;
}}
.sb-company-price-value {{
    font-size: 1rem;
    font-weight: 800;
    color: #fff !important;
}}
.sb-company-price-change {{
    font-size: 0.7rem;
    font-weight: 600;
}}
.sb-company-price-change.up {{ color: #10B981 !important; }}
.sb-company-price-change.down {{ color: #EF4444 !important; }}
.sb-company-invalid {{
    background: rgba(239,68,68,0.1);
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 12px;
    padding: 0.6rem 0.9rem;
    margin: 0.5rem 0;
    font-size: 0.75rem;
    color: #EF4444 !important;
    text-align: center;
}}
/* Role label styling */
.sb-role-label {{
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #6B5CE7 !important;
    margin-bottom: 0.3rem;
    display: block;
}}
.sb-role-label.acquirer {{ color: #9B8AFF !important; }}
.sb-role-label.target {{ color: #E8638B !important; }}
}}

/* ── SIDEBAR SECTIONS (merger mode) ─────────────────────── */
.sb-section {{
    background: linear-gradient(135deg, rgba(107,92,231,0.1), rgba(232,99,139,0.03));
    border-left: 3px solid #6B5CE7;
    border-radius: 0 8px 8px 0;
    padding: 0.45rem 0.75rem;
    margin: 0.9rem 0 0.4rem 0;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.8px;
    color: #A8A3C7 !important;
    animation: slideInLeft 0.4s ease-out both;
}}
.sb-section-icon {{
    color: #9B8AFF !important;
    margin-right: 0.3rem;
    font-size: 0.55rem;
}}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [role="slider"] {{
    background: #9B8AFF !important;
    border-color: #6B5CE7 !important;
    box-shadow: 0 0 8px rgba(107,92,231,0.4);
    width: 14px !important; height: 14px !important;
}}
section[data-testid="stSidebar"] .stSlider label p {{
    font-size: 0.72rem !important;
    color: #8A85AD !important;
}}
.sb-split-bar {{
    display: flex;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin: 0.5rem 0 0.3rem 0;
    background: rgba(255,255,255,0.05);
}}
.sb-split-cash {{
    background: linear-gradient(90deg, #6B5CE7, #9B8AFF);
    border-radius: 4px 0 0 4px;
    transition: width 0.4s ease;
    overflow: hidden;
    animation: sb-fill 0.6s ease-out;
}}
.sb-split-stock {{
    background: linear-gradient(90deg, #E8638B, #F5A4BD);
    border-radius: 0 4px 4px 0;
    transition: width 0.4s ease;
    overflow: hidden;
    animation: sb-fill 0.6s ease-out;
}}
.sb-split-labels {{
    display: flex;
    justify-content: space-between;
    font-size: 0.65rem;
    font-weight: 600;
    margin-top: 0.15rem;
}}
.sb-split-labels .cash-label {{ color: #9B8AFF !important; }}
.sb-split-labels .stock-label {{ color: #E8638B !important; }}
.sb-divider {{
    height: 1px;
    border: none;
    margin: 0.6rem 0;
    background: linear-gradient(90deg, transparent, rgba(107,92,231,0.3), transparent);
}}

/* ── HERO / HEADER (profile view) ──────────────────────── */
.hero-header {{
    background: linear-gradient(135deg, #050816 0%, #0B0E1A 40%, #151933 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    border-bottom: 3px solid rgba(107,92,231,0.5);
    box-shadow: 0 8px 40px rgba(11,14,26,0.4);
    position: relative;
    overflow: hidden;
}}
.hero-header::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: transparent;
    box-shadow: {_gen_stars(50, 800)};
    width: 1px; height: 1px;
    opacity: 0.5;
    pointer-events: none;
}}
.hero-header::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 20% 50%, rgba(107,92,231,0.1) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 30%, rgba(232,99,139,0.06) 0%, transparent 50%);
    pointer-events: none;
}}
.hero-title {{
    font-size: 2.2rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.5px;
    position: relative; z-index: 1;
}}
.hero-accent {{ color: #9B8AFF; }}
.hero-sub {{
    font-size: 1rem;
    color: #A8A3C7;
    margin-top: 0.3rem;
    font-weight: 400;
    position: relative; z-index: 1;
}}
.hero-tagline {{
    display: inline-block;
    background: rgba(107,92,231,0.15);
    color: #9B8AFF;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 0.5rem;
    position: relative; z-index: 1;
}}

/* ── COMPANY HEADER CARD ─────────────────────────────────── */
.company-card {{
    background: linear-gradient(135deg, #050816 0%, #0B0E1A 50%, #151933 100%);
    border-radius: 20px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.2rem;
    border-left: 4px solid;
    border-image: linear-gradient(180deg, #6B5CE7, #E8638B) 1;
    box-shadow: 0 4px 30px rgba(11,14,26,0.3);
    position: relative;
    overflow: hidden;
    animation: cardReveal 0.6s ease-out both;
}}
.company-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 80% 20%, rgba(107,92,231,0.08) 0%, transparent 60%);
    pointer-events: none;
}}
.company-card::after {{
    content: '';
    position: absolute;
    width: 80px; height: 80px; border-radius: 50%;
    background: rgba(107,92,231,0.06);
    filter: blur(40px);
    top: -20px; right: 40px;
    animation: float1 20s ease-in-out infinite;
    pointer-events: none;
}}
.company-name {{
    font-size: 1.8rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
    letter-spacing: -0.3px;
}}
.company-meta {{
    font-size: 0.85rem;
    color: #A8A3C7;
    margin-top: 0.25rem;
}}
.company-meta span {{ color: #9B8AFF; font-weight: 600; }}
.price-tag {{ font-size: 1.5rem; font-weight: 700; margin: 0; }}
.price-up {{ color: #10B981; }}
.price-down {{ color: #EF4444; }}
.price-change {{
    font-size: 0.85rem; font-weight: 600;
    padding: 0.15rem 0.5rem; border-radius: 6px;
    display: inline-block; margin-left: 0.5rem;
}}
.change-up {{ background: rgba(16,185,129,0.15); color: #10B981; }}
.change-down {{ background: rgba(239,68,68,0.15); color: #EF4444; }}

/* ── SECTION STYLING ─────────────────────────────────────── */
.section-header {{
    display: flex; align-items: center; gap: 0.8rem;
    margin: 2.5rem 0 1rem 0; padding-bottom: 0.6rem;
    position: relative;
    animation: slideUpBounce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}}
.section-header::after {{
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #6B5CE7, #E8638B, transparent);
    animation: glowPulse 3s ease-in-out infinite;
    border-radius: 2px;
}}
.section-header h3 {{
    font-size: 1.3rem; font-weight: 800; color: #E0DCF5; margin: 0; letter-spacing: -0.3px;
}}
.section-header .accent-bar {{
    width: 5px; height: 26px; background: linear-gradient(180deg, #6B5CE7, #E8638B); border-radius: 3px;
}}

/* ── GRADIENT DIVIDER ────────────────────────────────────── */
.gradient-divider {{
    height: 1px; border: none; margin: 1.5rem 0;
    background: linear-gradient(90deg, transparent, rgba(107,92,231,0.3), rgba(232,99,139,0.2), transparent);
}}

/* ── METRIC CARDS ────────────────────────────────────────── */
div[data-testid="stMetric"] {{
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(107,92,231,0.15);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    box-shadow: 0 4px 15px rgba(107,92,231,0.1);
    position: relative;
    overflow: hidden;
    animation: slideUpBounce 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}}
div[data-testid="stMetric"]::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6B5CE7, #9B8AFF, #E8638B);
    opacity: 0; transition: opacity 0.3s ease;
}}
div[data-testid="stMetric"]:hover {{
    border-color: rgba(107,92,231,0.4);
    box-shadow: 0 10px 30px rgba(107,92,231,0.25);
    transform: translateY(-5px);
}}
div[data-testid="stMetric"]:hover::before {{
    opacity: 1;
}}
div[data-testid="stMetric"] label {{
    font-size: 0.75rem !important; font-weight: 600 !important;
    text-transform: uppercase; letter-spacing: 0.8px; color: #8A85AD !important;
}}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
    font-size: 1.25rem !important; font-weight: 700 !important; color: #E0DCF5 !important;
}}

/* ── TABS ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0; background: rgba(255,255,255,0.05); border-radius: 12px; padding: 4px;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px; font-weight: 600; font-size: 0.82rem;
    padding: 0.5rem 1.2rem; color: #8A85AD;
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    background: linear-gradient(135deg, #6B5CE7, #9B8AFF);
    color: #ffffff;
    box-shadow: 0 2px 12px rgba(107,92,231,0.4);
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
.stTabs [data-baseweb="tab-border"] {{ display: none; }}

/* ── EXPANDERS ───────────────────────────────────────────── */
.streamlit-expanderHeader {{
    font-weight: 600 !important; font-size: 0.95rem !important;
    color: #E0DCF5 !important; background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1); border-radius: 12px;
}}

/* ── DATAFRAMES ──────────────────────────────────────────── */
.stDataFrame {{
    border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; overflow: hidden;
}}

/* ── DOWNLOAD BUTTON ─────────────────────────────────────── */
.stDownloadButton > button {{
    background: linear-gradient(135deg, #6B5CE7, #E8638B, #F5A623) !important;
    background-size: 200% 200% !important;
    animation: gradientShift 6s ease infinite !important;
    color: white !important; font-weight: 700 !important;
    border: none !important; border-radius: 14px !important;
    padding: 0.8rem 2rem !important; font-size: 1rem !important;
    width: 100% !important; transition: all 0.3s ease;
    box-shadow: 0 4px 25px rgba(107,92,231,0.3);
}}
.stDownloadButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 35px rgba(107,92,231,0.5);
}}

/* ── NEWS CARDS ──────────────────────────────────────────── */
.news-item {{
    padding: 0.65rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);
    transition: background 0.15s;
}}
.news-item:hover {{ background: rgba(255,255,255,0.03); }}
.news-title {{
    font-weight: 600; color: #E0DCF5; font-size: 0.88rem; text-decoration: none;
}}
.news-title:hover {{ color: #9B8AFF; }}
.news-pub {{ font-size: 0.72rem; color: #8A85AD; font-weight: 500; }}

/* ── PILLS ──────────────────────────────────────────────── */
.pill {{
    display: inline-block; padding: 0.2rem 0.7rem; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px;
}}
.pill-purple {{ background: rgba(107,92,231,0.12); color: #6B5CE7; }}
.pill-dark {{ background: rgba(26,29,46,0.08); color: #1A1D2E; }}
.pill-green {{ background: rgba(16,185,129,0.12); color: #10B981; }}

/* ── PLOTLY CHARTS ──────────────────────────────────────── */
.stPlotlyChart {{
    border: 1px solid rgba(107,92,231,0.2);
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(107,92,231,0.15);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    background: rgba(107,92,231,0.03);
    animation: chartBounceIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
    filter: saturate(0.85);
}}
.stPlotlyChart:hover {{
    border-color: rgba(107,92,231,0.5);
    box-shadow: 0 12px 40px rgba(107,92,231,0.3), 0 0 60px rgba(107,92,231,0.08);
    transform: translateY(-6px) scale(1.012);
    filter: saturate(1.1);
}}

/* ── RADIO BUTTONS ──────────────────────────────────────── */
.stRadio > div {{ gap: 0.3rem; }}
.stRadio > div > label {{
    background: rgba(255,255,255,0.05); border-radius: 8px; padding: 0.3rem 1rem;
    font-weight: 600; font-size: 0.8rem; border: 1px solid rgba(255,255,255,0.1); color: #B8B3D7;
}}
.stRadio > div > label[data-checked="true"] {{
    background: linear-gradient(135deg, #6B5CE7, #9B8AFF); color: #ffffff;
}}

/* ── SCROLLBAR ──────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.03); border-radius: 10px; }}
::-webkit-scrollbar-thumb {{ background: rgba(107,92,231,0.4); border-radius: 10px; }}
::-webkit-scrollbar-thumb:hover {{ background: #9B8AFF; }}

/* ── SPINNER ────────────────────────────────────────────── */
.stSpinner > div > div {{ border-top-color: #6B5CE7 !important; }}

/* ── HIDE BRANDING ──────────────────────────────────────── */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
header {{ visibility: hidden; }}

/* ── PRICE DISPLAY BAR ──────────────────────────────────── */
.price-bar {{
    border-radius: 14px; padding: 1rem 1.5rem; margin-bottom: 1rem;
    display: flex; gap: 1.5rem; align-items: center;
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}}

/* ── MERGER CHART WRAPPER ──────────────────────────────── */
.merger-chart-wrapper {{
    background: linear-gradient(135deg, rgba(107,92,231,0.05), rgba(232,99,139,0.02));
    border: 1px solid rgba(107,92,231,0.15);
    border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0 1rem 0;
    animation: bounceIn 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) both,
               chartGlow 4s ease-in-out 1s infinite;
}}

/* ── PRECEDENT & INSIDER TABLES ────────────────────────── */
.precedent-table, .insider-table {{
    width: 100%; border-collapse: separate; border-spacing: 0;
    border-radius: 14px; overflow: hidden;
    animation: bounceIn 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}}
.precedent-table th, .insider-table th {{
    background: rgba(107,92,231,0.15); color: #9B8AFF; font-size: 0.7rem;
    text-transform: uppercase; letter-spacing: 1px;
    padding: 0.7rem 0.8rem; font-weight: 700;
    border-bottom: 2px solid rgba(107,92,231,0.3);
}}
.precedent-table td, .insider-table td {{
    padding: 0.55rem 0.8rem; font-size: 0.8rem; color: #C8C3E3;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}}
.precedent-table tr:hover td, .insider-table tr:hover td {{
    background: rgba(107,92,231,0.08);
}}

/* ── NEWS SENTIMENT CARDS ──────────────────────────────── */
.news-card {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 0.8rem 1rem; margin-bottom: 0.6rem;
    animation: slideUpBounce 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    transition: all 0.25s ease;
}}
.news-card:hover {{
    border-color: rgba(107,92,231,0.3);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(107,92,231,0.15);
}}
.news-sentiment-bullish {{ border-left: 3px solid #10B981; }}
.news-sentiment-bearish {{ border-left: 3px solid #EF4444; }}
.news-sentiment-neutral {{ border-left: 3px solid #8A85AD; }}

/* ── EARNINGS SURPRISE CHART CARD ─────────────────────── */
.earnings-beat {{ color: #10B981; font-weight: 700; }}
.earnings-miss {{ color: #EF4444; font-weight: 700; }}

/* ── PROFILE CHART WRAPPER ───────────────────────────── */
.profile-chart-wrapper {{
    background: linear-gradient(135deg, rgba(107,92,231,0.04), rgba(6,182,212,0.02));
    border: 1px solid rgba(107,92,231,0.12);
    border-radius: 20px; padding: 1.5rem; margin: 0.5rem 0 1rem 0;
    position: relative; overflow: hidden;
    animation: chartBounceIn 0.8s cubic-bezier(0.34, 1.56, 0.64, 1) both,
               chartGlow 4s ease-in-out 1s infinite;
}}
.profile-chart-wrapper::before {{
    content: '';
    position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
    background: radial-gradient(circle at 30% 40%, rgba(107,92,231,0.03) 0%, transparent 50%),
                radial-gradient(circle at 70% 60%, rgba(6,182,212,0.02) 0%, transparent 50%);
    pointer-events: none;
    animation: nebulaPulse 20s ease-in-out infinite;
}}

/* ── SCANNER LOADING (profile mode) ──────────────────── */
.scanner-control {{
    background: linear-gradient(170deg, #020515 0%, #0B0E1A 40%, #151933 100%);
    border-radius: 24px;
    padding: 2.5rem;
    min-height: 360px;
    position: relative;
    overflow: hidden;
    animation: fadeInScale 0.5s ease-out both;
    border: 1px solid rgba(6,182,212,0.2);
}}
.scanner-control::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background:
        radial-gradient(ellipse at 25% 30%, rgba(6,182,212,0.08) 0%, transparent 55%),
        radial-gradient(ellipse at 75% 70%, rgba(59,130,246,0.05) 0%, transparent 55%);
    pointer-events: none;
}}
.scanner-control::after {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: transparent;
    box-shadow: {_gen_stars(40, 600)};
    width: 1px; height: 1px;
    opacity: 0.4;
    pointer-events: none;
}}
.scanner-dish-container {{
    text-align: center;
    height: 100px;
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}}
.scanner-dish {{
    font-size: 3.5rem;
    filter: drop-shadow(0 0 12px rgba(6,182,212,0.5));
    position: relative;
    z-index: 2;
}}
.scanner-dish-scanning {{
    animation: scannerSweep 2s ease-in-out infinite;
}}
.scanner-dish-locked {{
    animation: scannerLock 1.5s ease-in-out infinite;
}}
.scanner-beam {{
    width: 60px; height: 3px;
    background: linear-gradient(90deg, transparent, rgba(6,182,212,0.6), transparent);
    border-radius: 2px;
    margin: -6px auto 0 auto;
    animation: scannerBeamSweep 1.5s ease-in-out infinite;
}}
.scanner-ring {{
    position: absolute;
    top: 50%; left: 50%;
    width: 40px; height: 40px;
    border-radius: 50%;
    border: 1px solid rgba(6,182,212,0.3);
    transform: translate(-50%, -50%);
    animation: scannerRingPulse 2s ease-out infinite;
}}
.scanner-ring-2 {{
    animation-delay: 0.7s;
}}
.scanner-ring-3 {{
    animation-delay: 1.4s;
}}
/* Cyan accent overrides for scanner */
.scanner-control .phase-indicator-active {{
    border-color: rgba(6,182,212,0.5);
    color: #06B6D4;
}}
.scanner-control .phase-indicator-active::after {{
    border-top-color: #06B6D4;
}}
.scanner-control .mission-phase-active {{
    background: rgba(6,182,212,0.1);
    border-color: rgba(6,182,212,0.25);
    animation: scannerPhasePulse 2s ease-in-out infinite;
}}
.scanner-control .mission-progress-fill {{
    background: linear-gradient(90deg, #06B6D4, #3B82F6, #6B5CE7, #06B6D4);
    background-size: 200% 100%;
}}
.scanner-control .mission-progress-fill::after {{
    box-shadow: 0 0 10px rgba(6,182,212,0.8), 0 0 20px rgba(6,182,212,0.4);
}}
.scanner-ticker {{
    text-align: center;
    margin-top: 1.2rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.06);
    position: relative;
    z-index: 1;
}}
.scanner-ticker span {{
    font-size: 1rem;
    font-weight: 800;
    color: #06B6D4;
    letter-spacing: 3px;
    text-shadow: 0 0 15px rgba(6,182,212,0.4);
}}
.scanner-dots {{
    display: inline-block;
    margin-left: 4px;
}}
.scanner-dots span {{
    display: inline-block;
    width: 4px; height: 4px;
    border-radius: 50%;
    background: #06B6D4;
    margin: 0 2px;
    animation: gentlePulse 1.5s ease-in-out infinite;
}}
.scanner-dots span:nth-child(2) {{ animation-delay: 0.3s; }}
.scanner-dots span:nth-child(3) {{ animation-delay: 0.6s; }}
</style>
""", unsafe_allow_html=True)

# ── Space-specific CSS (starfield, nebula, orbs, glass cards) ──
st.markdown(f"""
<style>
/* ── SPLASH HERO ────────────────────────────────────────── */
.splash-hero {{
    background: transparent;
    border-radius: 0; padding: 5rem 3rem 4rem; text-align: center;
    margin: -1rem calc(-50vw + 50%); width: 100vw;
    position: relative; overflow: hidden;
    min-height: 90vh;
}}

/* Star Layer 1 — small distant stars */
.star-layer-1 {{
    position: absolute; top: 0; left: 0; width: 1px; height: 1px;
    box-shadow: {_STARS1};
    opacity: 0.6;
    animation: starDrift1 150s linear infinite;
}}
.star-layer-1::after {{
    content: ''; position: absolute; top: 2000px; left: 0;
    width: 1px; height: 1px;
    box-shadow: {_STARS1};
}}

/* Star Layer 2 — medium stars */
.star-layer-2 {{
    position: absolute; top: 0; left: 0; width: 1.5px; height: 1.5px;
    box-shadow: {_STARS2};
    opacity: 0.8;
    animation: starDrift2 100s linear infinite;
}}
.star-layer-2::after {{
    content: ''; position: absolute; top: 2000px; left: 0;
    width: 1.5px; height: 1.5px;
    box-shadow: {_STARS2};
}}

/* Star Layer 3 — large close stars */
.star-layer-3 {{
    position: absolute; top: 0; left: 0; width: 2px; height: 2px;
    box-shadow: {_STARS3};
    opacity: 1.0;
    animation: starDrift3 75s linear infinite;
}}
.star-layer-3::after {{
    content: ''; position: absolute; top: 2000px; left: 0;
    width: 2px; height: 2px;
    box-shadow: {_STARS3};
}}

/* Nebula overlay */
.nebula-overlay {{
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background:
        radial-gradient(ellipse at 20% 50%, rgba(107,92,231,0.15) 0%, transparent 50%),
        radial-gradient(ellipse at 75% 20%, rgba(232,99,139,0.1) 0%, transparent 45%),
        radial-gradient(ellipse at 50% 80%, rgba(59,130,246,0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 70%, rgba(45,195,195,0.06) 0%, transparent 40%);
    animation: nebulaPulse 30s ease-in-out infinite;
    pointer-events: none;
}}

/* Floating luminous orbs */
.orb {{
    position: absolute;
    border-radius: 50%;
    pointer-events: none;
}}
.orb-1 {{
    width: 200px; height: 200px;
    background: rgba(107,92,231,0.12);
    filter: blur(80px);
    top: 10%; left: 5%;
    animation: float1 20s ease-in-out infinite, orbBreath1 10s ease-in-out infinite;
}}
.orb-2 {{
    width: 160px; height: 160px;
    background: rgba(232,99,139,0.1);
    filter: blur(70px);
    top: 60%; right: 10%;
    animation: float2 22s ease-in-out infinite;
}}
.orb-3 {{
    width: 120px; height: 120px;
    background: rgba(59,130,246,0.08);
    filter: blur(60px);
    top: 30%; right: 25%;
    animation: float3 18s ease-in-out infinite;
}}
.orb-4 {{
    width: 180px; height: 180px;
    background: rgba(155,138,255,0.08);
    filter: blur(90px);
    bottom: 10%; left: 30%;
    animation: float4 25s ease-in-out infinite, orbBreath4 12s ease-in-out 3s infinite;
}}
.orb-5 {{
    width: 100px; height: 100px;
    background: rgba(45,195,195,0.06);
    filter: blur(60px);
    top: 15%; right: 5%;
    animation: float2 19s ease-in-out infinite reverse;
}}

/* Shooting stars */
.shooting-star {{
    position: absolute;
    width: 120px; height: 1.5px;
    background: linear-gradient(90deg, rgba(255,255,255,0.8), transparent);
    border-radius: 50%;
    pointer-events: none;
    opacity: 0;
}}
.shooting-star-1 {{
    top: 15%; right: -120px;
    animation: shootingStar 8s ease-in-out 2s infinite;
}}
.shooting-star-2 {{
    top: 40%; right: -120px;
    animation: shootingStar 10s ease-in-out 5s infinite;
}}
.shooting-star-3 {{
    top: 25%; right: -120px;
    animation: shootingStar 12s ease-in-out 8s infinite;
}}
.shooting-star-4 {{
    top: 55%; right: -120px;
    animation: shootingStar 15s ease-in-out 11s infinite;
    transform: rotate(-8deg);
}}
.shooting-star-5 {{
    top: 8%; right: -120px;
    animation: shootingStar 20s ease-in-out 16s infinite;
    transform: rotate(5deg);
}}

/* Noise/grain overlay */
.noise-overlay {{
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    opacity: 0.04;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    pointer-events: none;
}}

/* Title glow halo */
.title-glow {{
    position: absolute;
    width: 400px; height: 200px;
    top: 50%; left: 50%;
    transform: translate(-50%, -70%);
    background: radial-gradient(ellipse, rgba(107,92,231,0.2) 0%, transparent 70%);
    animation: titleGlow 4s ease-in-out infinite;
    pointer-events: none;
}}

/* Content layer */
.splash-content {{
    position: relative; z-index: 10;
}}

.splash-title {{
    font-size: 4.5rem; font-weight: 900; color: #ffffff; margin: 0;
    letter-spacing: -2px; animation: fadeInUp 0.6s ease-out;
    text-shadow: 0 0 60px rgba(107,92,231,0.3);
}}
.splash-accent {{
    background: linear-gradient(135deg, #9B8AFF, #E8638B, #F5A623, #9B8AFF);
    background-size: 200% auto;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer 3s linear infinite;
}}
.splash-subtitle {{
    font-size: 1.2rem; color: #B8B3D7; margin-top: 0.8rem;
    font-weight: 300; animation: fadeInUp 0.8s ease-out;
    letter-spacing: 0.5px;
}}
.splash-stats {{
    display: flex; justify-content: center; gap: 3rem; margin-top: 2.5rem;
    animation: fadeInUp 1s ease-out;
}}
.splash-stat-value {{
    font-size: 1.8rem; font-weight: 800; color: #fff;
    animation: gentlePulse 3s ease-in-out infinite;
    position: relative;
}}
.splash-stat {{
    position: relative;
}}
.splash-stat:nth-child(1) .splash-stat-value {{ animation-delay: 0s; }}
.splash-stat:nth-child(2) .splash-stat-value {{ animation-delay: 0.5s; }}
.splash-stat:nth-child(3) .splash-stat-value {{ animation-delay: 1.0s; }}
.splash-stat-icon {{
    position: relative;
    display: inline-block;
}}
.splash-stat-icon::before {{
    content: '';
    position: absolute;
    inset: -6px;
    border-radius: 50%;
    border: 2px solid rgba(107,92,231,0.4);
    animation: pulseRing 2s ease-out infinite;
    pointer-events: none;
}}
.splash-stat-label {{
    font-size: 0.7rem; color: #A8A3C7; text-transform: uppercase;
    letter-spacing: 1px; font-weight: 500;
}}
.pill-row {{
    display: flex; justify-content: center; gap: 0.7rem; margin-top: 1.8rem;
    flex-wrap: wrap;
    animation: fadeInUp 1.2s ease-out;
}}
.feature-pill {{
    border: 1px solid rgba(107,92,231,0.3); border-radius: 24px;
    padding: 0.4rem 1.1rem; font-size: 0.75rem; font-weight: 600;
    color: #B8B3D7; background: rgba(107,92,231,0.06);
    backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}}
.feature-pill:hover {{
    border-color: rgba(155,138,255,0.6);
    box-shadow: 0 0 15px rgba(107,92,231,0.2);
    color: #fff;
}}

/* ── SPACE SECTION (dark container for glass cards) ──── */
.space-section {{
    background: rgba(11,14,26,0.5);
    border-radius: 0;
    padding: 2.5rem 3rem;
    margin: 0 calc(-50vw + 50%); width: 100vw;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}}
.space-section-title {{
    font-size: 0.75rem; font-weight: 600; color: #A8A3C7;
    text-transform: uppercase; letter-spacing: 2px;
    text-align: center; margin-bottom: 1.5rem;
}}

/* ── GLASS STEP CARDS ──────────────────────────────────── */
.step-grid {{
    display: flex; gap: 1.2rem; margin: 0 0 2rem 0;
    position: relative;
}}
.step-card {{
    flex: 1;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px; padding: 1.5rem; text-align: center;
    transition: all 0.3s ease;
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    position: relative; overflow: hidden;
    animation: fadeInUp 0.6s ease-out both;
}}
.step-card:nth-child(1) {{ animation-delay: 0.1s; }}
.step-card:nth-child(2) {{ animation-delay: 0.2s; }}
.step-card:nth-child(3) {{ animation-delay: 0.3s; }}
.step-card:nth-child(4) {{ animation-delay: 0.4s; }}
.step-card::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    border-radius: 18px;
    padding: 1px;
    background: linear-gradient(135deg, rgba(107,92,231,0.3), rgba(232,99,139,0.1), transparent);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    opacity: 0; transition: opacity 0.3s;
    pointer-events: none;
}}
.step-card:hover {{
    border-color: rgba(107,92,231,0.3); transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(107,92,231,0.15);
}}
.step-card:hover::before {{ opacity: 1; }}
.step-num {{
    background: linear-gradient(135deg, #6B5CE7, #9B8AFF);
    color: #fff; width: 38px; height: 38px; border-radius: 50%;
    display: inline-flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1rem; margin-bottom: 0.6rem;
    box-shadow: 0 4px 15px rgba(107,92,231,0.3);
}}
.step-label {{ font-size: 0.88rem; font-weight: 700; color: #E0DCF5; }}
.step-detail {{ font-size: 0.72rem; color: #8A85AD; margin-top: 0.3rem; }}

/* Connector lines between steps */
.step-connector {{
    position: absolute; top: 50%; height: 2px; z-index: 0;
    background: linear-gradient(90deg, rgba(107,92,231,0.2), rgba(232,99,139,0.2), rgba(107,92,231,0.2));
    background-size: 200% 100%;
    animation: shimmerLine 3s linear infinite;
}}

/* ── GLASS FEATURE CARDS ───────────────────────────────── */
.feature-grid {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1rem; margin-top: 0.5rem;
}}
.feature-card {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px; padding: 1.5rem 1.2rem; text-align: center;
    transition: all 0.3s ease;
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    animation: fadeInScale 0.6s ease-out both;
    position: relative; overflow: hidden;
}}
.feature-card:nth-child(1) {{ animation-delay: 0.05s; }}
.feature-card:nth-child(2) {{ animation-delay: 0.1s; }}
.feature-card:nth-child(3) {{ animation-delay: 0.15s; }}
.feature-card:nth-child(4) {{ animation-delay: 0.2s; }}
.feature-card:nth-child(5) {{ animation-delay: 0.25s; }}
.feature-card:nth-child(6) {{ animation-delay: 0.3s; }}
.feature-card:nth-child(7) {{ animation-delay: 0.35s; }}
.feature-card:nth-child(8) {{ animation-delay: 0.4s; }}
.feature-card::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    border-radius: 18px;
    padding: 1px;
    background: linear-gradient(135deg, rgba(107,92,231,0.3), rgba(232,99,139,0.1), transparent);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    opacity: 0; transition: opacity 0.3s;
    pointer-events: none;
}}
.feature-card:hover {{
    border-color: rgba(107,92,231,0.3); transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(107,92,231,0.15);
}}
.feature-card:hover::before {{ opacity: 1; }}
.feature-icon {{ font-size: 2.2rem; margin-bottom: 0.5rem; }}
.feature-title {{ font-size: 0.88rem; font-weight: 700; color: #E0DCF5; margin-bottom: 0.3rem; }}
.feature-desc {{ font-size: 0.72rem; color: #8A85AD; line-height: 1.6; }}

/* ── MISSION CONTROL (Merger Loading) ──────────────────── */
.mission-control {{
    background: linear-gradient(170deg, #020515 0%, #0B0E1A 40%, #151933 100%);
    border-radius: 24px;
    padding: 2.5rem;
    min-height: 420px;
    position: relative;
    overflow: hidden;
    animation: fadeInScale 0.5s ease-out both;
    border: 1px solid rgba(107,92,231,0.2);
}}
.mission-control::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background:
        radial-gradient(ellipse at 25% 30%, rgba(107,92,231,0.08) 0%, transparent 55%),
        radial-gradient(ellipse at 75% 70%, rgba(232,99,139,0.05) 0%, transparent 55%);
    pointer-events: none;
}}
.mission-control::after {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: transparent;
    box-shadow: {_gen_stars(40, 600)};
    width: 1px; height: 1px;
    opacity: 0.4;
    pointer-events: none;
}}
.mission-header {{
    text-align: center;
    margin-bottom: 1.5rem;
    position: relative;
    z-index: 1;
}}
.mission-title {{
    font-size: 1.1rem;
    font-weight: 800;
    color: #E0DCF5;
    text-transform: uppercase;
    letter-spacing: 3px;
    margin: 0;
    text-shadow: 0 0 20px rgba(107,92,231,0.4);
}}
.mission-subtitle {{
    font-size: 0.72rem;
    color: #8A85AD;
    margin-top: 0.3rem;
    text-transform: uppercase;
    letter-spacing: 2px;
}}
.rocket-container {{
    text-align: center;
    height: 120px;
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}}
.rocket {{
    font-size: 3.5rem;
    filter: drop-shadow(0 0 12px rgba(107,92,231,0.5));
    position: relative;
    z-index: 2;
}}
.rocket-idle {{
    animation: float1 6s ease-in-out infinite;
}}
.rocket-launching {{
    animation: rocketLaunch 2s ease-in forwards;
}}
.rocket-flame {{
    font-size: 1.5rem;
    filter: drop-shadow(0 0 8px rgba(255,165,0,0.7));
    animation: flameFlicker 0.3s ease-in-out infinite;
    margin-top: -8px;
}}
.exhaust-trail {{
    width: 4px;
    height: 30px;
    background: linear-gradient(to bottom, rgba(255,165,0,0.4), rgba(107,92,231,0.2), transparent);
    filter: blur(2px);
    margin: 0 auto;
    animation: exhaustTrail 0.8s ease-out infinite;
}}
.mission-progress-track {{
    height: 6px;
    background: rgba(255,255,255,0.06);
    border-radius: 3px;
    margin: 1.2rem 0;
    overflow: hidden;
    position: relative;
    z-index: 1;
}}
.mission-progress-fill {{
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, #6B5CE7, #9B8AFF, #E8638B, #6B5CE7);
    background-size: 200% 100%;
    animation: progressGlow 2s linear infinite;
    transition: width 0.6s ease;
    position: relative;
}}
.mission-progress-fill::after {{
    content: '';
    position: absolute;
    right: 0; top: 50%;
    transform: translateY(-50%);
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #fff;
    box-shadow: 0 0 10px rgba(155,138,255,0.8), 0 0 20px rgba(107,92,231,0.4);
}}
.mission-phases {{
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    position: relative;
    z-index: 1;
}}
.mission-phase {{
    display: flex;
    align-items: center;
    gap: 0.8rem;
    padding: 0.6rem 1rem;
    border-radius: 12px;
    transition: all 0.3s ease;
}}
.mission-phase-active {{
    background: rgba(107,92,231,0.1);
    border: 1px solid rgba(107,92,231,0.25);
    animation: missionPulse 2s ease-in-out infinite;
}}
.mission-phase-complete {{
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.15);
}}
.mission-phase-pending {{
    opacity: 0.4;
    border: 1px solid transparent;
}}
.phase-indicator {{
    width: 28px; height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 700;
    flex-shrink: 0;
}}
.phase-indicator-active {{
    border: 2px solid rgba(107,92,231,0.5);
    color: #9B8AFF;
    position: relative;
}}
.phase-indicator-active::after {{
    content: '';
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    border: 2px solid transparent;
    border-top-color: #9B8AFF;
    animation: spin 1s linear infinite;
}}
.phase-indicator-complete {{
    background: rgba(16,185,129,0.2);
    color: #10B981;
    animation: checkPop 0.4s ease-out both;
}}
.phase-indicator-pending {{
    border: 1px solid rgba(255,255,255,0.15);
    color: #555;
}}
.phase-label {{
    font-size: 0.82rem;
    font-weight: 600;
    color: #E0DCF5;
}}
.phase-sublabel {{
    font-size: 0.68rem;
    color: #8A85AD;
    margin-top: 0.1rem;
}}
.mission-stats {{
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 0.8rem;
    margin-top: 1.2rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255,255,255,0.06);
    position: relative;
    z-index: 1;
}}
.mission-stats span {{
    font-size: 0.85rem;
    font-weight: 700;
    color: #9B8AFF;
    letter-spacing: 1px;
}}
.mission-stats .mission-x {{
    font-size: 1.2rem;
    color: #E8638B;
    font-weight: 300;
}}
</style>
""", unsafe_allow_html=True)


# ── HELPER: Mission Control loading screen ───────────────────
def _render_mission_control(acquirer: str, target: str, current_phase: int, total_phases: int = 5) -> str:
    """Return HTML for the animated mission control loading UI."""
    phases = [
        (f"Acquiring Target Intel: {acquirer}", "Scanning financial databases..."),
        (f"Locking Signal: {target}", "Establishing secure data link..."),
        ("Mapping Sector Constellation", "Triangulating peer coordinates..."),
        ("Computing Orbital Mechanics", "Pro forma trajectory analysis..."),
        ("Synthesizing Mission Report", "AI engines generating insights..."),
    ]
    completed = min(current_phase, total_phases)
    pct = int((completed / total_phases) * 100)

    # Rocket state
    if current_phase >= total_phases:
        rocket_cls = "rocket rocket-launching"
        flame_html = ""
        exhaust_html = ""
    else:
        rocket_cls = "rocket rocket-idle"
        flame_html = '<div class="rocket-flame">🔥</div>'
        exhaust_html = '<div class="exhaust-trail"></div>'

    # Build phase rows
    phase_rows = ""
    for i, (label, sublabel) in enumerate(phases):
        if i < current_phase:
            row_cls = "mission-phase mission-phase-complete"
            ind_cls = "phase-indicator phase-indicator-complete"
            ind_content = "✓"
        elif i == current_phase:
            row_cls = "mission-phase mission-phase-active"
            ind_cls = "phase-indicator phase-indicator-active"
            ind_content = str(i + 1)
        else:
            row_cls = "mission-phase mission-phase-pending"
            ind_cls = "phase-indicator phase-indicator-pending"
            ind_content = str(i + 1)
        phase_rows += (
            f'<div class="{row_cls}">'
            f'<div class="{ind_cls}">{ind_content}</div>'
            f'<div><div class="phase-label">{label}</div>'
            f'<div class="phase-sublabel">{sublabel}</div></div>'
            f'</div>'
        )

    return (
        f'<div class="mission-control">'
        f'<div class="mission-header">'
        f'<div class="mission-title">Merger Analysis Mission Control</div>'
        f'<div class="mission-subtitle">Phase {completed} of {total_phases}</div>'
        f'</div>'
        f'<div class="rocket-container">'
        f'<div class="{rocket_cls}">🚀</div>'
        f'{flame_html}'
        f'{exhaust_html}'
        f'</div>'
        f'<div class="mission-progress-track">'
        f'<div class="mission-progress-fill" style="width:{pct}%;"></div>'
        f'</div>'
        f'<div class="mission-phases">{phase_rows}</div>'
        f'<div class="mission-stats">'
        f'<span>{acquirer}</span>'
        f'<span class="mission-x">×</span>'
        f'<span>{target}</span>'
        f'</div>'
        f'</div>'
    )


# ── HELPER: Profile scanner loading screen ────────────────────
def _render_profile_scanner(ticker: str, current_phase: int, total_phases: int = 3) -> str:
    """Return HTML for the animated scanner loading UI for company profiles."""
    phases = [
        ("Scanning Financial Databases", "Fetching market data & fundamentals..."),
        ("Analyzing Financials & Peers", "Comparing against sector peers..."),
        ("Generating AI Insights", "Building investment thesis..."),
    ]
    completed = min(current_phase, total_phases)
    pct = int((completed / total_phases) * 100)

    # Dish state
    if current_phase >= total_phases:
        dish_cls = "scanner-dish scanner-dish-locked"
        beam_html = ""
        ring_html = ""
    else:
        dish_cls = "scanner-dish scanner-dish-scanning"
        beam_html = '<div class="scanner-beam"></div>'
        ring_html = (
            '<div class="scanner-ring"></div>'
            '<div class="scanner-ring scanner-ring-2"></div>'
            '<div class="scanner-ring scanner-ring-3"></div>'
        )

    # Build phase rows (reuse mission-phase classes)
    phase_rows = ""
    for i, (label, sublabel) in enumerate(phases):
        if i < current_phase:
            row_cls = "mission-phase mission-phase-complete"
            ind_cls = "phase-indicator phase-indicator-complete"
            ind_content = "\u2713"
        elif i == current_phase:
            row_cls = "mission-phase mission-phase-active"
            ind_cls = "phase-indicator phase-indicator-active"
            ind_content = str(i + 1)
        else:
            row_cls = "mission-phase mission-phase-pending"
            ind_cls = "phase-indicator phase-indicator-pending"
            ind_content = str(i + 1)
        phase_rows += (
            f'<div class="{row_cls}">'
            f'<div class="{ind_cls}">{ind_content}</div>'
            f'<div><div class="phase-label">{label}</div>'
            f'<div class="phase-sublabel">{sublabel}</div></div>'
            f'</div>'
        )

    dots = '<span class="scanner-dots"><span></span><span></span><span></span></span>'

    return (
        f'<div class="scanner-control">'
        f'<div class="mission-header">'
        f'<div class="mission-title">Company Scanner</div>'
        f'<div class="mission-subtitle">Phase {completed} of {total_phases}</div>'
        f'</div>'
        f'<div class="scanner-dish-container">'
        f'<div class="{dish_cls}">\U0001F4E1</div>'
        f'{beam_html}'
        f'{ring_html}'
        f'</div>'
        f'<div class="mission-progress-track">'
        f'<div class="mission-progress-fill" style="width:{pct}%;"></div>'
        f'</div>'
        f'<div class="mission-phases">{phase_rows}</div>'
        f'<div class="scanner-ticker">'
        f'<span>{ticker}</span>{dots}'
        f'</div>'
        f'</div>'
    )


# ── HELPER: Section header with accent bar ──────────────────
def _section(title, icon=""):
    st.markdown(
        f'<div class="section-header">'
        f'<div class="accent-bar"></div>'
        f'<h3>{icon}  {title}</h3>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── HELPER: Gradient divider between sections ────────────────
def _divider():
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)


# ── HELPER: Peer radar chart ────────────────────────────────
def _build_peer_radar_chart(cd):
    """Build a Plotly radar chart comparing target vs peer median."""
    if not cd.peer_data:
        return

    metrics = ["P/E", "Fwd P/E", "EV/EBITDA", "Gross Margin", "Op Margin", "ROE"]

    target_vals = [
        cd.trailing_pe, cd.forward_pe, cd.ev_to_ebitda,
        (cd.gross_margins or 0) * 100, (cd.operating_margins or 0) * 100,
        (cd.return_on_equity or 0) * 100,
    ]

    peer_keys = ["trailing_pe", "forward_pe", "ev_to_ebitda",
                 "gross_margins", "operating_margins", "return_on_equity"]
    pct_keys = {"gross_margins", "operating_margins", "return_on_equity"}

    peer_medians = []
    for key in peer_keys:
        vals = [p.get(key) for p in cd.peer_data if p.get(key) is not None]
        if key in pct_keys:
            vals = [v * 100 for v in vals]
        peer_medians.append(float(np.median(vals)) if vals else 0)

    # Normalize to 0-100 scale
    norm_target, norm_peer = [], []
    for t, p in zip(target_vals, peer_medians):
        t = t if t is not None else 0
        mx = max(abs(t), abs(p), 1)
        norm_target.append(min(t / mx * 100, 120))
        norm_peer.append(min(p / mx * 100, 120))

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=norm_target + [norm_target[0]],
        theta=metrics + [metrics[0]],
        fill='toself', name=cd.ticker,
        fillcolor='rgba(107,92,231,0.15)',
        line=dict(color='#6B5CE7', width=3),
        marker=dict(size=8, line=dict(color="#fff", width=1.5)),
    ))
    fig.add_trace(go.Scatterpolar(
        r=norm_peer + [norm_peer[0]],
        theta=metrics + [metrics[0]],
        fill='toself', name='Peer Median',
        fillcolor='rgba(232,99,139,0.08)',
        line=dict(color='#E8638B', width=3),
        marker=dict(size=7, line=dict(color="#fff", width=1.5)),
    ))
    fig.update_layout(
        **_CHART_LAYOUT_BASE,
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 120], tickfont=dict(size=8, color="#8A85AD"),
                            gridcolor="rgba(107,92,231,0.1)"),
            angularaxis=dict(tickfont=dict(size=10, color="#8A85AD"),
                             gridcolor="rgba(107,92,231,0.08)"),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True, height=400,
        margin=dict(t=40, b=40, l=60, r=60),
        legend=dict(font=dict(size=11, color="#B8B3D7")),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── CHART: Revenue & Margins ──────────────────────────────────
def _build_revenue_margin_chart(cd, key="rev_margin"):
    """Revenue bars with gross/EBITDA/net margin lines on secondary y-axis."""
    if cd.revenue is None or len(cd.revenue) == 0:
        st.info("Revenue data not available for chart.")
        return
    rev = cd.revenue.dropna().sort_index()
    years = [idx.strftime("%Y") if hasattr(idx, "strftime") else str(idx) for idx in rev.index]
    n = len(years)
    # Progressive alpha — older bars dimmer, newest brightest
    bar_alphas = [0.35 + 0.45 * (i / max(n - 1, 1)) for i in range(n)]
    bar_colors = [f"rgba(107,92,231,{a:.2f})" for a in bar_alphas]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=rev.values, name="Revenue",
        marker=dict(color=bar_colors, line=dict(color="rgba(255,255,255,0.15)", width=1)),
        text=[format_number(v, currency_symbol=cd.currency_symbol) for v in rev.values],
        textposition="outside", textfont=dict(size=9, color="#B8B3D7"),
    ))
    for series, name, color in [
        (cd.gross_margin_series, "Gross Margin", "#10B981"),
        (cd.ebitda_margin, "EBITDA Margin", "#E8638B"),
        (cd.net_margin_series, "Net Margin", "#F5A623"),
    ]:
        if series is not None and len(series) > 0:
            s = series.dropna().sort_index()
            yrs = [idx.strftime("%Y") if hasattr(idx, "strftime") else str(idx) for idx in s.index]
            _glow_line_traces(fig, yrs, s.values, color, name, yaxis="y2")
    fig.update_layout(
        **_CHART_LAYOUT_BASE,
        height=380, margin=dict(t=30, b=30, l=50, r=50),
        xaxis=dict(tickfont=dict(size=9, color="#8A85AD"), showgrid=False),
        yaxis=dict(title=dict(text="Revenue", font=dict(size=10, color="#8A85AD")),
                   tickfont=dict(size=9, color="#8A85AD")),
        yaxis2=dict(title=dict(text="Margin %", font=dict(size=10, color="#8A85AD")),
                    overlaying="y", side="right", showgrid=False,
                    tickfont=dict(size=9, color="#8A85AD"), ticksuffix="%"),
        legend=dict(font=dict(size=10, color="#B8B3D7"), orientation="h", yanchor="bottom", y=1.02),
        barmode="group",
    )
    _apply_space_grid(fig)
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── CHART: Cash Flow ──────────────────────────────────────────
def _build_cashflow_chart(cd, key="cashflow"):
    """Grouped bars: OCF, CapEx (negative), FCF, dividends."""
    series_map = [
        (cd.operating_cashflow_series, "Operating CF", "#6B5CE7"),
        (cd.capital_expenditure, "CapEx", "#EF4444"),
        (cd.free_cashflow_series, "Free CF", "#10B981"),
        (cd.dividends_paid, "Dividends", "#F5A623"),
    ]
    has_data = any(s is not None and len(s) > 0 for s, _, _ in series_map)
    if not has_data:
        st.info("Cash flow data not available for chart.")
        return
    fig = go.Figure()
    for series, name, color in series_map:
        if series is not None and len(series) > 0:
            s = series.dropna().sort_index()
            years = [idx.strftime("%Y") if hasattr(idx, "strftime") else str(idx) for idx in s.index]
            nc = len(years)
            bar_alphas = [0.4 + 0.5 * (i / max(nc - 1, 1)) for i in range(nc)]
            # Parse hex to build progressive rgba
            r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
            bar_cols = [f"rgba({r},{g},{b},{a:.2f})" for a in bar_alphas]
            fig.add_trace(go.Bar(
                x=years, y=s.values, name=name,
                marker=dict(color=bar_cols, line=dict(color="rgba(255,255,255,0.15)", width=1)),
            ))
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
    fig.update_layout(
        **_CHART_LAYOUT_BASE,
        height=380, margin=dict(t=30, b=30, l=50, r=50),
        xaxis=dict(tickfont=dict(size=9, color="#8A85AD"), showgrid=False),
        yaxis=dict(title=dict(text="Amount", font=dict(size=10, color="#8A85AD")),
                   tickfont=dict(size=9, color="#8A85AD")),
        legend=dict(font=dict(size=10, color="#B8B3D7"), orientation="h", yanchor="bottom", y=1.02),
        barmode="group",
    )
    _apply_space_grid(fig)
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── CHART: Balance Sheet ──────────────────────────────────────
def _build_balance_sheet_chart(cd, key="balance_sheet"):
    """Stacked equity+debt bars with cash and total assets overlay lines."""
    has_data = any(
        s is not None and len(s) > 0
        for s in [cd.total_equity, cd.total_debt, cd.cash_and_equivalents, cd.total_assets]
    )
    if not has_data:
        st.info("Balance sheet data not available for chart.")
        return
    fig = go.Figure()
    # Stacked bars: equity + debt with progressive alpha
    for series, name, base_rgba in [
        (cd.total_equity, "Equity", (107, 92, 231)),
        (cd.total_debt, "Debt", (239, 68, 68)),
    ]:
        if series is not None and len(series) > 0:
            s = series.dropna().sort_index()
            years = [idx.strftime("%Y") if hasattr(idx, "strftime") else str(idx) for idx in s.index]
            nc = len(years)
            bar_alphas = [0.3 + 0.45 * (i / max(nc - 1, 1)) for i in range(nc)]
            bar_colors = [f"rgba({base_rgba[0]},{base_rgba[1]},{base_rgba[2]},{a:.2f})" for a in bar_alphas]
            fig.add_trace(go.Bar(
                x=years, y=s.values, name=name,
                marker=dict(color=bar_colors, line=dict(color="rgba(255,255,255,0.15)", width=1)),
            ))
    # Overlay lines with glow
    for series, name, color in [
        (cd.cash_and_equivalents, "Cash", "#10B981"),
        (cd.total_assets, "Total Assets", "#F5A623"),
    ]:
        if series is not None and len(series) > 0:
            s = series.dropna().sort_index()
            years = [idx.strftime("%Y") if hasattr(idx, "strftime") else str(idx) for idx in s.index]
            _glow_line_traces(fig, years, s.values, color, name)
    fig.update_layout(
        **_CHART_LAYOUT_BASE,
        height=380, margin=dict(t=30, b=30, l=50, r=50),
        xaxis=dict(tickfont=dict(size=9, color="#8A85AD"), showgrid=False),
        yaxis=dict(tickfont=dict(size=9, color="#8A85AD")),
        legend=dict(font=dict(size=10, color="#B8B3D7"), orientation="h", yanchor="bottom", y=1.02),
        barmode="stack",
    )
    _apply_space_grid(fig)
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── CHART: Peer Valuation Comparison ──────────────────────────
def _build_peer_valuation_chart(cd, key="peer_val"):
    """Horizontal grouped bars: company vs peer median on key multiples."""
    if not cd.peer_data:
        st.info("Peer data not available for valuation comparison.")
        return
    metrics = [
        ("P/E", "trailing_pe", cd.trailing_pe),
        ("Fwd P/E", "forward_pe", cd.forward_pe),
        ("EV/EBITDA", "ev_to_ebitda", cd.ev_to_ebitda),
        ("P/S", "price_to_sales", cd.price_to_sales),
    ]
    labels, company_vals, peer_vals = [], [], []
    for label, key, company_val in metrics:
        if company_val is None:
            continue
        peer_raw = [p.get(key) for p in cd.peer_data if p.get(key) is not None]
        if not peer_raw:
            continue
        labels.append(label)
        company_vals.append(company_val)
        peer_vals.append(float(np.median(peer_raw)))
    if not labels:
        st.info("Insufficient data for peer valuation chart.")
        return
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=labels, x=company_vals, orientation="h", name=cd.ticker,
        marker=dict(color="#6B5CE7", line=dict(color="rgba(255,255,255,0.15)", width=1)),
        text=[f"{v:.1f}x" for v in company_vals],
        textposition="outside", textfont=dict(size=10, color="#B8B3D7"),
    ))
    fig.add_trace(go.Bar(
        y=labels, x=peer_vals, orientation="h", name="Peer Median",
        marker=dict(color="#E8638B", line=dict(color="rgba(255,255,255,0.15)", width=1)),
        text=[f"{v:.1f}x" for v in peer_vals],
        textposition="outside", textfont=dict(size=10, color="#B8B3D7"),
    ))
    # Premium/discount annotations
    for i, (cv, pv) in enumerate(zip(company_vals, peer_vals)):
        if pv != 0:
            pct = (cv - pv) / abs(pv) * 100
            color = "#10B981" if pct < 0 else "#EF4444"
            sign = "+" if pct >= 0 else ""
            fig.add_annotation(
                y=labels[i], x=max(cv, pv) * 1.15,
                text=f"{sign}{pct:.0f}%", showarrow=False,
                font=dict(size=9, color=color, family="Inter"),
            )
    fig.update_layout(
        **_CHART_LAYOUT_BASE,
        height=280, margin=dict(t=30, b=20, l=80, r=80),
        xaxis=dict(tickfont=dict(size=9, color="#8A85AD")),
        yaxis=dict(tickfont=dict(size=10, color="#8A85AD"), autorange="reversed"),
        legend=dict(font=dict(size=10, color="#B8B3D7"), orientation="h", yanchor="bottom", y=1.02),
        barmode="group",
    )
    _apply_space_grid(fig, show_x_grid=True)
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── CHART: Earnings Surprise ─────────────────────────────────
def _build_earnings_surprise_chart(cd, key="earnings_surprise"):
    """Color-coded bars: green for beats, red for misses."""
    if cd.earnings_dates is None or cd.earnings_dates.empty:
        st.info("Earnings data not available for surprise chart.")
        return
    df = cd.earnings_dates.copy()
    # Try to find EPS columns
    est_col = None
    act_col = None
    for c in df.columns:
        cl = str(c).lower()
        if "estimate" in cl or "eps estimate" in cl:
            est_col = c
        if "reported" in cl or "actual" in cl or "eps actual" in cl:
            act_col = c
    if est_col is None or act_col is None:
        st.info("Earnings surprise data not available.")
        return
    df = df.dropna(subset=[est_col, act_col])
    if df.empty:
        st.info("No earnings surprise data to display.")
        return
    df = df.head(8).sort_index()
    surprises = df[act_col].astype(float) - df[est_col].astype(float)
    labels = [f"{s:+.2f}" for s in surprises]
    dates = [idx.strftime("%b %Y") if hasattr(idx, "strftime") else str(idx) for idx in df.index]
    # Intensity-proportional alpha: bigger surprise = brighter
    max_abs = max(abs(s) for s in surprises) if len(surprises) > 0 else 1
    bar_colors = []
    for s in surprises:
        intensity = 0.4 + 0.6 * (abs(s) / max(max_abs, 0.01))
        if s >= 0:
            bar_colors.append(f"rgba(16,185,129,{intensity:.2f})")
        else:
            bar_colors.append(f"rgba(239,68,68,{intensity:.2f})")

    fig = go.Figure(go.Bar(
        x=dates, y=surprises.values,
        marker=dict(color=bar_colors, line=dict(color="rgba(255,255,255,0.15)", width=1)),
        text=labels, textposition="outside",
        textfont=dict(size=10, color="#B8B3D7"),
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
    fig.update_layout(
        **_CHART_LAYOUT_BASE,
        height=280, margin=dict(t=30, b=30, l=50, r=30),
        xaxis=dict(tickfont=dict(size=9, color="#8A85AD"), showgrid=False),
        yaxis=dict(title=dict(text="EPS Surprise", font=dict(size=10, color="#8A85AD")),
                   tickfont=dict(size=9, color="#8A85AD")),
    )
    _apply_space_grid(fig)
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── CHART: Accretion/Dilution Waterfall ───────────────────────
def _build_accretion_waterfall(pro_forma, key="accretion_waterfall"):
    """Waterfall chart showing EPS bridge from standalone to pro forma."""
    steps = pro_forma.waterfall_steps
    if not steps:
        st.info("Waterfall data not available.")
        return

    labels = [s["label"] for s in steps]
    values = [s["value"] for s in steps]
    types = [s["type"] for s in steps]

    # Build Plotly waterfall measure types
    measures = []
    for t in types:
        if t == "absolute":
            measures.append("absolute")
        elif t == "total":
            measures.append("total")
        else:
            measures.append("relative")

    colors = []
    for i, (v, t) in enumerate(zip(values, types)):
        if t == "absolute":
            colors.append("#6B5CE7")
        elif t == "total":
            colors.append("#9B8AFF" if v >= values[0] else "#EF4444")
        else:
            colors.append("#10B981" if v >= 0 else "#EF4444")

    # Determine totals marker outline
    totals_color = "#9B8AFF" if values[-1] >= values[0] else "#EF4444"
    fig = go.Figure(go.Waterfall(
        x=labels, y=values, measure=measures,
        text=[f"${v:.2f}" for v in values],
        textposition="outside",
        textfont=dict(size=10, color="#B8B3D7"),
        connector=dict(line=dict(color="rgba(107,92,231,0.2)", width=1, dash="dot")),
        increasing=dict(marker=dict(color="#10B981", line=dict(color="rgba(255,255,255,0.15)", width=1))),
        decreasing=dict(marker=dict(color="#EF4444", line=dict(color="rgba(255,255,255,0.15)", width=1))),
        totals=dict(marker=dict(color=totals_color, line=dict(color="#fff", width=1.5))),
    ))

    fig.update_layout(
        **_CHART_LAYOUT_BASE,
        height=480, margin=dict(t=30, b=30, l=50, r=50),
        xaxis=dict(tickfont=dict(size=10, color="#8A85AD"), showgrid=False),
        yaxis=dict(title=dict(text="EPS ($)", font=dict(size=10, color="#8A85AD")),
                   tickfont=dict(size=9, color="#8A85AD"),
                   tickprefix="$"),
    )
    _apply_space_grid(fig)
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── CHART: Football Field Valuation ──────────────────────────
def _build_football_field_chart(football_field, currency_symbol="$", key="football_field"):
    """Horizontal range bars with offer price reference line."""
    offer_price = football_field.get("_offer_price", 0)
    methods = {k: v for k, v in football_field.items() if not k.startswith("_")}

    if not methods:
        st.info("Insufficient data for football field chart.")
        return

    labels = list(methods.keys())
    lows = [methods[m]["low"] for m in labels]
    highs = [methods[m]["high"] for m in labels]

    colors = ["#6B5CE7", "#10B981", "#F5A623", "#E8638B", "#3B82F6"]

    fig = go.Figure()
    for i, label in enumerate(labels):
        fig.add_trace(go.Bar(
            y=[label], x=[highs[i] - lows[i]],
            base=[lows[i]], orientation="h",
            marker=dict(
                color=colors[i % len(colors)], opacity=0.85,
                line=dict(color="rgba(255,255,255,0.15)", width=1),
            ),
            name=label,
            text=[f"{format_number(lows[i], currency_symbol=currency_symbol)} \u2014 {format_number(highs[i], currency_symbol=currency_symbol)}"],
            textposition="inside",
            textfont=dict(size=9, color="#fff"),
            hoverinfo="text",
            showlegend=False,
        ))

    if offer_price > 0:
        # Shaded band around offer price (+-5%)
        band_lo = offer_price * 0.95
        band_hi = offer_price * 1.05
        fig.add_vrect(
            x0=band_lo, x1=band_hi,
            fillcolor="rgba(239,68,68,0.06)", line_width=0,
        )
        fig.add_vline(
            x=offer_price, line_dash="dash", line_color="#EF4444", line_width=2,
            annotation_text=f"Offer: {format_number(offer_price, currency_symbol=currency_symbol)}",
            annotation_position="top",
            annotation_font=dict(size=10, color="#EF4444"),
        )

    fig.update_layout(
        **_CHART_LAYOUT_BASE,
        height=420, margin=dict(t=40, b=30, l=120, r=60),
        xaxis=dict(tickfont=dict(size=9, color="#8A85AD")),
        yaxis=dict(tickfont=dict(size=10, color="#8A85AD"), autorange="reversed"),
        barmode="stack",
    )
    _apply_space_grid(fig, show_x_grid=True)
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── CHART: Deal Structure Donut ──────────────────────────────
def _build_deal_structure_donut(assumptions, key="deal_donut"):
    """Pie chart with hole showing cash/stock split."""
    # Pull the larger slice
    pull_vals = [0.05, 0] if assumptions.pct_cash >= assumptions.pct_stock else [0, 0.05]
    fig = go.Figure(go.Pie(
        labels=["Cash", "Stock"],
        values=[assumptions.pct_cash, assumptions.pct_stock],
        hole=0.55,
        pull=pull_vals,
        marker=dict(
            colors=["#6B5CE7", "#E8638B"],
            line=dict(color="#fff", width=1.5),
        ),
        textinfo="label+percent",
        textfont=dict(size=12, color="#fff"),
        hoverinfo="label+percent+value",
    ))
    fig.update_layout(
        **_CHART_LAYOUT_BASE,
        height=340, margin=dict(t=30, b=30, l=30, r=30),
        showlegend=False,
        annotations=[dict(text="Deal<br>Mix", x=0.5, y=0.5, font_size=14,
                         font_color="#E0DCF5", showarrow=False)],
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── CHART: Company Comparison Bars ───────────────────────────
def _build_company_comparison_bars(acq_cd, tgt_cd, key="company_compare"):
    """Grouped horizontal bars comparing acquirer vs target on key metrics."""
    metrics = []
    acq_vals = []
    tgt_vals = []

    for label, acq_v, tgt_v in [
        ("Gross Margin %", (acq_cd.gross_margins or 0) * 100, (tgt_cd.gross_margins or 0) * 100),
        ("Op Margin %", (acq_cd.operating_margins or 0) * 100, (tgt_cd.operating_margins or 0) * 100),
        ("Net Margin %", (acq_cd.profit_margins or 0) * 100, (tgt_cd.profit_margins or 0) * 100),
        ("ROE %", (acq_cd.return_on_equity or 0) * 100, (tgt_cd.return_on_equity or 0) * 100),
    ]:
        metrics.append(label)
        acq_vals.append(acq_v)
        tgt_vals.append(tgt_v)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=metrics, x=acq_vals, orientation="h", name=acq_cd.ticker,
        marker=dict(color="#6B5CE7", line=dict(color="rgba(255,255,255,0.15)", width=1)),
        text=[f"{v:.1f}%" for v in acq_vals],
        textposition="outside", textfont=dict(size=10, color="#B8B3D7"),
    ))
    fig.add_trace(go.Bar(
        y=metrics, x=tgt_vals, orientation="h", name=tgt_cd.ticker,
        marker=dict(color="#E8638B", line=dict(color="rgba(255,255,255,0.15)", width=1)),
        text=[f"{v:.1f}%" for v in tgt_vals],
        textposition="outside", textfont=dict(size=10, color="#B8B3D7"),
    ))
    # Star annotation on winning metric
    for i, (av, tv) in enumerate(zip(acq_vals, tgt_vals)):
        winner_x = max(av, tv) * 1.12
        fig.add_annotation(
            y=metrics[i], x=winner_x,
            text="\u2605", showarrow=False,
            font=dict(size=10, color="#F5A623"),
        )
    fig.update_layout(
        **_CHART_LAYOUT_BASE,
        height=380, margin=dict(t=30, b=20, l=100, r=70),
        xaxis=dict(tickfont=dict(size=9, color="#8A85AD"), ticksuffix="%"),
        yaxis=dict(tickfont=dict(size=10, color="#8A85AD"), autorange="reversed"),
        legend=dict(font=dict(size=10, color="#B8B3D7"), orientation="h", yanchor="bottom", y=1.02),
        barmode="group",
    )
    _apply_space_grid(fig, show_x_grid=True)
    st.plotly_chart(fig, use_container_width=True, key=key)


# ── RENDER: SWOT Grid ─────────────────────────────────────────
def _render_swot_grid(swot):
    """2x2 CSS grid with color-coded SWOT cards."""
    if not swot:
        st.info("SWOT analysis not available.")
        return
    quadrants = [
        ("Strengths", swot.get("strengths", []), "#10B981", "rgba(16,185,129,0.08)", "rgba(16,185,129,0.25)"),
        ("Weaknesses", swot.get("weaknesses", []), "#EF4444", "rgba(239,68,68,0.08)", "rgba(239,68,68,0.25)"),
        ("Opportunities", swot.get("opportunities", []), "#6B5CE7", "rgba(107,92,231,0.08)", "rgba(107,92,231,0.25)"),
        ("Threats", swot.get("threats", []), "#F5A623", "rgba(245,166,35,0.08)", "rgba(245,166,35,0.25)"),
    ]
    html = '<div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem;">'
    for title, items, color, bg, border_color in quadrants:
        bullets = "".join(
            f'<div style="font-size:0.84rem; color:#B8B3D7; line-height:1.7; padding:0.15rem 0;">&bull; {item}</div>'
            for item in items
        ) if items else '<div style="font-size:0.84rem; color:#8A85AD;">No data available</div>'
        html += (
            f'<div style="background:{bg}; border:1px solid {border_color}; border-radius:14px; padding:1.2rem;">'
            f'<div style="font-size:0.85rem; font-weight:700; color:{color}; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.5px;">{title}</div>'
            f'{bullets}'
            f'</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── RENDER: Growth Outlook ────────────────────────────────────
def _render_growth_outlook(growth, cd):
    """Rating badge + thesis sub-sections + catalyst/risk columns."""
    if not growth:
        st.info("Growth outlook not available.")
        return
    rating = growth.get("growth_rating", "MODERATE")
    rating_colors = {"STRONG": "#10B981", "MODERATE": "#F5A623", "WEAK": "#EF4444"}
    rating_color = rating_colors.get(rating, "#8A85AD")
    rating_bg = {"STRONG": "rgba(16,185,129,0.12)", "MODERATE": "rgba(245,166,35,0.12)", "WEAK": "rgba(239,68,68,0.12)"}

    st.markdown(
        f'<div style="display:inline-block; background:{rating_bg.get(rating, "rgba(138,133,173,0.12)")}; '
        f'color:{rating_color}; padding:0.4rem 1.2rem; border-radius:20px; font-weight:700; '
        f'font-size:0.9rem; letter-spacing:1px; margin-bottom:1rem;">Growth Rating: {rating}</div>',
        unsafe_allow_html=True,
    )

    for key, title in [("revenue_thesis", "Revenue Thesis"), ("margin_thesis", "Margin Thesis"), ("earnings_path", "Earnings Path")]:
        text = growth.get(key, "")
        if text:
            # Clean bullet prefix
            clean = text.strip()
            if clean.startswith("- "):
                clean = clean[2:]
            st.markdown(
                f'<div style="margin-bottom:0.8rem;">'
                f'<div style="font-size:0.8rem; font-weight:700; color:#9B8AFF; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.2rem;">{title}</div>'
                f'<div style="font-size:0.85rem; color:#B8B3D7; line-height:1.7;">{clean}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Catalysts & Risks in two columns
    cat_col, risk_col = st.columns(2)
    with cat_col:
        st.markdown('<div style="font-size:0.8rem; font-weight:700; color:#10B981; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.3rem;">Key Catalysts</div>', unsafe_allow_html=True)
        for item in growth.get("key_catalysts", []):
            st.markdown(f'<div style="font-size:0.84rem; color:#B8B3D7; line-height:1.7; padding:0.1rem 0;">&bull; {item}</div>', unsafe_allow_html=True)
    with risk_col:
        st.markdown('<div style="font-size:0.8rem; font-weight:700; color:#EF4444; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.3rem;">Key Risks to Growth</div>', unsafe_allow_html=True)
        for item in growth.get("key_risks_to_growth", []):
            st.markdown(f'<div style="font-size:0.84rem; color:#B8B3D7; line-height:1.7; padding:0.1rem 0;">&bull; {item}</div>', unsafe_allow_html=True)


# ── RENDER: Capital Allocation ────────────────────────────────
def _render_capital_allocation(ca, cd):
    """Letter grade badge + border-left styled sub-section cards."""
    if not ca:
        st.info("Capital allocation analysis not available.")
        return
    grade = ca.get("capital_allocation_grade", "B")
    grade_colors = {"A": "#10B981", "B": "#6B5CE7", "C": "#F5A623", "D": "#EF4444"}
    grade_color = grade_colors.get(grade, "#8A85AD")
    grade_bg = {"A": "rgba(16,185,129,0.12)", "B": "rgba(107,92,231,0.12)", "C": "rgba(245,166,35,0.12)", "D": "rgba(239,68,68,0.12)"}

    st.markdown(
        f'<div style="display:inline-block; background:{grade_bg.get(grade, "rgba(138,133,173,0.12)")}; '
        f'color:{grade_color}; padding:0.4rem 1.2rem; border-radius:20px; font-weight:700; '
        f'font-size:0.9rem; letter-spacing:1px; margin-bottom:1rem;">Capital Allocation Grade: {grade}</div>',
        unsafe_allow_html=True,
    )

    sections = [
        ("Strategy Summary", ca.get("strategy_summary", ""), "#6B5CE7"),
        ("CapEx Assessment", ca.get("capex_assessment", ""), "#E8638B"),
        ("Shareholder Returns", ca.get("shareholder_returns", ""), "#10B981"),
        ("M&A Strategy", ca.get("ma_strategy", ""), "#F5A623"),
        ("Debt Management", ca.get("debt_management", ""), "#8A85AD"),
    ]
    for title, text, color in sections:
        if text:
            clean = text.strip()
            if clean.startswith("- "):
                clean = clean[2:]
            st.markdown(
                f'<div style="border-left:3px solid {color}; padding:0.6rem 0 0.6rem 1rem; margin-bottom:0.6rem;">'
                f'<div style="font-size:0.8rem; font-weight:700; color:{color}; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.15rem;">{title}</div>'
                f'<div style="font-size:0.85rem; color:#B8B3D7; line-height:1.7;">{clean}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Sidebar Helper: Render Company Preview Card ───────────────
def _render_company_card(ticker: str, role: str = "") -> None:
    """Render a company preview card in the sidebar."""
    if not ticker or len(ticker) < 1:
        return

    info = _quick_ticker_lookup(ticker)
    if not info or not info.get("valid"):
        st.markdown(
            f'<div class="sb-company-invalid">⚠️ Could not find: {ticker}</div>',
            unsafe_allow_html=True,
        )
        return

    name = info.get("name", ticker)
    price = info.get("price")
    currency = info.get("currency", "USD")
    change_pct = info.get("change_pct")
    logo_url = info.get("logo_url", "")

    # Currency symbol
    curr_sym = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CAD": "C$"}.get(currency, "$")

    # Price display
    price_str = f"{curr_sym}{price:,.2f}" if price else "—"

    # Change display
    if change_pct is not None:
        change_class = "up" if change_pct >= 0 else "down"
        change_str = f'<div class="sb-company-price-change {change_class}">{change_pct:+.2f}%</div>'
    else:
        change_str = ""

    # Logo with fallback
    logo_html = f'<img src="{logo_url}" class="sb-company-logo" onerror="this.style.display=\'none\'">' if logo_url else ""
    if not logo_html:
        logo_html = f'<div class="sb-company-logo" style="display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:800;background:linear-gradient(135deg,#6B5CE7,#9B8AFF);color:#fff;">{ticker[0]}</div>'

    # Role label
    role_html = f'<span class="sb-role-label {role.lower()}">{role}</span>' if role else ""

    st.markdown(
        f'{role_html}'
        f'<div class="sb-company-card">'
        f'{logo_html}'
        f'<div class="sb-company-info">'
        f'<div class="sb-company-name">{name}</div>'
        f'<div class="sb-company-ticker">{ticker}</div>'
        f'</div>'
        f'<div class="sb-company-price">'
        f'<div class="sb-company-price-value">{price_str}</div>'
        f'{change_str}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    # Logo / Brand Header
    st.markdown(
        '<div style="text-align:center; padding: 1.5rem 0 1rem 0;">'
        '<div style="font-size:1.6rem; font-weight:800; letter-spacing:-0.5px; color:#fff;">M&A Profile</div>'
        '<div style="font-size:1.6rem; font-weight:800; background:linear-gradient(135deg,#9B8AFF,#E8638B);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-top:-0.4rem;">Builder</div>'
        '<div style="font-size:0.65rem; color:#A8A3C7; margin-top:0.4rem; letter-spacing:2px; text-transform:uppercase;">Investment Research Platform</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    # Mode Toggle
    analysis_mode = st.radio("Mode", ["Company Profile", "Merger Analysis"], horizontal=True, label_visibility="collapsed")

    st.markdown('<div style="height:0.8rem;"></div>', unsafe_allow_html=True)

    if analysis_mode == "Company Profile":
        # ── Company Profile Mode ──
        st.markdown(
            '<div class="sb-section"><span class="sb-section-icon">📊</span> COMPANY</div>',
            unsafe_allow_html=True,
        )

        ticker_input = st.text_input(
            "Stock Ticker", value="", max_chars=10,
            placeholder="Enter ticker (e.g. AAPL)",
            label_visibility="collapsed",
        ).strip().upper()

        # Show company preview card
        if ticker_input:
            _render_company_card(ticker_input)

        st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)
        generate_btn = st.button("🚀 Generate Profile", type="primary", use_container_width=True)

        # Merger-specific variables (unused in this mode)
        acquirer_input = ""
        target_input = ""
        merger_btn = False
        merger_assumptions = MergerAssumptions()

    else:
        # ── Merger Analysis Mode ──
        ticker_input = ""
        generate_btn = False

        # Acquirer
        st.markdown(
            '<div class="sb-section"><span class="sb-section-icon">🏢</span> ACQUIRER</div>',
            unsafe_allow_html=True,
        )
        acquirer_input = st.text_input(
            "Acquirer", value="", max_chars=10,
            placeholder="Enter ticker (e.g. MSFT)",
            label_visibility="collapsed",
        ).strip().upper()
        if acquirer_input:
            _render_company_card(acquirer_input, "Acquirer")

        # Target
        st.markdown(
            '<div class="sb-section"><span class="sb-section-icon">🎯</span> TARGET</div>',
            unsafe_allow_html=True,
        )
        target_input = st.text_input(
            "Target", value="", max_chars=10,
            placeholder="Enter ticker (e.g. ATVI)",
            label_visibility="collapsed",
        ).strip().upper()
        if target_input:
            _render_company_card(target_input, "Target")

        # ── Section: Deal Structure ──
        st.markdown(
            '<div class="sb-section"><span class="sb-section-icon">💰</span> DEAL STRUCTURE</div>',
            unsafe_allow_html=True,
        )
        offer_premium = st.slider("Offer Premium (%)", 0, 100, 30, 5)
        pct_cash = st.slider("Cash Consideration (%)", 0, 100, 50, 5)
        pct_stock = 100 - pct_cash
        st.markdown(
            f'<div class="sb-split-bar">'
            f'<div class="sb-split-cash" style="width:{pct_cash}%"></div>'
            f'<div class="sb-split-stock" style="width:{pct_stock}%"></div>'
            f'</div>'
            f'<div class="sb-split-labels">'
            f'<span class="cash-label">Cash {pct_cash}%</span>'
            f'<span class="stock-label">Stock {pct_stock}%</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Section: Synergies ──
        st.markdown(
            '<div class="sb-section"><span class="sb-section-icon">⚡</span> SYNERGIES</div>',
            unsafe_allow_html=True,
        )
        cost_syn = st.slider("Cost Synergies (% of Target SG&A)", 0, 30, 10, 1)
        rev_syn = st.slider("Revenue Synergies (% of Target Rev)", 0, 10, 2, 1)

        # ── Section: Financing & Fees ──
        st.markdown(
            '<div class="sb-section"><span class="sb-section-icon">🏦</span> FINANCING &amp; FEES</div>',
            unsafe_allow_html=True,
        )
        txn_fees = st.slider("Transaction Fees (%)", 0.5, 5.0, 2.0, 0.5)
        adv_cost_of_debt = st.slider("Cost of Debt (%)", 2.0, 10.0, 5.0, 0.5)
        adv_tax_rate = st.slider("Tax Rate (%)", 10, 40, 25, 1)

        merger_assumptions = MergerAssumptions(
            offer_premium_pct=offer_premium,
            pct_cash=pct_cash,
            pct_stock=pct_stock,
            cost_synergies_pct=cost_syn,
            revenue_synergies_pct=rev_syn,
            transaction_fees_pct=txn_fees,
            tax_rate=adv_tax_rate,
            cost_of_debt=adv_cost_of_debt,
        )

        st.markdown('<div style="height:0.8rem;"></div>', unsafe_allow_html=True)
        merger_btn = st.button("🚀 Analyze Deal", type="primary", use_container_width=True)

    # Footer
    st.markdown('<div class="sb-divider" style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center; padding: 0.3rem 0;">'
        '<div style="font-size:0.6rem; color:#4B5563; letter-spacing:0.5px; line-height:1.9;">'
        'DATA: YAHOO FINANCE • CHARTS: PLOTLY<br>'
        'AI: OPENAI (OPT.) • LOGOS: CLEARBIT'
        '</div></div>',
        unsafe_allow_html=True,
    )

# ── Main Area ────────────────────────────────────────────────
if analysis_mode == "Company Profile":
    st.markdown(
        '<div class="hero-header">'
        '<p class="hero-title">M&A Profile <span class="hero-accent">Builder</span></p>'
        '<p class="hero-sub">Comprehensive company research & 8-slide tear sheet generator</p>'
        '<span class="hero-tagline">Powered by Live Market Data</span>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="hero-header">'
        '<p class="hero-title">Merger <span class="hero-accent">Simulator</span></p>'
        '<p class="hero-sub">Pro forma analysis, accretion/dilution & deal book generation</p>'
        '<span class="hero-tagline">Powered by Live Market Data</span>'
        '</div>',
        unsafe_allow_html=True,
    )

if analysis_mode == "Company Profile" and generate_btn and ticker_input:
    # ── Data Fetching (with scanner loading animation) ───
    _scanner_slot = st.empty()

    try:
        _scanner_slot.markdown(_render_profile_scanner(ticker_input.upper(), 0), unsafe_allow_html=True)
    except Exception:
        pass  # Scanner rendering is non-critical

    try:
        cd = fetch_company_data(ticker_input)
    except Exception as e:
        _scanner_slot.empty()
        st.error(f"Failed to fetch data for **{ticker_input}**: {e}")
        st.stop()

    try:
        _scanner_slot.markdown(_render_profile_scanner(ticker_input.upper(), 1), unsafe_allow_html=True)
    except Exception:
        pass

    try:
        cd = fetch_peer_data(cd)
    except Exception:
        pass  # Peer data is non-critical

    try:
        _scanner_slot.markdown(_render_profile_scanner(ticker_input.upper(), 2), unsafe_allow_html=True)
    except Exception:
        pass

    try:
        cd = generate_insights(cd)
    except Exception as e:
        print(f"Insights generation warning: {e}")  # Non-fatal

    try:
        _scanner_slot.markdown(_render_profile_scanner(ticker_input.upper(), 3), unsafe_allow_html=True)
        time.sleep(1.2)
    except Exception:
        pass

    _scanner_slot.empty()

    cs = cd.currency_symbol  # shorthand

    # ══════════════════════════════════════════════════════
    # 1. COMPANY HEADER CARD (with logo)
    # ══════════════════════════════════════════════════════
    chg_class = "price-up" if cd.price_change >= 0 else "price-down"
    chg_badge = "change-up" if cd.price_change >= 0 else "change-down"
    arrow = "&#9650;" if cd.price_change >= 0 else "&#9660;"

    logo_html = ""
    if cd.logo_url:
        _ld = getattr(cd, 'logo_domain', '')
        logo_fallback = f"this.onerror=null; this.src='https://logo.clearbit.com/{_ld}';" if _ld else "this.style.display='none';"
        logo_html = (
            f'<img src="{cd.logo_url}" '
            f'style="width:52px; height:52px; border-radius:10px; object-fit:contain; '
            f'background:white; padding:4px; margin-right:1.2rem; flex-shrink:0;" '
            f'onerror="{logo_fallback}">'
        )

    st.markdown(
        f'<div class="company-card">'
        f'<div style="display:flex; align-items:center; position:relative;">'
        f'{logo_html}'
        f'<div>'
        f'<p class="company-name">{cd.name}</p>'
        f'<p class="company-meta"><span>{cd.ticker}</span> &nbsp;&middot;&nbsp; {cd.exchange} &nbsp;&middot;&nbsp; {cd.sector} &rarr; {cd.industry}</p>'
        f'</div>'
        f'</div>'
        f'<div style="display:flex; align-items:baseline; gap:1rem; margin-top:0.8rem; position:relative;">'
        f'<p class="price-tag {chg_class}">{cs}{cd.current_price:,.2f}</p>'
        f'<span class="price-change {chg_badge}">{arrow} {cd.price_change:+.2f} ({cd.price_change_pct:+.2f}%)</span>'
        f'<span style="font-size:0.75rem; color:#A8A3C7; margin-left:0.5rem;">{cd.currency_code}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════
    # 2. PROMINENT PRICE / VOLUME DISPLAY
    # ══════════════════════════════════════════════════════
    price_color = "#10B981" if cd.price_change >= 0 else "#EF4444"
    price_bg = "rgba(16,185,129,0.05)" if cd.price_change >= 0 else "rgba(239,68,68,0.05)"

    st.markdown(
        f'<div class="price-bar" style="background:{price_bg}; border:1px solid {"rgba(16,185,129,0.15)" if cd.price_change >= 0 else "rgba(239,68,68,0.15)"};">'
        f'<div style="flex:1;">'
        f'<div style="font-size:0.65rem; font-weight:600; color:#8A85AD; text-transform:uppercase; letter-spacing:1px;">Current Price</div>'
        f'<div style="font-size:2rem; font-weight:800; color:{price_color};">'
        f'{cs}{cd.current_price:,.2f}'
        f'<span style="font-size:0.9rem; margin-left:0.5rem;">{arrow} {cd.price_change:+.2f} ({cd.price_change_pct:+.2f}%)</span></div>'
        f'</div>'
        f'<div style="flex:0 0 180px; text-align:center; border-left:1px solid rgba(255,255,255,0.1); padding-left:1rem;">'
        f'<div style="font-size:0.65rem; font-weight:600; color:#8A85AD; text-transform:uppercase; letter-spacing:1px;">Volume</div>'
        f'<div style="font-size:1.3rem; font-weight:700; color:#E0DCF5;">{format_number(cd.volume, prefix="", decimals=0)}</div>'
        f'<div style="font-size:0.6rem; color:#8A85AD;">Avg: {format_number(cd.avg_volume, prefix="", decimals=0)}</div>'
        f'</div>'
        f'<div style="flex:0 0 220px; text-align:center; border-left:1px solid rgba(255,255,255,0.1); padding-left:1rem;">'
        f'<div style="font-size:0.65rem; font-weight:600; color:#8A85AD; text-transform:uppercase; letter-spacing:1px;">52W Range</div>'
        f'<div style="font-size:1.1rem; font-weight:600; color:#E0DCF5;">'
        f'{cs}{cd.fifty_two_week_low:,.2f} &mdash; {cs}{cd.fifty_two_week_high:,.2f}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Quick KPI strip
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Market Cap", format_number(cd.market_cap, currency_symbol=cs))
    k2.metric("Enterprise Value", format_number(cd.enterprise_value, currency_symbol=cs))
    k3.metric("Revenue (TTM)", format_number(cd.revenue.iloc[0], currency_symbol=cs) if cd.revenue is not None and len(cd.revenue) > 0 else "N/A")
    k4.metric("Net Income", format_number(cd.net_income.iloc[0], currency_symbol=cs) if cd.net_income is not None and len(cd.net_income) > 0 else "N/A")
    k5.metric("Free Cash Flow", format_number(cd.free_cashflow_series.iloc[0], currency_symbol=cs) if cd.free_cashflow_series is not None and len(cd.free_cashflow_series) > 0 else "N/A")
    k6.metric("Dividend Yield", format_pct(cd.dividend_yield) if cd.dividend_yield else "N/A")

    # ══════════════════════════════════════════════════════
    # 3. BUSINESS OVERVIEW
    # ══════════════════════════════════════════════════════
    _section("Business Overview")
    with st.expander("Company Description", expanded=True):
        if cd.long_business_summary:
            st.markdown(f"<div style='line-height:1.7; color:#B8B3D7; font-size:0.9rem;'>{cd.long_business_summary}</div>", unsafe_allow_html=True)
        else:
            st.info("Business description not available.")
        b1, b2, b3 = st.columns(3)
        with b1:
            emp_val = f"{cd.full_time_employees:,}" if cd.full_time_employees else "N/A"
            st.markdown(f'<div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:0.6rem 0.8rem; text-align:center;"><div style="font-size:0.65rem; font-weight:600; text-transform:uppercase; letter-spacing:0.7px; color:#8A85AD; margin-bottom:0.2rem;">Employees</div><div style="font-size:1rem; font-weight:700; color:#E0DCF5;">{emp_val}</div></div>', unsafe_allow_html=True)
        with b2:
            hq = f"{cd.city}, {cd.state}" if cd.city else "N/A"
            if cd.country and cd.country != "United States":
                hq += f", {cd.country}"
            st.markdown(f'<div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:0.6rem 0.8rem; text-align:center;"><div style="font-size:0.65rem; font-weight:600; text-transform:uppercase; letter-spacing:0.7px; color:#8A85AD; margin-bottom:0.2rem;">Headquarters</div><div style="font-size:1rem; font-weight:700; color:#E0DCF5;">{hq}</div></div>', unsafe_allow_html=True)
        with b3:
            web_display = cd.website.replace("https://", "").replace("http://", "").rstrip("/") if cd.website else "N/A"
            st.markdown(f'<div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); border-radius:10px; padding:0.6rem 0.8rem; text-align:center;"><div style="font-size:0.65rem; font-weight:600; text-transform:uppercase; letter-spacing:0.7px; color:#8A85AD; margin-bottom:0.2rem;">Website</div><div style="font-size:1rem; font-weight:700; color:#E0DCF5;">{web_display}</div></div>', unsafe_allow_html=True)

    _divider()

    # ══════════════════════════════════════════════════════
    # 4. PRICE CHART
    # ══════════════════════════════════════════════════════
    _section("Price History")

    period_choice = st.radio("Period", ["1Y", "3Y", "5Y"], horizontal=True, index=2, label_visibility="collapsed")

    hist = cd.hist_5y if cd.hist_5y is not None and not cd.hist_5y.empty else cd.hist_1y
    if hist is not None and not hist.empty:
        if period_choice == "1Y" and cd.hist_1y is not None:
            plot_hist = cd.hist_1y
        elif period_choice == "3Y" and hist is not None:
            plot_hist = hist.last("3Y") if hasattr(hist, "last") else hist.tail(756)
        else:
            plot_hist = hist

        fig = go.Figure()
        # Glow underlay + main price line
        _glow_line_traces(fig, plot_hist.index, plot_hist["Close"], "#6B5CE7", "Close")
        # Area fill
        fig.add_trace(go.Scatter(
            x=plot_hist.index, y=plot_hist["Close"],
            mode="lines", line=dict(width=0), fill="tozeroy",
            fillcolor="rgba(107,92,231,0.06)",
            showlegend=False, hoverinfo="skip",
        ))
        # Color-coded volume bars
        if "Volume" in plot_hist.columns:
            close_vals = plot_hist["Close"].values
            vol_colors = []
            for i in range(len(close_vals)):
                if i == 0:
                    vol_colors.append("rgba(107,92,231,0.15)")
                elif close_vals[i] >= close_vals[i - 1]:
                    vol_colors.append("rgba(107,92,231,0.15)")
                else:
                    vol_colors.append("rgba(232,99,139,0.12)")
            fig.add_trace(go.Bar(
                x=plot_hist.index, y=plot_hist["Volume"],
                name="Volume", yaxis="y2",
                marker_color=vol_colors,
            ))
            fig.update_layout(
                yaxis2=dict(overlaying="y", side="right", showgrid=False,
                            title=dict(text="Volume", font=dict(size=10, color="#8A85AD")),
                            tickformat=".2s", tickfont=dict(size=8, color="#8A85AD")),
            )
        # 52-week high/low reference lines
        if cd.fifty_two_week_high:
            fig.add_hline(y=cd.fifty_two_week_high, line_dash="dash",
                         line_color="rgba(16,185,129,0.3)", line_width=1,
                         annotation_text="52w High", annotation_position="bottom right",
                         annotation_font=dict(size=8, color="#10B981"))
        if cd.fifty_two_week_low:
            fig.add_hline(y=cd.fifty_two_week_low, line_dash="dash",
                         line_color="rgba(239,68,68,0.3)", line_width=1,
                         annotation_text="52w Low", annotation_position="top right",
                         annotation_font=dict(size=8, color="#EF4444"))
        fig.update_layout(
            **_CHART_LAYOUT_BASE,
            height=420,
            margin=dict(t=10, b=30, l=50, r=50),
            xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#8A85AD"), rangeslider=dict(visible=False)),
            yaxis=dict(
                title=dict(text=f"Price ({cs})", font=dict(size=10, color="#8A85AD")),
                tickfont=dict(size=9, color="#8A85AD"),
                tickprefix=cs,
            ),
            showlegend=False,
        )
        _apply_space_grid(fig)
        st.markdown('<div class="profile-chart-wrapper">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Price history not available.")

    _divider()

    # ══════════════════════════════════════════════════════
    # 5. VALUATION DASHBOARD
    # ══════════════════════════════════════════════════════
    _section("Valuation Dashboard")

    vd1, vd2, vd3, vd4, vd5 = st.columns(5)
    vd1.metric("P/E (TTM)", f"{cd.trailing_pe:.1f}x" if cd.trailing_pe else "N/A")
    vd2.metric("Forward P/E", f"{cd.forward_pe:.1f}x" if cd.forward_pe else "N/A")
    vd3.metric("EV/EBITDA", format_multiple(cd.ev_to_ebitda))
    vd4.metric("P/S (TTM)", f"{cd.price_to_sales:.1f}x" if cd.price_to_sales else "N/A")
    vd5.metric("PEG Ratio", f"{cd.peg_ratio:.2f}" if cd.peg_ratio else "N/A")

    # Premium/Discount vs Peers
    if cd.peer_data:
        st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#8A85AD; text-transform:uppercase; letter-spacing:1px; margin:0.8rem 0 0.3rem 0;'>Premium / Discount vs. Peer Median</p>", unsafe_allow_html=True)

        def _calc_premium(company_val, peers, key):
            if company_val is None:
                return None
            vals = [p.get(key) for p in peers if p.get(key) is not None]
            if not vals:
                return None
            median = float(np.median(vals))
            if median == 0:
                return None
            return ((company_val - median) / abs(median)) * 100

        premium_items = [
            ("P/E", _calc_premium(cd.trailing_pe, cd.peer_data, "trailing_pe")),
            ("Fwd P/E", _calc_premium(cd.forward_pe, cd.peer_data, "forward_pe")),
            ("EV/EBITDA", _calc_premium(cd.ev_to_ebitda, cd.peer_data, "ev_to_ebitda")),
            ("P/S", _calc_premium(cd.price_to_sales, cd.peer_data, "price_to_sales")),
        ]

        pc_cols = st.columns(4)
        for col, (label, prem) in zip(pc_cols, premium_items):
            if prem is not None:
                word = "Premium" if prem > 0 else "Discount"
                col.metric(f"{label} vs Peers", f"{prem:+.1f}%", delta=word,
                           delta_color="inverse" if prem > 0 else "normal")
            else:
                col.metric(f"{label} vs Peers", "N/A")

    # ══════════════════════════════════════════════════════
    # 6. PEER COMPARISON
    # ══════════════════════════════════════════════════════
    if cd.peer_data:
        _section("Peer Comparison")

        peer_rows = []
        peer_rows.append({
            "Company": f"{cd.name} \u2605",
            "Ticker": cd.ticker,
            "Mkt Cap": format_number(cd.market_cap, currency_symbol=cs),
            "P/E": f"{cd.trailing_pe:.1f}" if cd.trailing_pe else "N/A",
            "Fwd P/E": f"{cd.forward_pe:.1f}" if cd.forward_pe else "N/A",
            "EV/EBITDA": format_multiple(cd.ev_to_ebitda),
            "P/S": f"{cd.price_to_sales:.1f}" if cd.price_to_sales else "N/A",
            "Gross Margin": format_pct(cd.gross_margins),
            "Op Margin": format_pct(cd.operating_margins),
            "ROE": format_pct(cd.return_on_equity),
        })
        for p in cd.peer_data:
            peer_rows.append({
                "Company": p.get("name", p.get("ticker", "")),
                "Ticker": p.get("ticker", ""),
                "Mkt Cap": format_number(p.get("market_cap"), currency_symbol=cs),
                "P/E": f"{p['trailing_pe']:.1f}" if p.get("trailing_pe") else "N/A",
                "Fwd P/E": f"{p['forward_pe']:.1f}" if p.get("forward_pe") else "N/A",
                "EV/EBITDA": format_multiple(p.get("ev_to_ebitda")),
                "P/S": f"{p['price_to_sales']:.1f}" if p.get("price_to_sales") else "N/A",
                "Gross Margin": format_pct(p.get("gross_margins")),
                "Op Margin": format_pct(p.get("operating_margins")),
                "ROE": format_pct(p.get("return_on_equity")),
            })

        peer_df = pd.DataFrame(peer_rows)

        def _highlight_target(row):
            if row["Ticker"] == cd.ticker:
                return ["background-color: rgba(107,92,231,0.1); font-weight: bold"] * len(row)
            return [""] * len(row)

        styled = peer_df.style.apply(_highlight_target, axis=1)
        st.dataframe(styled, use_container_width=True, hide_index=True, height=300)

        # Radar chart
        rc1, rc2 = st.columns([3, 2])
        with rc1:
            st.markdown('<div class="profile-chart-wrapper">', unsafe_allow_html=True)
            _build_peer_radar_chart(cd)
            st.markdown('</div>', unsafe_allow_html=True)
        with rc2:
            st.markdown("")
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#E0DCF5; margin-bottom:0.5rem;'>Peer Group</p>", unsafe_allow_html=True)
            for p in cd.peer_data:
                st.markdown(
                    f"<div style='font-size:0.82rem; color:#B8B3D7; padding:0.2rem 0;'>"
                    f"<span style='font-weight:600; color:#9B8AFF;'>{p['ticker']}</span> &mdash; {p.get('name', '')}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(f"<div style='font-size:0.7rem; color:#8A85AD; margin-top:0.5rem;'>Industry: {cd.industry}</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 7. KEY STATISTICS
    # ══════════════════════════════════════════════════════
    _section("Key Statistics")

    st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#8A85AD; text-transform:uppercase; letter-spacing:1px; margin:0.5rem 0 0.3rem 0;'>Valuation</p>", unsafe_allow_html=True)
    v1, v2, v3, v4, v5 = st.columns(5)
    v1.metric("P/E (TTM)", f"{cd.trailing_pe:.1f}" if cd.trailing_pe else "N/A")
    v2.metric("Forward P/E", f"{cd.forward_pe:.1f}" if cd.forward_pe else "N/A")
    v3.metric("PEG Ratio", f"{cd.peg_ratio:.2f}" if cd.peg_ratio else "N/A")
    v4.metric("EV/EBITDA", format_multiple(cd.ev_to_ebitda))
    v5.metric("EV/Revenue", format_multiple(cd.ev_to_revenue))

    st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#8A85AD; text-transform:uppercase; letter-spacing:1px; margin:0.8rem 0 0.3rem 0;'>Profitability</p>", unsafe_allow_html=True)
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Gross Margin", format_pct(cd.gross_margins))
    p2.metric("Op. Margin", format_pct(cd.operating_margins))
    p3.metric("Net Margin", format_pct(cd.profit_margins))
    p4.metric("ROE", format_pct(cd.return_on_equity))
    p5.metric("ROA", format_pct(cd.return_on_assets))

    st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#8A85AD; text-transform:uppercase; letter-spacing:1px; margin:0.8rem 0 0.3rem 0;'>Financial Health</p>", unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns(5)
    f1.metric("P/S (TTM)", f"{cd.price_to_sales:.2f}" if cd.price_to_sales else "N/A")
    f2.metric("Price/Book", f"{cd.price_to_book:.2f}" if cd.price_to_book else "N/A")
    f3.metric("Current Ratio", f"{cd.current_ratio:.2f}" if cd.current_ratio else "N/A")
    f4.metric("D/E Ratio", f"{cd.debt_to_equity / 100:.2f}x" if cd.debt_to_equity else "N/A")
    f5.metric("Beta", f"{cd.beta:.2f}" if cd.beta else "N/A")

    _divider()

    # ══════════════════════════════════════════════════════
    # 8. FINANCIAL STATEMENTS (formatted)
    # ══════════════════════════════════════════════════════
    _section("Financial Statements")

    def _display_financial_df(df, label, quarterly=False):
        if df is not None and not df.empty:
            display_df = df.copy()
            fmt = "%b %Y" if quarterly else "%Y"
            new_cols = []
            for c in display_df.columns:
                col_str = c.strftime(fmt) if hasattr(c, "strftime") else str(c)
                base, n = col_str, 1
                while col_str in new_cols:
                    n += 1
                    col_str = f"{base} ({n})"
                new_cols.append(col_str)
            display_df.columns = new_cols

            # Format numeric values
            def _fmt_cell(val):
                if pd.isna(val):
                    return "N/A"
                try:
                    v = float(val)
                    abs_v = abs(v)
                    sign = "-" if v < 0 else ""
                    if abs_v >= 1e9:
                        return f"{sign}{cs}{abs_v / 1e9:.1f}B"
                    elif abs_v >= 1e6:
                        return f"{sign}{cs}{abs_v / 1e6:.1f}M"
                    elif abs_v >= 1e3:
                        return f"{sign}{cs}{abs_v / 1e3:.1f}K"
                    elif abs_v == 0:
                        return f"{cs}0"
                    else:
                        return f"{sign}{cs}{abs_v:,.2f}"
                except (TypeError, ValueError):
                    return str(val)

            formatted_df = display_df.map(_fmt_cell)
            st.dataframe(formatted_df, use_container_width=True, height=400)
        else:
            st.info(f"{label} not available.")

    fin_tab1, fin_tab2, fin_tab3, fin_tab4 = st.tabs([
        "Income Statement", "Balance Sheet", "Cash Flow", "Quarterly Income"
    ])
    with fin_tab1:
        _display_financial_df(cd.income_stmt, "Income Statement")
    with fin_tab2:
        _display_financial_df(cd.balance_sheet, "Balance Sheet")
    with fin_tab3:
        _display_financial_df(cd.cashflow, "Cash Flow Statement")
    with fin_tab4:
        _display_financial_df(cd.quarterly_income_stmt, "Quarterly Income Statement", quarterly=True)

    # ══════════════════════════════════════════════════════
    # 9. ANALYST CONSENSUS
    # ══════════════════════════════════════════════════════
    _section("Analyst Consensus")
    a1, a2 = st.columns([3, 2])

    with a1:
        if cd.recommendations_summary is not None and not cd.recommendations_summary.empty:
            try:
                row = cd.recommendations_summary.iloc[0]
                cats = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
                keys = ["strongBuy", "buy", "hold", "sell", "strongSell"]
                vals = [int(row.get(k, 0)) for k in keys]
                colors = ["#10B981", "#34D399", "#F59E0B", "#EF4444", "#991B1B"]
                total = sum(vals)

                # Wider bar for the majority category
                max_idx = vals.index(max(vals)) if vals else -1
                widths = [0.7 if i == max_idx else 0.5 for i in range(len(vals))]
                fig_rec = go.Figure(go.Bar(
                    x=vals, y=cats, orientation="h",
                    marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.15)", width=1)),
                    width=widths,
                    text=[f"  {v} ({v/total*100:.0f}%)" if total > 0 else f"  {v}" for v in vals],
                    textposition="outside",
                    textfont=dict(size=11, color="#B8B3D7", family="Inter"),
                ))
                fig_rec.update_layout(
                    **_CHART_LAYOUT_BASE,
                    height=280, margin=dict(t=40, b=20, l=110, r=60),
                    title=dict(text="Analyst Recommendation Distribution",
                               font=dict(size=13, color="#E0DCF5", family="Inter")),
                    xaxis=dict(title=dict(text="# Analysts", font=dict(size=10, color="#8A85AD")),
                               tickfont=dict(size=9, color="#8A85AD")),
                    yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#8A85AD")),
                    bargap=0.35,
                )
                _apply_space_grid(fig_rec, show_x_grid=True)
                st.markdown('<div class="profile-chart-wrapper">', unsafe_allow_html=True)
                st.plotly_chart(fig_rec, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception:
                st.info("Recommendation data not available.")
        else:
            st.info("Analyst recommendation data not available.")

    with a2:
        if cd.analyst_price_targets:
            pt = cd.analyst_price_targets
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#E0DCF5; margin-bottom:0.5rem;'>Price Targets</p>", unsafe_allow_html=True)
            pt1, pt2 = st.columns(2)
            pt1.metric("Mean", f"{cs}{pt.get('mean', 0):,.2f}" if pt.get("mean") else "N/A")
            pt2.metric("Median", f"{cs}{pt.get('median', 0):,.2f}" if pt.get("median") else "N/A")
            pt3, pt4 = st.columns(2)
            pt3.metric("Low", f"{cs}{pt.get('low', 0):,.2f}" if pt.get("low") else "N/A")
            pt4.metric("High", f"{cs}{pt.get('high', 0):,.2f}" if pt.get("high") else "N/A")
            if pt.get("mean") and cd.current_price:
                upside = (pt["mean"] - cd.current_price) / cd.current_price * 100
                color = "#10B981" if upside >= 0 else "#EF4444"
                st.markdown(
                    f'<div style="text-align:center; margin-top:0.5rem; padding:0.5rem; '
                    f'background:{"rgba(16,185,129,0.08)" if upside >= 0 else "rgba(239,68,68,0.08)"}; '
                    f'border-radius:10px;">'
                    f'<span style="font-size:0.75rem; color:#8A85AD; font-weight:600;">IMPLIED UPSIDE</span><br>'
                    f'<span style="font-size:1.3rem; font-weight:800; color:{color};">{upside:+.1f}%</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Price target data not available.")

    # ══════════════════════════════════════════════════════
    # 10. EARNINGS HISTORY
    # ══════════════════════════════════════════════════════
    _section("Earnings History")
    if cd.earnings_dates is not None and not cd.earnings_dates.empty:
        st.dataframe(cd.earnings_dates.head(8), use_container_width=True)
    else:
        st.info("Earnings data not available.")

    _divider()

    # ══════════════════════════════════════════════════════
    # 11. M&A HISTORY
    # ══════════════════════════════════════════════════════
    _section("M&A History")
    if cd.ma_deals:
        deal_count = len(cd.ma_deals)
        source_link = f' &middot; <a href="{cd.ma_source}" target="_blank" style="color:#6B5CE7; text-decoration:none; font-weight:500;">View on Wikipedia &rarr;</a>' if cd.ma_source else ""
        st.markdown(
            f'<div style="margin-bottom:0.8rem;">'
            f'<span class="pill pill-purple">{deal_count} Acquisitions</span>'
            f'{source_link}'
            f'</div>',
            unsafe_allow_html=True,
        )
        ma_df = pd.DataFrame([
            {
                "Date": d.get("date", ""),
                "Target": d.get("company", ""),
                "Business": d.get("business", ""),
                "Country": d.get("country", ""),
                "Value (USD)": d.get("value", "Undisclosed"),
            }
            for d in cd.ma_deals[:30]
        ])
        st.dataframe(ma_df, use_container_width=True, hide_index=True, height=400)
        if deal_count > 30:
            st.caption(f"Showing 30 of {deal_count} deals.")
    elif cd.ma_history:
        st.markdown(cd.ma_history)
    else:
        st.info("No public M&A history found for this company.")

    # ══════════════════════════════════════════════════════
    # 12. MANAGEMENT
    # ══════════════════════════════════════════════════════
    _section("Management Team")
    mgmt_col1, mgmt_col2 = st.columns([3, 2])
    with mgmt_col1:
        if cd.officers:
            mgmt_data = []
            for o in cd.officers[:10]:
                mgmt_data.append({
                    "Name": o.get("name", "N/A"),
                    "Title": o.get("title", "N/A"),
                    "Age": o.get("age", ""),
                    "Total Pay": format_number(o.get("totalPay"), currency_symbol=cs) if o.get("totalPay") else "\u2014",
                })
            st.dataframe(pd.DataFrame(mgmt_data), use_container_width=True, hide_index=True)
        else:
            st.info("Management data not available.")
    with mgmt_col2:
        if cd.mgmt_sentiment:
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#E0DCF5; margin-bottom:0.3rem;'>Management Assessment</p>", unsafe_allow_html=True)
            for line in cd.mgmt_sentiment.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"<div style='font-size:0.82rem; color:#B8B3D7; line-height:1.7; padding:0.15rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 13. NEWS
    # ══════════════════════════════════════════════════════
    _section("Recent News")
    if cd.news:
        for n in cd.news[:10]:
            title = n.get("title", "")
            publisher = n.get("publisher", "")
            link = n.get("link", "")
            if link:
                st.markdown(
                    f'<div class="news-item">'
                    f'<a href="{link}" target="_blank" class="news-title">{title}</a>'
                    f'<span class="news-pub"> &mdash; {publisher}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="news-item">'
                    f'<span class="news-title">{title}</span>'
                    f'<span class="news-pub"> &mdash; {publisher}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.info("No recent news available.")

    # ══════════════════════════════════════════════════════
    # 14a. EARNINGS SURPRISE CHART (Alpha Vantage)
    # ══════════════════════════════════════════════════════
    if getattr(cd, "earnings_history", None) and len(cd.earnings_history) > 0:
        _section("Earnings Surprise")
        earnings = cd.earnings_history[:8]  # last 8 quarters, most recent first
        earnings = list(reversed(earnings))  # oldest first for chart
        eq_dates = [e.get("date", "")[:7] for e in earnings]
        eq_actual = [e.get("actual_eps") for e in earnings]
        eq_estimate = [e.get("estimated_eps") for e in earnings]

        # Build colors: green for beat, red for miss
        bar_colors = []
        for a, est in zip(eq_actual, eq_estimate):
            if a is not None and est is not None:
                bar_colors.append("#10B981" if a >= est else "#EF4444")
            else:
                bar_colors.append("#8A85AD")

        fig_earn = go.Figure()
        # Ghost bar for estimates (transparent fill + outline)
        fig_earn.add_trace(go.Bar(
            x=eq_dates, y=eq_estimate, name="Estimate",
            marker=dict(
                color="rgba(138,133,173,0.08)",
                line=dict(color="rgba(138,133,173,0.5)", width=1.5),
            ),
            text=[f"{v:.2f}" if v is not None else "" for v in eq_estimate],
            textposition="outside", textfont=dict(size=9, color="#8A85AD"),
        ))
        # Solid actuals with white outline
        fig_earn.add_trace(go.Bar(
            x=eq_dates, y=eq_actual, name="Actual",
            marker=dict(
                color=bar_colors,
                line=dict(color="rgba(255,255,255,0.2)", width=1),
            ),
            text=[f"{v:.2f}" if v is not None else "" for v in eq_actual],
            textposition="outside", textfont=dict(size=9, color="#B8B3D7"),
        ))
        fig_earn.update_layout(
            **_CHART_LAYOUT_BASE,
            height=380, barmode="group",
            margin=dict(t=30, b=30, l=50, r=30),
            xaxis=dict(tickfont=dict(size=10, color="#8A85AD"), showgrid=False),
            yaxis=dict(title=dict(text="EPS", font=dict(size=10, color="#8A85AD")),
                       tickfont=dict(size=9, color="#8A85AD"),
                       tickprefix=cd.currency_symbol),
            legend=dict(font=dict(size=10, color="#B8B3D7"), orientation="h",
                        yanchor="bottom", y=1.02),
        )
        _apply_space_grid(fig_earn)
        st.markdown('<div class="profile-chart-wrapper">', unsafe_allow_html=True)
        st.plotly_chart(fig_earn, use_container_width=True, key="earnings_surprise_chart")
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 14b. NEWS SENTIMENT (Alpha Vantage)
    # ══════════════════════════════════════════════════════
    if getattr(cd, "news_sentiment", None) and len(cd.news_sentiment) > 0:
        _section("News Sentiment")
        for ns in cd.news_sentiment[:10]:
            title = ns.get("title", "")
            url = ns.get("url", "")
            source = ns.get("source", "")
            published = ns.get("published", "")
            sentiment = ns.get("overall_sentiment", "Neutral").lower()
            score = ns.get("overall_score")
            score_str = f"{score:.2f}" if score is not None else ""

            if "bullish" in sentiment or "positive" in sentiment:
                css_class = "news-sentiment-bullish"
                badge = '<span style="color:#10B981; font-weight:700; font-size:0.7rem;">BULLISH</span>'
            elif "bearish" in sentiment or "negative" in sentiment:
                css_class = "news-sentiment-bearish"
                badge = '<span style="color:#EF4444; font-weight:700; font-size:0.7rem;">BEARISH</span>'
            else:
                css_class = "news-sentiment-neutral"
                badge = '<span style="color:#8A85AD; font-weight:700; font-size:0.7rem;">NEUTRAL</span>'

            link_html = f'<a href="{url}" target="_blank" style="color:#E0DCF5; text-decoration:none; font-weight:600; font-size:0.85rem;">{title}</a>' if url else f'<span style="color:#E0DCF5; font-weight:600; font-size:0.85rem;">{title}</span>'
            st.markdown(
                f'<div class="news-card {css_class}">'
                f'{link_html}'
                f'<div style="margin-top:0.3rem; display:flex; gap:0.8rem; align-items:center;">'
                f'{badge}'
                f'<span style="color:#8A85AD; font-size:0.7rem;">{source} &middot; {published}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    # ══════════════════════════════════════════════════════
    # 14c. INSIDER ACTIVITY (Alpha Vantage)
    # ══════════════════════════════════════════════════════
    av_insiders = getattr(cd, "av_insider_transactions", None)
    if av_insiders and len(av_insiders) > 0:
        _section("Insider Activity")
        rows_html = ""
        for t in av_insiders[:20]:
            date = t.get("date", "")
            insider = t.get("insider", "")
            title = t.get("title", "")
            txn_type = t.get("type", "")
            shares = t.get("shares")
            value = t.get("value")

            if txn_type == "A":
                type_label = '<span style="color:#10B981; font-weight:700;">Buy</span>'
                row_bg = "rgba(16,185,129,0.04)"
            elif txn_type == "D":
                type_label = '<span style="color:#EF4444; font-weight:700;">Sell</span>'
                row_bg = "rgba(239,68,68,0.04)"
            else:
                type_label = txn_type
                row_bg = "transparent"

            shares_str = f"{shares:,.0f}" if shares else "—"
            value_str = f"{cd.currency_symbol}{value:,.0f}" if value else "—"
            rows_html += (
                f'<tr style="background:{row_bg};">'
                f'<td>{date}</td><td>{insider}</td><td style="font-size:0.72rem;">{title}</td>'
                f'<td>{type_label}</td><td style="text-align:right;">{shares_str}</td>'
                f'<td style="text-align:right;">{value_str}</td></tr>'
            )
        st.markdown(
            f'<table class="insider-table">'
            f'<thead><tr><th>Date</th><th>Insider</th><th>Title</th>'
            f'<th>Type</th><th style="text-align:right;">Shares</th>'
            f'<th style="text-align:right;">Value</th></tr></thead>'
            f'<tbody>{rows_html}</tbody></table>'.replace("$", "&#36;"),
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════
    # 15. INSIGHTS — 7 Rich Tabs
    # ══════════════════════════════════════════════════════
    _section("Insights")
    ai_tab1, ai_tab2, ai_tab3, ai_tab4, ai_tab5, ai_tab6, ai_tab7 = st.tabs([
        "Executive Summary", "Financial Trends", "SWOT Analysis",
        "Growth Outlook", "Capital Allocation", "Industry Analysis", "Risk Factors"
    ])

    # ── Tab 1: Executive Summary ──────────────────────
    with ai_tab1:
        es_left, es_right = st.columns([3, 2])
        with es_left:
            if cd.executive_summary_bullets:
                for b in cd.executive_summary_bullets:
                    st.markdown(f"<div style='font-size:0.88rem; color:#B8B3D7; line-height:1.7; padding:0.2rem 0;'>&bull; {b}</div>", unsafe_allow_html=True)
            else:
                st.info("Executive summary not available.")
            if cd.product_overview:
                st.markdown('<div style="margin-top:1rem;"><div style="font-size:0.8rem; font-weight:700; color:#9B8AFF; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.3rem;">Product Overview</div></div>', unsafe_allow_html=True)
                for line in cd.product_overview.split("\n"):
                    line = line.strip()
                    if line.startswith("- "):
                        line = line[2:]
                    if line:
                        st.markdown(f"<div style='font-size:0.84rem; color:#B8B3D7; line-height:1.7; padding:0.15rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)
        with es_right:
            st.markdown('<div class="profile-chart-wrapper">', unsafe_allow_html=True)
            _build_peer_valuation_chart(cd)
            _build_earnings_surprise_chart(cd)
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Tab 2: Financial Trends ───────────────────────
    with ai_tab2:
        ft_c1, ft_c2 = st.columns(2)
        with ft_c1:
            st.markdown('<div style="font-size:0.8rem; font-weight:700; color:#9B8AFF; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.3rem;">Revenue & Margins</div>', unsafe_allow_html=True)
            st.markdown('<div class="profile-chart-wrapper">', unsafe_allow_html=True)
            _build_revenue_margin_chart(cd)
            st.markdown('</div>', unsafe_allow_html=True)
        with ft_c2:
            st.markdown('<div style="font-size:0.8rem; font-weight:700; color:#9B8AFF; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.3rem;">Cash Flow</div>', unsafe_allow_html=True)
            st.markdown('<div class="profile-chart-wrapper">', unsafe_allow_html=True)
            _build_cashflow_chart(cd)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.8rem; font-weight:700; color:#9B8AFF; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.3rem; margin-top:0.5rem;">Balance Sheet</div>', unsafe_allow_html=True)
        st.markdown('<div class="profile-chart-wrapper">', unsafe_allow_html=True)
        _build_balance_sheet_chart(cd)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Tab 3: SWOT Analysis ─────────────────────────
    with ai_tab3:
        _render_swot_grid(cd.swot_analysis)

    # ── Tab 4: Growth Outlook ────────────────────────
    with ai_tab4:
        go_left, go_right = st.columns([3, 2])
        with go_left:
            _render_growth_outlook(cd.growth_outlook, cd)
        with go_right:
            st.markdown('<div style="font-size:0.8rem; font-weight:700; color:#9B8AFF; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.3rem;">Revenue & Margin Trends</div>', unsafe_allow_html=True)
            st.markdown('<div class="profile-chart-wrapper">', unsafe_allow_html=True)
            _build_revenue_margin_chart(cd, key="rev_margin_growth")
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Tab 5: Capital Allocation ────────────────────
    with ai_tab5:
        ca_left, ca_right = st.columns([3, 2])
        with ca_left:
            _render_capital_allocation(cd.capital_allocation_analysis, cd)
        with ca_right:
            st.markdown('<div style="font-size:0.8rem; font-weight:700; color:#9B8AFF; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.3rem;">Cash Flow Trends</div>', unsafe_allow_html=True)
            st.markdown('<div class="profile-chart-wrapper">', unsafe_allow_html=True)
            _build_cashflow_chart(cd, key="cashflow_capalloc")
            st.markdown('</div>', unsafe_allow_html=True)

    # ── Tab 6: Industry Analysis ─────────────────────
    with ai_tab6:
        if cd.industry_analysis:
            for line in cd.industry_analysis.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"<div style='font-size:0.88rem; color:#B8B3D7; line-height:1.7; padding:0.2rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)
        else:
            st.info("Industry analysis not available.")

    # ── Tab 7: Risk Factors (color-coded severity) ───
    with ai_tab7:
        if cd.risk_factors:
            for line in cd.risk_factors.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if not line:
                    continue
                # Detect severity tag
                severity_color = "#8A85AD"
                severity_bg = "rgba(138,133,173,0.05)"
                severity_border = "rgba(138,133,173,0.2)"
                if line.startswith("[HIGH]"):
                    line = line[6:].strip()
                    severity_color = "#EF4444"
                    severity_bg = "rgba(239,68,68,0.06)"
                    severity_border = "rgba(239,68,68,0.3)"
                elif line.startswith("[MEDIUM]"):
                    line = line[8:].strip()
                    severity_color = "#F5A623"
                    severity_bg = "rgba(245,166,35,0.06)"
                    severity_border = "rgba(245,166,35,0.3)"
                elif line.startswith("[LOW]"):
                    line = line[5:].strip()
                    severity_color = "#10B981"
                    severity_bg = "rgba(16,185,129,0.06)"
                    severity_border = "rgba(16,185,129,0.3)"
                st.markdown(
                    f'<div style="border-left:3px solid {severity_border}; background:{severity_bg}; '
                    f'padding:0.5rem 0.8rem; margin-bottom:0.4rem; border-radius:0 8px 8px 0;">'
                    f'<div style="font-size:0.86rem; color:#B8B3D7; line-height:1.7;">{line}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Risk factors not available.")

    _divider()

    # ══════════════════════════════════════════════════════
    # 15. DOWNLOAD PPTX
    # ══════════════════════════════════════════════════════
    st.markdown("")
    st.markdown("")
    _section("Download Tear Sheet")

    if not os.path.exists("assets/template.pptx"):
        with st.spinner("Creating template..."):
            from create_template import build
            build()

    with st.spinner("Building 8-slide PowerPoint presentation..."):
        pptx_buf = generate_presentation(cd)

    dl1, dl2, dl3 = st.columns([1, 2, 1])
    with dl2:
        st.download_button(
            label=f"Download {cd.ticker} M&A Profile  (8 slides)",
            data=pptx_buf,
            file_name=f"{cd.ticker}_MA_Profile.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )
        st.markdown(
            "<p style='text-align:center; font-size:0.72rem; color:#8A85AD; margin-top:0.3rem;'>"
            "Professional IB-grade presentation &middot; Editable charts &middot; Navy/Gold palette"
            "</p>",
            unsafe_allow_html=True,
        )

elif analysis_mode == "Company Profile" and generate_btn and not ticker_input:
    st.warning("Please enter a ticker symbol in the sidebar.")

elif analysis_mode == "Merger Analysis" and merger_btn and acquirer_input and target_input:
    # ══════════════════════════════════════════════════════
    # MERGER ANALYSIS DASHBOARD
    # ══════════════════════════════════════════════════════

    # ── Mission Control animated loading ─────────────────
    mission = st.empty()
    acq_label = acquirer_input.upper()
    tgt_label = target_input.upper()

    # Phase 0 → fetch acquirer
    mission.markdown(_render_mission_control(acq_label, tgt_label, 0), unsafe_allow_html=True)
    try:
        acq_cd = fetch_company_data(acquirer_input)
    except Exception as e:
        mission.empty()
        st.error(f"Failed to fetch data for **{acquirer_input}**: {e}")
        st.stop()

    # Phase 1 → fetch target (with rate limit delay)
    mission.markdown(_render_mission_control(acq_label, tgt_label, 1), unsafe_allow_html=True)
    time.sleep(1)
    try:
        tgt_cd = fetch_company_data(target_input)
    except Exception as e:
        mission.empty()
        st.error(f"Failed to fetch data for **{target_input}**: {e}")
        st.stop()

    # Phase 2 → fetch peers
    mission.markdown(_render_mission_control(acq_label, tgt_label, 2), unsafe_allow_html=True)
    try:
        tgt_cd = fetch_peer_data(tgt_cd)
    except Exception:
        pass

    # Phase 3 → compute pro forma + precedent transactions
    mission.markdown(_render_mission_control(acq_label, tgt_label, 3), unsafe_allow_html=True)
    try:
        pro_forma = calculate_pro_forma(acq_cd, tgt_cd, merger_assumptions)
    except Exception as e:
        mission.empty()
        st.error(f"Failed to calculate pro forma: {e}")
        import traceback
        st.code(traceback.format_exc())
        st.stop()

    # Fetch precedent transactions
    precedent = None
    try:
        from precedent_deals import fetch_precedent_transactions
        precedent = fetch_precedent_transactions(
            target_input, getattr(tgt_cd, "cik", ""), tgt_cd.sector
        )
    except Exception as e:
        print(f"Precedent transactions fetch failed: {e}")

    try:
        pro_forma.football_field = build_football_field(acq_cd, tgt_cd, pro_forma, precedent)
    except Exception as e:
        st.warning(f"Football field build failed: {e}")
        pro_forma.football_field = {}

    # Phase 4 → generate insights
    mission.markdown(_render_mission_control(acq_label, tgt_label, 4), unsafe_allow_html=True)
    try:
        merger_insights = generate_merger_insights(acq_cd, tgt_cd, pro_forma, merger_assumptions)
    except Exception as e:
        st.warning(f"Merger insights generation failed: {e}")
        from ai_insights import MergerInsights
        merger_insights = MergerInsights()

    # Phase 5 → mission complete, rocket launches
    mission.markdown(_render_mission_control(acq_label, tgt_label, 5), unsafe_allow_html=True)
    time.sleep(1.5)
    mission.empty()

    acq_cs = acq_cd.currency_symbol
    tgt_cs = tgt_cd.currency_symbol

    # ── Warnings ──────────────────────────────────────────
    for warn in pro_forma.warnings:
        st.warning(warn)

    # Helper: escape $ to prevent Streamlit LaTeX rendering in markdown
    def _mhtml(html_str):
        """Render HTML via st.markdown with $ escaped to prevent LaTeX."""
        st.markdown(html_str.replace("$", "&#36;"), unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # M1. DEAL HEADER
    # ══════════════════════════════════════════════════════
    acq_logo = ""
    if acq_cd.logo_url:
        _ald = getattr(acq_cd, 'logo_domain', '')
        acq_fallback = f"this.onerror=null; this.src='https://logo.clearbit.com/{_ald}';" if _ald else "this.style.display='none';"
        acq_logo = (
            f'<img src="{acq_cd.logo_url}" '
            f'style="width:48px; height:48px; border-radius:10px; object-fit:contain; '
            f'background:white; padding:4px;" onerror="{acq_fallback}">'
        )
    tgt_logo = ""
    if tgt_cd.logo_url:
        _tld = getattr(tgt_cd, 'logo_domain', '')
        tgt_fallback = f"this.onerror=null; this.src='https://logo.clearbit.com/{_tld}';" if _tld else "this.style.display='none';"
        tgt_logo = (
            f'<img src="{tgt_cd.logo_url}" '
            f'style="width:48px; height:48px; border-radius:10px; object-fit:contain; '
            f'background:white; padding:4px;" onerror="{tgt_fallback}">'
        )

    st.markdown(
        f'<div class="company-card">'
        f'<div style="display:flex; align-items:center; gap:1.2rem; position:relative;">'
        f'{acq_logo}'
        f'<div>'
        f'<p class="company-name" style="font-size:1.5rem;">{acq_cd.name}</p>'
        f'<p class="company-meta"><span>{acq_cd.ticker}</span> &middot; {acq_cd.sector}</p>'
        f'</div>'
        f'<div style="font-size:2rem; font-weight:300; color:#6B5CE7; margin:0 1rem;">+</div>'
        f'{tgt_logo}'
        f'<div>'
        f'<p class="company-name" style="font-size:1.5rem;">{tgt_cd.name}</p>'
        f'<p class="company-meta"><span>{tgt_cd.ticker}</span> &middot; {tgt_cd.sector}</p>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════
    # M2. COMPANY COMPARISON
    # ══════════════════════════════════════════════════════
    _section("Company Comparison")

    cc1, cc2, cc3, cc4, cc5, cc6 = st.columns(6)
    cc1.metric(f"{acq_cd.ticker} Mkt Cap", format_number(acq_cd.market_cap, currency_symbol=acq_cs))
    cc2.metric(f"{tgt_cd.ticker} Mkt Cap", format_number(tgt_cd.market_cap, currency_symbol=tgt_cs))
    cc3.metric(f"{acq_cd.ticker} Revenue", format_number(pro_forma.acq_revenue, currency_symbol=acq_cs))
    cc4.metric(f"{tgt_cd.ticker} Revenue", format_number(pro_forma.tgt_revenue, currency_symbol=tgt_cs))
    cc5.metric(f"{acq_cd.ticker} EBITDA", format_number(pro_forma.acq_ebitda, currency_symbol=acq_cs))
    cc6.metric(f"{tgt_cd.ticker} EBITDA", format_number(pro_forma.tgt_ebitda, currency_symbol=tgt_cs))

    # Company comparison bars
    _mhtml('<div class="merger-chart-wrapper">')
    _build_company_comparison_bars(acq_cd, tgt_cd)
    _mhtml('</div>')

    _divider()

    # ══════════════════════════════════════════════════════
    # M3. DEAL TERMS
    # ══════════════════════════════════════════════════════
    _section("Deal Terms")

    dt1, dt2, dt3, dt4, dt5 = st.columns(5)
    dt1.metric("Purchase Price", format_number(pro_forma.purchase_price, currency_symbol=acq_cs))
    dt2.metric("Offer Premium", f"{merger_assumptions.offer_premium_pct:.0f}%")
    dt3.metric("Implied EV/EBITDA", f"{pro_forma.implied_ev_ebitda:.1f}x" if pro_forma.implied_ev_ebitda else "N/A")
    dt4.metric("Implied P/E", f"{pro_forma.implied_pe:.1f}x" if pro_forma.implied_pe else "N/A")
    dt5.metric("Transaction Fees", format_number(pro_forma.transaction_fees, currency_symbol=acq_cs))

    # Deal structure donut
    deal_col1, deal_col2 = st.columns([2, 3])
    with deal_col1:
        _build_deal_structure_donut(merger_assumptions)
    with deal_col2:
        _mhtml(
            f'<div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.1); '
            f'border-radius:14px; padding:1.2rem;">'
            f'<div style="font-size:0.75rem; font-weight:600; color:#8A85AD; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">Consideration Detail</div>'
            f'<div style="font-size:0.9rem; color:#B8B3D7; line-height:2;">'
            f'Cash: {format_number(pro_forma.cash_consideration, currency_symbol=acq_cs)} (debt-funded)<br>'
            f'Stock: {format_number(pro_forma.stock_consideration, currency_symbol=acq_cs)} '
            f'({pro_forma.new_shares_issued / 1e6:,.1f}M new shares @ {acq_cs}{acq_cd.current_price:,.2f})<br>'
            f'Offer Price: {acq_cs}{pro_forma.offer_price_per_share:,.2f}/share '
            f'(vs current {tgt_cs}{tgt_cd.current_price:,.2f})'
            f'</div></div>'
        )

    _divider()

    # ══════════════════════════════════════════════════════
    # M4. PRO FORMA FINANCIALS
    # ══════════════════════════════════════════════════════
    _section("Pro Forma Financials")

    tax_r = merger_assumptions.tax_rate / 100
    ats = pro_forma.total_synergies * (1 - tax_r)
    ati = pro_forma.incremental_interest * (1 - tax_r)

    pf_data = {
        "": ["Revenue", "EBITDA", "Net Income", "Shares (M)", "EPS"],
        acq_cd.ticker: [
            format_number(pro_forma.acq_revenue, currency_symbol=acq_cs),
            format_number(pro_forma.acq_ebitda, currency_symbol=acq_cs),
            format_number(pro_forma.acq_net_income, currency_symbol=acq_cs),
            f"{pro_forma.acq_shares / 1e6:,.0f}" if pro_forma.acq_shares else "N/A",
            f"{acq_cs}{pro_forma.acq_eps:.2f}" if pro_forma.acq_eps else "N/A",
        ],
        tgt_cd.ticker: [
            format_number(pro_forma.tgt_revenue, currency_symbol=tgt_cs),
            format_number(pro_forma.tgt_ebitda, currency_symbol=tgt_cs),
            format_number(pro_forma.tgt_net_income, currency_symbol=tgt_cs),
            "—",
            "—",
        ],
        "Adjustments": [
            format_number(pro_forma.revenue_synergies, currency_symbol=acq_cs),
            format_number(pro_forma.total_synergies, currency_symbol=acq_cs),
            format_number(ats - ati, currency_symbol=acq_cs),
            f"+{pro_forma.new_shares_issued / 1e6:,.0f}" if pro_forma.new_shares_issued else "—",
            "—",
        ],
        "Pro Forma": [
            format_number(pro_forma.pf_revenue, currency_symbol=acq_cs),
            format_number(pro_forma.pf_ebitda, currency_symbol=acq_cs),
            format_number(pro_forma.pf_net_income, currency_symbol=acq_cs),
            f"{pro_forma.pf_shares_outstanding / 1e6:,.0f}" if pro_forma.pf_shares_outstanding else "N/A",
            f"{acq_cs}{pro_forma.pf_eps:.2f}" if pro_forma.pf_eps else "N/A",
        ],
    }
    pf_df = pd.DataFrame(pf_data)
    st.dataframe(pf_df, use_container_width=True, hide_index=True, height=230)

    _divider()

    # ══════════════════════════════════════════════════════
    # M5. ACCRETION / DILUTION
    # ══════════════════════════════════════════════════════
    _section("Accretion / Dilution Analysis")

    acc_color = "#10B981" if pro_forma.is_accretive else "#EF4444"
    acc_word = "ACCRETIVE" if pro_forma.is_accretive else "DILUTIVE"
    acc_bg = "rgba(16,185,129,0.08)" if pro_forma.is_accretive else "rgba(239,68,68,0.08)"

    _mhtml(
        f'<div style="text-align:center; padding:1rem; background:{acc_bg}; border-radius:14px; margin-bottom:1rem;">'
        f'<div style="font-size:0.7rem; font-weight:600; color:#8A85AD; text-transform:uppercase; letter-spacing:1px;">EPS Impact</div>'
        f'<div style="font-size:2.5rem; font-weight:800; color:{acc_color};">{pro_forma.accretion_dilution_pct:+.1f}%</div>'
        f'<div style="font-size:1rem; font-weight:700; color:{acc_color};">{acc_word}</div>'
        f'<div style="font-size:0.8rem; color:#B8B3D7; margin-top:0.3rem;">'
        f'Standalone: {acq_cs}{pro_forma.acq_eps:.2f} &rarr; Pro Forma: {acq_cs}{pro_forma.pf_eps:.2f}</div>'
        f'</div>'
    )

    _mhtml('<div class="merger-chart-wrapper">')
    _build_accretion_waterfall(pro_forma)
    _mhtml('</div>')

    _divider()

    # ══════════════════════════════════════════════════════
    # M6. FOOTBALL FIELD VALUATION
    # ══════════════════════════════════════════════════════
    if pro_forma.football_field and len([k for k in pro_forma.football_field if not k.startswith("_")]) > 0:
        _section("Football Field Valuation")
        _mhtml('<div class="merger-chart-wrapper">')
        _build_football_field_chart(pro_forma.football_field, acq_cs)
        _mhtml('</div>')
        _divider()

    # ══════════════════════════════════════════════════════
    # M6b. PRECEDENT TRANSACTIONS TABLE
    # ══════════════════════════════════════════════════════
    if precedent and precedent.deals:
        _section("Precedent Transactions")
        rows_html = ""
        for d in precedent.deals[:15]:
            name = d.get("name", d.get("target", ""))
            date = d.get("date", "")
            ev_eb = d.get("ev_ebitda")
            ev_rev = d.get("ev_revenue")
            dval = d.get("deal_value")
            ev_eb_str = f"{ev_eb:.1f}x" if ev_eb else "—"
            ev_rev_str = f"{ev_rev:.1f}x" if ev_rev else "—"
            dval_str = format_number(dval, currency_symbol=tgt_cs) if dval else "—"
            rows_html += (
                f"<tr><td>{date}</td><td>{name}</td>"
                f"<td>{dval_str}</td><td>{ev_eb_str}</td><td>{ev_rev_str}</td></tr>"
            )
        source_note = ""
        if precedent.source_url:
            source_note = f'<div style="font-size:0.7rem; color:#8A85AD; margin-top:0.5rem;">Source: {precedent.source} — <a href="{precedent.source_url}" style="color:#9B8AFF;" target="_blank">Filing</a></div>'
        elif precedent.source:
            source_note = f'<div style="font-size:0.7rem; color:#8A85AD; margin-top:0.5rem;">Source: {precedent.source}</div>'
        _mhtml(
            f'<table class="precedent-table">'
            f'<thead><tr><th>Date</th><th>Transaction</th>'
            f'<th>Deal Value</th><th>EV/EBITDA</th><th>EV/Revenue</th></tr></thead>'
            f'<tbody>{rows_html}</tbody></table>'
            f'{source_note}'
        )
        _divider()

    # ══════════════════════════════════════════════════════
    # M7. SOURCES & USES
    # ══════════════════════════════════════════════════════
    _section("Sources & Uses")

    su1, su2 = st.columns(2)
    with su1:
        st.markdown('<div style="font-size:0.85rem; font-weight:700; color:#E0DCF5; margin-bottom:0.5rem;">Sources</div>', unsafe_allow_html=True)
        for k, v in pro_forma.sources.items():
            weight = "700" if k.startswith("Total") else "400"
            _mhtml(
                f'<div style="display:flex; justify-content:space-between; padding:0.3rem 0; '
                f'border-bottom:1px solid rgba(255,255,255,0.05); font-size:0.85rem; color:#B8B3D7; font-weight:{weight};">'
                f'<span>{k}</span><span>{format_number(v, currency_symbol=acq_cs)}</span></div>'
            )
    with su2:
        st.markdown('<div style="font-size:0.85rem; font-weight:700; color:#E0DCF5; margin-bottom:0.5rem;">Uses</div>', unsafe_allow_html=True)
        for k, v in pro_forma.uses.items():
            weight = "700" if k.startswith("Total") else "400"
            _mhtml(
                f'<div style="display:flex; justify-content:space-between; padding:0.3rem 0; '
                f'border-bottom:1px solid rgba(255,255,255,0.05); font-size:0.85rem; color:#B8B3D7; font-weight:{weight};">'
                f'<span>{k}</span><span>{format_number(v, currency_symbol=acq_cs)}</span></div>'
            )

    _divider()

    # ══════════════════════════════════════════════════════
    # M8. PRO FORMA CREDIT
    # ══════════════════════════════════════════════════════
    _section("Pro Forma Credit Profile")

    cr1, cr2, cr3, cr4 = st.columns(4)

    def _lev_color(val):
        if val is None: return "#8A85AD"
        if val < 2: return "#10B981"
        if val < 4: return "#F5A623"
        return "#EF4444"

    def _cov_color(val):
        if val is None: return "#8A85AD"
        if val > 5: return "#10B981"
        if val > 2.5: return "#F5A623"
        return "#EF4444"

    lev_c = _lev_color(pro_forma.pf_leverage_ratio)
    cov_c = _cov_color(pro_forma.pf_interest_coverage)

    cr1.metric("PF Debt / EBITDA", f"{pro_forma.pf_leverage_ratio:.1f}x" if pro_forma.pf_leverage_ratio else "N/A")
    cr2.metric("PF Interest Coverage", f"{pro_forma.pf_interest_coverage:.1f}x" if pro_forma.pf_interest_coverage else "N/A")
    cr3.metric("PF Total Debt", format_number(pro_forma.pf_total_debt, currency_symbol=acq_cs))
    cr4.metric("PF Net Debt", format_number(pro_forma.pf_net_debt, currency_symbol=acq_cs))

    _mhtml(
        f'<div style="display:flex; gap:1rem; margin-top:0.5rem;">'
        f'<div style="flex:1; text-align:center; padding:0.6rem; background:rgba(255,255,255,0.04); border-radius:10px; border-left:3px solid {lev_c};">'
        f'<div style="font-size:0.65rem; font-weight:600; color:#8A85AD; text-transform:uppercase;">Leverage</div>'
        f'<div style="font-size:1.1rem; font-weight:700; color:{lev_c};">'
        f'{"Conservative" if (pro_forma.pf_leverage_ratio or 0) < 2 else "Moderate" if (pro_forma.pf_leverage_ratio or 0) < 4 else "Aggressive"}</div></div>'
        f'<div style="flex:1; text-align:center; padding:0.6rem; background:rgba(255,255,255,0.04); border-radius:10px; border-left:3px solid {cov_c};">'
        f'<div style="font-size:0.65rem; font-weight:600; color:#8A85AD; text-transform:uppercase;">Coverage</div>'
        f'<div style="font-size:1.1rem; font-weight:700; color:{cov_c};">'
        f'{"Strong" if (pro_forma.pf_interest_coverage or 0) > 5 else "Adequate" if (pro_forma.pf_interest_coverage or 0) > 2.5 else "Tight"}</div></div>'
        f'<div style="flex:1; text-align:center; padding:0.6rem; background:rgba(255,255,255,0.04); border-radius:10px;">'
        f'<div style="font-size:0.65rem; font-weight:600; color:#8A85AD; text-transform:uppercase;">Goodwill</div>'
        f'<div style="font-size:1.1rem; font-weight:700; color:#E0DCF5;">{format_number(pro_forma.goodwill, currency_symbol=acq_cs)}</div></div>'
        f'</div>'
    )

    _divider()

    # ══════════════════════════════════════════════════════
    # M9. AI STRATEGIC RATIONALE
    # ══════════════════════════════════════════════════════
    _section("Strategic Rationale")

    _sr_tag_config = [
        ("[DEAL LOGIC]", "Deal Logic", "#6B5CE7", "rgba(107,92,231,0.06)", "rgba(107,92,231,0.3)"),
        ("[FINANCIAL MERIT]", "Financial Merit", "#E8638B", "rgba(232,99,139,0.06)", "rgba(232,99,139,0.3)"),
        ("[STRATEGIC FIT]", "Strategic Fit", "#10B981", "rgba(16,185,129,0.06)", "rgba(16,185,129,0.3)"),
        ("[COMPETITIVE POSITIONING]", "Competitive Positioning", "#F5A623", "rgba(245,166,35,0.06)", "rgba(245,166,35,0.3)"),
    ]

    for line in merger_insights.strategic_rationale.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            line = line[2:]
        if not line:
            continue
        matched_tag = False
        for tag, label, color, bg, border in _sr_tag_config:
            if line.startswith(tag):
                line = line[len(tag):].strip().replace("$", "&#36;")
                st.markdown(
                    f'<div style="border-left:3px solid {border}; background:{bg}; '
                    f'padding:0.5rem 0.8rem; margin-bottom:0.5rem; border-radius:0 8px 8px 0;">'
                    f'<div style="font-size:0.7rem; font-weight:700; color:{color}; text-transform:uppercase; '
                    f'letter-spacing:0.5px; margin-bottom:0.2rem;">{label}</div>'
                    f'<div style="font-size:0.86rem; color:#B8B3D7; line-height:1.7;">{line}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                matched_tag = True
                break
        if not matched_tag and line:
            line = line.replace("$", "&#36;")
            st.markdown(f"<div style='font-size:0.88rem; color:#B8B3D7; line-height:1.7; padding:0.2rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)

    _divider()

    # ══════════════════════════════════════════════════════
    # M10. AI DEAL RISKS
    # ══════════════════════════════════════════════════════
    _section("Deal Risk Assessment")

    _risk_tag_config = [
        ("[VALUATION]", "Valuation", "#EF4444", "rgba(239,68,68,0.06)", "rgba(239,68,68,0.3)"),
        ("[FINANCIAL]", "Financial", "#E8638B", "rgba(232,99,139,0.06)", "rgba(232,99,139,0.3)"),
        ("[INTEGRATION]", "Integration", "#F5A623", "rgba(245,166,35,0.06)", "rgba(245,166,35,0.3)"),
        ("[EXECUTION]", "Execution", "#6B5CE7", "rgba(107,92,231,0.06)", "rgba(107,92,231,0.3)"),
        ("[MARKET]", "Market", "#10B981", "rgba(16,185,129,0.06)", "rgba(16,185,129,0.3)"),
        # Legacy tag support
        ("[ANTITRUST]", "Antitrust", "#EF4444", "rgba(239,68,68,0.06)", "rgba(239,68,68,0.3)"),
    ]

    # Severity keyword tinting — override base colors for high-severity language
    _high_severity_words = {"distressed", "unsustainable", "aggressive", "concerning", "substantial", "significant", "elevated", "transformative"}
    _low_severity_words = {"manageable", "adequate", "comfortable", "low", "conservative", "modest", "contained"}

    for line in merger_insights.deal_risks.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            line = line[2:]
        if not line:
            continue

        tag_label = ""
        tag_color = "#8A85AD"
        tag_bg = "rgba(138,133,173,0.05)"
        tag_border = "rgba(138,133,173,0.2)"

        for tag, label, color, bg, border in _risk_tag_config:
            if line.startswith(tag):
                line = line[len(tag):].strip()
                tag_label = label
                tag_color = color
                tag_bg = bg
                tag_border = border
                break

        # Severity-based tint adjustment (before escaping)
        line_lower = line.lower()
        has_high = any(w in line_lower for w in _high_severity_words)
        has_low = any(w in line_lower for w in _low_severity_words)

        if has_high and not has_low:
            severity_indicator = '<span style="color:#EF4444; font-size:0.7rem; margin-left:0.4rem;">&#9650; ELEVATED</span>'
        elif has_low and not has_high:
            severity_indicator = '<span style="color:#10B981; font-size:0.7rem; margin-left:0.4rem;">&#9660; LOW</span>'
        else:
            severity_indicator = ""

        header_html = ""
        if tag_label:
            header_html = (
                f'<div style="font-size:0.7rem; font-weight:700; color:{tag_color}; text-transform:uppercase; '
                f'letter-spacing:0.5px; margin-bottom:0.2rem;">{tag_label}{severity_indicator}</div>'
            )

        line = line.replace("$", "&#36;")
        st.markdown(
            f'<div style="border-left:3px solid {tag_border}; background:{tag_bg}; '
            f'padding:0.5rem 0.8rem; margin-bottom:0.5rem; border-radius:0 8px 8px 0;">'
            f'{header_html}'
            f'<div style="font-size:0.86rem; color:#B8B3D7; line-height:1.7;">{line}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    _divider()

    # ══════════════════════════════════════════════════════
    # M11. AI DEAL VERDICT
    # ══════════════════════════════════════════════════════
    _section("Deal Verdict")

    grade_colors = {"A": "#10B981", "B": "#6B5CE7", "C": "#F5A623", "D": "#EF4444", "F": "#EF4444"}
    grade_c = grade_colors.get(merger_insights.deal_grade, "#8A85AD")
    grade_bg = {"A": "rgba(16,185,129,0.12)", "B": "rgba(107,92,231,0.12)",
                "C": "rgba(245,166,35,0.12)", "D": "rgba(239,68,68,0.12)", "F": "rgba(239,68,68,0.12)"}

    st.markdown(
        f'<div style="display:inline-block; background:{grade_bg.get(merger_insights.deal_grade, "rgba(138,133,173,0.12)")}; '
        f'color:{grade_c}; padding:0.5rem 1.5rem; border-radius:20px; font-weight:800; '
        f'font-size:1.2rem; letter-spacing:1px; margin-bottom:1rem;">Deal Grade: {merger_insights.deal_grade}</div>',
        unsafe_allow_html=True,
    )

    _verdict_tag_config = {
        "[OVERALL]": ("Overall Assessment", None, "rgba(255,255,255,0.04)", "rgba(138,133,173,0.3)"),
        "[BULL CASE]": ("Bull Case", "#10B981", "rgba(16,185,129,0.06)", "rgba(16,185,129,0.35)"),
        "[BEAR CASE]": ("Bear Case", "#EF4444", "rgba(239,68,68,0.06)", "rgba(239,68,68,0.35)"),
        "[KEY CONDITION]": ("Key Condition", "#F5A623", "rgba(245,166,35,0.08)", "rgba(245,166,35,0.35)"),
    }

    for line in merger_insights.deal_verdict.split("\n"):
        line = line.strip()
        if line.startswith("- "):
            line = line[2:]
        if not line:
            continue

        matched_tag = False
        for tag, (label, color, bg, border) in _verdict_tag_config.items():
            if line.startswith(tag):
                line = line[len(tag):].strip().replace("$", "&#36;")
                header_color = color or "#B8B3D7"
                st.markdown(
                    f'<div style="border-left:3px solid {border}; background:{bg}; '
                    f'padding:0.6rem 0.8rem; margin-bottom:0.5rem; border-radius:0 8px 8px 0;">'
                    f'<div style="font-size:0.7rem; font-weight:700; color:{header_color}; text-transform:uppercase; '
                    f'letter-spacing:0.5px; margin-bottom:0.2rem;">{label}</div>'
                    f'<div style="font-size:0.86rem; color:#B8B3D7; line-height:1.7;">{line}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                matched_tag = True
                break

        if not matched_tag and line:
            line = line.replace("$", "&#36;")
            st.markdown(f"<div style='font-size:0.88rem; color:#B8B3D7; line-height:1.7; padding:0.2rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)

    _divider()

    # ══════════════════════════════════════════════════════
    # M12. DOWNLOAD DEAL BOOK
    # ══════════════════════════════════════════════════════
    _section("Download Deal Book")

    if not os.path.exists("assets/template.pptx"):
        with st.spinner("Creating template..."):
            from create_template import build
            build()

    with st.spinner("Building 10-slide Deal Book..."):
        deal_book_buf = generate_deal_book(acq_cd, tgt_cd, pro_forma, merger_insights, merger_assumptions)

    dl1, dl2, dl3 = st.columns([1, 2, 1])
    with dl2:
        st.download_button(
            label=f"Download {acq_cd.ticker}+{tgt_cd.ticker} Deal Book  (10 slides)",
            data=deal_book_buf,
            file_name=f"{acq_cd.ticker}_{tgt_cd.ticker}_Deal_Book.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
        )
        st.markdown(
            "<p style='text-align:center; font-size:0.72rem; color:#8A85AD; margin-top:0.3rem;'>"
            "Professional deal book &middot; Pro forma analysis &middot; AI-powered insights"
            "</p>",
            unsafe_allow_html=True,
        )

elif analysis_mode == "Merger Analysis" and merger_btn and (not acquirer_input or not target_input):
    st.warning("Please enter both Acquirer and Target tickers in the sidebar.")

else:
    # ══════════════════════════════════════════════════════
    # SPLASH / LANDING PAGE — Immersive space experience
    # ══════════════════════════════════════════════════════
    if analysis_mode == "Merger Analysis":
        # Merger-specific splash
        st.markdown(
            '<div class="splash-hero">'
            '<div class="star-layer-1">&#8203;</div>'
            '<div class="star-layer-2">&#8203;</div>'
            '<div class="star-layer-3">&#8203;</div>'
            '<div class="nebula-overlay">&#8203;</div>'
            '<div class="orb orb-1">&#8203;</div>'
            '<div class="orb orb-2">&#8203;</div>'
            '<div class="orb orb-3">&#8203;</div>'
            '<div class="orb orb-4">&#8203;</div>'
            '<div class="orb orb-5">&#8203;</div>'
            '<div class="shooting-star shooting-star-1">&#8203;</div>'
            '<div class="shooting-star shooting-star-2">&#8203;</div>'
            '<div class="shooting-star shooting-star-3">&#8203;</div>'
            '<div class="shooting-star shooting-star-4">&#8203;</div>'
            '<div class="shooting-star shooting-star-5">&#8203;</div>'
            '<div class="noise-overlay">&#8203;</div>'
            '<div class="title-glow">&#8203;</div>'
            '<div class="splash-content">'
            '<p class="splash-title">Merger <span class="splash-accent">Simulator</span></p>'
            '<p class="splash-subtitle">Pro forma merger analysis, accretion/dilution &amp; deal book generation</p>'
            '<div class="pill-row">'
            '<span class="feature-pill">Pro Forma Analysis</span>'
            '<span class="feature-pill">Accretion/Dilution</span>'
            '<span class="feature-pill">Football Field</span>'
            '<span class="feature-pill">AI Insights</span>'
            '<span class="feature-pill">Deal Book PPTX</span>'
            '</div>'
            '<div class="splash-stats">'
            '<div class="splash-stat"><div class="splash-stat-value">12</div><div class="splash-stat-label">Dashboard Sections</div></div>'
            '<div class="splash-stat"><div class="splash-stat-value">10</div><div class="splash-stat-label">Deal Book Slides</div></div>'
            '<div class="splash-stat"><div class="splash-stat-value">4</div><div class="splash-stat-label">AI Analyses</div></div>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="space-section">'
            '<div class="space-section-title">How It Works</div>'
            '<div class="step-grid">'
            '<div class="step-card"><div class="step-num">1</div><div class="step-label">Enter Tickers</div><div class="step-detail">Acquirer + Target company tickers</div></div>'
            '<div class="step-card"><div class="step-num">2</div><div class="step-label">Set Assumptions</div><div class="step-detail">Premium, cash/stock mix, synergies</div></div>'
            '<div class="step-card"><div class="step-num">3</div><div class="step-label">Analyze Deal</div><div class="step-detail">Pro forma financials &amp; AI insights</div></div>'
            '<div class="step-card"><div class="step-num">4</div><div class="step-label">Download Book</div><div class="step-detail">10-slide deal book PowerPoint</div></div>'
            '</div>'
            '<div class="space-section-title">Analysis Features</div>'
            '<div class="feature-grid">'
            '<div class="feature-card"><div class="feature-icon">&#128200;</div><div class="feature-title">Pro Forma P&amp;L</div><div class="feature-desc">Combined income statement with synergy adjustments</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#128202;</div><div class="feature-title">Accretion/Dilution</div><div class="feature-desc">Waterfall chart showing EPS bridge</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#127919;</div><div class="feature-title">Football Field</div><div class="feature-desc">Multi-method valuation range analysis</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#128176;</div><div class="feature-title">Sources &amp; Uses</div><div class="feature-desc">Classic IB deal structure breakdown</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#128161;</div><div class="feature-title">AI Rationale</div><div class="feature-desc">Strategic fit and synergy assessment</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#9888;</div><div class="feature-title">Risk Analysis</div><div class="feature-desc">Antitrust, integration, financial risks</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#127942;</div><div class="feature-title">Deal Grade</div><div class="feature-desc">AI-powered A-F deal verdict</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#128196;</div><div class="feature-title">Deal Book</div><div class="feature-desc">10-slide professional PPTX export</div></div>'
            '</div>'
            '<p style="font-size:0.72rem; color:#8A85AD; margin-top:2rem; text-align:center;">'
            'Enter Acquirer &amp; Target tickers in the sidebar to begin<br>'
            'Set <code style="color:#9B8AFF;">OPENAI_API_KEY</code> for AI-powered deal insights'
            '</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="splash-hero">'
            '<div class="star-layer-1">&#8203;</div>'
            '<div class="star-layer-2">&#8203;</div>'
            '<div class="star-layer-3">&#8203;</div>'
            '<div class="nebula-overlay">&#8203;</div>'
            '<div class="orb orb-1">&#8203;</div>'
            '<div class="orb orb-2">&#8203;</div>'
            '<div class="orb orb-3">&#8203;</div>'
            '<div class="orb orb-4">&#8203;</div>'
            '<div class="orb orb-5">&#8203;</div>'
            '<div class="shooting-star shooting-star-1">&#8203;</div>'
            '<div class="shooting-star shooting-star-2">&#8203;</div>'
            '<div class="shooting-star shooting-star-3">&#8203;</div>'
            '<div class="shooting-star shooting-star-4">&#8203;</div>'
            '<div class="shooting-star shooting-star-5">&#8203;</div>'
            '<div class="noise-overlay">&#8203;</div>'
            '<div class="title-glow">&#8203;</div>'
            '<div class="splash-content">'
            '<p class="splash-title">M&amp;A Profile <span class="splash-accent">Builder</span></p>'
            '<p class="splash-subtitle">Institutional-grade company research &amp; tear sheet generation</p>'
            '<div class="pill-row">'
            '<span class="feature-pill">Live Market Data</span>'
            '<span class="feature-pill">Wikipedia M&amp;A</span>'
            '<span class="feature-pill">Peer Analysis</span>'
            '<span class="feature-pill">AI Powered</span>'
            '<span class="feature-pill">Global Exchanges</span>'
            '</div>'
            '<div class="splash-stats">'
            '<div class="splash-stat"><div class="splash-stat-value">60+</div><div class="splash-stat-label">Data Points</div></div>'
            '<div class="splash-stat"><div class="splash-stat-value">8</div><div class="splash-stat-label">PPTX Slides</div></div>'
            '<div class="splash-stat"><div class="splash-stat-value">20+</div><div class="splash-stat-label">Exchanges</div></div>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Step cards and feature grid in dark space-section
        st.markdown(
            '<div class="space-section">'
            '<div class="space-section-title">How It Works</div>'
            '<div class="step-grid">'
            '<div class="step-card"><div class="step-num">1</div><div class="step-label">Enter Ticker</div><div class="step-detail">Any global exchange &mdash; AAPL, RY.TO, NVDA.L</div></div>'
            '<div class="step-card"><div class="step-num">2</div><div class="step-label">Generate Profile</div><div class="step-detail">60+ data points pulled in real-time</div></div>'
            '<div class="step-card"><div class="step-num">3</div><div class="step-label">Explore Dashboard</div><div class="step-detail">Charts, peer comparison &amp; insights</div></div>'
            '<div class="step-card"><div class="step-num">4</div><div class="step-label">Download PPTX</div><div class="step-detail">8-slide IB-grade PowerPoint</div></div>'
            '</div>'
            '<div class="space-section-title">Platform Features</div>'
            '<div class="feature-grid">'
            '<div class="feature-card"><div class="feature-icon">&#128200;</div><div class="feature-title">Price &amp; Valuation</div><div class="feature-desc">Live prices, multiples, and historical charts</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#128101;</div><div class="feature-title">Peer Comparison</div><div class="feature-desc">Side-by-side valuation vs industry peers</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#128202;</div><div class="feature-title">Financial Statements</div><div class="feature-desc">Income, balance sheet, cash flow analysis</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#129309;</div><div class="feature-title">M&amp;A History</div><div class="feature-desc">Deal history scraped from Wikipedia</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#127919;</div><div class="feature-title">Analyst Consensus</div><div class="feature-desc">Recommendations &amp; price targets</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#128161;</div><div class="feature-title">AI Insights</div><div class="feature-desc">Powered by GPT (optional API key)</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#127760;</div><div class="feature-title">Global Exchanges</div><div class="feature-desc">TSX, LSE, JPX and more with local currencies</div></div>'
            '<div class="feature-card"><div class="feature-icon">&#128196;</div><div class="feature-title">PowerPoint Export</div><div class="feature-desc">8-slide professional presentation</div></div>'
            '</div>'
            '<p style="font-size:0.72rem; color:#8A85AD; margin-top:2rem; text-align:center;">'
            'M&amp;A history scraped from Wikipedia &mdash; no API key needed<br>'
            'Set <code style="color:#9B8AFF;">OPENAI_API_KEY</code> for enhanced insights'
            '</p>'
            '</div>',
            unsafe_allow_html=True,
        )
