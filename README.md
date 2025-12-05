# Measles & Rubella Interactive Dashboard

![Dashboard Preview](https://img.shields.io/badge/Streamlit-App-ff4b4b?style=for-the-badge&logo=streamlit)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> An interactive web application for exploring global measles and rubella disease trends, regional patterns, and anomaly detection to support public health decision-making.

🌐 **Live App**: https://idsgroup4-eeug6zosmgzbetqsaa37pi.streamlit.app/

**Course:** INFO-H 501 (26346) - Intro to Data Science Programming  
**Semester:** Fall 2025  
**Institution:** Indiana University Indianapolis

---

## Abstract

The Measles & Rubella Interactive Dashboard provides public health officials, researchers, and policymakers with an intuitive tool to visualize and analyze disease case data across countries and regions from 2012-2025. Users can explore global trends, compare countries, identify geographic hotspots via an interactive 3D globe, and detect statistical anomalies that may indicate outbreaks or data quality issues. 

**Key Outcomes:**
- Enables rapid identification of countries with highest disease burden (absolute and per-capita)
- Reveals regional epidemic patterns through multi-year rolling averages and year-over-year growth metrics
- Flags unusual case spikes using machine learning-based anomaly detection
- Provides downloadable filtered datasets for further analysis

**Stakeholders:** This tool benefits WHO regional offices, national ministries of health, epidemiologists, and international NGOs working on vaccine-preventable disease elimination. They can use it to allocate resources to high-burden areas, monitor progress toward elimination targets, and quickly respond to potential outbreaks flagged by the anomaly detection system.

---

## Data Description

**Source:** World Health Organization (WHO) and UNICEF measles/rubella surveillance data (2012-2025)

**Dataset Structure:**
- **Original format:** Excel file (`Measles_Rubella_Final.xlsx`)
- **Records:** ~3,000+ country-year observations
- **Key fields:**
  - `Country`, `Region`, `Year`
  - `Measles_Cases`, `Rubella_Cases` (absolute counts)
  - `Population`
  - `Measles_Cases_Per_100K`, `Rubella_Cases_Per_100K` (normalized rates)

**Data Cleaning:**
- Standardized country/region names (e.g., "Democratic Republic of Congo" variants)
- Converted case counts and population to numeric types, handling missing values
- Generated long-format dataset for time-series analysis (disease as categorical variable)
- Computed rolling averages (3, 5, 7-year windows) and year-over-year growth rates per country

**Known Limitations:**
- Reported cases depend on surveillance quality; countries with weak health systems may underreport
- Some territories with naming disputes (e.g., Pakistan-Occupied Kashmir, Kosovo) may not render on the choropleth map due to geographic database limitations
- Missing data for certain country-years (handled via interpolation or exclusion)

---

## Algorithm Description

### 1. **Data Transformation Pipeline** (`apputil.py`)
- **Input:** Raw Excel upload
- **Process:**
  - Column normalization (rename, type casting)
  - Long-form pivot (Measles/Rubella as separate rows)
  - Rolling window calculations (Pandas `.rolling()`)
  - Year-over-year percentage change computation
- **Output:** Clean wide-format + long-format DataFrames

### 2. **Interactive Filtering**
- Multi-select filters for disease type, year range, and regions
- Dynamic data subsetting using Pandas boolean indexing
- Cached transformations via Streamlit's `@st.cache_data` for performance

### 3. **Visualization Engine**
- **Plotly Express/Graph Objects** for all charts:
  - Bar charts with rolling average overlays (global/country trends)
  - Multi-line regional comparison charts
  - Horizontal bar charts for country rankings
  - **3D Orthographic Choropleth Map** (globe projection) with dynamic year slider
- **Hover modes:** Unified x-axis hovering for time-series comparisons

### 4. **Anomaly Detection** (`anomaly_detector.py`)
- **Algorithm:** Isolation Forest (scikit-learn)
- **Method:**
  - Fits separate models for Measles, Rubella, and joint (both diseases) features
  - Uses default contamination rate (10%) to flag ~10% of data points as anomalies
  - Returns anomaly scores and binary labels (-1 = anomaly, 1 = normal)
- **Limitations:** 
  - Currently applies uniform model across all countries (aggregation bias concern)
  - Sensitive to contamination parameter tuning
- **Future Work:** Normalize by population before detection to account for country size differences

---

## Tools Used

| Tool | Purpose |
|------|---------|
| **Python 3.8+** | Core programming language |
| **Streamlit** | Web app framework for interactive dashboard |
| **Pandas** | Data manipulation, cleaning, and aggregation |
| **NumPy** | Numerical computations (rolling windows, growth rates) |
| **Plotly** | Interactive visualizations (charts, globe map) |
| **scikit-learn** | Machine learning (Isolation Forest for anomaly detection) |
| **GitHub** | Version control and code repository |
| **Streamlit Cloud** | Deployment and hosting |
| **Excel/XLSX** | Data storage format (user upload capability) |

---

## Ethical Concerns

### 1. **Representation Bias in Geographic Visualization**
**Issue:** The choropleth map fails to render countries with naming mismatches or disputed territories (e.g., POK, Taiwan, Kosovo), making their disease burden invisible.

**Mitigation:** Added a warning message above the map stating: *"Some countries/territories may not appear on the map due to naming variations or political recognition issues. All countries remain available in rankings and analysis."* This ensures users don't misinterpret blank areas as "no disease burden."

**Reference:** Suresh & Guttag (2021), Section 3.2: Representation Bias

### 2. **Measurement Bias in Reported Cases**
**Issue:** "Reported cases" is a proxy for "actual disease burden," but surveillance quality varies drastically by country wealth/infrastructure. Strong surveillance systems may report more cases than weak ones, even with similar true disease prevalence. This can stigmatize countries with good reporting.

**Mitigation:** 
- Provide per-capita metrics (cases per 100K) to account for population differences
- Include a disclaimer in the app explaining that case counts reflect *reporting capacity* as much as disease burden
- Encourage users to consider context (vaccination rates, outbreak response) when interpreting data

**Reference:** Suresh & Guttag (2021), Section 3.3: Measurement Bias

### 3. **Aggregation Bias in Anomaly Detection**
**Issue:** The Isolation Forest model uses the same parameters for all countries, ignoring that a 1,000-case spike means something very different for Maldives (catastrophic) vs. India (routine noise).

**Mitigation (Proposed):** Normalize features by population before anomaly detection, or use country-specific contamination rates. This limitation has been documented as a known fairness issue for future implementation.

**Reference:** Suresh & Guttag (2021), Section 3.4: Aggregation Bias

### 4. **Deployment Risk: Misinterpretation of Anomalies**
**Issue:** Flagged "anomalies" could represent outbreaks, data errors, surveillance improvements, or seasonal variation. Users may over-react to false positives or ignore true signals.

**Mitigation:** 
- Anomaly detection is opt-in (checkbox in sidebar)
- Explanatory text states: *"Anomalies indicate unusual patterns that may reflect outbreaks, data quality issues, or changes in surveillance. Investigate further before taking action."*
- Display anomaly scores alongside binary flags for transparency

**Reference:** Suresh & Guttag (2021), Section 3.7: Deployment Bias

### 5. **Data Provenance and Use**
**Issue:** WHO/UNICEF data is collected for surveillance, not necessarily for public dashboards. Misuse could harm countries' international reputation or affect tourism/investment.

**Mitigation:** 
- Clearly cite data sources
- Frame visualizations around "supporting public health response" rather than "naming and shaming"
- Include context that high case counts often reflect *better surveillance*, not worse disease control

---

## Installation & Running Locally

-Clone this repository
-Install dependencies
-pip install -r requirements.txt
-Run app
-streamlit run app.py
-Upload the `Measles_Rubella_Final.xlsx` file when prompted.
-Visualizations will pop up

---

## Project Structure
```
├── app.py # Main Streamlit application
├── apputil.py # Data loading and transformation utilities
├── anomaly_detector.py # Isolation Forest anomaly detection
├── Dockerfile # Container configuration for deployment
├── test_app_utils.py # Unit tests
├── requirements.txt # Python dependencies
├── .gitignore # Ignored files (cache, .env, data)
├── .env # Environment variables (not in repo)
├── README.md # This file
└── Measles_Rubella_Final.xlsx # Data file (uploaded by user)
```
---

## References

- Suresh, H., & Guttag, J. (2021). *A Framework for Understanding Sources of Harm throughout the Machine Learning Life Cycle*. EAAMO '21. https://arxiv.org/pdf/1901.10002.pdf
- World Health Organization. Measles Surveillance Data. https://www.who.int/
- UNICEF. Immunization Data Portal. https://data.unicef.org/

---

## License

This project is for educational purposes as part of INFO-H 501 at Indiana University Indianapolis. Data courtesy of WHO/UNICEF.
