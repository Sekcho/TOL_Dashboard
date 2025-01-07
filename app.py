from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import numpy as np
import os
from datetime import datetime

# Load Dataset
data_path = os.path.join(os.path.dirname(__file__), 'TOL_dataset_numeric.csv') 
data = pd.read_csv(data_path)

# Convert 'L2 Inservice date' to datetime format for consistency
data['L2 Inservice date'] = pd.to_datetime(data['L2 Inservice date'], errors='coerce')

# Ensure 'L2_Aging' is numeric
data['L2_Aging'] = pd.to_numeric(data['L2_Aging'], errors='coerce').fillna(0).astype(int)

# Create Dash App
app = Dash(__name__)
server = app.server  # For deployment

# Layout
app.layout = html.Div([
    html.H1("TOL Sales Targeting Dashboard", style={'textAlign': 'center'}),

    # Filters
    html.Div([
        html.Label("Select Province:"),
        dcc.Dropdown(
            id='province-filter',
            options=[{'label': prov, 'value': prov} for prov in data['Province'].unique()],
            placeholder="Select Province",
        ),
        html.Label("Select District:"),
        dcc.Dropdown(
            id='district-filter',
            placeholder="Select District",
        ),
        html.Label("Select Sub-district:"),
        dcc.Dropdown(
            id='subdistrict-filter',
            placeholder="Select Sub-district",
        ),
        html.Label("L2 Aging Range (Months):"),
        dcc.RangeSlider(
            id='l2-aging-slider',
            min=int(data['L2_Aging'].min()),
            max=int(data['L2_Aging'].max()),
            step=1,
            marks={i: str(i) for i in range(int(data['L2_Aging'].min()), int(data['L2_Aging'].max()) + 1, 12)},
            value=[int(data['L2_Aging'].min()), int(data['L2_Aging'].max())],
            tooltip={"placement": "bottom", "always_visible": True},
        ),
    ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),

    # Map Display
    dcc.Graph(id='map', style={'width': '65%', 'display': 'inline-block'}),
])

# Callbacks for cascading filters
@app.callback(
    Output('district-filter', 'options'),
    Input('province-filter', 'value')
)
def update_district_options(selected_province):
    if selected_province:
        filtered = data[data['Province'] == selected_province]
        return [{'label': dist, 'value': dist} for dist in filtered['District'].unique()]
    return []

@app.callback(
    Output('subdistrict-filter', 'options'),
    [Input('province-filter', 'value'), Input('district-filter', 'value')]
)
def update_subdistrict_options(selected_province, selected_district):
    filtered = data.copy()
    if selected_province:
        filtered = filtered[filtered['Province'] == selected_province]
    if selected_district:
        filtered = filtered[filtered['District'] == selected_district]
    return [{'label': subdist, 'value': subdist} for subdist in filtered['Sub-district'].unique()]

# Callback for Map Update
@app.callback(
    Output('map', 'figure'),
    [Input('province-filter', 'value'),
     Input('district-filter', 'value'),
     Input('subdistrict-filter', 'value'),
     Input('l2-aging-slider', 'value')]
)
def update_map(province, district, subdistrict, l2_aging_range):
    filtered = data.copy()

    if province:
        filtered = filtered[filtered['Province'] == province]
    if district:
        filtered = filtered[filtered['District'] == district]
    if subdistrict:
        filtered = filtered[filtered['Sub-district'] == subdistrict]

    filtered = filtered[
        (filtered['L2_Aging'] >= l2_aging_range[0]) &
        (filtered['L2_Aging'] <= l2_aging_range[1])
    ]

    if filtered.empty:
        return {
            "data": [],
            "layout": {
                "title": "No data available",
                "mapbox": {"style": "open-street-map"},
            },
        }

    fig = px.scatter_mapbox(
        filtered,
        lat="Latitude",
        lon="Longitude",
        size="Port Use",  # Size by Port Use
        color="L2_Aging",  # Color by L2 Aging
        hover_name="Sub-district",
        hover_data={
            "L2_Aging": True,
            "Latitude": False,
            "Longitude": False
        },
        color_continuous_scale="Viridis",
        title="L2 Aging Insights",
    )
    fig.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig

# Run App
if __name__ == '__main__':
    app.run_server(debug=True)
