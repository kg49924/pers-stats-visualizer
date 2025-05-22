import streamlit as st
import os
import altair as alt
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import pymongo
from pymongo import MongoClient

# Page config for full screen utilization
st.set_page_config(
    layout='wide',
    initial_sidebar_state='collapsed',
    page_title='Productivity Dashboard',
)

# Enhanced CSS for full page utilization and responsive design
st.markdown(
    """
<style>
    /* Remove all default padding and margins */
    .main .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
    }
    
    /* Hide Streamlit header and footer */
    header[data-testid="stHeader"] {
        display: none;
    }
    
    .stApp > footer {
        display: none;
    }
    
    /* Full height container */
    .stApp {
        margin: 0;
        padding: 0;
    }
    
    /* Main content area */
    section.main > div {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Ensure charts scale properly */
    .vega-embed {
        width: 100% !important;
        height: 100% !important;
    }
    
    /* Full viewport height for main container */
    .main-container {
        height: 100vh;
        display: flex;
        flex-direction: row;
        align-items: stretch;
    }
    
    /* Chart container */
    .chart-container {
        flex: 4;
        height: 100vh;
        padding: 1vh;
        box-sizing: border-box;
    }
    
    /* Metrics container */
    .metrics-container {
        flex: 1;
        height: 100vh;
        padding: 2vh 1vw;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: center;
        background: rgba(0, 0, 0, 0.02);
    }
    
    /* Responsive font sizes using clamp() */
    .metric-label {
        margin: 0;
        font-size: clamp(1rem, 2.5vw, 1.8rem);
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        margin: 0.5vh 0 2vh 0;
        font-size: clamp(2rem, 6vw, 4.5rem);
        font-weight: bold;
        line-height: 1;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-container {
            flex-direction: column;
            height: 100vh;
        }
        
        .chart-container {
            flex: 3;
            height: 70vh;
            padding: 0.5vh;
        }
        
        .metrics-container {
            flex: 1;
            height: 30vh;
            flex-direction: row;
            padding: 1vh;
        }
        
        .metric-item {
            flex: 1;
            text-align: center;
            padding: 0 1vw;
        }
        
        .metric-value {
            font-size: clamp(1.5rem, 8vw, 2.5rem);
            margin: 0.2vh 0;
        }
        
        .metric-label {
            font-size: clamp(0.8rem, 3vw, 1.2rem);
        }
    }
    
    /* Very small screens */
    @media (max-width: 480px) {
        .metric-value {
            font-size: clamp(1.2rem, 10vw, 2rem);
        }
        
        .metric-label {
            font-size: clamp(0.7rem, 4vw, 1rem);
        }
    }
    
    /* Large screens optimization */
    @media (min-width: 1400px) {
        .metric-value {
            font-size: clamp(3rem, 5vw, 6rem);
        }
        
        .metric-label {
            font-size: clamp(1.2rem, 2vw, 2.2rem);
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
    df['tasks_in_time'] = df['avg_task_duration'].apply(lambda x: 30 / x)
    df = df[['datetime', 'time_usage_perc', 'avg_task_duration', 'tasks_in_time']]
    df['target'] = 0.6
    return df


# Get data
df = get_data_from_mongo()

# Create base chart with responsive settings
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
            labelFontSize=14,
            titleFontSize=16,
            tickCount=8,
        ),
        scale=alt.Scale(domain=[0, 0.8]),
    )
)

line_target = base.mark_line(color='white', strokeDash=[5, 5]).encode(
    y=alt.Y(
        'target:Q',
        axis=None,
        scale=alt.Scale(domain=[0, 1]),
    )
)

# Get latest values
latest = df.iloc[-1]
latest_usage = latest['time_usage_perc'] * 100
tasks_in_45_mins = latest['tasks_in_time'] * 100

# Create chart optimized for full screen
chart = (
    alt.layer(line1, line2, line_target)
    .resolve_scale(y='independent')
    .properties(
        width='container',
        height=600,  # Fixed height that works well with full viewport
        padding={'left': 60, 'right': 60, 'top': 30, 'bottom': 60},
    )
)

# Use columns with full width
col_chart, col_metrics = st.columns([4, 1], gap='small')

with col_chart:
    # Chart with full container utilization
    st.altair_chart(chart, use_container_width=True, theme='streamlit')

with col_metrics:
    st.markdown(
        f"""
        <div class="metrics-container">
            <div class="metric-item">
                <h2 class="metric-label" style="color: #4CAF50;">Time Usage</h3>
                <h1 class="metric-value" style="color: #4CAF50;">{int(latest_usage)}%</h1>
            </div>
            <div class="metric-item">
                <h2 class="metric-label" style="color: #FF5252;">Task Completion</h2>
                <h1 class="metric-value" style="color: #FF5252;">{int(tasks_in_45_mins)}%</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Add JavaScript for dynamic height adjustment
st.markdown(
    """
    <script>
    function adjustHeight() {
        const viewportHeight = window.innerHeight;
        const chartElements = document.querySelectorAll('.vega-embed');
        
        chartElements.forEach(element => {
            if (window.innerWidth > 768) {
                element.style.height = (viewportHeight * 0.9) + 'px';
            } else {
                element.style.height = (viewportHeight * 0.6) + 'px';
            }
        });
    }
    
    // Adjust on load and resize
    window.addEventListener('load', adjustHeight);
    window.addEventListener('resize', adjustHeight);
    </script>
    """,
    unsafe_allow_html=True,
)
