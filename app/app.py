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

# Add custom CSS for better responsive behavior
st.markdown(
    """
<style>
    /* Make the main container fully responsive */
    .block-container {
        padding: 1rem 1rem 10rem;
        max-width: 100%;
    }
    
    /* Ensure charts scale properly */
    .vega-embed {
        width: 100% !important;
    }
    
    /* Responsive metrics container */
    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 100% !important;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)

# Auto-refresh setup
refresh_interval = 30
st.markdown(
    f"""
    <meta http-equiv="refresh" content="{refresh_interval}">
    """,
    unsafe_allow_html=True,
)

# [Your existing MongoDB functions remain the same]


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
    df['tasks_in_time'] = df['avg_task_duration'].apply(lambda x: 45 / x)
    df = df[['datetime', 'time_usage_perc', 'avg_task_duration', 'tasks_in_time']]
    return df


# Page title

# Get data
df = get_data_from_mongo()

# Create base chart with improved responsive settings
base = alt.Chart(df).encode(
    x=alt.X(
        'datetime:T',
        axis=alt.Axis(
            title='Date',
            labelColor='white',
            titleColor='white',
            labelAngle=45,
            format='%H:%M, %Y-%m-%d',
            labelFontSize=12,
            titleFontSize=16,
        ),
    )
)

# Create lines
line1 = base.mark_line(color='#4CAF50', strokeWidth=3).encode(
    y=alt.Y(
        'time_usage_perc:Q',
        axis=alt.Axis(
            title='Time Usage %',
            format='%',
            labelColor='white',
            titleColor='#4CAF50',
            labelFontSize=14,
            titleFontSize=16,
            tickCount=8,
        ),
        scale=alt.Scale(domain=[0, 1]),
    )
)

line2 = base.mark_line(color='#FF5252', strokeWidth=3).encode(
    y=alt.Y(
        'tasks_in_time:Q',
        axis=alt.Axis(
            title='Task % in 45 mins',
            format='%',
            labelColor='white',
            titleColor='#FF5252',
            labelFontSize=14,
            titleFontSize=16,
            tickCount=8,
        ),
    )
)
# Get latest values
latest = df.iloc[-1]
latest_usage = latest['time_usage_perc'] * 100
tasks_in_45_mins = latest['tasks_in_time'] * 100

# Create chart with improved responsive properties
chart = (
    alt.layer(line1, line2)
    .resolve_scale(y='independent')
    .properties(
        width='container',
        height=600,
        padding={'left': 50, 'right': 50, 'top': 20, 'bottom': 50},
    )
)

# Use more flexible column ratios
col_chart, col_metrics = st.columns([4, 1], gap='small')

with col_chart:
    # Use container for better responsiveness
    with st.container():
        st.altair_chart(chart, use_container_width=True, theme='streamlit')

with col_metrics:
    st.markdown(
        f"""
        <div style="padding: 2vh 1vw; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <div style="padding: 1vh 0; margin-bottom: 3vh;">
                <p style="color: #4CAF50; margin: 0; font-size: clamp(14px, 2vw, 20px);">Time Usage</p>
                <h2 style="color: #4CAF50; font-size: clamp(24px, 3vw, 36px); margin: 0.5vh 0;">{latest_usage:.1f} %</h2>
            </div>
            <div style="padding: 1vh 0;">
                <p style="color: #FF5252; margin: 0; font-size: clamp(14px, 2vw, 20px);">Task Completion</p>
                <h2 style="color: #FF5252; font-size: clamp(24px, 3vw, 36px); margin: 0.5vh 0;">{tasks_in_45_mins:.1f} %</h2>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
