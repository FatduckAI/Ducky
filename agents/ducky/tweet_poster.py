from datetime import datetime, timedelta, timezone

import pytz
from dateutil import parser
from discord import Embed
from psycopg2.extras import RealDictCursor

from db.db_postgres import get_db_connection
from lib.twitter import post_tweet

EST = pytz.timezone('US/Eastern')


def format_timestamp(db_timestamp, logger):
    """Convert database timestamp to UTC and EST display format"""
    try:
        # Parse the timestamp using dateutil (more flexible parsing)
        posttime_utc = parser.parse(str(db_timestamp))
        
        # Make sure it's UTC aware
        if posttime_utc.tzinfo is None:
            utc = pytz.UTC
            posttime_utc = posttime_utc.replace(tzinfo=utc)
        
        # Convert to Eastern Time
        eastern = pytz.timezone('US/Eastern')
        posttime_est = posttime_utc.astimezone(eastern)
        
        # Format for display
        return f"{posttime_est.strftime('%I:%M %p %Z')} ({posttime_utc.strftime('%I:%M %p UTC')})"
    except Exception as e:
        logger.error(f"Error parsing timestamp {db_timestamp}: {e}")
        return str(db_timestamp)  # Return original if parsing fails


async def get_scheduled_tweets(logger):
    """Get all unposted tweets that have a posttime"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, content, tweet_id, posttime, conversation_id 
            FROM ducky_ai 
            WHERE posted = FALSE 
            AND posttime IS NOT NULL
            AND speaker = 'Ducky'
            AND tweet_id LIKE 'ducky_reflection_%'
            ORDER BY posttime ASC
        """)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching scheduled tweets: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

