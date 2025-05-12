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
            format='%b %d',  # Format: May 08 14:30
        ),
    )
)

# Lines with better visibility
line1 = base.mark_line(color='#4CAF50', strokeWidth=3).encode(
    y=alt.Y(
        'time_usage_perc:Q',
        axis=alt.Axis(
            title='Time Usage %', format='%', labelColor='white', titleColor='#4CAF50'
        ),
        scale=alt.Scale(domain=[0, 1]),
    )
)

line2 = base.mark_line(color='#FF5252', strokeWidth=3).encode(
    y=alt.Y(
        'avg_task_duration:Q',
        axis=alt.Axis(
            title='Avg Task Duration (mins)', labelColor='white', titleColor='#FF5252'
        ),
    )
)

# Simple layered chart
chart = (
    alt.layer(line1, line2)
    .resolve_scale(y='independent')
    .properties(width='container', height=400)
)

st.altair_chart(chart, use_container_width=True)
