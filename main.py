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

from data_engine import (
    fetch_company_data, fetch_peer_data,
    format_number, format_pct, format_multiple
)
from ai_insights import generate_insights
from pptx_generator import generate_presentation

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

.block-container {{
    padding-top: 1rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}}

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

/* ── SIDEBAR ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0B0E1A 0%, #151933 100%);
    border-right: 2px solid rgba(107,92,231,0.3);
}}
section[data-testid="stSidebar"] * {{
    color: #C8C3E3 !important;
}}
section[data-testid="stSidebar"] .stTextInput > div > div > input {{
    background: rgba(107,92,231,0.08);
    border: 1px solid rgba(107,92,231,0.3);
    border-radius: 12px;
    color: #fff !important;
    font-weight: 600;
    font-size: 1.1rem;
    letter-spacing: 2px;
    text-align: center;
    padding: 0.7rem;
}}
section[data-testid="stSidebar"] .stTextInput > div > div > input:focus {{
    border-color: #6B5CE7;
    box-shadow: 0 0 15px rgba(107,92,231,0.3);
}}
section[data-testid="stSidebar"] .stButton > button {{
    background: linear-gradient(135deg, #6B5CE7 0%, #9B8AFF 100%) !important;
    color: #fff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.7rem 2rem !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(107,92,231,0.3);
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(107,92,231,0.5);
}}
section[data-testid="stSidebar"] hr {{
    border-color: rgba(107,92,231,0.2) !important;
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
    display: flex; align-items: center; gap: 0.6rem;
    margin: 2rem 0 0.8rem 0; padding-bottom: 0.5rem;
    border-bottom: none;
    position: relative;
}}
.section-header::after {{
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #6B5CE7, #E8638B, transparent);
    animation: glowPulse 3s ease-in-out infinite;
    border-radius: 2px;
}}
.section-header h3 {{
    font-size: 1.15rem; font-weight: 700; color: #1A1D2E; margin: 0;
}}
.section-header .accent-bar {{
    width: 4px; height: 22px; background: linear-gradient(180deg, #6B5CE7, #E8638B); border-radius: 2px;
}}

/* ── GRADIENT DIVIDER ────────────────────────────────────── */
.gradient-divider {{
    height: 1px; border: none; margin: 1.5rem 0;
    background: linear-gradient(90deg, transparent, rgba(107,92,231,0.3), rgba(232,99,139,0.2), transparent);
}}

/* ── METRIC CARDS ────────────────────────────────────────── */
div[data-testid="stMetric"] {{
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 0.8rem 1rem;
    transition: all 0.25s ease;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
}}
div[data-testid="stMetric"]::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #6B5CE7, #9B8AFF);
    opacity: 0; transition: opacity 0.3s ease;
}}
div[data-testid="stMetric"]:hover {{
    border-color: #6B5CE7;
    box-shadow: 0 4px 25px rgba(107,92,231,0.18);
    transform: translateY(-2px);
}}
div[data-testid="stMetric"]:hover::before {{
    opacity: 1;
}}
div[data-testid="stMetric"] label {{
    font-size: 0.7rem !important; font-weight: 600 !important;
    text-transform: uppercase; letter-spacing: 0.8px; color: #6B7280 !important;
}}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
    font-size: 1.1rem !important; font-weight: 700 !important; color: #1A1D2E !important;
}}

/* ── TABS ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0; background: #F3F4F6; border-radius: 12px; padding: 4px;
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px; font-weight: 600; font-size: 0.82rem;
    padding: 0.5rem 1.2rem; color: #6B7280;
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    background: linear-gradient(135deg, #1A1D2E, #2a2040);
    color: #ffffff;
    box-shadow: 0 2px 12px rgba(107,92,231,0.25);
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
.stTabs [data-baseweb="tab-border"] {{ display: none; }}

/* ── EXPANDERS ───────────────────────────────────────────── */
.streamlit-expanderHeader {{
    font-weight: 600 !important; font-size: 0.95rem !important;
    color: #1A1D2E !important; background: #F9FAFB;
    border: 1px solid #E5E7EB; border-radius: 12px;
}}

