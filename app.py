# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF
import io
import plotly.io as pio
from PIL import Image

from apputil import load_data_via_uploader

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

# Create tabs for better organization
tab1, tab2, tab3, tab4 = st.tabs(["🌐 Global & Regional", "🗺️ Geographic Analysis", "🔍 Country Deep Dive", "⚠️ Anomaly Detection"])

with tab1:
    # 1) Global Trends
    st.subheader("📈 Global Trend Over Time")
    global_agg = (long_f.groupby(["disease","year"], as_index=False)["value"].sum().sort_values("year"))
    if not global_agg.empty:
        if disease_sel == "Both":
            g = global_agg.groupby("year", as_index=False)["value"].sum()
            g["rolling"] = g["value"].rolling(roll_window, min_periods=1).mean()
            g["yoy"] = g["value"].pct_change()
            title = "Global Cases (Measles + Rubella)"
        else:
            g = global_agg[global_agg["disease"]==disease_sel][["year","value"]].copy()
            g["rolling"] = g["value"].rolling(roll_window, min_periods=1).mean()
            g["yoy"] = g["value"].pct_change()
            title = f"Global Cases ({disease_sel})"
        
        fig_global = go.Figure()
        fig_global.add_trace(go.Bar(x=g["year"], y=g["value"], name="Annual Cases", 
                                    marker_color="#e3f2fd", marker_line_color="#1976d2", marker_line_width=1))
        if roll_window > 1:
            fig_global.add_trace(go.Scatter(x=g["year"], y=g["rolling"], name=f"{roll_window}Y Rolling Avg", 
                                            mode="lines+markers", line=dict(color="#d32f2f", width=3),
                                            marker=dict(size=6)))
        if show_yoy:
            fig_global.add_trace(go.Scatter(x=g["year"], y=g["yoy"], name="YoY Growth", mode="lines+markers",
                                            line=dict(color="#1976d2", width=2, dash="dash"), 
                                            marker=dict(size=5), yaxis="y2"))
            fig_global.update_layout(
                yaxis2=dict(title="YoY Growth Rate", overlaying="y", side="right", tickformat=".0%",
                           showgrid=False)
            )
        fig_global.update_layout(
            title=title, height=450, 
            margin=dict(l=20,r=20,t=50,b=10), 
            yaxis=dict(title="Number of Cases"),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_global, use_container_width=True)
    else:
        st.info("No data for selected filters.")

    # 2) Regional Trends
    st.subheader("🌍 Regional Trends")
    reg_agg = (long_f.groupby(["region","year"], as_index=False)["value"].sum().sort_values(["region","year"]))
    if not reg_agg.empty:
        reg_agg["rolling"] = reg_agg.groupby("region")["value"].transform(lambda s: s.rolling(roll_window, min_periods=1).mean())
        
        fig_reg = go.Figure()
        colors = px.colors.qualitative.Set2
        for idx, reg in enumerate(reg_agg["region"].unique()):
            dreg = reg_agg[reg_agg["region"]==reg]
            color = colors[idx % len(colors)]
            # Actual values
            fig_reg.add_trace(go.Scatter(
                x=dreg["year"], y=dreg["value"], name=reg,
                mode="lines+markers", line=dict(color=color, width=2),
                marker=dict(size=6)
            ))
            # Rolling average (dotted)
            if roll_window > 1:
                fig_reg.add_trace(go.Scatter(
                    x=dreg["year"], y=dreg["rolling"], 
                    name=f"{reg} (avg)", mode="lines", 
                    line=dict(color=color, width=2, dash="dot"),
                    showlegend=False, opacity=0.6
                ))
        
        fig_reg.update_layout(
            height=450, 
            margin=dict(l=20,r=20,t=10,b=10),
            yaxis=dict(title="Cases"),
            xaxis=dict(title="Year"),
            hovermode="x unified",
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="right", x=1)
        )
        st.plotly_chart(fig_reg, use_container_width=True)
    else:
        st.info("No regional data for selected filters.")

