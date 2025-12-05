# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from pdf_report import generate_pdf_report
from apputil import load_data_via_uploader

# ---------- PDF EXPORT FUNCTION ----------
def df_to_pdf(df):
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=landscape(letter))

    # Convert DataFrame to table data
    data = [df.columns.tolist()] + df.values.tolist()

    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.black),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
        ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
    ]))

    pdf.build([table])
    buffer.seek(0)
    return buffer
# -----------------------------------------


st.set_page_config(page_title="Measles/Rubella Dashboard", layout="wide", initial_sidebar_state="expanded")

# Initialize session state for country selection
if "selected_country" not in st.session_state:
    st.session_state.selected_country = None

# Header with description
st.markdown("<h1 style='text-align:center; font-size:44px; margin-bottom:10px;'>Measles & Rubella Interactive Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#666; font-size:16px;'>Explore global disease trends, regional patterns, and country-specific insights</p>", unsafe_allow_html=True)

# Load data via uploader
base_wide, base_long = load_data_via_uploader()

# Sidebar filters
st.sidebar.header("🎛️ Filters")
disease_options = ["Measles","Rubella","Both"]
if {"Measles_per100k","Rubella_per100k"}.issubset(set(base_long["disease"].unique())):
    disease_options += ["Measles_per100k","Rubella_per100k"]
disease_sel = st.sidebar.selectbox("📊 Disease metric", disease_options, index=0)

years_all = sorted([int(y) for y in base_long["year"].dropna().unique().tolist()])
yr_min, yr_max = (years_all[0], years_all[-1]) if years_all else (2012, 2025)
year_range = st.sidebar.slider("📅 Year range", min_value=int(yr_min), max_value=int(yr_max), value=(int(yr_min), int(yr_max)), step=1)

regions = sorted(base_long["region"].dropna().unique().tolist())
regions_sel = st.sidebar.multiselect("🌍 Regions", regions, default=regions)

st.sidebar.markdown("---")
st.sidebar.subheader("📈 Analysis Options")
top_n = st.sidebar.number_input("Top N countries", min_value=5, max_value=50, value=10, step=1)
roll_window = st.sidebar.select_slider("Rolling window (years)", options=[1,3,5,7], value=3)
show_yoy = st.sidebar.checkbox("Show YoY growth", value=True)

# Helpers
def apply_filters(long_df, disease_sel, regions, year_range):
    df = long_df.copy()
    if disease_sel == "Both":
        df = df[df["disease"].isin(["Measles","Rubella"])]
    else:
        df = df[df["disease"] == disease_sel]
    df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]
    if regions:
        df = df[df["region"].isin(regions)]
    return df

def fmt_pct(x):
    return "—" if pd.isna(x) else f"{x*100:.1f}%"

def fmt_number(x):
    if x >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    elif x >= 1_000:
        return f"{x/1_000:.1f}K"
    return f"{int(x)}"

long_f = apply_filters(base_long, disease_sel, regions_sel, year_range)

# Preview (collapsible)
with st.expander("🔍 Preview data"):
    st.dataframe(base_wide.head(20), use_container_width=True)

# KPI section with better styling
st.markdown("### 📊 Key Metrics")
kcol1, kcol2, kcol3, kcol4, kcol5 = st.columns(5)
tot_period = long_f["value"].sum() if not long_f.empty else 0
latest_year = int(long_f["year"].max()) if not long_f.empty else None
latest_total = long_f[long_f["year"]==latest_year]["value"].sum() if latest_year else 0
prev_total = long_f[long_f["year"]==latest_year-1]["value"].sum() if latest_year and (latest_year-1) in long_f["year"].unique() else np.nan
yoy_latest = (latest_total/prev_total-1) if prev_total and prev_total>0 else np.nan

# Calculate average cases per year
avg_per_year = tot_period / len(long_f["year"].unique()) if not long_f.empty else 0

with kcol1: 
    st.metric("Total Cases", fmt_number(tot_period), help="Total cases in selected period")
with kcol2: 
    st.metric(f"Cases in {latest_year if latest_year else '—'}", fmt_number(latest_total) if latest_year else "—")
with kcol3: 
    st.metric("YoY Change", fmt_pct(yoy_latest), delta=fmt_pct(yoy_latest) if not pd.isna(yoy_latest) else None)
with kcol4: 
    st.metric("Countries", f"{long_f['country'].nunique():,}", help="Number of countries with data")
with kcol5:
    st.metric("Avg/Year", fmt_number(avg_per_year), help="Average cases per year")

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🌐 Global & Regional", "🗺️ Geographic Analysis", "🔍 Country Deep Dive", "⚠️ Anomaly Detection"])

# --- Tab 1 content omitted for brevity (same as your code) ---
# --- Tab 2 content ---
# --- Tab 3 content ---
# --- Tab 4 content ---
# (Everything unchanged except download section)

# Download section
st.markdown("---")
st.subheader("💾 Download Data")

if not long_f.empty:
    col1, col2, col3 = st.columns([3,1,1])

    with col1:
        st.write(f"Download filtered dataset ({len(long_f):,} rows)")

    # CSV download button
  #  with col2:
  #      st.download_button(
  #          "📥 CSV",
  #          data=long_f.sort_values(["country","region","disease","year"]).to_csv(index=False).encode("utf-8"),
  #          file_name=f"measles_rubella_{disease_sel}_{year_range[0]}-{year_range[1]}.csv",
  #          mime="text/csv",
  #          use_container_width=True
  #      )

    # PDF download button
    #with col3:
    #    pdf_buffer = generate_pdf_report(long_f.sort_values(["country","region","disease","year"]))
    #    st.download_button(
    #        "📄 PDF",
    #        data=pdf_buffer,
    #        file_name=f"measles_rubella_{disease_sel}_{year_range[0]}-{year_range[1]}.pdf",
    #        mime="application/pdf",
    #        use_container_width=True
    #    )
csv_data = base_long.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download CSV",
    data=csv_data,
    file_name="measles_rubella_long.csv",
    mime="text/csv"
)

# PDF download button — new addition
pdf_bytes = generate_pdf_report(base_wide, base_long)
st.download_button(
    label="Download PDF",
    data=pdf_bytes,
    file_name="measles_rubella_report.pdf",
    mime="application/pdf"
)

