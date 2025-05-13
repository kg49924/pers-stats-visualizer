from enum import auto
import streamlit as st
import os
import altair as alt
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pymongo
from pymongo import MongoClient

# Page config for larger space
st.set_page_config(layout='wide')

# Auto-refresh setup (add this)
refresh_interval = 30  # seconds
st.markdown(
    f"""
    <meta http-equiv="refresh" content="{refresh_interval}">
    """,
    unsafe_allow_html=True,
)

# Display current time to confirm refreshes
# st.write(f'Last updated: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}')


# Connect to MongoDB
def get_mongo_client():
    # Replace with your connection string
    client = MongoClient(os.environ.get('PERS_MONGO_DB', 'mongodb://localhost:27017/'))
    return client


# Query data with aggregation
def get_data_from_mongo():
    client = get_mongo_client()
    db = client['timeseries_data']
    collection = db['productivity_charts']

    results = list(collection.find({}))

    # Convert to DataFrame
    df = pd.DataFrame(results)
    df['date'] = pd.to_datetime(df['time_ist_date']).dt.date
    df['datetime'] = pd.to_datetime(df['time_ist_raw'])
    # Sort by actual datetime object
    df.sort_values('datetime', inplace=True)
    df = df[['datetime', 'time_usage_perc', 'avg_task_duration']]
    return df


# Get data (using sample data as fallback)
df = get_data_from_mongo()

# Page title
st.title('Usage and duration trend')


base = alt.Chart(df).encode(
    x=alt.X(
        'datetime:T',
        axis=alt.Axis(
            title='Date',
            labelColor='white',
            titleColor='white',
            labelAngle=45,
            format='%H:%M, %Y-%m-%d',
            labelFontSize=12,  # Bigger x-axis labels
            titleFontSize=16,  # Bigger x-axis title
        ),
    )
)

# Lines with better visibility
line1 = base.mark_line(color='#4CAF50', strokeWidth=3).encode(
    y=alt.Y(
        'time_usage_perc:Q',
        axis=alt.Axis(
            title='Time Usage %',
            format='%',
            labelColor='white',
            titleColor='#4CAF50',
            labelFontSize=14,  # Bigger y-axis labels
            titleFontSize=16,  # Bigger y-axis title
            tickCount=8,  # More tick marks
        ),
        scale=alt.Scale(domain=[0, 1]),
    )
)

line2 = base.mark_line(color='#FF5252', strokeWidth=3).encode(
    y=alt.Y(
        'avg_task_duration:Q',
        axis=alt.Axis(
            title='Avg Task Duration (mins)',
            labelColor='white',
            titleColor='#FF5252',
            labelFontSize=14,  # Bigger y-axis labels
            titleFontSize=16,  # Bigger y-axis title
            tickCount=8,  # More tick marks
        ),
    )
)
# After creating the chart, add this code:

# Get latest values
latest = df.iloc[-1]
latest_usage = latest['time_usage_perc'] * 100  # Convert to percentage
latest_duration = latest['avg_task_duration']

# Simple layered chart
# Make chart responsive to viewport
chart = (
    alt.layer(line1, line2)
    .resolve_scale(y='independent')
    .properties(width='container', height=500)
    .configure_view(continuousHeight=500, continuousWidth=800)
)

# Create responsive layout
col_chart, col_metrics = st.columns([4, 1], gap='medium')

with col_chart:
    # Create container with full height
    chart_container = st.container()
    with chart_container:
        st.altair_chart(chart, use_container_width=True, theme='streamlit')

with col_metrics:
    # Stack metrics vertically
    st.markdown(
        f"""
        <div style="text-align: center; padding: 10px; margin-bottom: 20px;">
            <h4 style="color: #4CAF50; margin-bottom: 5px;">Time Usage</h4>
            <h2 style="color: #4CAF50; font-size: 32px; margin: 0;">{latest_usage:.1f}%</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="text-align: center; padding: 10px;">
            <h4 style="color: #FF5252; margin-bottom: 5px;">Avg Task Duration</h4>
            <h2 style="color: #FF5252; font-size: 32px; margin: 0;">{latest_duration:.1f} mins</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
