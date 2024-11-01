from typing import Tuple

import pandas as pd

from sentiment_analysis.dframes import DataAnalyzer


def get_top_sentiment_messages(analyzer: DataAnalyzer, n: int = 50) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get top positive and negative messages with their sentiment scores.
    
    Args:
        analyzer: DataAnalyzer instance
        n: Number of top messages to retrieve for each sentiment
        
    Returns:
        Tuple of (positive_df, negative_df)
    """
    # Get top positive messages
    positive_df = analyzer.get_top_messages(
        sentiment_type='positive',
        n=n,
        min_length=10,
        similarity_threshold=0.85,
        show_usernames=False
    )
    
    # Get top negative messages
    negative_df = analyzer.get_top_messages(
        sentiment_type='negative',
        n=n,
        min_length=10,
        similarity_threshold=0.85,
        show_usernames=False
    )
    
    # Select and rename columns for final output
    columns_to_keep = ['ID', 'User', 'Content', 'Timestamp', 'Score', 
                      'Positive', 'Negative', 'Helpful', 'Sarcastic']
    
    positive_df = positive_df[columns_to_keep]
    negative_df = negative_df[columns_to_keep]
    
    return positive_df, negative_df

# Usage:
analyzer = DataAnalyzer()
pos_df, neg_df = get_top_sentiment_messages(analyzer, n=50)

# Export to CSV
pos_df.to_csv('./sentiment_analysis/top_positive_messages.csv', index=False)
neg_df.to_csv('./sentiment_analysis/top_negative_messages.csv', index=False)

# Display preview
print("\nTop Positive Messages Preview:")
print(pos_df.head(3))
print("\nTop Negative Messages Preview:")
print(neg_df.head(3))