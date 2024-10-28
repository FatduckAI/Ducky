import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from dotenv import load_dotenv
from plotly.subplots import make_subplots

from db.db_postgres import get_db_connection

# Load environment variables
load_dotenv()

class SentimentVisualizer:
    def __init__(self):
        pass
        
    def get_data(self):
        """Get sentiment data from database."""
        conn = get_db_connection()
        
        # Daily averages
        daily_query = """
            SELECT 
                DATE(timestamp) as date,
                AVG(sentiment_positive) as positive,
                AVG(sentiment_negative) as negative,
                AVG(sentiment_helpful) as helpful,
                AVG(sentiment_sarcastic) as sarcastic,
                COUNT(*) as message_count
            FROM telegram_messages
            WHERE sentiment_analyzed = TRUE
            AND timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(timestamp)
            ORDER BY date;
        """
        
        # Hourly pattern
        hourly_query = """
            SELECT 
                EXTRACT(HOUR FROM timestamp) as hour,
                AVG(sentiment_positive) as positive,
                AVG(sentiment_negative) as negative,
                AVG(sentiment_helpful) as helpful,
                AVG(sentiment_sarcastic) as sarcastic,
                COUNT(*) as message_count
            FROM telegram_messages
            WHERE sentiment_analyzed = TRUE
            GROUP BY hour
            ORDER BY hour;
        """
        
        # Top users query
        users_query = """
            SELECT 
                sender_username,
                AVG(sentiment_positive) as positive,
                AVG(sentiment_negative) as negative,
                AVG(sentiment_helpful) as helpful,
                AVG(sentiment_sarcastic) as sarcastic,
                COUNT(*) as message_count
            FROM telegram_messages
            WHERE sentiment_analyzed = TRUE
            AND sender_username IS NOT NULL
            GROUP BY sender_username
            HAVING COUNT(*) >= 10
            ORDER BY COUNT(*) DESC
            LIMIT 20;
        """
        
        daily_df = pd.read_sql_query(daily_query, conn)
        hourly_df = pd.read_sql_query(hourly_query, conn)
        users_df = pd.read_sql_query(users_query, conn)
        
        conn.close()
        return daily_df, hourly_df, users_df

    def create_daily_trends(self, df):
        """Create daily sentiment trends chart."""
        fig = go.Figure()
        
        # Add traces for each sentiment
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['positive'],
            name='Positive', line=dict(color='#2ecc71', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['negative'],
            name='Negative', line=dict(color='#e74c3c', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['helpful'],
            name='Helpful', line=dict(color='#3498db', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=df['date'], y=df['sarcastic'],
            name='Sarcastic', line=dict(color='#9b59b6', width=2)
        ))

        # Update layout
        fig.update_layout(
            title='Daily Sentiment Trends (30 Days)',
            xaxis_title='Date',
            yaxis_title='Average Sentiment Score',
            template='plotly_dark',
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            )
        )
        
        fig.write_html("sentiment_daily_trends.html")
        return fig

    def create_hourly_pattern(self, df):
        """Create hourly pattern chart."""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Hourly Sentiment Pattern', 'Message Volume by Hour'),
            vertical_spacing=0.15
        )
        
        # Add sentiment traces
        fig.add_trace(
            go.Scatter(x=df['hour'], y=df['positive'], name='Positive',
                      line=dict(color='#2ecc71', width=2)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['hour'], y=df['negative'], name='Negative',
                      line=dict(color='#e74c3c', width=2)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['hour'], y=df['helpful'], name='Helpful',
                      line=dict(color='#3498db', width=2)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['hour'], y=df['sarcastic'], name='Sarcastic',
                      line=dict(color='#9b59b6', width=2)),
            row=1, col=1
        )
        
        # Add message volume bar chart
        fig.add_trace(
            go.Bar(x=df['hour'], y=df['message_count'], name='Message Count',
                  marker_color='#f39c12'),
            row=2, col=1
        )

        # Update layout
        fig.update_layout(
            height=800,
            template='plotly_dark',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            )
        )
        
        fig.update_xaxes(title_text="Hour of Day", row=2, col=1)
        fig.update_yaxes(title_text="Sentiment Score", row=1, col=1)
        fig.update_yaxes(title_text="Message Count", row=2, col=1)
        
        fig.write_html("sentiment_hourly_pattern.html")
        return fig

    def create_user_analysis(self, df):
        """Create user sentiment analysis chart."""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                'Top Users by Message Count',
                'Average Sentiment by User'
            ),
            vertical_spacing=0.25,
            specs=[[{"type": "bar"}], [{"type": "heatmap"}]]
        )
        
        # Message count bar chart
        fig.add_trace(
            go.Bar(
                x=df['sender_username'],
                y=df['message_count'],
                name='Message Count',
                marker_color='#f39c12'
            ),
            row=1, col=1
        )
        
        # Sentiment heatmap data
        sentiment_data = df[['positive', 'negative', 'helpful', 'sarcastic']].values.T
        
        # Sentiment heatmap
        fig.add_trace(
            go.Heatmap(
                z=sentiment_data,
                x=df['sender_username'],
                y=['Positive', 'Negative', 'Helpful', 'Sarcastic'],
                colorscale='Viridis',
                name='Sentiment'
            ),
            row=2, col=1
        )

        # Update layout
        fig.update_layout(
            height=1000,
            template='plotly_dark',
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Username", row=1, col=1)
        fig.update_xaxes(title_text="Username", row=2, col=1)
        fig.update_yaxes(title_text="Message Count", row=1, col=1)
        fig.update_yaxes(title_text="Sentiment Type", row=2, col=1)
        
        fig.write_html("user_sentiment_analysis.html")
        return fig

def main():
    visualizer = SentimentVisualizer()
    daily_df, hourly_df, users_df = visualizer.get_data()
    
    # Create all visualizations
    visualizer.create_daily_trends(daily_df)
    visualizer.create_hourly_pattern(hourly_df)
    visualizer.create_user_analysis(users_df)
    
    print("Visualizations have been created:")
    print("1. sentiment_daily_trends.html")
    print("2. sentiment_hourly_pattern.html")
    print("3. user_sentiment_analysis.html")

if __name__ == "__main__":
    main()