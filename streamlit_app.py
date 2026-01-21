import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import linregress
import streamlit as st

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Life Expectancy Dashboard")

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

# 2. Data Filtering
YEAR_START, YEAR_END = 2010, 2022
mask = (df['Year'].between(YEAR_START, YEAR_END)) & (df['Code'] != 'NA')
filtered_df = df[mask].copy()

def get_slope(group):
    if len(group) < 2: return 0
    slope, _, _, _, _ = linregress(group['Year'], group['Life expectancy-female'])
    return slope

slopes = filtered_df.groupby('Entity').apply(get_slope, include_groups=False).reset_index(name='Growth_Rate')
top_10 = slopes.nlargest(10, 'Growth_Rate').sort_values('Growth_Rate', ascending=True)

# 3. Side Note (Positioned at the top for clarity)
st.info("💡 **Interactive Guide:** Click on a bar in the **Top 10** chart or any country on the **Map** to view its specific historical data in the trend line at the bottom.")

# 4. Constructing Main Dashboard
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Top 10 Growth Rates (Click a Bar)", 
        "Global Life Expectancy Map", 
        "Distribution by Continent"
    ),
    vertical_spacing=0.18,
    horizontal_spacing=0.25,
    specs=[[{"colspan": 2}, None], 
           [{"type": "geo"}, {"type": "box"}]]
)

# Bar Chart (with selection persistence)
fig.add_trace(go.Bar(
    x=top_10['Growth_Rate'], y=top_10['Entity'], orientation='h',
    marker=dict(color=top_10['Growth_Rate'], colorscale='Viridis'), 
    showlegend=False, customdata=top_10['Entity'],
    unselected=dict(marker=dict(opacity=1)),
    selected=dict(marker=dict(opacity=1))
), row=1, col=1)

# Map
latest_year_data = filtered_df[filtered_df['Year'] == YEAR_END]
fig.add_trace(go.Choropleth(
    locations=latest_year_data['Code'],
    z=latest_year_data['Life expectancy-female'],
    text=latest_year_data['Entity'],
    colorscale='Cividis',
    colorbar=dict(thickness=15, len=0.5, x=-0.12, y=0.2, title="Age"),
    name="Map",
    customdata=latest_year_data['Entity'],
    unselected=dict(marker=dict(opacity=1)),
    selected=dict(marker=dict(opacity=1))
), row=2, col=1)

# Box Plots
for continent in filtered_df['Continent'].unique():
    fig.add_trace(go.Box(
        y=filtered_df[filtered_df['Continent'] == continent]['Life expectancy-female'],
        name=str(continent), showlegend=False
    ), row=2, col=2)

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    height=850,
    margin=dict(t=80, b=20, l=20, r=20),
    title_text="Global Life Expectancy: Spatial & Temporal Analysis",
    title_x=0.5,
    clickmode='event+select'
)
fig.update_geos(projection_type="robinson", showocean=True, oceancolor="#1a1a1a", row=2, col=1)

# 5. Interaction Logic
event_data = st.plotly_chart(fig, use_container_width=True, on_select="rerun")

selected_country = top_10['Entity'].iloc[-1] 

if event_data and "selection" in event_data:
    points = event_data["selection"]["points"]
    if points:
        selected_country = points[0].get("customdata") or points[0].get("text") or points[0].get("y")

# 6. Dynamic Detail Plot
st.divider()
st.subheader(f"Historical Trend Analysis: {selected_country}")

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
    yaxis_title="Life Expectancy (Age)",
    margin=dict(t=20, b=40, l=40, r=20),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(30,30,30,0.5)"
)

st.plotly_chart(trend_fig, use_container_width=True)

