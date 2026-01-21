import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import linregress
import streamlit as st

# Set Streamlit Page Config (Must be the first Streamlit command)
st.set_page_config(layout="wide", page_title="Life Expectancy Dashboard")

# --- 1. Load and Clean Data ---
@st.cache_data # This makes the app much faster by caching the data
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
    # Updated to follow new Pandas rules
    slope, _, _, _, _ = linregress(group['Year'], group['Life expectancy-female'])
    return slope

slopes = filtered_df.groupby('Entity').apply(get_slope, include_groups=False).reset_index(name='Growth_Rate')
top_10 = slopes.nlargest(10, 'Growth_Rate').sort_values('Growth_Rate', ascending=True)

# --- 3. Constructing Dashboard ---
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Top 10 Growth Rates", 
        "Historical Trend",
        "Global Life Expectancy Map", 
        "Distribution by Continent"
    ),
    vertical_spacing=0.25,
    horizontal_spacing=0.22, # Increased from 0.15 to prevent overlap
    specs=[[{"type": "bar"}, {"type": "scatter"}],
           [{"type": "geo"}, {"type": "box"}]]
)

# Plot 1: Bar
fig.add_trace(go.Bar(x=top_10['Growth_Rate'], y=top_10['Entity'], orientation='h',
                     marker=dict(color=top_10['Growth_Rate'], colorscale='Viridis'), showlegend=False), row=1, col=1)

# --- NEW: Streamlit Sidebar Interaction ---
st.sidebar.title("Controls")
selected_country = st.sidebar.selectbox("Select Country for Trend Line", top_10['Entity'].unique())

# Plot 2: Line (Filtered by Streamlit selection)
country_df = filtered_df[filtered_df['Entity'] == selected_country]
fig.add_trace(go.Scatter(x=country_df['Year'], y=country_df['Life expectancy-female'],
                         mode='lines+markers', name=selected_country), row=1, col=2)

# Plot 3: Map
latest_year_data = filtered_df[filtered_df['Year'] == YEAR_END]
fig.add_trace(go.Choropleth(
    locations=latest_year_data['Code'],
    z=latest_year_data['Life expectancy-female'],
    text=latest_year_data['Entity'],
    colorscale='Cividis',
    colorbar=dict(thickness=15, len=0.4, x=0.48, y=0.2, title="Age"),
    name="Map"), row=2, col=1)

# Plot 4: Box Plot
for continent in filtered_df['Continent'].unique():
    fig.add_trace(go.Box(y=filtered_df[filtered_df['Continent'] == continent]['Life expectancy-female'],
                         name=str(continent), showlegend=False), row=2, col=2)

# Layout adjustments
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)", # Transparent to match Streamlit theme
    plot_bgcolor="rgba(0,0,0,0)",
    height=800,
    margin=dict(t=80, b=20, l=20, r=20),
    title_text="Global Life Expectancy: Spatial & Temporal Analysis",
    title_x=0.5
)
fig.update_geos(projection_type="robinson", showocean=True, oceancolor="#1a1a1a", row=2, col=1)

# Render the Plotly figure in Streamlit
st.plotly_chart(fig, use_container_width=True)

