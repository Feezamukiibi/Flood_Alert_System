import streamlit as st
import geopandas as gpd
import pandas as pd
import os
from datetime import datetime
import matplotlib.colors as mcolors
import folium
from streamlit_folium import folium_static
from branca.colormap import LinearColormap

# ==============================================
# CONFIGURATION - VIBRANT COLOR SCHEME
# ==============================================
KAMPALA_COORDS = (0.3476, 32.5825)  # (latitude, longitude)
ALERT_THRESHOLD = 1.0  # Risk score threshold for alerts
DATA_DIR = "flood_risk_outputs"
REFRESH_INTERVAL = 300  # 5 minutes in seconds

# Vibrant risk categories with appealing colors
RISK_CATEGORIES = {
    'No Risk': (0, 2),
    'Low Risk': (2, 4),
    'Moderate Risk': (4, 6),
    'High Risk': (6, 8),
    'Extreme Risk': (8, 10)
}

# Color palette - vibrant and appealing
COLOR_PALETTE = {
    'No Risk': '#00FF7F',  # Spring Green
    'Low Risk': '#FFD700',  # Gold
    'Moderate Risk': '#FF8C00',  # Dark Orange
    'High Risk': '#FF4500',  # Orange Red
    'Extreme Risk': '#FF0000',  # Red
    'No Data': '#A9A9A9',  # Dark Gray
    'Invalid Data': '#696969'  # Dim Gray
}

# Gradient colors for smooth transitions
GRADIENT_COLORS = ['#00FF7F', '#FFD700', '#FF8C00', '#FF4500', '#FF0000']

# ==============================================
# UTILITY FUNCTIONS
# ==============================================
def get_risk_category(score):
    """Categorize risk score with robust error handling"""
    if score is None:
        return 'No Data'
    try:
        score = float(score)
        for category, (lower, upper) in RISK_CATEGORIES.items():
            if lower <= score < upper:
                return category
        return 'Invalid Data'
    except (TypeError, ValueError):
        return 'Invalid Data'

def get_color(score):
    """Generate vibrant color gradient from risk score"""
    if score is None:
        return COLOR_PALETTE['No Data']
    try:
        score = float(score)
        if score < 0 or score > 10:
            return COLOR_PALETTE['Invalid Data']
        cmap = LinearColormap(GRADIENT_COLORS, vmin=0, vmax=10)
        return cmap(score)
    except (TypeError, ValueError):
        return COLOR_PALETTE['Invalid Data']

def safe_float_format(value, precision=1):
    """Safely format float values with error handling"""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{precision}f}"
    except (TypeError, ValueError):
        return "N/A"

def load_latest_data():
    """Load most recent GeoJSON file with comprehensive error handling"""
    try:
        if not os.path.exists(DATA_DIR):
            return None, None, None, "Data directory not found"
            
        files = [f for f in os.listdir(DATA_DIR) 
                if f.endswith('.geojson') and os.path.getsize(os.path.join(DATA_DIR, f)) > 0]
        
        if not files:
            return None, None, None, "No valid GeoJSON files found"
            
        latest_file = max(files, key=lambda x: os.path.getctime(os.path.join(DATA_DIR, x)))
        data = gpd.read_file(os.path.join(DATA_DIR, latest_file))
        
        # Validate required columns
        required_cols = ['risk_score', 'geometry']
        if not all(col in data.columns for col in required_cols):
            return None, None, None, "Missing required columns in data"
            
        # Add risk category column
        if 'risk_score' in data.columns:
            data['risk_category'] = data['risk_score'].apply(get_risk_category)
            
        update_time = datetime.fromtimestamp(os.path.getctime(os.path.join(DATA_DIR, latest_file)))
        return data, update_time, latest_file, None
        
    except Exception as e:
        return None, None, None, f"Error loading data: {str(e)}"

def create_legend_map():
    """Create a vibrant folium legend with appealing design"""
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 180px; height: 300px; 
                border:2px solid {COLOR_PALETTE['High Risk']}; 
                z-index:9999; font-size:14px;
                background-color:white;
                opacity:0.9;
                padding:10px;
                border-radius:8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.2);">
      <p style="margin-top:0;
                font-weight:bold;
                text-align:center;
                color:{COLOR_PALETTE['Extreme Risk']};
                font-size:16px;
                padding-bottom:5px;
                border-bottom:1px solid #ddd;">
                Risk Categories</p>
      <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <div style="width: 22px; height: 22px; background: {COLOR_PALETTE['No Risk']}; 
                    margin-right: 8px; border-radius:3px;"></div>
        <div>No Risk (0-2)</div>
      </div>
      <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <div style="width: 22px; height: 22px; background: {COLOR_PALETTE['Low Risk']}; 
                    margin-right: 8px; border-radius:3px;"></div>
        <div>Low Risk (2-4)</div>
      </div>
      <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <div style="width: 22px; height: 22px; background: {COLOR_PALETTE['Moderate Risk']}; 
                    margin-right: 8px; border-radius:3px;"></div>
        <div>Moderate (4-6)</div>
      </div>
      <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <div style="width: 22px; height: 22px; background: {COLOR_PALETTE['High Risk']}; 
                    margin-right: 8px; border-radius:3px;"></div>
        <div>High Risk (6-8)</div>
      </div>
      <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <div style="width: 22px; height: 22px; background: {COLOR_PALETTE['Extreme Risk']}; 
                    margin-right: 8px; border-radius:3px;"></div>
        <div>Extreme (8-10)</div>
      </div>
      <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <div style="width: 22px; height: 22px; background: {COLOR_PALETTE['No Data']}; 
                    margin-right: 8px; border-radius:3px;"></div>
        <div>No Data</div>
      </div>
      <div style="display: flex; align-items: center;">
        <div style="width: 22px; height: 22px; background: {COLOR_PALETTE['Invalid Data']}; 
                    margin-right: 8px; border-radius:3px;"></div>
        <div>Invalid Data</div>
      </div>
    </div>
    '''
    return legend_html

# ==============================================
# DASHBOARD LAYOUT - VIBRANT DESIGN
# ==============================================
st.set_page_config(
    page_title="🌊 Kampala Flood Monitor",
    layout="wide",
    page_icon="⚠️"
)

# Custom CSS with vibrant styling
st.markdown(f"""
<style>
    .stAlert {{ 
        padding: 20px;
        background-color: #FFF3E0;
        border-left: 5px solid {COLOR_PALETTE['High Risk']};
    }}
    .metric-value {{ 
        font-size: 1.5rem !important;
        color: {COLOR_PALETTE['Extreme Risk']} !important;
    }}
    .metric-label {{
        font-size: 1rem !important;
        color: #333 !important;
    }}
    .map-container {{ 
        border-radius: 12px; 
        border: 2px solid {COLOR_PALETTE['Moderate Risk']};
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}
    .risk-tooltip {{ 
        font-weight: bold; 
        font-size: 14px;
        background-color: white;
        padding: 8px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        border: 1px solid {COLOR_PALETTE['Low Risk']};
    }}
    .stButton>button {{
        background-color: {COLOR_PALETTE['Moderate Risk']};
        color: white;
        border-radius: 6px;
        padding: 8px 16px;
        border: none;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: {COLOR_PALETTE['High Risk']};
    }}
    .css-1aumxhk {{
        background-color: #F5F5F5;
    }}
</style>
""", unsafe_allow_html=True)

# Header with vibrant styling
st.markdown(f"""
<div style="background: linear-gradient(to right, {COLOR_PALETTE['No Risk']}, {COLOR_PALETTE['Extreme Risk']});
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
    <h1 style="color: white; 
               text-align: center; 
               text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
               margin: 0;">
        🌊 Kampala Flood Monitoring System
    </h1>
</div>
""", unsafe_allow_html=True)

# Data Loading
data, update_time, filename, error = load_latest_data()

# Refresh Control with vibrant button
refresh_col = st.columns([1, 1, 1])
with refresh_col[1]:
    if st.button('🔄 Refresh Data', help="Click to manually refresh the data"):
        data, update_time, filename, error = load_latest_data()
        st.experimental_rerun()

# Error Handling with styled alert
if error:
    st.error(f"🚨 Data Error: {error}")
    st.stop()

# Status Display with vibrant metrics
if update_time and filename:
    time_diff = (datetime.now() - update_time).total_seconds() / 60
    cols = st.columns(3)
    with cols[0]:
        st.metric("📅 Last Update", update_time.strftime("%Y-%m-%d %H:%M:%S"))
    with cols[1]:
        st.metric("⏳ Data Age", f"{time_diff:.1f} minutes")
    with cols[2]:
        st.metric("📂 File", filename)
else:
    st.warning("⚠️ No data files available. Run the monitoring script first.")
    st.stop()

# Main Dashboard Content
if data is not None and not data.empty:
    # Metrics Row with vibrant colors
    st.markdown("### 📊 Risk Overview")
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("📍 Total Zones", len(data))
    with metric_cols[1]:
        valid_scores = [x for x in data['risk_score'] if x is not None]
        try:
            valid_scores = [float(x) for x in valid_scores]
            max_risk = max(valid_scores) if valid_scores else 0
            st.metric("🔥 Highest Risk", safe_float_format(max_risk))
        except:
            st.metric("🔥 Highest Risk", "N/A")
    with metric_cols[2]:
        try:
            area = data.geometry.area.sum()/1e6 if not data.empty else 0
            st.metric("📏 Area", f"{area:.2f} km²")
        except:
            st.metric("📏 Area", "N/A")
    with metric_cols[3]:
        alert_count = sum(1 for x in data['risk_score'] 
                      if x is not None and float(x) > ALERT_THRESHOLD)
        st.metric("🚨 Alert Zones", alert_count)

    # Risk Category Distribution with vibrant chart
    if 'risk_category' in data.columns:
        st.markdown("### 📈 Risk Distribution")
        try:
            all_categories = list(RISK_CATEGORIES.keys()) + ['No Data', 'Invalid Data']
            risk_counts = data['risk_category'].value_counts().reindex(all_categories, fill_value=0)
            st.bar_chart(risk_counts, color=COLOR_PALETTE['High Risk'])
        except Exception as e:
            st.error(f"Could not display risk distribution: {str(e)}")

    # Interactive Map with vibrant styling
    st.markdown("### 🗺️ Live Risk Map")
    try:
        m = folium.Map(
            location=[KAMPALA_COORDS[0], KAMPALA_COORDS[1]],
            zoom_start=12,
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr='OpenStreetMap contributors',
            control_scale=True
        )
        
        # Add vibrant risk areas
        for _, row in data.iterrows():
            risk_score = row.get('risk_score')
            risk_category = row.get('risk_category', 'No Data')
            tooltip_text = f"""
                <div class='risk-tooltip'>
                    <b>Risk Score:</b> {safe_float_format(risk_score)}<br>
                    <b>Category:</b> {risk_category}
                </div>
            """
            
            folium.GeoJson(
                row['geometry'],
                style_function=lambda x, score=risk_score: {
                    'fillColor': get_color(score),
                    'color': '#333',
                    'weight': 1.5,
                    'fillOpacity': 0.8,
                    'dashArray': '5, 5' if risk_category == 'Invalid Data' else None
                },
                tooltip=tooltip_text
            ).add_to(m)
        
        # Add vibrant legend
        legend_html = create_legend_map()
        m.get_root().html.add_child(folium.Element(legend_html))
        
        folium_static(m, width=1200, height=650)
    except Exception as e:
        st.error(f"Map rendering error: {str(e)}")

    # Data Table with vibrant styling
    st.markdown("### 📝 Risk Zone Details")
    try:
        if 'risk_score' in data.columns:
            display_data = data.copy()
            display_data['_sort_key'] = display_data['risk_score'].apply(
                lambda x: float(x) if x is not None else -1)
            display_data = display_data.sort_values('_sort_key', ascending=False)
        else:
            display_data = data
            
        st.dataframe(
            display_data.assign(
                area_km2=lambda x: x.geometry.area/1e6,
                risk_score_display=lambda x: x['risk_score'].apply(
                    lambda s: safe_float_format(s) if s is not None else 'N/A')
            )[['risk_score_display', 'area_km2', 'risk_category'] if 'risk_category' in data.columns else ['risk_score_display', 'area_km2']],
            column_config={
                "risk_score_display": st.column_config.NumberColumn(
                    "Risk Score",
                    help="Flood risk score (0-10 scale)"
                ),
                "area_km2": st.column_config.NumberColumn(
                    "Area (km²)", 
                    format="%.2f",
                    help="Area of the risk zone in square kilometers"
                ),
                "risk_category": st.column_config.TextColumn(
                    "Risk Category",
                    help="Classification based on risk score"
                )
            },
            hide_index=True,
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Data display error: {str(e)}")
else:
    st.warning("⚠️ No valid risk data available in the loaded file.")

# Auto-refresh
st.experimental_rerun_interval = REFRESH_INTERVAL * 1000