with tab2:
    col_rank, col_map = st.columns([1, 1.5])
    
    with col_rank:
        # 3) Country Rankings
        st.subheader("Countries with Highest Reported Cases")
        rank_df = (long_f.groupby("country", as_index=False)["value"].sum().sort_values("value", ascending=False))
        show_top = rank_df.head(int(top_n))
        
        if not show_top.empty:
            fig_bar = px.bar(
                show_top, y="country", x="value", 
                orientation="h",
                labels={"value":"Total Cases", "country":"Country"},
                title=f"Highest reported cases in top {min(int(top_n), len(show_top))} countries",
                color="value",
                color_continuous_scale="Reds"
            )
            fig_bar.update_layout(
                height=600, 
                margin=dict(l=20,r=20,t=50,b=10),
                showlegend=False,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No ranking data available.")
    
    with col_map:
        # 4) Choropleth Map
        st.subheader("🗺️ Geographic Distribution")
        st.info("⚠️ Note: Some countries/territories may not appear on the map due to naming variations or political recognition issues in the geographic database. All countries remain available in rankings and country-specific analysis.")
        map_year = st.slider("Select year", min_value=year_range[0], max_value=year_range[1], value=year_range[1], step=1)
        map_df = long_f[long_f["year"]==map_year].groupby("country", as_index=False)["value"].sum()
        
        if not map_df.empty:
            fig_map = px.choropleth(
                map_df, locations="country", locationmode="country names",
                color="value", color_continuous_scale="YlOrRd",
                hover_name="country", hover_data={"value":":,.0f"},
                title=f"{disease_sel if disease_sel!='Both' else 'Measles + Rubella'} Cases in {map_year}",
                labels={"value": "Cases"}
            )
            fig_map.update_layout(
                height=600, 
                margin=dict(l=20,r=20,t=50,b=10),
                geo=dict(showframe=True, framecolor="#1976d2", framewidth=2, showcoastlines=True, projection_type='orthographic')
            )
            fig_map.update_traces(marker_line_width=1.0, marker_line_color="#333333")
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("No data for selected map year.")

with tab3:
    # 5) Country Trend
    st.subheader("📊 Country-Specific Analysis")
    rank_df = (long_f.groupby("country", as_index=False)["value"].sum().sort_values("value", ascending=False))
    
    col1, col2 = st.columns([2, 1])
    with col1:
        sel_cty = st.selectbox("Select a country", rank_df["country"].tolist() if not rank_df.empty else [], key="country_select")
    with col2:
        show_comparison = st.checkbox("Compare with global average", value=False)
    
    if sel_cty:
        cty_ts = (long_f[long_f["country"]==sel_cty].groupby("year", as_index=False)["value"].sum().sort_values("year"))
        
        if not cty_ts.empty:
            cty_ts["rolling"] = cty_ts["value"].rolling(roll_window, min_periods=1).mean()
            cty_ts["yoy"] = cty_ts["value"].pct_change()
            
            # Main chart
            fig_cty = go.Figure()
            fig_cty.add_trace(go.Bar(
                x=cty_ts["year"], y=cty_ts["value"], name="Annual Cases",
                marker_color="#bbdefb", marker_line_color="#1976d2", marker_line_width=1
            ))
            fig_cty.add_trace(go.Scatter(
                x=cty_ts["year"], y=cty_ts["rolling"], name=f"{roll_window}Y Rolling Avg",
                line=dict(color="#d32f2f", width=3), mode="lines+markers",
                marker=dict(size=6)
            ))
            
            # Add global average comparison if requested
            if show_comparison:
                global_avg = long_f.groupby("year", as_index=False)["value"].mean()
                global_avg = global_avg[global_avg["year"].isin(cty_ts["year"])]
                fig_cty.add_trace(go.Scatter(
                    x=global_avg["year"], y=global_avg["value"], 
                    name="Global Avg (per country)",
                    line=dict(color="#ff9800", width=2, dash="dash"),
                    mode="lines"
                ))
            
            if show_yoy:
                fig_cty.add_trace(go.Scatter(
                    x=cty_ts["year"], y=cty_ts["yoy"], name="YoY Growth", yaxis="y2",
                    line=dict(color="#1976d2", dash="dash", width=2),
                    mode="lines+markers", marker=dict(size=5)
                ))
                fig_cty.update_layout(
                    yaxis2=dict(title="YoY Growth Rate", overlaying="y", side="right", 
                               tickformat=".0%", showgrid=False)
                )
            
            fig_cty.update_layout(
                title=f"<b>{sel_cty}</b> - {disease_sel if disease_sel!='Both' else 'Measles + Rubella'}",
                height=500, 
                margin=dict(l=20,r=20,t=50,b=10), 
                yaxis=dict(title="Number of Cases"),
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_cty, use_container_width=True)
            
            # Summary statistics for selected country
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Cases", f"{int(cty_ts['value'].sum()):,}")
            with col2:
                st.metric("Peak Year", f"{int(cty_ts.loc[cty_ts['value'].idxmax(), 'year'])}")
            with col3:
                st.metric("Peak Cases", f"{int(cty_ts['value'].max()):,}")
            with col4:
                avg_annual = cty_ts['value'].mean()
                st.metric("Avg Annual", f"{int(avg_annual):,}")
        else:
            st.info(f"No data available for {sel_cty} in selected period.")
    
    # Country Comparison Tool
    st.markdown("---")
    with st.expander("⚖️ Country Comparison Tool", expanded=False):
        st.write("Compare multiple countries side-by-side")
        
        available_countries = rank_df["country"].tolist() if not rank_df.empty else []
        
        compare_countries = st.multiselect(
            "Select countries to compare (2-5 recommended)",
            available_countries,
            default=available_countries[:3] if len(available_countries) >= 3 else available_countries
        )
        
        if compare_countries and len(compare_countries) >= 2:
            comparison_data = long_f[long_f["country"].isin(compare_countries)]
            yearly_comparison = comparison_data.groupby(["country", "year"])["value"].sum().reset_index()
            
            # Line chart comparison
            fig_compare = px.line(
                yearly_comparison, 
                x="year", 
                y="value", 
                color="country",
                markers=True,
                labels={"value": "Cases", "year": "Year"},
                title="Side-by-Side Country Comparison"
            )
            fig_compare.update_layout(
                height=400,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig_compare, use_container_width=True)
            
            # Summary statistics table
            st.write("#### Comparison Statistics")
            comp_stats = []
            for country in compare_countries:
                country_data = yearly_comparison[yearly_comparison["country"] == country]["value"]
                comp_stats.append({
                    "Country": country,
                    "Total": f"{int(country_data.sum()):,}",
                    "Average": f"{int(country_data.mean()):,}",
                    "Peak": f"{int(country_data.max()):,}",
                    "Min": f"{int(country_data.min()):,}",
                    "Std Dev": f"{int(country_data.std()):,}"
                })
            st.dataframe(pd.DataFrame(comp_stats), use_container_width=True, hide_index=True)
        else:
            st.info("Select at least 2 countries to compare")

with tab4:
    # 6) Anomaly Detection
    st.subheader("🔍 Anomaly Detection")
    st.markdown("Detect unusual patterns in disease case data using Isolation Forest algorithm")

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚠️ Anomaly Detection")
    run_anomaly = st.sidebar.checkbox("Enable anomaly detection", value=False)
    contamination = st.sidebar.slider("Contamination (expected % anomalies)", min_value=0.05, max_value=0.3, value=0.1, step=0.05)

    if run_anomaly:
        try:
            from anomaly_detector import detect_anomalies_for_country
            
            st.write("### Country-specific anomaly analysis")
            anomaly_country = st.selectbox("Select country for anomaly analysis", 
                                           rank_df["country"].tolist() if not rank_df.empty else [],
                                           key="anomaly_country_select")
            
            if anomaly_country:
                with st.spinner(f"Running anomaly detection for {anomaly_country}..."):
                    anomaly_result = detect_anomalies_for_country(base_wide, anomaly_country, contamination)
                
                if anomaly_result is not None and not anomaly_result.empty:
                    fig_anom = go.Figure()
                    if "measles" in anomaly_result:
                        fig_anom.add_trace(go.Scatter(
                            x=anomaly_result["year"], y=anomaly_result["measles"],
                            mode="lines+markers", name="Measles cases",
                            line=dict(color="#1f77b4", width=2)
                        ))
                        if "measles_anomaly" in anomaly_result:
                            anom_m = anomaly_result[anomaly_result["measles_anomaly"] == -1]
                            fig_anom.add_trace(go.Scatter(
                                x=anom_m["year"], y=anom_m["measles"],
                                mode="markers", name="Measles anomaly",
                                marker=dict(size=14, color="red", symbol="x", line=dict(width=2))
                            ))
                    if "rubella" in anomaly_result:
                        fig_anom.add_trace(go.Scatter(
                            x=anomaly_result["year"], y=anomaly_result["rubella"],
                            mode="lines+markers", name="Rubella cases",
                            line=dict(color="#ff7f0e", width=2), yaxis="y2"
                        ))
                        if "rubella_anomaly" in anomaly_result:
                            anom_r = anomaly_result[anomaly_result["rubella_anomaly"] == -1]
                            fig_anom.add_trace(go.Scatter(
                                x=anom_r["year"], y=anom_r["rubella"],
                                mode="markers", name="Rubella anomaly",
                                marker=dict(size=14, color="darkred", symbol="x", line=dict(width=2)),
                                yaxis="y2"
                            ))
                    fig_anom.update_layout(
                        height=500,
                        yaxis=dict(title="Measles cases"),
                        yaxis2=dict(title="Rubella cases", overlaying="y", side="right"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig_anom, use_container_width=True)
                    
                    st.write("#### 📋 Detected Anomalies")
                    anom_years = anomaly_result[
                        (anomaly_result.get("measles_anomaly", 1) == -1) | 
                        (anomaly_result.get("rubella_anomaly", 1) == -1) |
                        (anomaly_result.get("joint_anomaly", 1) == -1)
                    ]
                    
                    if not anom_years.empty:
                        display_cols = ["year", "measles", "rubella"]
                        if "measles_anomaly_score" in anom_years.columns:
                            display_cols.append("measles_anomaly_score")
                        if "rubella_anomaly_score" in anom_years.columns:
                            display_cols.append("rubella_anomaly_score")
                        
                        st.dataframe(
                            anom_years[display_cols].style.format({
                                "measles_anomaly_score": "{:.3f}", 
                                "rubella_anomaly_score": "{:.3f}"
                            }),
                            use_container_width=True
                        )
                    else:
                        st.info("✅ No anomalies detected for this country with current settings.")
                else:
                    st.warning(f"Could not perform anomaly detection for {anomaly_country}. Insufficient data.")
        except ImportError:
            st.error("❌ Anomaly detector module not found. Please ensure 'anomaly_detector.py' is available.")
    else:
        st.info("👈 Enable anomaly detection in the sidebar to analyze unusual patterns.")

# Download section
st.markdown("---")
st.subheader("💾 Download Data")
if not long_f.empty:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"Download filtered dataset ({len(long_f):,} rows)")
    with col2:
        st.download_button(
            "📥 Download CSV",
            data=long_f.sort_values(["country","region","disease","year"]).to_csv(index=False).encode("utf-8"),
            file_name=f"measles_rubella_{disease_sel}_{year_range[0]}-{year_range[1]}.csv",
            mime="text/csv",
            use_container_width=True
        )
# Collect all your figures in a list
chart_list = [fig_global, fig_reg, fig_bar, fig_map, fig_cty, fig_compare, fig_anom]

# Function to generate HTML for all charts
def generate_html_report(charts, title="Measles & Rubella Dashboard"):
    html_parts = [f"<h1>{title}</h1>"]
    for idx, fig in enumerate(charts):
        # Convert Plotly figure to standalone HTML div
        fig_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
        html_parts.append(fig_html)
        html_parts.append("<hr>")
    return "<html><head><meta charset='utf-8'></head><body>" + "".join(html_parts) + "</body></html>"

# Generate HTML content
html_report = generate_html_report(chart_list)

# Add Streamlit download button
st.download_button(
    label="📥 Download HTML Report",
    data=html_report,
    file_name=f"measles_rubella_report_{disease_sel}_{year_range[0]}-{year_range[1]}.html",
    mime="text/html",
    use_container_width=True
)