async def cancel_scheduled_tweet(db_id, logger):
    """Cancel a scheduled tweet by removing its posttime"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE ducky_ai 
            SET posttime = NULL
            WHERE id = %s 
            AND posted = FALSE
            RETURNING id, content, posttime
        """, (db_id,))
        result = cursor.fetchone()
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        logger.error(f"Error canceling tweet with ID {db_id}: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

async def handle_tweet_commands(message, command_parts, logger):
    if len(command_parts) < 2:
        try:
            await message.reply(
                "📝 Available tweet commands:\n"
                "`@Ducky tweets list` - Show all scheduled tweets\n"
                "`@Ducky tweets cancel <database_id>` - Cancel a scheduled tweet",
            )
        except AttributeError:
            await message.reply(
                "📝 Available tweet commands:\n"
                "`@Ducky tweets list` - Show all scheduled tweets\n"
                "`@Ducky tweets cancel <database_id>` - Cancel a scheduled tweet"
            )
        return

    subcommand = command_parts[1].lower()

    if subcommand == "list":
        scheduled_tweets = await get_scheduled_tweets(logger)
        
        if not scheduled_tweets:
            try:
                await message.reply("🕊️ No scheduled tweets found!")
            except AttributeError:
                await message.reply("🕊️ No scheduled tweets found!")
            return

        embed = Embed(
            title="📅 Scheduled Tweets",
            color=0x1DA1F2,
            description="Here are all tweets scheduled for posting. Use the Database ID to cancel a tweet."
        )

        for tweet in scheduled_tweets:
            time_display = format_timestamp(tweet['posttime'], logger)
            preview = tweet['content']
            embed.add_field(
                name=f"Id: {tweet['id']}\nScheduled for: {time_display}",
                value=f"```{preview}```\n**Conversation:** `{tweet['conversation_id']}`",
                inline=False
            )

        embed.set_footer(text="To cancel a tweet, use: @Ducky tweets cancel <database_id>")
        
        try:
            await message.reply(embed=embed)
        except AttributeError:
            await message.reply(embed=embed)

    elif subcommand == "cancel":
        if len(command_parts) < 3:
            try:
                await message.reply(
                    "⚠️ Please specify the database ID to cancel!\nExample: `@Ducky tweets cancel 123`"
                  )
            except AttributeError:
                await message.reply(
                    "⚠️ Please specify the database ID to cancel!\nExample: `@Ducky tweets cancel 123`"
                )
            return
            
        try:
            db_id = int(command_parts[2])
            result = await cancel_scheduled_tweet(db_id, logger)
            
            if result:
                embed = Embed(
                    title="✅ Tweet Cancelled",
                    color=0x00FF00,
                    description=f"Tweet with Database ID {result[0]} has been removed from the schedule."
                )
                
                preview = result[1]
                if len(preview) > 200:
                    preview = preview[:197] + "..."
                
                embed.add_field(
                    name="Cancelled Tweet Content:",
                    value=f"```{preview}```",
                    inline=False
                )
                
                if result[2]:
                    embed.add_field(
                        name="Was scheduled for:",
                        value=result[2].strftime("%Y-%m-%d %I:%M %p UTC"),
                        inline=False
                    )
                
                try:
                    await message.reply(embed=embed)
                except AttributeError:
                    await message.reply(embed=embed)
            else:
                try:
                    await message.reply(
                        "❌ Could not find an unposted tweet with that database ID!"
                    )
                except AttributeError:
                    await message.reply(
                        "❌ Could not find an unposted tweet with that database ID!"
                    )
                
        except ValueError:
            try:
                await message.reply(
                    "⚠️ Please provide a valid database ID! (numbers only)"
                )
            except AttributeError:
                await message.reply(
                    "⚠️ Please provide a valid database ID! (numbers only)"
                )
        except Exception as e:
            logger.error(f"Error in cancel command: {e}")
            try:
                await message.reply(
                    f"❌ An error occurred: {str(e)}"
                )
            except AttributeError:
                await message.reply(
                    f"❌ An error occurred: {str(e)}"
                )





def get_next_due_tweet():
    """
    Get the next unposted tweet that is due for posting based on UTC time.
    Includes a small buffer time to account for cron job delay.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current UTC time with 5-minute buffer
        current_utc = datetime.now(timezone.utc)
        buffer_time = current_utc + timedelta(minutes=10)
        
        cursor.execute("""
            SELECT id, content, tweet_id, posttime 
            FROM ducky_ai 
            WHERE posted = FALSE 
            AND posttime IS NOT NULL
            AND posttime <= %s
            AND speaker = 'Ducky'
            ORDER BY posttime ASC 
            LIMIT 1
        """, (buffer_time,))
        
        tweet = cursor.fetchone()
        if tweet:
            print(f"Found tweet scheduled for {tweet['posttime']} UTC")
        return tweet
    except Exception as e:
        print(f"Error fetching next due tweet: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_tweet_status(tweet_id, tweet_url):
    """
    Update the tweet as posted and store its URL with UTC timestamp
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        posted_at = datetime.now(timezone.utc)
        cursor.execute("""
            UPDATE ducky_ai 
            SET posted = TRUE, 
                tweet_url = %s,
                posted_at = %s
            WHERE id = %s
            RETURNING id
        """, (tweet_url, posted_at, tweet_id))
        
        updated_row = cursor.fetchone()
        if not updated_row:
            raise Exception(f"No tweet found with ID {tweet_id}")
            
        conn.commit()
        print(f"Updated tweet {tweet_id} status - posted at {posted_at} UTC")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error updating tweet status: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def handle_hourly_tweet():
    """
    Handle hourly tweet posting based on UTC schedule.
    This function will be called by cron job.
    """
    current_utc = datetime.now(timezone.utc)
    print(f"Running tweet check at {current_utc} UTC")
    
    try:
        # Get the next tweet due for posting
        next_tweet = get_next_due_tweet()
        
        if next_tweet:
            print(f"Posting tweet scheduled for {next_tweet['posttime']} UTC")
            print(f"Tweet content: {next_tweet['content'][:50]}...")
            
            # Post the tweet
            tweet_url = post_tweet(next_tweet['content'])
            
            # Update the status after successful posting
            update_tweet_status(next_tweet['id'], tweet_url)
            
            print(f"Successfully posted tweet {next_tweet['id']} at {datetime.now(timezone.utc)} UTC")
        else:
            print(f"No tweets due for posting at {current_utc} UTC")
    except Exception as e:
        print(f"Error in handle_hourly_tweet: {e}")

if __name__ == "__main__":
    handle_hourly_tweet()