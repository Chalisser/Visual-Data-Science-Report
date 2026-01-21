import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import linregress

# 1. Load and Clean Data
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

slopes = filtered_df.groupby('Entity').apply(get_slope).reset_index(name='Growth_Rate')
top_10 = slopes.nlargest(10, 'Growth_Rate').sort_values('Growth_Rate', ascending=True)

# --- 3. Constructing Dashboard with Grid Adjustments ---
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Top 10 Growth Rates", 
        "Historical Trend",
        "Global Life Expectancy Map", 
        "Distribution by Continent"
    ),
    vertical_spacing=0.25, # Space between Row 1 and Row 2
    horizontal_spacing=0.15,
    specs=[[{"type": "bar"}, {"type": "scatter"}],
           [{"type": "geo"}, {"type": "box"}]]
)

# Plot 1: Bar
fig.add_trace(go.Bar(x=top_10['Growth_Rate'], y=top_10['Entity'], orientation='h',
                     marker=dict(color=top_10['Growth_Rate'], colorscale='Viridis'), showlegend=False), row=1, col=1)

# Plot 2: Line
for i, country in enumerate(top_10['Entity']):
    country_df = filtered_df[filtered_df['Entity'] == country]
    fig.add_trace(go.Scatter(x=country_df['Year'], y=country_df['Life expectancy-female'],
                             mode='lines+markers', name=country, visible=(i == 0)), row=1, col=2)

# Plot 3: Map
latest_year_data = filtered_df[filtered_df['Year'] == YEAR_END]
fig.add_trace(go.Choropleth(
    locations=latest_year_data['Code'],
    z=latest_year_data['Life expectancy-female'],
    text=latest_year_data['Entity'],
    colorscale='Cividis',
    colorbar=dict(thickness=15, len=0.4, x=-0.12, y=0.2, title="Age"),
    name="Map"), row=2, col=1)

# Plot 4: Box Plot
for continent in filtered_df['Continent'].unique():
    fig.add_trace(go.Box(y=filtered_df[filtered_df['Continent'] == continent]['Life expectancy-female'],
                         name=str(continent), showlegend=False), row=2, col=2)

# --- 4. Dropdown Buttons ---
#buttons = []
#num_boxes = len(filtered_df['Continent'].unique())
#for i, country in enumerate(top_10['Entity']):
#    visibility = [True] + [False] * 10 + [True] + [True] * num_boxes
#    visibility[i + 1] = True
#    buttons.append(dict(label=country, method="update", args=[{"visible": visibility}]))

buttons = []
# Index 0: Bar Chart (Always True)
# Indices 1 to 10: The 10 Scatter traces for countries
# Index 11: Choropleth (Always True)
# Remaining indices: Box Plots (Always True)

num_countries = len(top_10)
num_boxes = len(filtered_df['Continent'].unique())

for i in range(num_countries):
    # Start with a base visibility list
    # Bar Chart (True), all Line Graphs (False), Map (True), Box Plots (True)
    visibility = [True] + [False] * num_countries + [True] + [True] * num_boxes
    
    # Set ONLY the current country's line to True
    # i + 1 because the Bar chart is at index 0
    visibility[i + 1] = True
    
    buttons.append(dict(
        label=top_10['Entity'].iloc[i],
        method="update",
        args=[{"visible": visibility}]
    ))

# --- 5. THE FINAL POSITIONING FIX ---
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="#111111",
    plot_bgcolor="#111111",
    
    # LEGEND FIX: 
    # Moving the legend to the right side, just below the dropdown 
    # so it stays near the line graph it represents.
    legend=dict(
        orientation="h", 
        yanchor="bottom", 
        y=0.95,       # Positioned slightly lower than the dropdown
        xanchor="right", 
        x=1,           # Far right
        font=dict(size=10)
    ),
    
    # DROPDOWN FIX:
    updatemenus=[dict(
        active=0, 
        buttons=buttons, 
        x=1,           # Far right (aligned with the edge of the line graph)
        y=1.05,        # Placed above the legend and plot
        xanchor="right", 
        yanchor="bottom", 
        bgcolor="#333333", 
        font=dict(color="white", size=12)
    )],
    
    # Margin adjustment to make sure the top doesn't feel cramped
    margin=dict(l=100, r=50, t=150, b=100), 
    height=1000, 
    width=1500,
    title_text="Global Life Expectancy: Spatial & Temporal Analysis",
    title_x=0.5,
    font=dict(color="white")
)

# ADJUST SUBPLOT TITLES
# We increase the y-offset to make sure they sit below the dropdown/legend
for i in range(len(fig.layout.annotations)):
    fig.layout.annotations[i].update(y = fig.layout.annotations[i].y + 0.05)

fig.update_geos(projection_type="robinson", showocean=True, oceancolor="#1a1a1a", row=2, col=1)

# --- 6. Seamless Dark Mode HTML Export ---
html_content = fig.to_html(full_html=False, include_plotlyjs='cdn')
final_html = f"""
<!DOCTYPE html>
<html style="background-color: #111111;">
<head>
    <style>
        body {{ background-color: #111111; margin: 0; padding: 20px; color: white; }}
    </style>
</head>
<body>{html_content}</body>
</html>
"""

with open("Report.html", "w", encoding="utf-8") as f:
    f.write(final_html)