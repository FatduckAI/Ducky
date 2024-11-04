# Import required libraries
import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from IPython.display import display

from db.db_postgres import get_db_connection

# Load environment variables (create a .env file with your database credentials)
load_dotenv()



# Test connection and show table info
def test_connection():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get table information
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns
        WHERE table_name = 'telegram_messages'
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    print("Table Structure:")
    for col in columns:
        print(f"{col[0]}: {col[1]}")
    
    # Get row count
    cur.execute("SELECT COUNT(*) FROM telegram_messages;")
    count = cur.fetchone()[0]
    print(f"\nTotal messages: {count:,}")
    
    cur.close()
    conn.close()

# Quick data preview
def preview_data():
    conn = get_db_connection()
    
    query = """
    SELECT 
        message_id,
        chat_id,
        sender_username,
        content,
        timestamp,
        sentiment_positive,
        sentiment_negative,
        sentiment_helpful,
        sentiment_sarcastic
    FROM telegram_messages
    WHERE sentiment_analyzed = TRUE
    ORDER BY timestamp DESC
    LIMIT 5;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Test the connection and show table structure
test_connection()

# Show data preview
print("\nRecent Messages Preview:")
recent_df = preview_data()
display(recent_df)

# Now let's create some basic analysis functions

def get_sentiment_overview():
    """Get sentiment statistics for different time periods."""
    conn = get_db_connection()
    
    query = """
    WITH TimeRanges AS (
        SELECT 
            CASE 
                WHEN timestamp >= NOW() - INTERVAL '24 hours' THEN 'Last 24 Hours'
                WHEN timestamp >= NOW() - INTERVAL '7 days' THEN 'Last 7 Days'
                WHEN timestamp >= NOW() - INTERVAL '30 days' THEN 'Last 30 Days'
                ELSE 'Older'
            END as time_period,
            sentiment_positive,
            sentiment_negative,
            sentiment_helpful,
            sentiment_sarcastic
        FROM telegram_messages
        WHERE sentiment_analyzed = TRUE
    )
    SELECT 
        time_period,
        COUNT(*) as message_count,
        ROUND(AVG(sentiment_positive)::numeric, 3) as avg_positive,
        ROUND(AVG(sentiment_negative)::numeric, 3) as avg_negative,
        ROUND(AVG(sentiment_helpful)::numeric, 3) as avg_helpful,
        ROUND(AVG(sentiment_sarcastic)::numeric, 3) as avg_sarcastic
    FROM TimeRanges
    GROUP BY time_period
    ORDER BY 
        CASE time_period
            WHEN 'Last 24 Hours' THEN 1
            WHEN 'Last 7 Days' THEN 2
            WHEN 'Last 30 Days' THEN 3
            ELSE 4
        END;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Get and display sentiment overview
sentiment_overview = get_sentiment_overview()
print("\nSentiment Overview by Time Period:")
display(sentiment_overview)

def get_hourly_activity():
    """Analyze message activity by hour of day."""
    conn = get_db_connection()
    
    query = """
    SELECT 
        EXTRACT(HOUR FROM timestamp) as hour_of_day,
        COUNT(*) as message_count,
        ROUND(AVG(sentiment_positive)::numeric, 3) as avg_positive,
        ROUND(AVG(sentiment_negative)::numeric, 3) as avg_negative
    FROM telegram_messages
    WHERE sentiment_analyzed = TRUE
    AND timestamp >= NOW() - INTERVAL '7 days'
    GROUP BY hour_of_day
    ORDER BY hour_of_day;
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Create hourly activity visualization
hourly_df = get_hourly_activity()

fig = go.Figure()

# Add message count bars
fig.add_trace(go.Bar(
    x=hourly_df['hour_of_day'],
    y=hourly_df['message_count'],
    name='Message Count',
    opacity=0.7
))

# Add sentiment lines
fig.add_trace(go.Scatter(
    x=hourly_df['hour_of_day'],
    y=hourly_df['avg_positive'],
    name='Positive Sentiment',
    line=dict(color='green', width=2),
    yaxis='y2'
))

fig.add_trace(go.Scatter(
    x=hourly_df['hour_of_day'],
    y=hourly_df['avg_negative'],
    name='Negative Sentiment',
    line=dict(color='red', width=2),
    yaxis='y2'
))

fig.update_layout(
    title='Message Activity and Sentiment by Hour',
    xaxis_title='Hour of Day',
    yaxis_title='Message Count',
    yaxis2=dict(
        title='Sentiment Score',
        overlaying='y',
        side='right'
    ),
    barmode='group'
)

fig.show()

# Example of how to query specific time periods or users
def analyze_specific_period(start_date, end_date, chat_id=None):
    """Analyze messages for a specific time period."""
    conn = get_db_connection()
    
    query = """
    SELECT 
        DATE(timestamp) as date,
        COUNT(*) as message_count,
        ROUND(AVG(sentiment_positive)::numeric, 3) as avg_positive,
        ROUND(AVG(sentiment_negative)::numeric, 3) as avg_negative,
        ROUND(AVG(sentiment_helpful)::numeric, 3) as avg_helpful
    FROM telegram_messages
    WHERE sentiment_analyzed = TRUE
    AND timestamp BETWEEN %s AND %s
    """
    
    if chat_id:
        query += " AND chat_id = %s"
        params = [start_date, end_date, chat_id]
    else:
        params = [start_date, end_date]
    
    query += " GROUP BY date ORDER BY date;"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# Example usage:
start_date = datetime.now() - timedelta(days=7)
end_date = datetime.now()
period_analysis = analyze_specific_period(start_date, end_date)
print("\nLast 7 Days Analysis:")
display(period_analysis)

# Save this code in a .py file for reuse
"""
To use this code:
1. Create a .env file with your database credentials:
   DB_HOST=your_host
   DB_NAME=your_database
   DB_USER=your_user
   DB_PASSWORD=your_password
   DB_PORT=5432

2. Import and use functions as needed:
   from analysis_helpers import get_db_connection, analyze_specific_period

3. Run analyses:
   period_analysis = analyze_specific_period(
       start_date=datetime.now() - timedelta(days=7),
       end_date=datetime.now()
   )
"""