/* ── DATAFRAMES ──────────────────────────────────────────── */
.stDataFrame {{
    border: 1px solid #E5E7EB; border-radius: 12px; overflow: hidden;
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
    padding: 0.65rem 0; border-bottom: 1px solid #F3F4F6;
    transition: background 0.15s;
}}
.news-item:hover {{ background: #F9FAFB; }}
.news-title {{
    font-weight: 600; color: #1A1D2E; font-size: 0.88rem; text-decoration: none;
}}
.news-title:hover {{ color: #6B5CE7; }}
.news-pub {{ font-size: 0.72rem; color: #6B7280; font-weight: 500; }}

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
    border: 1px solid #E5E7EB; border-radius: 14px;
    overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    transition: all 0.3s ease;
}}
.stPlotlyChart:hover {{
    border-color: rgba(107,92,231,0.4);
    box-shadow: 0 4px 20px rgba(107,92,231,0.1);
}}

/* ── RADIO BUTTONS ──────────────────────────────────────── */
.stRadio > div {{ gap: 0.3rem; }}
.stRadio > div > label {{
    background: #F3F4F6; border-radius: 8px; padding: 0.3rem 1rem;
    font-weight: 600; font-size: 0.8rem; border: 1px solid transparent;
}}
.stRadio > div > label[data-checked="true"] {{
    background: #1A1D2E; color: #ffffff;
}}

/* ── SCROLLBAR ──────────────────────────────────────────── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: #F3F4F6; border-radius: 10px; }}
::-webkit-scrollbar-thumb {{ background: #C8C3E3; border-radius: 10px; }}
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
}}
</style>
""", unsafe_allow_html=True)

# ── Space-specific CSS (starfield, nebula, orbs, glass cards) ──
st.markdown(f"""
<style>
/* ── SPLASH HERO ────────────────────────────────────────── */
.splash-hero {{
    background: linear-gradient(170deg, #020515 0%, #0B0E1A 30%, #151933 60%, #1a1040 80%, #2d1b69 100%);
    border-radius: 24px; padding: 5rem 3rem 4rem; text-align: center;
    margin-bottom: 0; position: relative; overflow: hidden;
    box-shadow: 0 12px 60px rgba(11,14,26,0.7);
    min-height: 500px;
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
}}

/* Star Layer 1 — small distant stars */
.star-layer-1 {{
    position: absolute; top: 0; left: 0; width: 1px; height: 1px;
    box-shadow: {_STARS1};
    opacity: 0.5;
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
    opacity: 0.7;
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
    opacity: 0.9;
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
    animation: float1 20s ease-in-out infinite;
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
    animation: float4 25s ease-in-out infinite;
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
    background: linear-gradient(135deg, #9B8AFF, #E8638B, #F5A623);
    background-size: 200% 200%;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientShift 6s ease infinite;
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
    background: linear-gradient(180deg, #0B0E1A 0%, #0f1225 50%, #151933 100%);
    border-radius: 0 0 24px 24px;
    padding: 2.5rem 3rem;
    margin-top: 0;
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
</style>
""", unsafe_allow_html=True)


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
        line=dict(color='#6B5CE7', width=2.5),
    ))
    fig.add_trace(go.Scatterpolar(
        r=norm_peer + [norm_peer[0]],
        theta=metrics + [metrics[0]],
        fill='toself', name='Peer Median',
        fillcolor='rgba(232,99,139,0.08)',
        line=dict(color='#E8638B', width=2),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 120], tickfont=dict(size=8, color="#999")),
            angularaxis=dict(tickfont=dict(size=10, color="#4B5563")),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True, height=400,
        margin=dict(t=40, b=40, l=60, r=60),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(size=11)),
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("")
    st.markdown(
        '<div style="text-align:center; padding: 1rem 0 0.5rem 0;">'
        '<div style="font-size:1.4rem; font-weight:800; letter-spacing:-0.5px; color:#fff;">M&A Profile</div>'
        '<div style="font-size:1.4rem; font-weight:800; background:linear-gradient(135deg,#9B8AFF,#E8638B);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-top:-0.3rem;">Builder</div>'
        '<div style="font-size:0.7rem; color:#A8A3C7; margin-top:0.3rem; letter-spacing:1.5px; text-transform:uppercase;">Investment Research Platform</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    ticker_input = st.text_input(
        "Stock Ticker", value="AAPL", max_chars=10,
        help="Enter any stock ticker (e.g. AAPL, RY.TO, NVDA.L, 7203.T)"
    ).strip().upper()

    generate_btn = st.button("Generate Profile", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; padding: 0.5rem 0;">'
        '<div style="font-size:0.65rem; color:#6B7280; letter-spacing:0.5px; line-height:1.8;">'
        'DATA: YAHOO FINANCE<br>'
        'M&A: WIKIPEDIA<br>'
        'CHARTS: PLOTLY<br>'
        'AI: OPENAI (OPT.)'
        '</div></div>',
        unsafe_allow_html=True,
    )

# ── Main Area ────────────────────────────────────────────────
st.markdown(
    '<div class="hero-header">'
    '<p class="hero-title">M&A Profile <span class="hero-accent">Builder</span></p>'
    '<p class="hero-sub">Comprehensive company research & 8-slide tear sheet generator</p>'
    '<span class="hero-tagline">Powered by Live Market Data</span>'
    '</div>',
    unsafe_allow_html=True,
)

if generate_btn and ticker_input:
    # ── Data Fetching ────────────────────────────────────
    with st.spinner(f"Fetching comprehensive data for {ticker_input}..."):
        try:
            cd = fetch_company_data(ticker_input)
        except Exception as e:
            st.error(f"Failed to fetch data for **{ticker_input}**: {e}")
            st.stop()

    with st.spinner("Fetching peer comparison data..."):
        try:
            cd = fetch_peer_data(cd)
        except Exception:
            pass  # Peer data is non-critical

    with st.spinner("Generating insights..."):
        cd = generate_insights(cd)

    cs = cd.currency_symbol  # shorthand

    # ══════════════════════════════════════════════════════
    # 1. COMPANY HEADER CARD (with logo)
    # ══════════════════════════════════════════════════════
    chg_class = "price-up" if cd.price_change >= 0 else "price-down"
    chg_badge = "change-up" if cd.price_change >= 0 else "change-down"
    arrow = "&#9650;" if cd.price_change >= 0 else "&#9660;"

    logo_html = ""
    if cd.logo_url:
        logo_html = (
            f'<img src="{cd.logo_url}" '
            f'style="width:52px; height:52px; border-radius:10px; object-fit:contain; '
            f'background:white; padding:4px; margin-right:1.2rem; flex-shrink:0;" '
            f'onerror="this.style.display=\'none\'">'
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
        f'<div style="font-size:0.65rem; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:1px;">Current Price</div>'
        f'<div style="font-size:2rem; font-weight:800; color:{price_color};">'
        f'{cs}{cd.current_price:,.2f}'
        f'<span style="font-size:0.9rem; margin-left:0.5rem;">{arrow} {cd.price_change:+.2f} ({cd.price_change_pct:+.2f}%)</span></div>'
        f'</div>'
        f'<div style="flex:0 0 180px; text-align:center; border-left:1px solid #E5E7EB; padding-left:1rem;">'
        f'<div style="font-size:0.65rem; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:1px;">Volume</div>'
        f'<div style="font-size:1.3rem; font-weight:700; color:#1A1D2E;">{format_number(cd.volume, prefix="", decimals=0)}</div>'
        f'<div style="font-size:0.6rem; color:#6B7280;">Avg: {format_number(cd.avg_volume, prefix="", decimals=0)}</div>'
        f'</div>'
        f'<div style="flex:0 0 220px; text-align:center; border-left:1px solid #E5E7EB; padding-left:1rem;">'
        f'<div style="font-size:0.65rem; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:1px;">52W Range</div>'
        f'<div style="font-size:1.1rem; font-weight:600; color:#1A1D2E;">'
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
            st.markdown(f"<div style='line-height:1.7; color:#4B5563; font-size:0.9rem;'>{cd.long_business_summary}</div>", unsafe_allow_html=True)
        else:
            st.info("Business description not available.")
        b1, b2, b3 = st.columns(3)
        with b1:
            emp_val = f"{cd.full_time_employees:,}" if cd.full_time_employees else "N/A"
            st.markdown(f'<div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:0.6rem 0.8rem; text-align:center;"><div style="font-size:0.65rem; font-weight:600; text-transform:uppercase; letter-spacing:0.7px; color:#6B7280; margin-bottom:0.2rem;">Employees</div><div style="font-size:1rem; font-weight:700; color:#1A1D2E;">{emp_val}</div></div>', unsafe_allow_html=True)
        with b2:
            hq = f"{cd.city}, {cd.state}" if cd.city else "N/A"
            if cd.country and cd.country != "United States":
                hq += f", {cd.country}"
            st.markdown(f'<div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:0.6rem 0.8rem; text-align:center;"><div style="font-size:0.65rem; font-weight:600; text-transform:uppercase; letter-spacing:0.7px; color:#6B7280; margin-bottom:0.2rem;">Headquarters</div><div style="font-size:1rem; font-weight:700; color:#1A1D2E;">{hq}</div></div>', unsafe_allow_html=True)
        with b3:
            web_display = cd.website.replace("https://", "").replace("http://", "").rstrip("/") if cd.website else "N/A"
            st.markdown(f'<div style="background:#F9FAFB; border:1px solid #E5E7EB; border-radius:10px; padding:0.6rem 0.8rem; text-align:center;"><div style="font-size:0.65rem; font-weight:600; text-transform:uppercase; letter-spacing:0.7px; color:#6B7280; margin-bottom:0.2rem;">Website</div><div style="font-size:1rem; font-weight:700; color:#1A1D2E;">{web_display}</div></div>', unsafe_allow_html=True)

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
        fig.add_trace(go.Scatter(
            x=plot_hist.index, y=plot_hist["Close"],
            mode="lines", name="Close",
            line=dict(color="#6B5CE7", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(107,92,231,0.06)",
        ))
        if "Volume" in plot_hist.columns:
            fig.add_trace(go.Bar(
                x=plot_hist.index, y=plot_hist["Volume"],
                name="Volume", yaxis="y2",
                marker_color="rgba(26,29,46,0.06)",
            ))
            fig.update_layout(
                yaxis2=dict(overlaying="y", side="right", showgrid=False,
                            title=dict(text="Volume", font=dict(size=10, color="#999")),
                            tickformat=".2s", tickfont=dict(size=8, color="#999")),
            )
        fig.update_layout(
            height=420,
            margin=dict(t=10, b=30, l=50, r=50),
            xaxis=dict(showgrid=False, tickfont=dict(size=9, color="#6B7280"), rangeslider=dict(visible=False)),
            yaxis=dict(
                title=dict(text=f"Price ({cs})", font=dict(size=10, color="#6B7280")),
                gridcolor="rgba(0,0,0,0.04)", tickfont=dict(size=9, color="#6B7280"),
                tickprefix=cs,
            ),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False, hovermode="x unified",
            hoverlabel=dict(bgcolor="#1A1D2E", font_size=11, font_color="#fff"),
        )
        st.plotly_chart(fig, use_container_width=True)
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
        st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:1px; margin:0.8rem 0 0.3rem 0;'>Premium / Discount vs. Peer Median</p>", unsafe_allow_html=True)

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
            _build_peer_radar_chart(cd)
        with rc2:
            st.markdown("")
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#1A1D2E; margin-bottom:0.5rem;'>Peer Group</p>", unsafe_allow_html=True)
            for p in cd.peer_data:
                st.markdown(
                    f"<div style='font-size:0.82rem; color:#4B5563; padding:0.2rem 0;'>"
                    f"<span style='font-weight:600; color:#6B5CE7;'>{p['ticker']}</span> &mdash; {p.get('name', '')}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(f"<div style='font-size:0.7rem; color:#6B7280; margin-top:0.5rem;'>Industry: {cd.industry}</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # 7. KEY STATISTICS
    # ══════════════════════════════════════════════════════
    _section("Key Statistics")

    st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:1px; margin:0.5rem 0 0.3rem 0;'>Valuation</p>", unsafe_allow_html=True)
    v1, v2, v3, v4, v5 = st.columns(5)
    v1.metric("P/E (TTM)", f"{cd.trailing_pe:.1f}" if cd.trailing_pe else "N/A")
    v2.metric("Forward P/E", f"{cd.forward_pe:.1f}" if cd.forward_pe else "N/A")
    v3.metric("PEG Ratio", f"{cd.peg_ratio:.2f}" if cd.peg_ratio else "N/A")
    v4.metric("EV/EBITDA", format_multiple(cd.ev_to_ebitda))
    v5.metric("EV/Revenue", format_multiple(cd.ev_to_revenue))

    st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:1px; margin:0.8rem 0 0.3rem 0;'>Profitability</p>", unsafe_allow_html=True)
    p1, p2, p3, p4, p5 = st.columns(5)
    p1.metric("Gross Margin", format_pct(cd.gross_margins))
    p2.metric("Op. Margin", format_pct(cd.operating_margins))
    p3.metric("Net Margin", format_pct(cd.profit_margins))
    p4.metric("ROE", format_pct(cd.return_on_equity))
    p5.metric("ROA", format_pct(cd.return_on_assets))

    st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#6B7280; text-transform:uppercase; letter-spacing:1px; margin:0.8rem 0 0.3rem 0;'>Financial Health</p>", unsafe_allow_html=True)
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

                fig_rec = go.Figure(go.Bar(
                    x=vals, y=cats, orientation="h",
                    marker_color=colors,
                    text=[f"  {v} ({v/total*100:.0f}%)" if total > 0 else f"  {v}" for v in vals],
                    textposition="outside",
                    textfont=dict(size=11, color="#4B5563", family="Inter"),
                ))
                fig_rec.update_layout(
                    height=280, margin=dict(t=40, b=20, l=110, r=60),
                    title=dict(text="Analyst Recommendation Distribution",
                               font=dict(size=13, color="#1A1D2E", family="Inter")),
                    xaxis=dict(title=dict(text="# Analysts", font=dict(size=10)),
                               showgrid=True, gridcolor="rgba(0,0,0,0.04)", tickfont=dict(size=9)),
                    yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#4B5563")),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", bargap=0.35,
                )
                st.plotly_chart(fig_rec, use_container_width=True)
            except Exception:
                st.info("Recommendation data not available.")
        else:
            st.info("Analyst recommendation data not available.")

    with a2:
        if cd.analyst_price_targets:
            pt = cd.analyst_price_targets
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#1A1D2E; margin-bottom:0.5rem;'>Price Targets</p>", unsafe_allow_html=True)
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
                    f'<span style="font-size:0.75rem; color:#6B7280; font-weight:600;">IMPLIED UPSIDE</span><br>'
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
            st.markdown("<p style='font-size:0.85rem; font-weight:700; color:#1A1D2E; margin-bottom:0.3rem;'>Management Assessment</p>", unsafe_allow_html=True)
            for line in cd.mgmt_sentiment.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"<div style='font-size:0.82rem; color:#4B5563; line-height:1.7; padding:0.15rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)

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
    # 14. INSIGHTS (renamed from "AI-Generated Insights")
    # ══════════════════════════════════════════════════════
    _section("Insights")
    ai_tab1, ai_tab2, ai_tab3, ai_tab4 = st.tabs([
        "Executive Summary", "Product Overview", "Industry Analysis", "Risk Factors"
    ])
    with ai_tab1:
        if cd.executive_summary_bullets:
            for b in cd.executive_summary_bullets:
                st.markdown(f"<div style='font-size:0.88rem; color:#4B5563; line-height:1.7; padding:0.2rem 0;'>&bull; {b}</div>", unsafe_allow_html=True)
        else:
            st.info("Executive summary not available.")
    with ai_tab2:
        if cd.product_overview:
            for line in cd.product_overview.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"<div style='font-size:0.88rem; color:#4B5563; line-height:1.7; padding:0.2rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)
        else:
            st.info("Product overview not available.")
    with ai_tab3:
        if cd.industry_analysis:
            for line in cd.industry_analysis.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"<div style='font-size:0.88rem; color:#4B5563; line-height:1.7; padding:0.2rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)
        else:
            st.info("Industry analysis not available.")
    with ai_tab4:
        if cd.risk_factors:
            for line in cd.risk_factors.split("\n"):
                line = line.strip()
                if line.startswith("- "):
                    line = line[2:]
                if line:
                    st.markdown(f"<div style='font-size:0.88rem; color:#4B5563; line-height:1.7; padding:0.2rem 0;'>&bull; {line}</div>", unsafe_allow_html=True)
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
            "<p style='text-align:center; font-size:0.72rem; color:#6B7280; margin-top:0.3rem;'>"
            "Professional IB-grade presentation &middot; Editable charts &middot; Navy/Gold palette"
            "</p>",
            unsafe_allow_html=True,
        )

elif generate_btn and not ticker_input:
    st.warning("Please enter a ticker symbol in the sidebar.")
else:
    # ══════════════════════════════════════════════════════
    # SPLASH / LANDING PAGE — Immersive space experience
    # ══════════════════════════════════════════════════════
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
        '<div><div class="splash-stat-value">60+</div><div class="splash-stat-label">Data Points</div></div>'
        '<div><div class="splash-stat-value">8</div><div class="splash-stat-label">PPTX Slides</div></div>'
        '<div><div class="splash-stat-value">20+</div><div class="splash-stat-label">Exchanges</div></div>'
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
        '<p style="font-size:0.72rem; color:#6B7280; margin-top:2rem; text-align:center;">'
        'M&amp;A history scraped from Wikipedia &mdash; no API key needed<br>'
        'Set <code style="color:#9B8AFF;">OPENAI_API_KEY</code> for enhanced insights'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )
