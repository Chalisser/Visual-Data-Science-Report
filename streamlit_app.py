import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import linregress
import streamlit as st

# Set Streamlit Page Config
st.set_page_config(layout="wide", page_title="Life Expectancy Dashboard")

# --- 1. Load and Clean Data ---
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    df = df.rename(columns={
        'Life expectancy - Sex: female - Age: 0 - Variant: estimates': 'Life expectancy-female',
        'Population - Sex: all - Age: all - Variant: estimates': 'Total Population'
    })
    df['Life expectancy-female'] = df.groupby('Entity')['Life expectancy-female'].transform(lambda x: x.fillna(x.median()))
    df['Code'] = df['Code'].fillna('NA')
    return df

df = load_data('dataset.csv')

# --- 2. Static Filters ---
YEAR_START, YEAR_END = 2010, 2022
mask = (df['Year'].between(YEAR_START, YEAR_END)) & (df['Code'] != 'NA')
filtered_df = df[mask].copy()

def get_slope(group):
    if len(group) < 2: return 0
    slope, _, _, _, _ = linregress(group['Year'], group['Life expectancy-female'])
    return slope

slopes = filtered_df.groupby('Entity').apply(get_slope, include_groups=False).reset_index(name='Growth_Rate')
top_10 = slopes.nlargest(10, 'Growth_Rate').sort_values('Growth_Rate', ascending=True)

# --- 3. Constructing Dashboard ---
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Top 10 Growth Rates (Click a Bar to See Trend Below)", # Row 1, Col 1 (Starts here)
        "Global Life Expectancy Map",                        # Row 2, Col 1 (Centers over Map)
        "Distribution by Continent"                          # Row 2, Col 2 (Centers over Box Plot)
    ),
    vertical_spacing=0.15,
    horizontal_spacing=0.25, # Slightly increased to give the Map title more room
    specs=[[{"colspan": 2}, None], 
           [{"type": "geo"}, {"type": "box"}]]
)

# Plot 1: Bar
fig.add_trace(go.Bar(
    x=top_10['Growth_Rate'], 
    y=top_10['Entity'], 
    orientation='h',
    marker=dict(color=top_10['Growth_Rate'], colorscale='Viridis'), 
    showlegend=False, 
    customdata=top_10['Entity'],
    # --- ADD THIS SECTION TO PREVENT DIMMING ---
    unselected=dict(
        marker=dict(opacity=1) # Keeps the bars at 100% opacity even when unselected
    ),
    selected=dict(
        marker=dict(opacity=1) # Ensures selected bars also stay at 100% opacity
    )
), row=1, col=1)

# Plot 3: Map
latest_year_data = filtered_df[filtered_df['Year'] == YEAR_END]
fig.add_trace(go.Choropleth(
    locations=latest_year_data['Code'],
    z=latest_year_data['Life expectancy-female'],
    text=latest_year_data['Entity'],
    colorscale='Cividis',
    colorbar=dict(thickness=15, len=0.5, x=-0.1, y=0.2, title="Age"),
    name="Map",
    customdata=latest_year_data['Entity']
), row=2, col=1)

# Plot 4: Box Plot
for continent in filtered_df['Continent'].unique():
    fig.add_trace(go.Box(
        y=filtered_df[filtered_df['Continent'] == continent]['Life expectancy-female'],
        name=str(continent), showlegend=False
    ), row=2, col=2)

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=800,
    margin=dict(t=80, b=20, l=20, r=20),
    title_text="Global Life Expectancy Analysis",
    title_x=0.5,
    clickmode='event+select'
)
fig.update_geos(projection_type="robinson", showocean=True, oceancolor="#1a1a1a", row=2, col=1)

# --- 4. BRUSHING INTERACTION ---
# Render main dashboard
event_data = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

# Initialize default country (The highest growth rate country)
selected_country = top_10['Entity'].iloc[-1] 

# Update selected_country if a user clicks a graph element
if event_data and "selection" in event_data:
    points = event_data["selection"]["points"]
    if points:
        selected_country = points[0].get("customdata") or points[0].get("text") or points[0].get("y")

# --- 5. THE DYNAMIC TREND LINE ---
st.divider()
st.subheader(f"Detailed Historical Trend: {selected_country}")

trend_fig = go.Figure()
country_df = filtered_df[filtered_df['Entity'] == selected_country]

trend_fig.add_trace(go.Scatter(
    x=country_df['Year'], y=country_df['Life expectancy-female'],
    mode='lines+markers', 
    line=dict(color='#00CC96', width=3),
    marker=dict(size=8, color='white', line=dict(width=2, color='#00CC96'))
))

trend_fig.update_layout(
    template="plotly_dark",
    height=400,
    xaxis_title="Year",
    yaxis_title="Age",
    margin=dict(t=20, b=40, l=40, r=20),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(20,20,20,0.5)"
)

st.plotly_chart(trend_fig, use_container_width=True)




