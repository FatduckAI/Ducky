import textwrap
import warnings
from difflib import SequenceMatcher

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from db.db_postgres import get_db_connection

warnings.filterwarnings('ignore')

# Set global pandas display options
pd.set_option('display.max_colwidth', None)  # Prevent column width truncation
pd.set_option('display.max_rows', None)      # Show all rows
pd.set_option('display.width', None)         # Don't limit display width
pd.set_option('display.max_columns', None)   # Show all columns
pd.set_option('display.expand_frame_repr', False)  # Don't wrap to multiple lines


class DataAnalyzer:
    def __init__(self):
        """Initialize analyzer and load data into DataFrame."""
        conn = get_db_connection()
        
        query = """
        SELECT *
        FROM telegram_messages
        WHERE sentiment_analyzed = TRUE;
        """
        self.df = pd.read_sql_query(query, conn)
        conn.close()
        
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df['sentiment_balance'] = self.df['sentiment_positive'] - self.df['sentiment_negative']
        self.df['date'] = self.df['timestamp'].dt.date
        self.df['hour'] = self.df['timestamp'].dt.hour
    
    def _are_messages_similar(self, msg1, msg2, threshold=0.85):
        """Check if two messages are similar using sequence matcher."""
        msg1 = str(msg1).lower().strip()
        msg2 = str(msg2).lower().strip()
        
        len_diff = abs(len(msg1) - len(msg2)) / max(len(msg1), len(msg2))
        if len_diff > 0.3:
            return False
        
        similarity = SequenceMatcher(None, msg1, msg2).ratio()
        return similarity >= threshold
    
    def _mask_username(self, username):
        """Create a consistent masked username."""
        if pd.isna(username):
            return "User_Unknown"
        return f"User_{hash(username) % 1000:03d}"
        
    def get_top_messages(self, sentiment_type='positive', n=5, min_length=10, similarity_threshold=0.85, show_usernames=False):
        """
        Get top messages by sentiment type, removing similar messages from same user.
        
        Parameters:
        - sentiment_type: 'positive', 'negative', 'helpful', 'sarcastic', or 'balance'
        - n: number of messages to return
        - min_length: minimum message length to consider
        - similarity_threshold: threshold for considering messages similar (0.0 to 1.0)
        - show_usernames: if True, shows actual usernames; if False, shows masked versions
        """
        valid_types = ['positive', 'negative', 'helpful', 'sarcastic', 'balance']
        if sentiment_type not in valid_types:
            raise ValueError(f"sentiment_type must be one of {valid_types}")

        # Filter out very short messages
        df_filtered = self.df[self.df['content'].str.len() > min_length].copy()
        
        # Determine which column to sort by
        column = 'sentiment_balance' if sentiment_type == 'balance' else f'sentiment_{sentiment_type}'
        
        # Sort by sentiment score
        df_sorted = df_filtered.sort_values(column, ascending=False)
        
        unique_messages = []
        used_indices = set()
        user_count = {}  # Track message count per user
        
        for idx, row in df_sorted.iterrows():
            if len(unique_messages) >= n:
                break
            
            if idx in used_indices:
                continue
            
            username = row['sender_username']
            
            # Check if this message is similar to any we've already kept
            is_duplicate = False
            for unique_msg in unique_messages:
                if (username == unique_msg['original_username'] and 
                    self._are_messages_similar(row['content'], unique_msg['content'], similarity_threshold)):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                displayed_username = username if show_usernames else self._mask_username(username)
                user_count[username] = user_count.get(username, 0) + 1
                content = str(row['content'])
  
                
                message_data = {
                    'message_id': row['message_id'],
                    'content': content,
                    'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M'),
                    'username': displayed_username,
                    'original_username': username,  # Keep original for duplicate checking
                    sentiment_type: round(row[column], 3),
                    'sentiment_positive': row['sentiment_positive'],
                    'sentiment_negative': row['sentiment_negative'],
                    'sentiment_helpful': row['sentiment_helpful'],
                    'sentiment_sarcastic': row['sentiment_sarcastic'],
                }
                
                unique_messages.append(message_data)
                
                # Mark similar messages from same user as used
                for other_idx, other_row in df_sorted.iterrows():
                    if (other_idx != idx and 
                        other_row['sender_username'] == username and
                        self._are_messages_similar(other_row['content'], row['content'], similarity_threshold)):
                        used_indices.add(other_idx)
        
        # Create DataFrame and clean up columns
        result_df = pd.DataFrame(unique_messages)
        if len(result_df) > 0:
            # Remove the original_username column and reorder
            result_df = result_df.drop('original_username', axis=1)
            columns = ['message_id', 'username', 'content', 'timestamp', sentiment_type, 'sentiment_positive', 'sentiment_negative', 'sentiment_helpful', 'sentiment_sarcastic']
            result_df = result_df[columns]
            
            # Rename columns for display
            column_names = {
                'message_id': 'ID',
                'username': 'User',
                'content': 'Content',
                sentiment_type: 'Score',
                'sentiment_positive': 'Positive',
                'sentiment_negative': 'Negative',
                'sentiment_helpful': 'Helpful',
                'sentiment_sarcastic': 'Sarcastic',
                'timestamp': 'Timestamp',
            }
            result_df = result_df.rename(columns=column_names)
        
        return result_df
    
    def get_most_active_users(self, n=10, show_usernames=False):
        """Get users with most messages and their sentiment profiles."""
        user_stats = (self.df.groupby('sender_username')
                     .agg({
                         'message_id': 'count',
                         'sentiment_positive': 'mean',
                         'sentiment_negative': 'mean',
                         'sentiment_balance': 'mean'
                     })
                     .round(3)
                     .sort_values('message_id', ascending=False)
                     .head(n))
        
        user_stats.columns = ['Message Count', 'Avg Positive', 'Avg Negative', 'Balance']
        
        if not show_usernames:
            # Create new index with masked usernames
            masked_index = [self._mask_username(username) for username in user_stats.index]
            user_stats.index = masked_index
        
        return user_stats
    
    def plot_sentiment_trends(self):
        """Plot sentiment trends over time."""
        daily_stats = self.df.groupby('date').agg({
            'sentiment_positive': 'mean',
            'sentiment_negative': 'mean',
            'message_id': 'count'
        }).reset_index()
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Scatter(x=daily_stats['date'], y=daily_stats['sentiment_positive'],
                      name='Positive', line=dict(color='green', width=2))
        )
        
        fig.add_trace(
            go.Scatter(x=daily_stats['date'], y=daily_stats['sentiment_negative'],
                      name='Negative', line=dict(color='red', width=2))
        )
        
        fig.add_trace(
            go.Bar(x=daily_stats['date'], y=daily_stats['message_id'],
                  name='Message Count', opacity=0.5),
            secondary_y=True
        )
        
        fig.update_layout(
            title='Sentiment Trends Over Time',
            template='plotly_dark',
            height=600
        )
        
        return fig
    
    def plot_hourly_patterns(self):
        """Plot hourly message patterns and sentiment."""
        hourly_stats = self.df.groupby('hour').agg({
            'sentiment_positive': 'mean',
            'sentiment_negative': 'mean',
            'message_id': 'count'
        }).reset_index()
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(x=hourly_stats['hour'], y=hourly_stats['message_id'],
                  name='Message Count', opacity=0.7),
            secondary_y=True
        )
        
        fig.add_trace(
            go.Scatter(x=hourly_stats['hour'], y=hourly_stats['sentiment_positive'],
                      name='Positive', line=dict(color='green', width=2))
        )
        
        fig.add_trace(
            go.Scatter(x=hourly_stats['hour'], y=hourly_stats['sentiment_negative'],
                      name='Negative', line=dict(color='red', width=2))
        )
        
        fig.update_layout(
            title='Hourly Activity and Sentiment Patterns',
            xaxis_title='Hour of Day',
            template='plotly_dark',
            height=500
        )
        
        return fig
    
    def get_sentiment_stats(self, by='overall', show_usernames=False):
        """
        Get sentiment statistics by different groupings.
        
        Parameters:
        - by: 'overall', 'date', 'hour', or 'user'
        - show_usernames: if True, shows actual usernames; if False, shows masked versions
        """
        valid_by = ['overall', 'date', 'hour', 'user']
        if by not in valid_by:
            raise ValueError(f"'by' must be one of {valid_by}")
        
        sentiment_cols = [
            'sentiment_positive', 
            'sentiment_negative', 
            'sentiment_helpful', 
            'sentiment_sarcastic', 
            'sentiment_balance'
        ]
        
        if by == 'overall':
            stats = self.df[sentiment_cols].agg([
                'count', 'mean', 'std', 'min', 'max'
            ]).round(3)
            
            # Rename columns for clarity
            stats.columns = [
                'Count', 'Average', 'Std Dev', 'Minimum', 'Maximum'
            ]
            # Rename index for clarity
            stats.index = [
                'Positive', 'Negative', 'Helpful', 
                'Sarcastic', 'Balance'
            ]
            return stats
            
        elif by == 'date':
            return (self.df.groupby('date')[sentiment_cols]
                   .agg(['mean', 'count'])
                   .round(3))
            
        elif by == 'hour':
            return (self.df.groupby('hour')[sentiment_cols]
                   .agg(['mean', 'count'])
                   .round(3))
            
        else:  # by user
            user_stats = (self.df.groupby('sender_username')[sentiment_cols]
                         .agg(['mean', 'count'])
                         .round(3)
                         .sort_values(('sentiment_positive', 'count'), 
                                    ascending=False))
            
            if not show_usernames:
                # Create new index with masked usernames
                masked_index = [self._mask_username(username) 
                              for username in user_stats.index]
                user_stats.index = masked_index
            
            return user_stats

    def get_sentiment_summary(self, show_usernames=False):
        """
        Get a simplified summary of sentiment statistics.
        """
        # Overall statistics
        overall = {
            'Total Messages': len(self.df),
            'Average Positive': self.df['sentiment_positive'].mean(),
            'Average Negative': self.df['sentiment_negative'].mean(),
            'Average Balance': self.df['sentiment_balance'].mean(),
            'Most Active Hour': self.df['hour'].mode().iloc[0],
            'Most Active Day': self.df['date'].mode().iloc[0]
        }
        
        # Top users
        top_users = self.df.groupby('sender_username').size()
        if not show_usernames:
            top_users.index = [self._mask_username(u) for u in top_users.index]
        
        top_users = top_users.sort_values(ascending=False).head(5)
        
        # Sentiment distribution
        sentiment_dist = pd.cut(
            self.df['sentiment_balance'],
            bins=[-1, -0.5, -0.2, 0.2, 0.5, 1],
            labels=['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']
        ).value_counts()
        
        return {
            'overall': pd.Series(overall).round(3),
            'top_users': top_users,
            'sentiment_distribution': sentiment_dist
        }
        
    def plot_detailed_sentiment_trends(self):
        daily_stats = self.df.groupby('date').agg({
            'sentiment_positive': 'mean',
            'sentiment_negative': 'mean',
            'message_id': 'count'
        }).reset_index()
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add sentiment lines
        fig.add_trace(
            go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['sentiment_positive'],
                name='Positive Sentiment',
                line=dict(color='green', width=2)
            )
        )
        
        fig.add_trace(
            go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['sentiment_negative'],
            name='Negative Sentiment',
            line=dict(color='red', width=2)
            )
        )
        
        # Add message volume bars
        fig.add_trace(
        go.Bar(
            x=daily_stats['date'],
            y=daily_stats['message_id'],
            name='Message Count',
            opacity=0.5,
            marker_color='rgba(100, 149, 237, 0.6)'
            ),
            secondary_y=True
        )
        
        # Update layout
        fig.update_layout(
        title='Sentiment Trends and Message Volume Over Time',
        template='plotly_white',
        height=600,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
        # Update axes
        fig.update_xaxes(title_text="Date", gridcolor='lightgray')
        fig.update_yaxes(
            title_text="Sentiment Score",
            gridcolor='lightgray',
            secondary_y=False
        )
        fig.update_yaxes(
            title_text="Message Count",
            gridcolor='lightgray',
            secondary_y=True
        )

        return fig

    def plot_detailed_hourly_patterns(self):
        hourly_stats = self.df.groupby('hour').agg({
            'sentiment_positive': 'mean',
            'sentiment_negative': 'mean',
            'message_id': 'count'
        }).reset_index()
    
        fig = make_subplots(specs=[[{"secondary_y": True}]])
    
        # Add message volume bars
        fig.add_trace(
              go.Bar(
                x=hourly_stats['hour'],
                y=hourly_stats['message_id'],
                name='Message Count',
                opacity=0.7,
                marker_color='rgba(100, 149, 237, 0.6)'
        ),
        secondary_y=True
    )
    
        # Add sentiment lines
        fig.add_trace(
            go.Scatter(
                x=hourly_stats['hour'],
            y=hourly_stats['sentiment_positive'],
            name='Positive Sentiment',
            line=dict(color='green', width=2)
        )
        )

        fig.add_trace(
            go.Scatter(
            x=hourly_stats['hour'],
            y=hourly_stats['sentiment_negative'],
            name='Negative Sentiment',
            line=dict(color='red', width=2)
        )
    )
    
        # Update layout
        fig.update_layout(
            title='Hourly Activity and Sentiment Patterns',
            template='plotly_white',
            height=500,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
                x=0.01
            )
        )
    
        # Update axes
        fig.update_xaxes(
            title_text="Hour of Day",
            gridcolor='lightgray',
            tickmode='array',
            ticktext=[f'{h:02d}:00' for h in range(24)],
                tickvals=list(range(24))
        )
        fig.update_yaxes(
            title_text="Sentiment Score",
            gridcolor='lightgray',
            secondary_y=False
        )
        fig.update_yaxes(
            title_text="Message Count",
            gridcolor='lightgray',
            secondary_y=True
        )

        return fig
      
    def plot_simple_sentiment_timeline(self, interval='hour'):
      """
      Plot a simple timeline showing just positive and negative sentiment trends.
      
      Parameters:
      - interval: 'hour' or 'day' to control data granularity
      """
      if interval == 'hour':
          # Create timestamp column for hourly grouping
          self.df['datetime'] = pd.to_datetime(self.df['timestamp'])
          
          # Group by hour
          stats = (self.df.groupby(pd.Grouper(key='datetime', freq='H'))
                  .agg({
                      'sentiment_positive': 'mean',
                      'sentiment_negative': 'mean'
                  })
                  .reset_index())
          
          # Remove rows with no data
          stats = stats.dropna()
          
          x_axis = stats['datetime']
          hover_template = '%{x|%Y-%m-%d %H:%M} <br>Score: %{y:.3f}'
          
      else:  # daily interval
          # Group by date
          stats = self.df.groupby('date').agg({
              'sentiment_positive': 'mean',
              'sentiment_negative': 'mean'
          }).reset_index()
          
          x_axis = stats['date']
          hover_template = '%{x|%Y-%m-%d} <br>Score: %{y:.3f}'
      
      # Create figure
      fig = go.Figure()
      
      # Add positive sentiment line
      fig.add_trace(
          go.Scatter(
              x=x_axis,
              y=stats['sentiment_positive'],
              name='Positive',
              line=dict(color='green', width=2),
              hovertemplate=hover_template
          )
      )
      
      # Add negative sentiment line
      fig.add_trace(
          go.Scatter(
              x=x_axis,
              y=stats['sentiment_negative'],
              name='Negative',
              line=dict(color='red', width=2),
              hovertemplate=hover_template
          )
      )
      
      # Update layout
      fig.update_layout(
          title=f'Sentiment Timeline ({interval}ly intervals)',
          xaxis_title='Time',
          yaxis_title='Sentiment Score',
          template='plotly_white',
          height=400,
          hovermode='x unified',
          showlegend=True,
          legend=dict(
              yanchor="top",
              y=0.99,
              xanchor="left",
              x=0.01
          )
      )
      
      # Update axes
      fig.update_xaxes(
          gridcolor='lightgray',
          rangeslider_visible=True  # Add range slider for easier navigation
      )
      fig.update_yaxes(
          gridcolor='lightgray',
          zeroline=True,
          zerolinecolor='gray',
          zerolinewidth=1
      )
      
      return fig
"""
      # Get overall sentiment stats
print("Overall Sentiment Statistics:")
overall_stats = analyzer.get_sentiment_stats(by='overall')
display(overall_stats)

# Get user-based stats (masked)
print("\nUser Sentiment Statistics (Masked):")
user_stats = analyzer.get_sentiment_stats(by='user', show_usernames=False)
display(user_stats)

# Get hourly stats
print("\nHourly Sentiment Statistics:")
hourly_stats = analyzer.get_sentiment_stats(by='hour')
display(hourly_stats)

"""