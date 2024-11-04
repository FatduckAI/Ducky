import os

import pandas as pd
import plotly.graph_objects as go
import psycopg2
from dotenv import load_dotenv
from plotly.subplots import make_subplots

from db.db_postgres import get_db_connection

load_dotenv()

class TopUsersSentimentVisualizer:
    def __init__(self):
        pass
        
    def get_top_users_data(self):
        """Get top users for each sentiment category."""
        conn = get_db_connection()
        
        # Fixed query with proper table aliases
        query = """
        WITH MinMessages AS (
            SELECT sender_username, COUNT(*) as msg_count
            FROM telegram_messages
            WHERE sentiment_analyzed = TRUE
            AND sender_username IS NOT NULL
            GROUP BY sender_username
            HAVING COUNT(*) >= 5
        ),
        RankedUsers AS (
            SELECT 
                t.sender_username,
                AVG(sentiment_positive) as positive_score,
                AVG(sentiment_negative) as negative_score,
                AVG(sentiment_helpful) as helpful_score,
                AVG(sentiment_sarcastic) as sarcastic_score,
                COUNT(*) as message_count,
                ROW_NUMBER() OVER (ORDER BY AVG(sentiment_positive) DESC) as positive_rank,
                ROW_NUMBER() OVER (ORDER BY AVG(sentiment_negative) DESC) as negative_rank,
                ROW_NUMBER() OVER (ORDER BY AVG(sentiment_helpful) DESC) as helpful_rank,
                ROW_NUMBER() OVER (ORDER BY AVG(sentiment_sarcastic) DESC) as sarcastic_rank
            FROM telegram_messages t
            JOIN MinMessages m ON t.sender_username = m.sender_username
            WHERE sentiment_analyzed = TRUE
            GROUP BY t.sender_username
        )
        SELECT 
            sender_username,
            positive_score,
            negative_score,
            helpful_score,
            sarcastic_score,
            message_count,
            positive_rank,
            negative_rank,
            helpful_rank,
            sarcastic_rank
        FROM RankedUsers
        WHERE positive_rank <= 3 
           OR negative_rank <= 3 
           OR helpful_rank <= 3 
           OR sarcastic_rank <= 3
        ORDER BY positive_rank;
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def create_top_users_chart(self, df):
        """Create an interactive chart showing top users in each sentiment category."""
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Most Positive Users',
                'Most Helpful Users',
                'Most Negative Users',
                'Most Sarcastic Users'
            ),
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )

        # Color scheme
        colors = {
            'positive': '#2ecc71',
            'helpful': '#3498db',
            'negative': '#e74c3c',
            'sarcastic': '#9b59b6'
        }

        # Add positive users (top left)
        top_positive = df.nsmallest(3, 'positive_rank')
        fig.add_trace(
            go.Bar(
                x=top_positive['sender_username'],
                y=top_positive['positive_score'],
                marker_color=colors['positive'],
                text=top_positive['positive_score'].round(2),
                textposition='auto',
                name='Positive Score',
                customdata=top_positive['message_count'],
                hovertemplate="User: %{x}<br>Positive Score: %{y:.2f}<br>Messages: %{customdata}<extra></extra>"
            ),
            row=1, col=1
        )

        # Add helpful users (top right)
        top_helpful = df.nsmallest(3, 'helpful_rank')
        fig.add_trace(
            go.Bar(
                x=top_helpful['sender_username'],
                y=top_helpful['helpful_score'],
                marker_color=colors['helpful'],
                text=top_helpful['helpful_score'].round(2),
                textposition='auto',
                name='Helpful Score',
                customdata=top_helpful['message_count'],
                hovertemplate="User: %{x}<br>Helpful Score: %{y:.2f}<br>Messages: %{customdata}<extra></extra>"
            ),
            row=1, col=2
        )

        # Add negative users (bottom left)
        top_negative = df.nsmallest(3, 'negative_rank')
        fig.add_trace(
            go.Bar(
                x=top_negative['sender_username'],
                y=top_negative['negative_score'],
                marker_color=colors['negative'],
                text=top_negative['negative_score'].round(2),
                textposition='auto',
                name='Negative Score',
                customdata=top_negative['message_count'],
                hovertemplate="User: %{x}<br>Negative Score: %{y:.2f}<br>Messages: %{customdata}<extra></extra>"
            ),
            row=2, col=1
        )

        # Add sarcastic users (bottom right)
        top_sarcastic = df.nsmallest(3, 'sarcastic_rank')
        fig.add_trace(
            go.Bar(
                x=top_sarcastic['sender_username'],
                y=top_sarcastic['sarcastic_score'],
                marker_color=colors['sarcastic'],
                text=top_sarcastic['sarcastic_score'].round(2),
                textposition='auto',
                name='Sarcastic Score',
                customdata=top_sarcastic['message_count'],
                hovertemplate="User: %{x}<br>Sarcastic Score: %{y:.2f}<br>Messages: %{customdata}<extra></extra>"
            ),
            row=2, col=2
        )

        # Update layout
        fig.update_layout(
            title_text="Top 3 Users in Each Sentiment Category",
            height=800,
            showlegend=False,
            template='plotly_dark',
            title_x=0.5,
            title_font_size=24
        )

        # Update axes
        for i in range(1, 3):
            for j in range(1, 3):
                fig.update_xaxes(title_text="Username", row=i, col=j, tickangle=45)
                fig.update_yaxes(title_text="Score", row=i, col=j, range=[0, 1])

        fig.add_annotation(
            text="* Only users with 5+ messages are included in rankings",
            xref="paper", yref="paper",
            x=0.5, y=-0.15,
            showarrow=False,
            font=dict(size=12, color="gray"),
            align="center"
        )

        # Write to HTML file
        fig.write_html("top_users_by_sentiment.html")
        
        # Create summary DataFrame
        summary_data = {
            'Category': ['Most Positive', 'Most Helpful', 'Most Negative', 'Most Sarcastic'],
            'First Place': [
                f"{top_positive.iloc[0]['sender_username']} ({top_positive.iloc[0]['positive_score']:.2f})",
                f"{top_helpful.iloc[0]['sender_username']} ({top_helpful.iloc[0]['helpful_score']:.2f})",
                f"{top_negative.iloc[0]['sender_username']} ({top_negative.iloc[0]['negative_score']:.2f})",
                f"{top_sarcastic.iloc[0]['sender_username']} ({top_sarcastic.iloc[0]['sarcastic_score']:.2f})"
            ],
            'Second Place': [
                f"{top_positive.iloc[1]['sender_username']} ({top_positive.iloc[1]['positive_score']:.2f})",
                f"{top_helpful.iloc[1]['sender_username']} ({top_helpful.iloc[1]['helpful_score']:.2f})",
                f"{top_negative.iloc[1]['sender_username']} ({top_negative.iloc[1]['negative_score']:.2f})",
                f"{top_sarcastic.iloc[1]['sender_username']} ({top_sarcastic.iloc[1]['sarcastic_score']:.2f})"
            ],
            'Third Place': [
                f"{top_positive.iloc[2]['sender_username']} ({top_positive.iloc[2]['positive_score']:.2f})",
                f"{top_helpful.iloc[2]['sender_username']} ({top_helpful.iloc[2]['helpful_score']:.2f})",
                f"{top_negative.iloc[2]['sender_username']} ({top_negative.iloc[2]['negative_score']:.2f})",
                f"{top_sarcastic.iloc[2]['sender_username']} ({top_sarcastic.iloc[2]['sarcastic_score']:.2f})"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv('top_users_summary.csv', index=False)
        
        return fig, summary_df

def main():
    visualizer = TopUsersSentimentVisualizer()
    df = visualizer.get_top_users_data()
    fig, summary_df = visualizer.create_top_users_chart(df)
    
    print("\nVisualization has been created: top_users_by_sentiment.html")
    print("\nTop Users Summary:")
    print(summary_df.to_string(index=False))

if __name__ == "__main__":
    main()