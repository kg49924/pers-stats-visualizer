import streamlit as st
import os
import altair as alt
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    layout='wide',
    initial_sidebar_state='collapsed',
    page_title='Productivity Dashboard',
)

# Minimal CSS
st.markdown(
    """
<style>
    .main .block-container {padding: 0 !important; margin: 0 !important; max-width: 100% !important;}
    header[data-testid="stHeader"], .stApp > footer {display: none;}
    .metric-label {font-size: 1.5rem; font-weight: 500; margin: 0;}
    .metric-value {font-size: 3.5rem; font-weight: bold; margin: 0.5rem 0;}
    @media (max-width: 768px) {
        .metric-value {font-size: 2rem;}
        .metric-label {font-size: 1rem;}
    }
</style>
<meta http-equiv="refresh" content="30">
""",
    unsafe_allow_html=True,
)


# Single MongoDB client
@st.cache_resource
def get_mongo_client():
    return MongoClient(
        os.environ.get('PERS_MONGO_DB', 'mongodb://localhost:27017/'),
        serverSelectionTimeoutMS=2000,
    )


# Cache historical data (older than 1 hour) for 24 hours
@st.cache_data(ttl=86400)
def get_historical_data(cutoff_time):
    try:
        client = get_mongo_client()
        db = client['timeseries_data']

        pipeline = [
            {'$match': {'time_ist_raw': {'$lt': cutoff_time}}},
            {
                '$project': {
                    'datetime': {'$dateFromString': {'dateString': '$time_ist_raw'}},
                    'time_usage_perc': 1,
                    'avg_task_duration': 1,
                    '_id': 0,
                }
            },
            {'$sort': {'datetime': 1}},
        ]

        results = list(db['productivity_charts'].aggregate(pipeline))
        return pd.DataFrame(results) if results else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# Get recent data (no cache)
def get_recent_data(cutoff_time):
    try:
        client = get_mongo_client()
        db = client['timeseries_data']

        pipeline = [
            {'$match': {'time_ist_raw': {'$gte': cutoff_time}}},
            {
                '$project': {
                    'datetime': {'$dateFromString': {'dateString': '$time_ist_raw'}},
                    'time_usage_perc': 1,
                    'avg_task_duration': 1,
                    '_id': 0,
                }
            },
            {'$sort': {'datetime': 1}},
        ]

        results = list(db['productivity_charts'].aggregate(pipeline))
        return pd.DataFrame(results) if results else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# Get all data
def get_all_data():
    cutoff = (datetime.now() - timedelta(hours=1)).isoformat()

    # Get cached historical + fresh recent data
    hist_df = get_historical_data(cutoff)
    recent_df = get_recent_data(cutoff)

    # Combine
    df = (
        pd.concat([hist_df, recent_df], ignore_index=True)
        if not hist_df.empty or not recent_df.empty
        else pd.DataFrame()
    )
    df = df[df['datetime'] >= datetime.now() - timedelta(days=5)]
    if df.empty:
        return None

    # Process
    df = df.drop_duplicates(subset=['datetime']).sort_values('datetime')
    df['tasks_in_time'] = 30 / df['avg_task_duration'].clip(lower=0.1)
    df['target'] = 0.6

    return df[['datetime', 'time_usage_perc', 'tasks_in_time', 'target']]


# Get data
df = get_all_data()

if df is None or df.empty:
    st.error('Unable to fetch data')
    st.stop()
base = alt.Chart(df).encode(
    x=alt.X(
        'datetime:T',
        axis=alt.Axis(
            title=None,
            labelColor='white',
            titleColor='white',
            labelAngle=45,
            format='%H:%M, %Y-%m-%d',
            labelFontSize=10,
            labelPadding=20,
        ),
    )
)
line1 = base.mark_line(color='#4CAF50', strokeWidth=3).encode(
    y=alt.Y(
        'time_usage_perc:Q',
        axis=alt.Axis(
            title='Time Usage %',
            format='%',
            labelColor='white',
            titleColor='#4CAF50',
            labelFontSize=20,
            titleFontSize=20,
            tickCount=5,
        ),
        scale=alt.Scale(domain=[0, 0.8]),
    )
)

line2 = base.mark_line(color='#FF5252', strokeWidth=3).encode(
    y=alt.Y(
        'tasks_in_time:Q',
        axis=alt.Axis(
            title='Task % in 30 mins',
            format='%',
            labelColor='white',
            titleColor='#FF5252',
            labelFontSize=20,
            titleFontSize=20,
            tickCount=5,
        ),
        scale=alt.Scale(domain=[0, 0.8]),
    )
)

line_target = base.mark_line(color='white', strokeDash=[5, 5]).encode(
    y=alt.Y(
        'target:Q',
        axis=None,
        scale=alt.Scale(domain=[0, 0.8]),  # Same scale as time_usage_perc
    )
)
# Create chart
# Layout
chart = (
    alt.layer(line1, line2, line_target)
    .resolve_scale(y='independent')
    .properties(
        width='container',
        height=700,
        padding={'left': 20, 'right': 20, 'top': 20, 'bottom': 40},
    )
)
# Use more flexible column ratios
col_chart, col_metrics = st.columns([4, 1], gap='small')

with col_chart:
    # Use container for better responsiveness
    with st.container():
        st.altair_chart(chart, use_container_width=True, theme='streamlit')

with col_metrics:
    latest = df.iloc[-1]
    st.markdown(
        f"""
        <div style="height: 100vh; display: flex; flex-direction: column; justify-content: center;">
            <div style="text-align: center;">
                <h2 class="metric-label" style="color: #4CAF50;">Time Usage</h2>
                <h1 class="metric-value" style="color: #4CAF50;">{int(latest['time_usage_perc'] * 100)}%</h1>
            </div>
            <div style="text-align: center; margin-top: 3rem;">
                <h2 class="metric-label" style="color: #FF5252;">Task Completion</h2>
                <h1 class="metric-value" style="color: #FF5252;">{int(latest['tasks_in_time'] * 100)}%</h1>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )
