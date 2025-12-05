# apputil.py
import pandas as pd
import numpy as np
import streamlit as st
import os
APP_ENV = os.getenv("APP_ENV", "production")

@st.cache_data(show_spinner=True)
def _read_excel_from_bytes(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_excel(file_bytes)

def normalize_and_transform(df: pd.DataFrame):
    # Standardize columns
    df = df.rename(columns={
        "Region":"region","Country":"country","Year":"year",
        "Measles_Cases":"measles","Rubella_Cases":"rubella",
        "Population":"population",
        "Measles_Cases_Per_100K":"measles_per100k",
        "Rubella_Cases_Per_100K":"rubella_per100k",
    })
    for c in ["region","country"]:
        df[c] = df[c].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    for c in ["measles","rubella","population","measles_per100k","rubella_per100k"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Build long-form totals
    measles_long = df[["region","country","year","measles"]].rename(columns={"measles":"value"}).assign(disease="Measles")
    rubella_long = df[["region","country","year","rubella"]].rename(columns={"rubella":"value"}).assign(disease="Rubella")
    long_df = pd.concat([measles_long, rubella_long], ignore_index=True).sort_values(["country","disease","year"])

    # Rolling averages and YoY per country+disease
    def add_rolls_yoy(g):
        g = g.sort_values("year")
        g["roll3"] = g["value"].rolling(3, min_periods=1).mean()
        g["roll5"] = g["value"].rolling(5, min_periods=1).mean()
        prev = g["value"].shift(1)
        g["yoy"] = np.where((prev.notna()) & (prev != 0), g["value"]/prev - 1, np.nan)
        return g

    long_df = long_df.groupby(["country","disease"], group_keys=False).apply(add_rolls_yoy)

    # Optional per-100k variants
    extras = []
    if "measles_per100k" in df.columns:
        m100 = df[["region","country","year","measles_per100k"]].rename(columns={"measles_per100k":"value"}).assign(disease="Measles_per100k")
        m100 = m100.sort_values(["country","year"]).groupby("country", group_keys=False).apply(add_rolls_yoy)
        extras.append(m100)
    if "rubella_per100k" in df.columns:
        r100 = df[["region","country","year","rubella_per100k"]].rename(columns={"rubella_per100k":"value"}).assign(disease="Rubella_per100k")
        r100 = r100.sort_values(["country","year"]).groupby("country", group_keys=False).apply(add_rolls_yoy)
        extras.append(r100)
    if extras:
        long_df = pd.concat([long_df] + extras, ignore_index=True)

    return df, long_df

def load_data_via_uploader():
    # Users can browse and upload; no path needed
    uploaded = st.file_uploader("Upload the Excel file (e.g., Measles_Rubella_Final.xlsx)", type=["xlsx"])
    if uploaded is None:
        st.info("Please upload your Excel file to begin.")  # prompt stays until user uploads
        st.stop()
    try:
        raw = _read_excel_from_bytes(uploaded.read())
    except Exception as e:
        st.error(f"Could not read the uploaded file: {e}")
        st.stop()
    base_wide, base_long = normalize_and_transform(raw)
    return base_wide, base_long
