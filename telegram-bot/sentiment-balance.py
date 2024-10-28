import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
from dotenv import load_dotenv
from plotly.subplots import make_subplots

from db.db_postgres import get_db_connection

load_dotenv()

class SentimentBalanceVisualizer:
    def __init__(self):
        pass
        
    def get_sentiment_data(self):
        """Get sentiment balance data from database."""
        conn = get_db_connection()
        
        # Query for daily sentiment averages
        daily_query = """
            WITH DailySentiment AS (
                SELECT 
                    DATE(timestamp) as date,
                    AVG(sentiment_positive) as avg_positive,
                    AVG(sentiment_negative) as avg_negative,
                    COUNT(*) as message_count
                FROM telegram_messages
                WHERE sentiment_analyzed = TRUE
                AND timestamp >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(timestamp)
                ORDER BY date
            )
            SELECT 
                date,
                avg_positive,
                avg_negative,
                (avg_positive - avg_negative) as sentiment_balance,
                message_count
            FROM DailySentiment
            ORDER BY date;
        """
        
        # Query for overall stats
        stats_query = """
            SELECT 
                COUNT(*) as total_messages,
                AVG(CASE WHEN sentiment_positive > sentiment_negative THEN 1 ELSE 0 END) as positive_ratio,
                AVG(sentiment_positive - sentiment_negative) as overall_balance
            FROM telegram_messages
            WHERE sentiment_analyzed = TRUE
            AND timestamp >= NOW() - INTERVAL '30 days';
        """
        
        daily_df = pd.read_sql_query(daily_query, conn)
        stats_df = pd.read_sql_query(stats_query, conn)
        conn.close()
        
        return daily_df, stats_df

    def create_sentiment_balance_chart(self, daily_df, stats_df):
        """Create an interactive chart showing sentiment balance trends."""
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                'Daily Sentiment Balance (Positive - Negative)',
                'Message Volume and Sentiment Comparison'
            ),
            vertical_spacing=0.2,
            specs=[[{"secondary_y": True}], [{"secondary_y": True}]]
        )

        # Add sentiment balance trace
        fig.add_trace(
            go.Scatter(
                x=daily_df['date'],
                y=daily_df['sentiment_balance'],
                name='Sentiment Balance',
                line=dict(color='#3498db', width=3),
                fill='tozeroy',
                fillcolor='rgba(52, 152, 219, 0.2)'
            ),
            row=1, col=1
        )

        # Add zero line for reference
        fig.add_hline(
            y=0, line_dash="dash", line_color="gray",
            annotation_text="Neutral", 
            annotation_position="right",
            row=1, col=1
        )

        # Add positive and negative lines with message volume
        fig.add_trace(
            go.Scatter(
                x=daily_df['date'],
                y=daily_df['avg_positive'],
                name='Positive',
                line=dict(color='#2ecc71', width=2)
            ),
            row=2, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=daily_df['date'],
                y=daily_df['avg_negative'],
                name='Negative',
                line=dict(color='#e74c3c', width=2)
            ),
            row=2, col=1
        )

        # Add message volume as bars on secondary y-axis
        fig.add_trace(
            go.Bar(
                x=daily_df['date'],
                y=daily_df['message_count'],
                name='Message Count',
                marker_color='rgba(155, 89, 182, 0.3)',
                opacity=0.5
            ),
            row=2, col=1,
            secondary_y=True
        )

        # Calculate overall stats for annotations
        overall_balance = stats_df['overall_balance'].iloc[0]
        positive_ratio = stats_df['positive_ratio'].iloc[0] * 100
        total_messages = stats_df['total_messages'].iloc[0]

        # Update layout
        fig.update_layout(
            title={
                'text': f"Community Sentiment Analysis (Last 30 Days)<br>" +
                       f"Overall Balance: {'Positive' if overall_balance > 0 else 'Negative'} " +
                       f"({abs(overall_balance):.3f})",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            height=1000,
            template='plotly_dark',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        # Update axes
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Sentiment Balance", row=1, col=1)
        fig.update_yaxes(title_text="Sentiment Score", row=2, col=1)
        fig.update_yaxes(title_text="Message Count", row=2, col=1, secondary_y=True)

        # Add annotations with statistics
        fig.add_annotation(
            text=f"Total Messages: {total_messages:,}<br>" +
                 f"Positive Ratio: {positive_ratio:.1f}%<br>" +
                 f"Average Balance: {overall_balance:.3f}",
            xref="paper", yref="paper",
            x=0.99, y=0.99,
            showarrow=False,
            font=dict(size=12),
            align="right",
            bgcolor="rgba(0,0,0,0.5)",
            bordercolor="gray",
            borderwidth=1,
            borderpad=4
        )

        # Write to HTML file
        fig.write_html("sentiment_balance.html")
        
        # Create summary DataFrame
        summary_data = {
            'Metric': ['Total Messages', 'Positive Message Ratio', 'Overall Sentiment Balance',
                      'Most Positive Day', 'Most Negative Day'],
            'Value': [
                f"{total_messages:,}",
                f"{positive_ratio:.1f}%",
                f"{overall_balance:.3f}",
                f"{daily_df.loc[daily_df['sentiment_balance'].idxmax(), 'date'].strftime('%Y-%m-%d')} ({daily_df['sentiment_balance'].max():.3f})",
                f"{daily_df.loc[daily_df['sentiment_balance'].idxmin(), 'date'].strftime('%Y-%m-%d')} ({daily_df['sentiment_balance'].min():.3f})"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv('sentiment_balance_summary.csv', index=False)
        
        return fig, summary_df

def main():
    visualizer = SentimentBalanceVisualizer()
    daily_df, stats_df = visualizer.get_sentiment_data()
    fig, summary_df = visualizer.create_sentiment_balance_chart(daily_df, stats_df)
    
    print("\nVisualization has been created: sentiment_balance.html")
    print("\nSentiment Balance Summary:")
    print(summary_df.to_string(index=False))

if __name__ == "__main__":
    main()