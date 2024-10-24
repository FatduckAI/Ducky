# follower_utils.py

import os
from datetime import datetime
from typing import Dict, List, Tuple

import pytz
import tweepy
from psycopg2.extras import execute_batch

from agents.twitter.twitter_client import twitter_client
from db.db_postgres import get_db_connection

EST = pytz.timezone('US/Eastern')


def store_follower_batch(cur, followers_batch: List[tuple], history_batch: List[tuple]) -> None:
    """Store batches of follower data and their history"""
    
    # Upsert followers
    execute_batch(cur, """
        INSERT INTO followers (
            id, username, name, created_at, verified,
            followers_count, following_count, tweet_count,
            description, location, profile_image_url,
            last_updated, is_active
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            username = EXCLUDED.username,
            name = EXCLUDED.name,
            verified = EXCLUDED.verified,
            followers_count = EXCLUDED.followers_count,
            following_count = EXCLUDED.following_count,
            tweet_count = EXCLUDED.tweet_count,
            description = EXCLUDED.description,
            location = EXCLUDED.location,
            profile_image_url = EXCLUDED.profile_image_url,
            last_updated = EXCLUDED.last_updated,
            is_active = TRUE
    """, followers_batch)
    
    # Insert history records
    execute_batch(cur, """
        INSERT INTO followers_history (
            follower_id, followers_count, following_count, tweet_count, snapshot_date
        ) VALUES (%s, %s, %s, %s, %s)
    """, history_batch)

def get_new_followers(batch_size: int = 1000) -> Tuple[int, int, List[str]]:
    """
    Fetch new followers since last check and update existing follower metrics.
    
    Args:
        twitter_client: Authenticated Tweepy client
        batch_size: Number of followers to process in each batch
    
    Returns:
        tuple: (new_followers_count, updated_followers_count, list of any errors)
    """
    new_followers_count = 0
    updated_followers_count = 0
    errors = []
    
    conn = None
    cur = None
    
    try:
        # Connect to the database
        conn = get_db_connection()
        if not conn:
            raise Exception("Could not establish database connection")
            
        cur = conn.cursor()
        
        # Get authenticated user's ID
        me = twitter_client.get_me()
        print(me.data.id)
        if not me or not me.data:
            raise Exception("Could not retrieve authenticated user data")
        
        # Get current timestamp in EST
        current_time = datetime.now(EST).isoformat()
        
        # Get current follower IDs from database
        cur.execute("SELECT id FROM followers WHERE is_active = TRUE")
        existing_follower_ids = set(row[0] for row in cur.fetchall())
        
        # Start new sync run
        cur.execute("""
            INSERT INTO follower_sync_runs (run_timestamp, run_status) 
            VALUES (%s, 'in_progress') 
            RETURNING id
        """, (current_time,))
        current_run_id = cur.fetchone()[0]
        conn.commit()
        
        try:
            current_follower_ids = set()
            followers_batch = []
            history_batch = []
            pagination_token = None
            
            while True:
                print(os.environ.get('TWITTER_ACCESS_TOKEN'))
                response = twitter_client.get_users_followers(
                    id=me.data.id,
                    max_results=100,
                    user_fields=[
                        'created_at',
                        'description',
                        'location',
                        'profile_image_url',
                        'public_metrics',
                        'verified'
                    ],
                    pagination_token=pagination_token
                )
                
                if not response.data:
                    break
                
                for follower in response.data:
                    current_follower_ids.add(follower.id)
                    is_new = follower.id not in existing_follower_ids
                    
                    if is_new:
                        new_followers_count += 1
                    else:
                        updated_followers_count += 1
                    
                    follower_data = (
                        follower.id,
                        follower.username,
                        follower.name,
                        follower.created_at.isoformat(),
                        follower.verified,
                        follower.public_metrics['followers_count'],
                        follower.public_metrics['following_count'],
                        follower.public_metrics['tweet_count'],
                        getattr(follower, 'description', None),
                        getattr(follower, 'location', None),
                        getattr(follower, 'profile_image_url', None),
                        current_time,
                        True
                    )
                    
                    history_data = (
                        follower.id,
                        follower.public_metrics['followers_count'],
                        follower.public_metrics['following_count'],
                        follower.public_metrics['tweet_count'],
                        current_time
                    )
                    
                    followers_batch.append(follower_data)
                    history_batch.append(history_data)
                    
                    if len(followers_batch) >= batch_size:
                        store_follower_batch(cur, followers_batch, history_batch)
                        followers_batch = []
                        history_batch = []
                
                pagination_token = response.meta.get('next_token')
                if not pagination_token:
                    break
            
            # Store any remaining followers
            if followers_batch:
                store_follower_batch(cur, followers_batch, history_batch)
            
            # Mark unfollowed users
            unfollowed_ids = existing_follower_ids - current_follower_ids
            if unfollowed_ids:
                cur.execute("""
                    UPDATE followers 
                    SET is_active = FALSE, 
                        last_updated = %s 
                    WHERE id = ANY(%s)
                """, (current_time, list(unfollowed_ids)))
            
            # Update sync run status
            cur.execute("""
                UPDATE follower_sync_runs 
                SET run_status = 'success',
                    total_followers = %s,
                    new_followers = %s,
                    updated_followers = %s
                WHERE id = %s
            """, (len(current_follower_ids), new_followers_count, updated_followers_count, current_run_id))
            
            conn.commit()
            
        except Exception as e:
            error_msg = str(e)
            errors.append(f"Error during follower sync: {error_msg}")
            
            # Mark sync run as failed
            cur.execute("""
                UPDATE follower_sync_runs 
                SET run_status = 'failed',
                    error_message = %s
                WHERE id = %s
            """, (error_msg, current_run_id))
            conn.commit()
            
    except Exception as e:
        errors.append(f"Fatal error: {str(e)}")
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    
    return new_followers_count, updated_followers_count, errors

def get_follower_stats() -> Dict:
    """Get summary statistics about followers"""
    conn = None
    cur = None
    stats = {}
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get total active followers
        cur.execute("""
            SELECT COUNT(*) 
            FROM followers 
            WHERE is_active = TRUE
        """)
        stats['active_followers'] = cur.fetchone()[0]
        
        # Get new followers today
        cur.execute("""
            SELECT COUNT(*) 
            FROM followers 
            WHERE DATE(created_at::timestamp) = CURRENT_DATE 
            AND is_active = TRUE
        """)
        stats['new_today'] = cur.fetchone()[0]
        
        # Get recently unfollowed count
        cur.execute("""
            SELECT COUNT(*) 
            FROM followers 
            WHERE is_active = FALSE 
            AND last_updated::timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        """)
        stats['unfollowed_24h'] = cur.fetchone()[0]
        
        # Get last sync status
        cur.execute("""
            SELECT run_timestamp, run_status, total_followers, new_followers 
            FROM follower_sync_runs 
            ORDER BY run_timestamp DESC 
            LIMIT 1
        """)
        last_sync = cur.fetchone()
        if last_sync:
            stats['last_sync'] = {
                'timestamp': last_sync[0],
                'status': last_sync[1],
                'total': last_sync[2],
                'new': last_sync[3]
            }
            
    except Exception as e:
        print(f"Error getting follower stats: {e}")
        stats['error'] = str(e)
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            
    return stats

# Example usage in a script:
def update_followers():
    new_count, updated_count, errors = get_new_followers()
    print(f"New followers: {new_count}")
    print(f"Updated followers: {updated_count}")
    if errors:
        print("Errors:", errors)

    stats = get_follower_stats()
    print("Current stats:", stats)

if __name__ == "__main__":
    update_followers()
