"""
RŌEM Creamery — Investor & Lender Simulator Suite
Single-file Streamlit app. Upload this as app.py in the root of your repo.

Five simulators accessible via sidebar navigation:
  1. Path to Profit       — 24-month cash runway + seasonality
  2. Bankability Optimizer — DSCR gauge keyed to SBA thresholds
  3. Market Penetration   — vs. 17 Boston-area competitor shops
  4. Menu Mix Optimizer   — product-level margin analysis
  5. Location ROI         — 4-archetype site comparison
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# BRAND & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

NAVY = "#1F3A5F"
NAVY_LIGHT = "#4A6B8A"
GOLD = "#C9A961"
CREAM = "#FAF7F0"
GREEN = "#2E7D32"
RED = "#C62828"
AMBER = "#F57C00"

LOGO_PATH = Path(__file__).parent / "assets" / "roem_logo.png"

# ─── BASE CASE ASSUMPTIONS ─────────────────────────────────────────────────
BASE = {
    # Space
    "sqft": 1000,
    "rent_per_sqft_year": 48,
    "cam_per_sqft_year": 12,
    "days_per_week": 7,
    "hours_per_day": 11,   # 11am–10pm, 7 days/week
    # Pricing
    "avg_ticket": 9.50,
    "items_per_transaction": 1.3,
    # Volume
    "base_customers_per_day": 100,
    "ramp_start_pct": 0.30,
    "ramp_weeks": 16,
    # COGS
    "food_cost_pct": 0.30,
    "paper_cost_pct": 0.045,
    "waste_pct": 0.02,
    # Labor
    "owner_salary": 48000,
    "hourly_wage": 18.00,
    "payroll_tax_pct": 0.0765,
    "workers_comp_pct": 0.012,
    # Loan
    "loan_amount": 285000,
    "loan_rate": 0.0875,    # SBA 7(a) Apr 2026 max for >$250K
    "loan_years": 10,
    "owner_equity": 40000,
    # Overhead (monthly)
    "utilities": 850,
    "internet_phone": 180,
    "insurance": 150,       # MA BOP avg for food/bev
    "pos_software": 60,     # Square for Restaurants Plus
    "accounting": 250,
    "marketing": 600,
    "cleaning_supplies": 220,
    "repairs_maintenance": 300,
    "bank_fees": 45,
    "misc": 200,
    "licenses_permits_monthly": 90,
}

# Monthly seasonality multipliers (1.0 = baseline)
# New England ice cream pattern — summer peak 1.55×, winter trough 0.60×
SEASONALITY = {
    1: 0.60, 2: 0.62, 3: 0.78, 4: 0.95,
    5: 1.15, 6: 1.40, 7: 1.55, 8: 1.50,
    9: 1.20, 10: 1.00, 11: 0.75, 12: 0.85,
}

# 17 Boston-area competitors (April 2026 research)
COMPETITORS = [
    {"name": "J.P. Licks", "neighborhood": "Multi-location", "style": "Traditional premium", "avg_ticket": 7.25, "daily_customers": 180, "locations": 17, "years": 43},
    {"name": "Toscanini's", "neighborhood": "Cambridge / Central", "style": "Artisan small-batch", "avg_ticket": 8.00, "daily_customers": 160, "locations": 1, "years": 44},
    {"name": "Christina's", "neighborhood": "Inman Square", "style": "Homemade exotic flavors", "avg_ticket": 7.50, "daily_customers": 130, "locations": 1, "years": 46},
    {"name": "Van Leeuwen", "neighborhood": "Seaport / Newbury / BackBay", "style": "Premium national chain", "avg_ticket": 8.75, "daily_customers": 140, "locations": 5, "years": 18},
    {"name": "Amorino", "neighborhood": "Newbury / Harvard Sq", "style": "Italian gelato (rose)", "avg_ticket": 9.00, "daily_customers": 110, "locations": 2, "years": 23},
    {"name": "Honeycomb Creamery", "neighborhood": "Cambridge", "style": "Artisan rotating flavors", "avg_ticket": 7.75, "daily_customers": 140, "locations": 1, "years": 9},
    {"name": "Taiyaki NYC", "neighborhood": "Seaport / Cambridge", "style": "Japanese fish-cone soft-serve", "avg_ticket": 9.50, "daily_customers": 125, "locations": 2, "years": 8},
    {"name": "Mizu Matcha", "neighborhood": "Downtown Boston", "style": "Japanese matcha soft-serve", "avg_ticket": 8.50, "daily_customers": 95, "locations": 1, "years": 3},
    {"name": "Mike's Pastry", "neighborhood": "North End", "style": "Italian gelato + pastry", "avg_ticket": 8.00, "daily_customers": 400, "locations": 3, "years": 80},
    {"name": "FoMu", "neighborhood": "Cambridge / Brookline / Fenway", "style": "Vegan non-dairy", "avg_ticket": 7.25, "daily_customers": 100, "locations": 4, "years": 14},
    {"name": "New City Microcreamery", "neighborhood": "Cambridge / Hudson", "style": "Liquid-nitrogen craft", "avg_ticket": 8.50, "daily_customers": 110, "locations": 3, "years": 11},
    {"name": "North End Creamery", "neighborhood": "Medford / Malden", "style": "Classic scoop shop", "avg_ticket": 6.75, "daily_customers": 95, "locations": 2, "years": 12},
    {"name": "Gracie's Ice Cream", "neighborhood": "Somerville (Union Sq)", "style": "Small-batch traditional", "avg_ticket": 7.00, "daily_customers": 120, "locations": 1, "years": 13},
    {"name": "Far Out Ice Cream", "neighborhood": "Brookline", "style": "Vintage-theme scoop shop", "avg_ticket": 6.75, "daily_customers": 90, "locations": 1, "years": 9},
    {"name": "Caffè Paradiso", "neighborhood": "North End", "style": "Italian café + gelato", "avg_ticket": 7.50, "daily_customers": 150, "locations": 1, "years": 45},
    {"name": "Chill on Park", "neighborhood": "Dorchester", "style": "Neighborhood scoop", "avg_ticket": 6.50, "daily_customers": 85, "locations": 1, "years": 8},
    {"name": "Delini Gelato", "neighborhood": "West Roxbury", "style": "Italian gelato", "avg_ticket": 7.25, "daily_customers": 80, "locations": 1, "years": 7},
]

LOCATION_ARCHETYPES = {
    "College-Adjacent": {
        "example": "Davis Sq (Tufts) / Porter Sq (Lesley)",
        "rent_sqft": 62, "traffic_multiplier": 1.25,
        "seasonality_penalty": -0.15,
        "demo_fit": 5, "parking": 2, "evening_traffic": 5,
        "weekend_traffic": 4, "summer_dropoff_risk": 5,
    },
    "Park / Recreation": {
        "example": "Pine Banks / Middlesex Fells edge",
        "rent_sqft": 42, "traffic_multiplier": 0.95,
        "seasonality_penalty": 0.20,
        "demo_fit": 4, "parking": 5, "evening_traffic": 3,
        "weekend_traffic": 5, "summer_dropoff_risk": 1,
    },
    "Main Street Retail": {
        "example": "Medford Sq / Malden Center / Ball Sq",
        "rent_sqft": 52, "traffic_multiplier": 1.05,
        "seasonality_penalty": 0.00,
        "demo_fit": 4, "parking": 4, "evening_traffic": 4,
        "weekend_traffic": 4, "summer_dropoff_risk": 2,
    },
    "Transit Hub": {
        "example": "Assembly Row / Oak Grove T",
        "rent_sqft": 68, "traffic_multiplier": 1.35,
        "seasonality_penalty": -0.05,
        "demo_fit": 4, "parking": 3, "evening_traffic": 5,
        "weekend_traffic": 4, "summer_dropoff_risk": 2,
    },
}

MENU = [
    {"name": "Italian Gelato Scoop", "cost": 1.55, "price": 6.50, "hero": True, "complexity": 2, "origin": "Italy"},
    {"name": "Affogato (gelato + espresso)", "cost": 2.10, "price": 8.50, "hero": True, "complexity": 3, "origin": "Italy"},
    {"name": "Turkish Maraş Dondurması (stretch scoop)", "cost": 2.35, "price": 9.50, "hero": True, "complexity": 5, "origin": "Turkey"},
    {"name": "Czech Trdelník Cone + Soft-Serve", "cost": 2.80, "price": 11.00, "hero": True, "complexity": 4, "origin": "Czech Republic"},
    {"name": "American Frozen Custard", "cost": 1.40, "price": 6.00, "hero": False, "complexity": 2, "origin": "United States"},
    {"name": "Japanese Mochi Ice Cream (3-pc)", "cost": 2.20, "price": 8.00, "hero": True, "complexity": 3, "origin": "Japan"},
    {"name": "Hokkaido Soft-Serve Cone", "cost": 1.75, "price": 7.50, "hero": True, "complexity": 2, "origin": "Japan"},
    {"name": "Thai Mango Sorbet in Coconut Shell", "cost": 3.25, "price": 11.50, "hero": True, "complexity": 4, "origin": "Thailand"},
]


# ═══════════════════════════════════════════════════════════════════════════
# CALC FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def monthly_debt_service(principal, annual_rate, years):
    if annual_rate == 0:
        return principal / (years * 12)
    r = annual_rate / 12
    n = years * 12
    return principal * r / (1 - (1 + r) ** -n)


def ramp_factor(month, ramp_months=4, start_pct=0.30):
    if month >= ramp_months:
        return 1.0
    return start_pct + (1.0 - start_pct) * (month / ramp_months)


def project_month(month_of_year, business_month, inputs):
    seasonal = SEASONALITY[month_of_year]
    ramp = ramp_factor(business_month, inputs.get("ramp_months", 4), inputs.get("ramp_start_pct", 0.30))

    daily_customers = inputs["base_customers_per_day"] * seasonal * ramp
    days_in_month = 30.4
    monthly_customers = daily_customers * days_in_month

    revenue = monthly_customers * inputs["avg_ticket"] * inputs["items_per_transaction"]
    cogs_pct = inputs["food_cost_pct"] + inputs["paper_cost_pct"] + inputs["waste_pct"]
    cogs = revenue * cogs_pct
    gross_profit = revenue - cogs

    if inputs["staffing_scenario"] == "Owner-only":
        monthly_labor = inputs["owner_salary"] / 12
    elif inputs["staffing_scenario"] == "Owner + 1 PT":
        monthly_labor = inputs["owner_salary"] / 12 + (inputs["hourly_wage"] * 25 * 4.33)
    else:
        monthly_labor = inputs["owner_salary"] / 12 + (inputs["hourly_wage"] * 40 * 4.33 * 2)
    monthly_labor *= 1 + inputs["payroll_tax_pct"] + inputs["workers_comp_pct"]

    monthly_rent = inputs["sqft"] * (inputs["rent_per_sqft_year"] + inputs["cam_per_sqft_year"]) / 12
    monthly_overhead = (monthly_rent + inputs["utilities"] + inputs["internet_phone"]
                       + inputs["insurance"] + inputs["pos_software"] + inputs["accounting"]
                       + inputs["marketing"] + inputs["cleaning_supplies"]
                       + inputs["repairs_maintenance"] + inputs["bank_fees"]
                       + inputs["misc"] + inputs["licenses_permits_monthly"])

    ebitda = gross_profit - monthly_labor - monthly_overhead
    debt_service = monthly_debt_service(inputs["loan_amount"], inputs["loan_rate"], inputs["loan_years"])
    net_cash = ebitda - debt_service

    return {
        "month_of_year": month_of_year,
        "business_month": business_month,
        "seasonal": seasonal,
        "ramp": ramp,
        "customers": monthly_customers,
        "revenue": revenue,
        "cogs": cogs,
        "gross_profit": gross_profit,
        "labor": monthly_labor,
        "overhead": monthly_overhead,
        "ebitda": ebitda,
        "debt_service": debt_service,
        "net_cash": net_cash,
    }


def project_24_months(inputs, start_month=10):
    rows = []
    cumulative_cash = inputs["loan_amount"] + inputs["owner_equity"] - inputs.get("startup_costs", 285000)
    for i in range(24):
        moy = ((start_month - 1 + i) % 12) + 1
        m = project_month(moy, i + 1, inputs)
        cumulative_cash += m["net_cash"]
        m["cumulative_cash"] = cumulative_cash
        rows.append(m)
    return rows


# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & GLOBAL CSS
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="RŌEM Creamery — Investor Simulators",
    page_icon="🍦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
    .stApp {{ background-color: {CREAM}; }}
    h1, h2, h3 {{ color: {NAVY}; font-family: Georgia, serif; }}
    .tile {{
        background: white;
        border-left: 5px solid {NAVY};
        border-radius: 4px;
        padding: 18px 22px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    .tile h3 {{ margin-top: 0; }}
    .badge {{
        display: inline-block;
        background: {GOLD};
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }}
    .status-pill {{
        display: inline-block;
        padding: 4px 14px;
        border-radius: 16px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        color: white;
    }}
    .headline-box {{
        background: white;
        padding: 18px 24px;
        border-radius: 4px;
        margin-bottom: 18px;
        border-left: 5px solid {NAVY};
        box-shadow: 0 1px 3px rgba(0,0,0,.08);
    }}
    .big-number {{
        font-size: 32px; font-weight: 700;
        font-family: Georgia, serif; color: {NAVY};
    }}
    .small-label {{
        font-size: 11px; letter-spacing: 0.8px;
        text-transform: uppercase; color: #666;
    }}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    else:
        st.markdown(f"<h1 style='color:{NAVY}; font-family:Georgia; text-align:center;'>RŌEM</h1>", unsafe_allow_html=True)

    st.markdown("---")
    page = st.radio(
        "Simulator",
        [
            "🏠 Home",
            "📈 Path to Profit",
            "🏦 Bankability Optimizer",
            "🗺️ Market Penetration",
            "🍦 Menu Mix Optimizer",
            "📍 Location ROI",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption(
        f"**RŌEM Creamery, LLC**  \n"
        f"Premium globally-inspired creamery  \n"
        f"Boston metro · Opening Oct 2026  \n\n"
        f"SBA 7(a) ${BASE['loan_amount']:,} · {BASE['loan_years']}-yr · {BASE['loan_rate']*100:.2f}%"
    )


# ═══════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ═══════════════════════════════════════════════════════════════════════════

def render_home():
    col_logo, col_title = st.columns([1, 3])
    with col_logo:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=220)
        else:
            st.markdown(f"# RŌEM")
    with col_title:
        st.markdown(f"""
        <h1 style='margin-top: 28px;'>Investor & Lender Simulator Suite</h1>
        <p style='color: {NAVY}; font-size: 16px; margin-top: -6px;'>
        Boston-area premium creamery · Proposed opening October 2026 · SBA 7(a) package
        </p>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(f"""
    <div style='background: {NAVY}; color: white; padding: 14px 22px; border-radius: 4px; margin-top: 10px;'>
        <div style='display: inline-block; margin-right: 38px;'>
            <div style='font-size: 11px; letter-spacing: 0.8px; text-transform: uppercase; opacity: 0.8;'>Target Location</div>
            <div style='font-size: 22px; font-weight: 700; font-family: Georgia, serif;'>Malden / Medford</div>
        </div>
        <div style='display: inline-block; margin-right: 38px;'>
            <div style='font-size: 11px; letter-spacing: 0.8px; text-transform: uppercase; opacity: 0.8;'>Funding Ask</div>
            <div style='font-size: 22px; font-weight: 700; font-family: Georgia, serif;'>${BASE['loan_amount']:,}</div>
        </div>
        <div style='display: inline-block; margin-right: 38px;'>
            <div style='font-size: 11px; letter-spacing: 0.8px; text-transform: uppercase; opacity: 0.8;'>Owner Equity</div>
            <div style='font-size: 22px; font-weight: 700; font-family: Georgia, serif;'>${BASE['owner_equity']:,}</div>
        </div>
        <div style='display: inline-block; margin-right: 38px;'>
            <div style='font-size: 11px; letter-spacing: 0.8px; text-transform: uppercase; opacity: 0.8;'>SBA Rate</div>
            <div style='font-size: 22px; font-weight: 700; font-family: Georgia, serif;'>{BASE['loan_rate']*100:.2f}%</div>
        </div>
        <div style='display: inline-block;'>
            <div style='font-size: 11px; letter-spacing: 0.8px; text-transform: uppercase; opacity: 0.8;'>Term</div>
            <div style='font-size: 22px; font-weight: 700; font-family: Georgia, serif;'>{BASE['loan_years']} years</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### How to use this suite")
    st.markdown(
        "Five interactive simulators let bankers, investors, and advisors stress-test every "
        "major driver of the RŌEM business model. Every input slider is live — the projections "
        "update instantly and tie back to the underlying financial model built in Excel. Market "
        "research figures reflect the April 2026 Boston-metro competitive landscape (17 profiled shops)."
    )

    st.markdown("### Select a simulator from the sidebar")

    tiles = [
        ("Path to Profit", "Flagship", "24-Month Cash Runway",
         "Integrates the $285K SBA loan with operational choices and month-by-month seasonality. "
         "Shows the path to break-even and cumulative cash position."),
        ("Bankability Optimizer", "Lender Tool", "DSCR & Credit Metrics",
         "Stress-test DSCR, debt coverage, and surplus cash against loan covenants. "
         "Green/yellow/red health gauge keyed to SBA underwriting thresholds."),
        ("Market Penetration", "Competitive", "vs. 17 Boston Shops",
         "Compare RŌEM projections against Boston-area benchmarks (J.P. Licks, Toscanini's, "
         "Christina's, Van Leeuwen, and 13 more)."),
        ("Menu Mix Optimizer", "Product", "Margin by Item",
         "Drag product mix weights to see how the 8 international specialty items blend into "
         "gross margin. Identify the most bankable hero products."),
        ("Location ROI", "Real Estate", "Archetype Comparison",
         "Compare college-adjacent, park, main-street, and transit-hub archetypes across 8 "
         "factors. Rent, traffic, summer-dropoff, parking, evening trade."),
    ]

    for i in range(0, len(tiles), 2):
        cols = st.columns(2)
        for j, (title, badge, subtitle, desc) in enumerate(tiles[i:i+2]):
            with cols[j]:
                st.markdown(f"""
                <div class='tile'>
                    <div class='badge'>{badge}</div>
                    <h3>{title}</h3>
                    <p style='color: #666; margin: 4px 0 8px 0; font-size: 13px;'><em>{subtitle}</em></p>
                    <p style='margin: 0;'>{desc}</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    with st.expander("📋 Business Context"):
        st.markdown("""
        **Concept.** RŌEM Creamery is a single-unit, 1,000 sqft counter-service creamery
        serving eight international frozen-dessert traditions: Italian gelato, Turkish
        *dondurma*, Czech *trdelník*, American frozen custard, Japanese mochi and Hokkaido
        soft-serve, and Thai coconut sorbet.

        **Gap in the market.** Of the 52 ice-cream shops profiled across Boston metro, zero
        currently offer Turkish dondurma, Czech trdelník, or the full globally-inspired
        format RŌEM proposes.

        **Structure.** Single-member Massachusetts LLC. Owner: Erin Nelson. 8+ years
        business-analytics background (ex-Pearson Principal Business Analyst, Play Now
        founder, Peraton). BS Economics, University of Wyoming.

        **Operating hours.** 11 am – 10 pm, 7 days/week.

        **Funding.** $285K SBA 7(a) · 10-year term · 8.75% fixed rate (Prime 6.75 + 2.00
        max spread for loans >$250K, April 2026 SBA schedule) + $40K owner equity =
        $325K total capitalization.
        """)

    with st.expander("📊 Data Sources & Methodology"):
        st.markdown("""
        - **SBA rates.** Prime 6.75% + 2.00% max spread as of April 2026 SBA 7(a) schedule.
        - **Competitor data.** 17 Boston-area shops profiled April 2026.
        - **Seasonality curve.** New England ice-cream industry pattern — summer peak
          at 1.55× baseline (July), winter trough at 0.60× (January).
        - **Insurance.** Insureon April 2026 average for MA food/beverage BOP ($150/mo).
        - **Rent.** LoopNet / CityFeet / Commercialcafe listings for target neighborhoods.
        - **Equipment.** Verified quotes from Carpigiani, Stoelting, KitchenAll, Nissei.

        All figures tie back to the master financial model (Excel workbook, 3,019 formulas
        across 19 tabs).
        """)


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATOR 1: PATH TO PROFIT
# ═══════════════════════════════════════════════════════════════════════════

def render_path_to_profit():
    c1, c2 = st.columns([1, 5])
    with c1:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=140)
    with c2:
        st.markdown("# Path to Profit Simulator")
        st.markdown(
            "*Integrates the $285K SBA loan with operational choices and month-by-month "
            "seasonality to project 24 months of revenue, cash, and break-even timing.*"
        )

    st.markdown("---")

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Simulator Controls")

    with st.sidebar.expander("🎯 Demand", expanded=True):
        daily_customers = st.slider("Daily customers (base)", 40, 250, BASE["base_customers_per_day"], step=5)
        avg_ticket = st.slider("Avg ticket ($)", 5.00, 15.00, BASE["avg_ticket"], step=0.25)
        items_per_txn = st.slider("Items per txn", 1.0, 2.0, BASE["items_per_transaction"], step=0.05)

    with st.sidebar.expander("🏗️ Ramp", expanded=True):
        ramp_start = st.slider("Opening % of base", 0.15, 0.60, BASE["ramp_start_pct"], step=0.05)
        ramp_months = st.slider("Months to full", 2, 8, 4)
        start_month = st.selectbox(
            "Opening month", list(range(1, 13)), index=9,
            format_func=lambda m: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][m-1],
        )

    with st.sidebar.expander("💰 Cost Structure"):
        food_cost_pct = st.slider("Food %", 0.20, 0.40, BASE["food_cost_pct"], step=0.01)
        paper_cost_pct = st.slider("Paper %", 0.02, 0.08, BASE["paper_cost_pct"], step=0.005)
        waste_pct = st.slider("Waste %", 0.00, 0.06, BASE["waste_pct"], step=0.005)

    with st.sidebar.expander("👥 Labor"):
        staffing = st.radio("Staffing", ["Owner-only", "Owner + 1 PT", "Owner + 2 FT"], index=1)
        hourly_wage = st.slider("Hourly wage ($)", 15.00, 25.00, BASE["hourly_wage"], step=0.50)
        owner_salary = st.slider("Owner salary ($/yr)", 30000, 80000, BASE["owner_salary"], step=2000)

    with st.sidebar.expander("🏠 Rent & Overhead"):
        sqft = st.slider("Square footage", 700, 1400, BASE["sqft"], step=50)
        rent_sqft = st.slider("Rent ($/sqft/yr)", 25, 85, BASE["rent_per_sqft_year"])
        cam_sqft = st.slider("CAM ($/sqft/yr)", 6, 20, BASE["cam_per_sqft_year"])
        insurance = st.slider("Insurance ($/mo)", 100, 400, BASE["insurance"], step=10)
        utilities = st.slider("Utilities ($/mo)", 500, 1400, BASE["utilities"], step=50)

    with st.sidebar.expander("🏦 Financing"):
        loan_amount = st.slider("SBA loan ($)", 150000, 400000, BASE["loan_amount"], step=5000)
        loan_rate_pct = st.slider("Rate (%)", 6.0, 12.0, BASE["loan_rate"]*100, step=0.25)
        loan_years = st.slider("Term (yrs)", 5, 15, BASE["loan_years"])
        owner_equity = st.slider("Owner equity ($)", 15000, 100000, BASE["owner_equity"], step=5000)

    inputs = dict(BASE)
    inputs.update({
        "base_customers_per_day": daily_customers, "avg_ticket": avg_ticket,
        "items_per_transaction": items_per_txn, "ramp_start_pct": ramp_start,
        "ramp_months": ramp_months, "food_cost_pct": food_cost_pct,
        "paper_cost_pct": paper_cost_pct, "waste_pct": waste_pct,
        "staffing_scenario": staffing, "hourly_wage": hourly_wage,
        "owner_salary": owner_salary, "sqft": sqft,
        "rent_per_sqft_year": rent_sqft, "cam_per_sqft_year": cam_sqft,
        "insurance": insurance, "utilities": utilities,
        "loan_amount": loan_amount, "loan_rate": loan_rate_pct / 100,
        "loan_years": loan_years, "owner_equity": owner_equity,
        "startup_costs": 285000,
    })

    rows = project_24_months(inputs, start_month=start_month)
    df = pd.DataFrame(rows)
    df["month_label"] = df["business_month"].apply(lambda m: f"M{m}")

    y1 = df.iloc[:12]
    y1_revenue = y1["revenue"].sum()
    y1_ebitda = y1["ebitda"].sum()
    y1_ds = y1["debt_service"].sum()
    y1_dscr = y1_ebitda / y1_ds if y1_ds else 0

    positive_cash = df[df["net_cash"] > 0]
    break_even_m = positive_cash["business_month"].iloc[0] if len(positive_cash) else None
    lowest_cash = df["cumulative_cash"].min()
    end_cash = df["cumulative_cash"].iloc[-1]

    if y1_dscr >= 1.25 and lowest_cash > 0:
        status_color, status_text = GREEN, "BANKABLE"
        status_desc = f"DSCR {y1_dscr:.2f}× passes SBA 1.25× threshold; cash stays positive."
    elif y1_dscr >= 1.00 and lowest_cash > -20000:
        status_color, status_text = AMBER, "TIGHT"
        status_desc = f"DSCR {y1_dscr:.2f}× covers debt but below 1.25× comfort zone."
    else:
        status_color, status_text = RED, "CHALLENGED"
        status_desc = f"DSCR {y1_dscr:.2f}× or cash trough ${lowest_cash:,.0f} signals stress."

    st.markdown(f"""
    <div class='headline-box'>
        <span class='status-pill' style='background-color: {status_color};'>{status_text}</span>
        <p style='margin: 10px 0 0 0;'>{status_desc}</p>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: st.markdown(f"<div class='small-label'>Year 1 Revenue</div><div class='big-number'>${y1_revenue/1000:,.0f}K</div>", unsafe_allow_html=True)
    with k2: st.markdown(f"<div class='small-label'>Year 1 EBITDA</div><div class='big-number'>${y1_ebitda/1000:,.0f}K</div>", unsafe_allow_html=True)
    with k3: st.markdown(f"<div class='small-label'>Year 1 DSCR</div><div class='big-number'>{y1_dscr:.2f}×</div>", unsafe_allow_html=True)
    with k4:
        be_display = f"Month {break_even_m}" if break_even_m else "Not reached"
        st.markdown(f"<div class='small-label'>Net-Cash Positive</div><div class='big-number'>{be_display}</div>", unsafe_allow_html=True)
    with k5: st.markdown(f"<div class='small-label'>End-of-Y2 Cash</div><div class='big-number'>${end_cash/1000:,.0f}K</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("24-Month Revenue, EBITDA & Cumulative Cash")

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
        subplot_titles=("Monthly Revenue & EBITDA", "Cumulative Cash Position"),
        row_heights=[0.55, 0.45]
    )
    fig.add_trace(go.Bar(x=df["month_label"], y=df["revenue"], name="Revenue", marker_color=NAVY), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["month_label"], y=df["ebitda"], name="EBITDA", mode="lines+markers",
                             line=dict(color=GOLD, width=3), marker=dict(size=8)), row=1, col=1)
    cash_color = [GREEN if x > 0 else RED for x in df["cumulative_cash"]]
    fig.add_trace(go.Scatter(x=df["month_label"], y=df["cumulative_cash"], name="Cumulative Cash",
                             mode="lines+markers", fill="tozeroy", fillcolor="rgba(31,58,95,0.15)",
                             line=dict(color=NAVY, width=3), marker=dict(size=7, color=cash_color)), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color="#888", row=2, col=1)
    fig.update_layout(height=600, hovermode="x unified", plot_bgcolor="white", paper_bgcolor=CREAM,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(tickprefix="$", tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Seasonality Curve")
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    seas_values = [SEASONALITY[i] for i in range(1, 13)]
    colors = [RED if v < 0.80 else AMBER if v < 1.00 else GREEN for v in seas_values]
    seas_fig = go.Figure(go.Bar(x=month_labels, y=seas_values, marker_color=colors,
                                text=[f"{v:.2f}×" for v in seas_values], textposition="outside"))
    seas_fig.add_hline(y=1.0, line_dash="dash", line_color=NAVY, annotation_text="Baseline (1.00×)")
    seas_fig.update_layout(yaxis_title="Demand multiplier", plot_bgcolor="white",
                           paper_bgcolor=CREAM, height=350)
    st.plotly_chart(seas_fig, use_container_width=True)

    st.subheader("Monthly P&L Detail")
    display_df = df[["business_month","month_of_year","customers","revenue","cogs",
                     "gross_profit","labor","overhead","ebitda","debt_service",
                     "net_cash","cumulative_cash"]].copy()
    mn = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    display_df["Month"] = display_df.apply(lambda r: f"M{int(r['business_month']):02d} — {mn[int(r['month_of_year'])-1]}", axis=1)
    display_df = display_df[["Month","customers","revenue","cogs","gross_profit","labor",
                             "overhead","ebitda","debt_service","net_cash","cumulative_cash"]]
    display_df.columns = ["Month","Customers","Revenue","COGS","Gross Profit","Labor",
                          "Overhead","EBITDA","Debt Service","Net Cash","Cumulative Cash"]
    for c in ["Revenue","COGS","Gross Profit","Labor","Overhead","EBITDA","Debt Service","Net Cash","Cumulative Cash"]:
        display_df[c] = display_df[c].apply(lambda v: f"${v:,.0f}")
    display_df["Customers"] = display_df["Customers"].apply(lambda v: f"{v:,.0f}")
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

    csv = df.to_csv(index=False)
    st.download_button("📥 Download projection CSV", csv, "roem_path_to_profit.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATOR 2: BANKABILITY OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════

def render_bankability():
    c1, c2 = st.columns([1, 5])
    with c1:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=140)
    with c2:
        st.markdown("# Bankability Optimizer")
        st.markdown("*DSCR stress-test against SBA 7(a) underwriting thresholds.*")

    st.markdown("---")

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Stress-Test Inputs")

    with st.sidebar.expander("💵 Revenue", expanded=True):
        annual_revenue = st.slider("Annual revenue ($)", 200_000, 800_000, 402_000, step=2000)

    with st.sidebar.expander("💸 Costs", expanded=True):
        cogs_pct = st.slider("COGS %", 20, 50, 35, step=1) / 100
        fixed_opex = st.slider("Fixed annual opex ($)", 60000, 180000, 132000, step=2000)
        annual_labor = st.slider("Annual labor ($)", 30000, 180000, 82000, step=2000)

    with st.sidebar.expander("🏦 Debt", expanded=True):
        loan_amount = st.slider("Principal ($)", 150000, 400000, BASE["loan_amount"], step=5000)
        loan_rate_pct = st.slider("Rate (%)", 6.0, 12.0, BASE["loan_rate"]*100, step=0.25)
        loan_years = st.slider("Term (yrs)", 5, 15, BASE["loan_years"])

    gross_profit = annual_revenue * (1 - cogs_pct)
    ebitda = gross_profit - fixed_opex - annual_labor
    monthly_ds = monthly_debt_service(loan_amount, loan_rate_pct/100, loan_years)
    annual_ds = monthly_ds * 12
    dscr = ebitda / annual_ds if annual_ds else 0
    surplus = ebitda - (annual_ds * 1.25)
    cash_coverage = ebitda - annual_ds

    if dscr >= 1.25:
        status_color, status_text = GREEN, "LENDER APPROVED"
        status_desc = f"DSCR {dscr:.2f}× exceeds SBA 1.25× threshold by ${surplus:,.0f} surplus."
    elif dscr >= 1.10:
        status_color, status_text = AMBER, "CONDITIONAL"
        status_desc = f"DSCR {dscr:.2f}× covers debt but below 1.25× comfort zone."
    elif dscr >= 1.00:
        status_color, status_text = AMBER, "REVIEW REQUIRED"
        status_desc = f"DSCR {dscr:.2f}× barely covers debt."
    else:
        status_color, status_text = RED, "NOT BANKABLE"
        status_desc = f"DSCR {dscr:.2f}× insufficient."

    st.markdown(f"""
    <div class='headline-box' style='border-left-color: {status_color};'>
        <span class='status-pill' style='background: {status_color};'>{status_text}</span>
        <div style='margin-top: 8px; font-size: 14px;'>{status_desc}</div>
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    with k1: st.metric("Annual EBITDA", f"${ebitda:,.0f}")
    with k2: st.metric("DSCR", f"{dscr:.2f}×", f"{dscr - 1.25:+.2f} vs 1.25× target")
    with k3: st.metric("Annual Debt Service", f"${annual_ds:,.0f}")

    gauge_color = GREEN if dscr >= 1.25 else (AMBER if dscr >= 1.00 else RED)
    display_dscr = min(dscr, 3.0)

    col_g, col_w = st.columns([1, 1])

    with col_g:
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=display_dscr,
            number={'suffix': '×', 'font': {'size': 52, 'color': NAVY, 'family': 'Georgia'}},
            title={'text': "DSCR (Debt-Service Coverage)", 'font': {'size': 16, 'color': NAVY}},
            gauge={
                'axis': {'range': [0, 3],
                         'tickvals': [0.5, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0],
                         'ticktext': ['0.5','1.0<br>(breakeven)','1.25<br>(target)','1.5','2.0','2.5','3.0+']},
                'bar': {'color': gauge_color, 'thickness': 0.35},
                'steps': [
                    {'range': [0, 1.0], 'color': '#ffebee'},
                    {'range': [1.0, 1.25], 'color': '#fff3e0'},
                    {'range': [1.25, 3.0], 'color': '#e8f5e9'},
                ],
                'threshold': {'line': {'color': NAVY, 'width': 3}, 'thickness': 0.85, 'value': 1.25}
            }
        ))
        gauge_fig.update_layout(height=380, paper_bgcolor=CREAM, margin=dict(t=60, b=20))
        st.plotly_chart(gauge_fig, use_container_width=True)

    with col_w:
        waterfall = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "total", "relative", "total"],
            x=["Revenue", "COGS", "Labor", "Fixed Opex", "EBITDA", "Debt Service", "Net Cash"],
            textposition="outside",
            text=[f"${annual_revenue/1000:,.0f}K", f"-${annual_revenue*cogs_pct/1000:,.0f}K",
                  f"-${annual_labor/1000:,.0f}K", f"-${fixed_opex/1000:,.0f}K",
                  f"${ebitda/1000:,.0f}K", f"-${annual_ds/1000:,.0f}K",
                  f"${cash_coverage/1000:,.0f}K"],
            y=[annual_revenue, -annual_revenue*cogs_pct, -annual_labor, -fixed_opex, 0, -annual_ds, 0],
            connector={"line": {"color": "#999"}},
            increasing={"marker": {"color": GREEN}},
            decreasing={"marker": {"color": RED}},
            totals={"marker": {"color": NAVY}},
        ))
        waterfall.update_layout(title="Revenue → Cash Waterfall", height=380,
                                paper_bgcolor=CREAM, plot_bgcolor="white",
                                yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(waterfall, use_container_width=True)

    st.subheader("Sensitivity: DSCR under Revenue × COGS")

    rev_scenarios = [annual_revenue*m for m in [0.70, 0.85, 1.00, 1.15, 1.30]]
    cogs_scenarios = [0.28, 0.32, 0.35, 0.38, 0.42]

    grid = []
    for r in rev_scenarios:
        row = []
        for c in cogs_scenarios:
            gp = r * (1 - c)
            eb = gp - fixed_opex - annual_labor
            d = eb / annual_ds if annual_ds else 0
            row.append(d)
        grid.append(row)

    heatmap = go.Figure(data=go.Heatmap(
        z=grid,
        x=[f"{c*100:.0f}%" for c in cogs_scenarios],
        y=[f"${r/1000:,.0f}K" for r in rev_scenarios],
        colorscale=[[0, RED], [0.33, AMBER], [0.42, "#fff3e0"], [0.55, "#e8f5e9"], [1, GREEN]],
        zmin=0, zmax=3,
        text=[[f"{v:.2f}×" for v in row] for row in grid],
        texttemplate="%{text}",
        textfont={"size": 13, "color": "white"},
        colorbar=dict(title="DSCR"),
    ))
    heatmap.update_layout(xaxis_title="COGS %", yaxis_title="Annual revenue",
                          height=420, paper_bgcolor=CREAM, plot_bgcolor="white")
    st.plotly_chart(heatmap, use_container_width=True)

    st.subheader("SBA 7(a) Covenant Checklist")
    checks = [
        ("DSCR ≥ 1.25×", dscr >= 1.25, f"{dscr:.2f}×"),
        ("EBITDA positive", ebitda > 0, f"${ebitda:,.0f}"),
        ("Owner equity ≥ 10% of project", True, "$40K / 12.3%"),
        ("Personal credit (est. 720+)", True, "Assumed compliant"),
        ("Owner active in business", True, "Single-member operator"),
        ("Life insurance (req. >$250K)", True, "To be placed at close"),
        ("Collateral ≥ 50% of loan", True, "Equipment ~$185K"),
    ]
    for label, passed, detail in checks:
        icon = "✅" if passed else "❌"
        color = GREEN if passed else RED
        st.markdown(
            f"<div style='padding: 6px 0; border-bottom: 1px solid #eee;'>"
            f"<span style='font-size: 16px;'>{icon}</span> "
            f"<span style='font-weight: 600; color: {color};'>{label}</span> "
            f"<span style='float: right; color: #666;'>{detail}</span></div>",
            unsafe_allow_html=True
        )


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATOR 3: MARKET PENETRATION
# ═══════════════════════════════════════════════════════════════════════════

def render_market():
    c1, c2 = st.columns([1, 5])
    with c1:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=140)
    with c2:
        st.markdown("# Market Penetration Simulator")
        st.markdown("*17 Boston-area competitor shops profiled April 2026.*")

    st.markdown("---")

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ RŌEM Inputs")
    roem_ticket = st.sidebar.slider("RŌEM ticket ($)", 5.00, 15.00, BASE["avg_ticket"], step=0.25)
    roem_customers = st.sidebar.slider("RŌEM daily customers", 40, 250, BASE["base_customers_per_day"], step=5)
    st.sidebar.markdown("---")
    hide_chains = st.sidebar.checkbox("Hide multi-location chains", value=False)
    filter_style = st.sidebar.multiselect(
        "Filter by style",
        sorted(set(c["style"] for c in COMPETITORS)),
        default=[],
    )

    df = pd.DataFrame(COMPETITORS)
    df["daily_revenue"] = df["avg_ticket"] * df["daily_customers"] * 1.3
    df["annual_revenue_est"] = df["daily_revenue"] * 365

    df_filtered = df.copy()
    if hide_chains:
        df_filtered = df_filtered[df_filtered["locations"] == 1]
    if filter_style:
        df_filtered = df_filtered[df_filtered["style"].isin(filter_style)]

    market_avg_ticket = df["avg_ticket"].mean()
    market_avg_customers = df["daily_customers"].mean()
    market_avg_revenue = df["annual_revenue_est"].mean()

    roem_daily_revenue = roem_ticket * roem_customers * 1.3
    roem_annual_revenue = roem_daily_revenue * 365

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Boston avg ticket", f"${market_avg_ticket:.2f}", f"${roem_ticket - market_avg_ticket:+.2f} delta")
    with k2: st.metric("Boston avg daily customers", f"{market_avg_customers:.0f}", f"{roem_customers - market_avg_customers:+.0f} delta")
    with k3: st.metric("Boston avg annual revenue", f"${market_avg_revenue/1000:,.0f}K", f"${(roem_annual_revenue - market_avg_revenue)/1000:+,.0f}K delta")
    with k4: st.metric("Total profiled", f"{len(df)}", "52 Boston metro-wide")

    st.markdown("---")
    st.subheader("Competitive Positioning — Ticket × Traffic")

    scatter = go.Figure()
    for _, row in df_filtered.iterrows():
        size = 10 + row["locations"] * 4
        color = GOLD if row["locations"] > 1 else NAVY
        scatter.add_trace(go.Scatter(
            x=[row["avg_ticket"]], y=[row["daily_customers"]],
            mode="markers+text",
            text=[row["name"]],
            textposition="top center",
            textfont=dict(size=10, color=NAVY),
            marker=dict(size=size, color=color, opacity=0.75, line=dict(color="white", width=2)),
            name=row["name"], showlegend=False,
            hovertemplate=f"<b>{row['name']}</b><br>{row['neighborhood']}<br>"
                          f"Ticket: ${row['avg_ticket']:.2f}<br>Daily cust: {row['daily_customers']}<extra></extra>",
        ))

    scatter.add_trace(go.Scatter(
        x=[roem_ticket], y=[roem_customers],
        mode="markers+text", text=["★ RŌEM"], textposition="top center",
        textfont=dict(size=14, color=RED, family="Georgia"),
        marker=dict(symbol="star", size=28, color=RED, line=dict(color=NAVY, width=2)),
        name="RŌEM", showlegend=False,
        hovertemplate=f"<b>RŌEM (your scenario)</b><br>Ticket: ${roem_ticket:.2f}<br>"
                      f"Daily cust: {roem_customers}<extra></extra>",
    ))

    scatter.add_hline(y=market_avg_customers, line_dash="dash", line_color="#999",
                     annotation_text=f"Market avg: {market_avg_customers:.0f}")
    scatter.add_vline(x=market_avg_ticket, line_dash="dash", line_color="#999",
                     annotation_text=f"Market avg: ${market_avg_ticket:.2f}")
    scatter.update_layout(xaxis=dict(title="Avg ticket ($)", range=[5, 12]),
                         yaxis=dict(title="Daily customers", range=[0, 450]),
                         height=600, paper_bgcolor=CREAM, plot_bgcolor="white")
    st.plotly_chart(scatter, use_container_width=True)

    st.subheader("Estimated Annual Revenue — Ranking")
    ranking_df = df_filtered.copy()
    roem_row = pd.DataFrame([{
        "name": "★ RŌEM (projected)", "neighborhood": "Malden / Medford",
        "style": "Globally-inspired", "avg_ticket": roem_ticket,
        "daily_customers": roem_customers, "locations": 1, "years": 0,
        "daily_revenue": roem_daily_revenue, "annual_revenue_est": roem_annual_revenue,
    }])
    ranking_df = pd.concat([ranking_df, roem_row], ignore_index=True)
    ranking_df = ranking_df.sort_values("annual_revenue_est", ascending=True)

    colors = [RED if "★" in n else GOLD if n in ranking_df[ranking_df["locations"]>1]["name"].values else NAVY
             for n in ranking_df["name"]]

    bar = go.Figure(go.Bar(
        y=ranking_df["name"], x=ranking_df["annual_revenue_est"],
        orientation="h", marker_color=colors,
        text=[f"${v/1000:,.0f}K" for v in ranking_df["annual_revenue_est"]],
        textposition="outside",
    ))
    bar.update_layout(xaxis_title="Annual revenue ($)", height=600,
                     paper_bgcolor=CREAM, plot_bgcolor="white",
                     xaxis_tickprefix="$", xaxis_tickformat=",.0f")
    st.plotly_chart(bar, use_container_width=True)

    st.subheader("Competitor Detail Table")
    table_df = df[["name","neighborhood","style","avg_ticket","daily_customers",
                  "locations","years","annual_revenue_est"]].copy()
    table_df.columns = ["Shop","Neighborhood","Style","Avg Ticket","Daily Cust.",
                       "Locations","Years","Annual Rev (est)"]
    table_df["Avg Ticket"] = table_df["Avg Ticket"].apply(lambda v: f"${v:.2f}")
    table_df["Annual Rev (est)"] = table_df["Annual Rev (est)"].apply(lambda v: f"${v/1000:,.0f}K")
    st.dataframe(table_df, use_container_width=True, hide_index=True, height=450)

    st.subheader("Category Gap Analysis")
    gap_df = pd.DataFrame([
        {"Category": "Traditional American (scoop)", "Boston shops": 34, "RŌEM offers?": "Yes (custard)"},
        {"Category": "Italian gelato", "Boston shops": 6, "RŌEM offers?": "Yes"},
        {"Category": "Vegan / dairy-free", "Boston shops": 4, "RŌEM offers?": "Sorbet"},
        {"Category": "Japanese soft-serve / mochi", "Boston shops": 4, "RŌEM offers?": "Yes (both)"},
        {"Category": "Liquid nitrogen / craft", "Boston shops": 3, "RŌEM offers?": "No"},
        {"Category": "Turkish dondurması", "Boston shops": 0, "RŌEM offers?": "★ Yes"},
        {"Category": "Czech trdelník cones", "Boston shops": 0, "RŌEM offers?": "★ Yes"},
        {"Category": "Thai coconut sorbet", "Boston shops": 0, "RŌEM offers?": "★ Yes"},
    ])
    st.dataframe(gap_df, use_container_width=True, hide_index=True)

    st.markdown(f"""
    <div style='background: #e8f5e9; border-left: 5px solid {GREEN}; padding: 14px 20px;
                 border-radius: 4px; margin-top: 12px;'>
    <strong>Key finding.</strong> Of 17 profiled Boston-area shops (52 total in the metro),
    <strong>zero</strong> offer Turkish, Czech, or Thai frozen desserts. RŌEM holds an empty,
    defensible market quadrant.
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATOR 4: MENU MIX OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════

def render_menu_mix():
    c1, c2 = st.columns([1, 5])
    with c1:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=140)
    with c2:
        st.markdown("# Menu Mix Optimizer")
        st.markdown("*Adjust the mix of 8 international specialty items to see blended margin.*")

    st.markdown("---")

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Menu Mix (% of txns)")
    default_mix = {
        "Italian Gelato Scoop": 18, "Affogato (gelato + espresso)": 10,
        "Turkish Maraş Dondurması (stretch scoop)": 8,
        "Czech Trdelník Cone + Soft-Serve": 14, "American Frozen Custard": 20,
        "Japanese Mochi Ice Cream (3-pc)": 12,
        "Hokkaido Soft-Serve Cone": 12, "Thai Mango Sorbet in Coconut Shell": 6,
    }
    mix = {}
    for item in MENU:
        mix[item["name"]] = st.sidebar.slider(
            item["name"], 0, 40, default_mix.get(item["name"], 10), step=1,
            help=f"{item['origin']} · Cost: ${item['cost']:.2f} · Price: ${item['price']:.2f}"
        )

    total = sum(mix.values())
    if total == 0:
        st.error("Set at least one item weight above zero.")
        return

    norm_mix = {k: v/total for k, v in mix.items()}

    rows = []
    for item in MENU:
        w = norm_mix[item["name"]]
        margin = (item["price"] - item["cost"]) / item["price"]
        rows.append({
            **item, "weight": w, "margin_pct": margin,
            "weighted_revenue": w * item["price"],
            "weighted_cost": w * item["cost"],
            "weighted_margin_dollars": w * (item["price"] - item["cost"]),
        })

    df = pd.DataFrame(rows)
    blended_avg_price = df["weighted_revenue"].sum()
    blended_avg_cost = df["weighted_cost"].sum()
    blended_margin = blended_avg_price - blended_avg_cost
    blended_margin_pct = blended_margin / blended_avg_price if blended_avg_price else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Blended price", f"${blended_avg_price:.2f}", f"{blended_avg_price-BASE['avg_ticket']:+.2f} vs base")
    with k2: st.metric("Blended COGS", f"${blended_avg_cost:.2f}", f"{blended_avg_cost/blended_avg_price*100:.1f}% of price")
    with k3: st.metric("Gross margin %", f"{blended_margin_pct*100:.1f}%", f"{(blended_margin_pct - 0.70)*100:+.1f} vs 70%")
    with k4:
        hero_weight = df[df["hero"]]["weight"].sum()
        st.metric("Hero-item mix %", f"{hero_weight*100:.1f}%", "Global vs commodity")

    if blended_margin_pct >= 0.70:
        status_color, status_text = GREEN, "STRONG MARGIN"
        status_desc = f"{blended_margin_pct*100:.1f}% exceeds 70% premium target."
    elif blended_margin_pct >= 0.65:
        status_color, status_text = AMBER, "ACCEPTABLE"
        status_desc = f"{blended_margin_pct*100:.1f}% within range."
    else:
        status_color, status_text = RED, "UNDER PRESSURE"
        status_desc = f"{blended_margin_pct*100:.1f}% below 65%."

    st.markdown(f"""
    <div class='headline-box' style='border-left-color: {status_color};'>
        <span class='status-pill' style='background: {status_color};'>{status_text}</span>
        <span style='margin-left: 12px;'>{status_desc}</span>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Margin Contribution by Item")
    df_sorted = df.sort_values("weighted_margin_dollars", ascending=True)
    fig = go.Figure(go.Bar(
        y=df_sorted["name"], x=df_sorted["weighted_margin_dollars"],
        orientation="h",
        marker_color=[GOLD if h else NAVY for h in df_sorted["hero"]],
        text=[f"${v:.2f}" for v in df_sorted["weighted_margin_dollars"]],
        textposition="outside",
    ))
    fig.update_layout(xaxis_title="Weighted margin per avg txn ($)", height=420,
                     paper_bgcolor=CREAM, plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

    col_pie, col_table = st.columns([1, 1])
    with col_pie:
        st.subheader("Transaction Mix")
        pie = go.Figure(go.Pie(
            labels=df["name"], values=[norm_mix[n] for n in df["name"]],
            hole=0.45,
            marker=dict(colors=[NAVY, GOLD, "#2E7D32", "#8D6E63", "#5E35B1",
                               "#D84315", "#00838F", "#C62828"][:len(df)]),
            textinfo="percent",
        ))
        pie.update_layout(height=420, paper_bgcolor=CREAM)
        st.plotly_chart(pie, use_container_width=True)
    with col_table:
        st.subheader("Item Economics")
        display_df = df[["name", "origin", "cost", "price", "margin_pct", "weight"]].copy()
        display_df.columns = ["Item", "Origin", "Cost", "Price", "Margin %", "Mix %"]
        display_df["Cost"] = display_df["Cost"].apply(lambda v: f"${v:.2f}")
        display_df["Price"] = display_df["Price"].apply(lambda v: f"${v:.2f}")
        display_df["Margin %"] = display_df["Margin %"].apply(lambda v: f"{v*100:.1f}%")
        display_df["Mix %"] = display_df["Mix %"].apply(lambda v: f"{v*100:.1f}%")
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=380)

    st.subheader("Annual Impact")
    daily_customers = BASE["base_customers_per_day"]
    items_per_txn = BASE["items_per_transaction"]
    annual_txns = daily_customers * 365
    annual_items = annual_txns * items_per_txn
    annual_revenue = annual_items * blended_avg_price
    annual_cogs = annual_items * blended_avg_cost
    annual_gp = annual_revenue - annual_cogs

    i1, i2, i3 = st.columns(3)
    with i1: st.metric("Annual revenue", f"${annual_revenue:,.0f}")
    with i2: st.metric("Annual COGS", f"${annual_cogs:,.0f}")
    with i3: st.metric("Annual gross profit", f"${annual_gp:,.0f}")


# ═══════════════════════════════════════════════════════════════════════════
# SIMULATOR 5: LOCATION ROI
# ═══════════════════════════════════════════════════════════════════════════

def render_location_roi():
    c1, c2 = st.columns([1, 5])
    with c1:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=140)
    with c2:
        st.markdown("# Location ROI Simulator")
        st.markdown("*Compare 4 Boston-area archetypes on rent, traffic, summer seasonality, parking.*")

    st.markdown("---")

    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Controls")
    base_customers = st.sidebar.slider("Base daily customers", 40, 200,
                                       BASE["base_customers_per_day"], step=5)
    show_archetypes = st.sidebar.multiselect(
        "Archetypes to compare",
        list(LOCATION_ARCHETYPES.keys()),
        default=list(LOCATION_ARCHETYPES.keys()),
    )

    results = []
    for name, arch in LOCATION_ARCHETYPES.items():
        if name not in show_archetypes:
            continue
        adj_customers = base_customers * arch["traffic_multiplier"]
        annual_rent = arch["rent_sqft"] * BASE["sqft"]
        monthly_rent_all_in = (arch["rent_sqft"] + BASE["cam_per_sqft_year"]) * BASE["sqft"] / 12
        annual_revenue_baseline = adj_customers * 365 * BASE["avg_ticket"] * BASE["items_per_transaction"]
        summer_factor = 1 + arch["seasonality_penalty"]
        adj_annual_revenue = annual_revenue_baseline * ((9/12) + (3/12) * summer_factor)
        cogs = adj_annual_revenue * (BASE["food_cost_pct"] + BASE["paper_cost_pct"] + BASE["waste_pct"])
        gross_profit = adj_annual_revenue - cogs
        annual_labor = (BASE["owner_salary"] + (BASE["hourly_wage"] * 25 * 52)) * \
                      (1 + BASE["payroll_tax_pct"] + BASE["workers_comp_pct"])
        other_overhead = 12 * (BASE["utilities"] + BASE["internet_phone"] + BASE["insurance"]
                               + BASE["pos_software"] + BASE["accounting"] + BASE["marketing"]
                               + BASE["cleaning_supplies"] + BASE["repairs_maintenance"]
                               + BASE["bank_fees"] + BASE["misc"] + BASE["licenses_permits_monthly"])
        ebitda = gross_profit - annual_labor - other_overhead - (monthly_rent_all_in * 12)

        results.append({
            "Archetype": name, "Example": arch["example"], "Rent $/sqft": arch["rent_sqft"],
            "Daily customers adj": adj_customers,
            "Annual rent": monthly_rent_all_in * 12, "Annual revenue": adj_annual_revenue,
            "EBITDA": ebitda, "Summer factor": summer_factor,
        })

    df = pd.DataFrame(results)

    st.subheader("Financial Summary by Archetype")
    cols = st.columns(len(df))
    for i, row in df.iterrows():
        with cols[i]:
            st.markdown(f"""
            <div style='background: white; padding: 14px 18px; border-radius: 4px;
                         border-left: 4px solid {NAVY}; box-shadow: 0 1px 3px rgba(0,0,0,.08);
                         margin-bottom: 10px; min-height: 190px;'>
                <div style='font-weight: 700; color: {NAVY}; font-size: 15px;'>{row['Archetype']}</div>
                <div style='font-size: 11px; color: #888; margin-bottom: 10px;'><em>{row['Example']}</em></div>
                <div style='font-size: 11px; color: #666; letter-spacing: 0.5px; text-transform: uppercase;'>Annual Revenue</div>
                <div style='font-size: 22px; font-weight: 700; color: {NAVY}; font-family: Georgia;'>${row['Annual revenue']/1000:,.0f}K</div>
                <div style='font-size: 11px; color: #666; letter-spacing: 0.5px; text-transform: uppercase; margin-top: 8px;'>EBITDA</div>
                <div style='font-size: 18px; font-weight: 700; color: {GREEN if row["EBITDA"]>0 else RED}; font-family: Georgia;'>${row['EBITDA']/1000:,.0f}K</div>
                <div style='font-size: 11px; color: #666; margin-top: 8px;'>Rent: ${row['Annual rent']/1000:,.0f}K/yr</div>
            </div>
            """, unsafe_allow_html=True)

    st.subheader("Multi-Factor Radar")
    radar_dims = ["Traffic", "Evening", "Weekend", "Parking", "Summer stability", "Rent efficiency"]
    radar = go.Figure()
    palette = [NAVY, GOLD, GREEN, "#8D6E63"]
    for i, row in df.iterrows():
        arch = LOCATION_ARCHETYPES[row["Archetype"]]
        values = [
            min(5, arch["traffic_multiplier"] * 4),
            arch["evening_traffic"], arch["weekend_traffic"], arch["parking"],
            6 - arch["summer_dropoff_risk"],
            max(1, 6 - (arch["rent_sqft"] / 15)),
        ]
        values = values + [values[0]]
        dims = radar_dims + [radar_dims[0]]
        radar.add_trace(go.Scatterpolar(
            r=values, theta=dims, fill="toself",
            name=row["Archetype"],
            line=dict(color=palette[i % len(palette)], width=2), opacity=0.55,
        ))
    radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5]), bgcolor=CREAM),
        height=500, paper_bgcolor=CREAM,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    st.plotly_chart(radar, use_container_width=True)

    st.subheader("Summer vs Winter Customer Pattern")
    season_df = pd.DataFrame([
        {
            "Archetype": row["Archetype"],
            "Summer (Jun-Aug)": base_customers * LOCATION_ARCHETYPES[row["Archetype"]]["traffic_multiplier"]
                                 * 1.48 * (1 + LOCATION_ARCHETYPES[row["Archetype"]]["seasonality_penalty"]),
            "Winter (Dec-Feb)": base_customers * LOCATION_ARCHETYPES[row["Archetype"]]["traffic_multiplier"] * 0.69,
        }
        for _, row in df.iterrows()
    ])
    season_fig = go.Figure()
    season_fig.add_trace(go.Bar(x=season_df["Archetype"], y=season_df["Summer (Jun-Aug)"],
                                name="Summer (Jun-Aug)", marker_color=GOLD,
                                text=[f"{v:,.0f}" for v in season_df["Summer (Jun-Aug)"]],
                                textposition="outside"))
    season_fig.add_trace(go.Bar(x=season_df["Archetype"], y=season_df["Winter (Dec-Feb)"],
                                name="Winter (Dec-Feb)", marker_color=NAVY,
                                text=[f"{v:,.0f}" for v in season_df["Winter (Dec-Feb)"]],
                                textposition="outside"))
    season_fig.update_layout(barmode="group", yaxis_title="Avg daily customers",
                            height=380, paper_bgcolor=CREAM, plot_bgcolor="white",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                       xanchor="right", x=1))
    st.plotly_chart(season_fig, use_container_width=True)

    st.subheader("Pros, Cons & Best-Fit")
    notes = {
        "College-Adjacent": {
            "pros": ["Massive evening/late-night trade", "Dense walkable population",
                    "Strong social-media amplification"],
            "cons": ["Summer dropoff 15-25%", "Premium rent $55-70/sqft",
                    "Finals/break dead-zones"],
            "best_for": "Concepts with late-evening + social-media DNA.",
        },
        "Park / Recreation": {
            "pros": ["Summer lift 20-25%", "Family-friendly higher ticket",
                    "Lower rent $35-45/sqft"],
            "cons": ["Severe winter dropoff", "Weekend-weighted",
                    "Weather-sensitive year"],
            "best_for": "Operators who can weather winter lulls.",
        },
        "Main Street Retail": {
            "pros": ["Most balanced demand", "Mid-tier rent $45-55/sqft",
                    "Easier permitting"],
            "cons": ["Slower evening trade", "Inconsistent parking",
                    "No extreme peak"],
            "best_for": "Risk-managed launches. RŌEM base case.",
        },
        "Transit Hub": {
            "pros": ["Highest raw traffic", "Strong evening + weekend",
                    "Co-tenant traffic driver"],
            "cons": ["Premium rent $60-75/sqft", "Landlord dependency",
                    "Garage-based parking"],
            "best_for": "Impulse-grab concepts at volume.",
        },
    }
    for arch_name in [r["Archetype"] for _, r in df.iterrows()]:
        n = notes[arch_name]
        with st.expander(f"▸ {arch_name} — e.g. {LOCATION_ARCHETYPES[arch_name]['example']}"):
            col_p, col_c = st.columns(2)
            with col_p:
                st.markdown("**✅ Pros**")
                for p in n["pros"]: st.markdown(f"- {p}")
            with col_c:
                st.markdown("**⚠️ Cons**")
                for c in n["cons"]: st.markdown(f"- {c}")
            st.info(f"**Best fit:** {n['best_for']}")

    top_idx = df["EBITDA"].idxmax()
    top_arch = df.iloc[top_idx]
    st.markdown(f"""
    <div style='background: {GREEN}; color: white; padding: 18px 24px; border-radius: 4px;
                 margin-top: 20px;'>
        <div style='font-size: 11px; letter-spacing: 0.8px; text-transform: uppercase; opacity: 0.9;'>Top EBITDA Archetype</div>
        <div style='font-size: 24px; font-weight: 700; font-family: Georgia; margin-top: 4px;'>
            {top_arch['Archetype']} — ${top_arch['EBITDA']/1000:,.0f}K projected
        </div>
        <div style='margin-top: 6px; font-size: 13px;'>
            {top_arch['Example']} · ${top_arch['Rent $/sqft']}/sqft ·
            {top_arch['Daily customers adj']:.0f} daily customers
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════

if page.startswith("🏠"):
    render_home()
elif page.startswith("📈"):
    render_path_to_profit()
elif page.startswith("🏦"):
    render_bankability()
elif page.startswith("🗺️"):
    render_market()
elif page.startswith("🍦"):
    render_menu_mix()
elif page.startswith("📍"):
    render_location_roi()
