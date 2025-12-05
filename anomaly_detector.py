# anomaly_detector.py
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import streamlit as st

@st.cache_data(show_spinner=True)
def detect_anomalies_for_country(df_wide: pd.DataFrame, country: str, contamination: float = 0.1):
    """
    Detect anomalies using Isolation Forest for a single country.
    Returns augmented dataframe with anomaly flags and scores.
    """
    # Filter country data
    country_data = df_wide[df_wide["country"] == country].sort_values("year").copy()
    
    if len(country_data) < 3:
        st.warning(f"Not enough data for {country} (need at least 3 years)")
        return None
    
    # Prepare features for each disease separately
    measles_features = country_data[["measles"]].values if "measles" in country_data else None
    rubella_features = country_data[["rubella"]].values if "rubella" in country_data else None
    
    # Joint features (both diseases)
    joint_features = country_data[["measles", "rubella"]].dropna().values if {"measles","rubella"}.issubset(country_data.columns) else None
    
    result = country_data.copy()
    
    # Measles anomalies
    if measles_features is not None and len(measles_features) >= 3:
        iso_m = IsolationForest(contamination=contamination, random_state=42)
        result["measles_anomaly"] = iso_m.fit_predict(measles_features)
        result["measles_anomaly_score"] = iso_m.score_samples(measles_features)
    
    # Rubella anomalies
    if rubella_features is not None and len(rubella_features) >= 3:
        iso_r = IsolationForest(contamination=contamination, random_state=42)
        result["rubella_anomaly"] = iso_r.fit_predict(rubella_features)
        result["rubella_anomaly_score"] = iso_r.score_samples(rubella_features)
    
    # Joint anomalies
    if joint_features is not None and len(joint_features) >= 3:
        iso_j = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
        result["joint_anomaly"] = iso_j.fit_predict(joint_features)
        result["joint_anomaly_score"] = iso_j.score_samples(joint_features)
    
    return result

def get_global_anomalies(df_wide: pd.DataFrame, top_n: int = 20, contamination: float = 0.1):
    """
    Run anomaly detection across all countries and return aggregated results.
    """
    all_anomalies = []
    countries = df_wide["country"].unique()
    
    progress_bar = st.progress(0)
    for idx, country in enumerate(countries):
        country_result = detect_anomalies_for_country(df_wide, country, contamination)
        if country_result is not None:
            all_anomalies.append(country_result)
        progress_bar.progress((idx + 1) / len(countries))
    
    progress_bar.empty()
    
    if not all_anomalies:
        return pd.DataFrame()
    
    combined = pd.concat(all_anomalies, ignore_index=True)
    return combined
