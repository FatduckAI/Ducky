# PostgreSQL schema definitions
PG_SCHEMA = {
    'edgelord': '''
        CREATE TABLE IF NOT EXISTS edgelord (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            tweet_id TEXT UNIQUE,
            timestamp TEXT NOT NULL
        )
    ''',
    'edgelord_oneoff': '''
        CREATE TABLE IF NOT EXISTS edgelord_oneoff (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            tweet_id TEXT UNIQUE,
            timestamp TEXT NOT NULL
        )
    ''',
    'hitchiker_conversations': '''
        CREATE TABLE IF NOT EXISTS hitchiker_conversations (
            id SERIAL PRIMARY KEY,
            timestamp TEXT,
            content TEXT,
            summary TEXT,
            tweet_url TEXT
        )
    ''',
    'narratives': '''
        CREATE TABLE IF NOT EXISTS narratives (
            id SERIAL PRIMARY KEY,
            timestamp TEXT,
            content TEXT,
            summary TEXT
        )
    ''',
    'price_data': '''
        CREATE TABLE IF NOT EXISTS price_data (
            id TEXT,
            timestamp TEXT,
            current_price DECIMAL,
            market_cap DECIMAL,
            market_cap_rank INTEGER,
            fully_diluted_valuation DECIMAL,
            total_volume DECIMAL,
            high_24h DECIMAL,
            low_24h DECIMAL,
            price_change_24h DECIMAL,
            price_change_percentage_24h DECIMAL,
            market_cap_change_24h DECIMAL,
            market_cap_change_percentage_24h DECIMAL,
            circulating_supply DECIMAL,
            total_supply DECIMAL,
            max_supply DECIMAL,
            ath DECIMAL,
            ath_change_percentage DECIMAL,
            ath_date TEXT,
            atl DECIMAL,
            atl_change_percentage DECIMAL,
            atl_date TEXT,
            roi TEXT,
            last_updated TEXT,
            PRIMARY KEY (id, timestamp),
            FOREIGN KEY (id) REFERENCES coin_info(id)
        )
    ''',
    'rate_limit': '''
        CREATE TABLE IF NOT EXISTS rate_limit (
            ip_address TEXT PRIMARY KEY,
            request_count INTEGER,
            last_request_time TEXT
        )
    ''',
    'ducky_ai': '''
        CREATE TABLE IF NOT EXISTS ducky_ai (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            tweet_id TEXT,
            postTime TEXT,
            posted BOOLEAN DEFAULT FALSE,
            timestamp TEXT NOT NULL,
            conversation_id VARCHAR(255),
            speaker TEXT
        )
    ''',
        'followers': '''
        CREATE TABLE IF NOT EXISTS followers (
            id BIGINT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            created_at TEXT NOT NULL,
            verified BOOLEAN DEFAULT FALSE,
            followers_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            tweet_count INTEGER DEFAULT 0,
            description TEXT,
            location VARCHAR(255),
            profile_image_url TEXT,
            last_updated TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''',
    'followers_history': '''
        CREATE TABLE IF NOT EXISTS followers_history (
            id SERIAL PRIMARY KEY,
            follower_id BIGINT,
            followers_count INTEGER,
            following_count INTEGER,
            tweet_count INTEGER,
            snapshot_date TEXT NOT NULL,
            FOREIGN KEY (follower_id) REFERENCES followers(id)
        )
    ''',
    'follower_sync_runs': '''
        CREATE TABLE IF NOT EXISTS follower_sync_runs (
            id SERIAL PRIMARY KEY,
            run_timestamp TEXT NOT NULL,
            total_followers BIGINT,
            new_followers BIGINT,
            updated_followers BIGINT,
            run_status TEXT,
            error_message TEXT
        )
    ''',
    'tweet_replies': '''
       CREATE TABLE IF NOT EXISTS tweet_replies (
            id TEXT PRIMARY KEY,
            parent_tweet_id TEXT NOT NULL,
            author TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            likes INTEGER DEFAULT 0,
            retweets INTEGER DEFAULT 0,
            author_followers INTEGER DEFAULT 0,
            author_verified BOOLEAN DEFAULT FALSE,
            processed BOOLEAN DEFAULT FALSE,
            response_tweet_id TEXT,
            processed_at TIMESTAMP,
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id VARCHAR(255),
            telegram_username VARCHAR(255),
            solana_address VARCHAR(44),  -- Solana addresses are 32-44 characters long
            twitter_username VARCHAR(15), -- Twitter usernames are limited to 15 characters
            twitter_name VARCHAR(50),    -- Twitter display names are limited to 50 characters
            eth_address VARCHAR(42),     -- Ethereum addresses are exactly 42 characters (including '0x')
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
    ''',
    'telegram_messages': '''
            CREATE TABLE IF NOT EXISTS telegram_messages (
            message_id BIGINT,
            chat_id BIGINT,
            sender_id BIGINT,
            sender_username VARCHAR(255),
            content TEXT,
            reply_to_message_id BIGINT,
            forward_from_id BIGINT,
            forward_from_name VARCHAR(255),
            media_type VARCHAR(50),
            media_file_id TEXT,
            timestamp TIMESTAMP,
            edited_timestamp TIMESTAMP,
            is_pinned BOOLEAN,
            PRIMARY KEY (message_id, chat_id)
        )
    ''',
    'mentioned_tweets': '''
        CREATE TABLE mentioned_tweets (
    -- Primary identifier from Twitter
    id TEXT PRIMARY KEY,
    
    -- Tweet content and metadata
    text TEXT NOT NULL,
    author TEXT NOT NULL,
    author_username TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    likes INTEGER NOT NULL DEFAULT 0,
    retweets INTEGER NOT NULL DEFAULT 0,
    author_followers INTEGER NOT NULL DEFAULT 0,
    author_verified BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Processing metadata
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Response tracking
    response_tweet_id TEXT,
    response_text TEXT,
    response_error TEXT,
    
    -- Search metadata
    search_query TEXT NOT NULL,
    mention_type mention_type NOT NULL,
    
    -- Metrics and scoring
    engagement_score FLOAT,
    sentiment_score FLOAT,
    priority_score FLOAT,
    
    -- Processing attempts tracking
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Soft delete support
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT mentioned_tweets_response_tweet_unique UNIQUE (response_tweet_id),
    CONSTRAINT mentioned_tweets_retry_count_check CHECK (retry_count >= 0),
    CONSTRAINT mentioned_tweets_created_at_check CHECK (created_at <= CURRENT_TIMESTAMP)
);
    '''
}


# Add indices for the follower tables
FOLLOWER_INDICES = '''
    CREATE INDEX IF NOT EXISTS idx_followers_username ON followers(username);
    CREATE INDEX IF NOT EXISTS idx_followers_created_at ON followers(created_at);
    CREATE INDEX IF NOT EXISTS idx_followers_last_updated ON followers(last_updated);
    CREATE INDEX IF NOT EXISTS idx_followers_is_active ON followers(is_active);
    CREATE INDEX IF NOT EXISTS idx_followers_history_follower_id ON followers_history(follower_id);
    CREATE INDEX IF NOT EXISTS idx_followers_history_date ON followers_history(snapshot_date);
    CREATE INDEX IF NOT EXISTS idx_sync_runs_timestamp ON follower_sync_runs(run_timestamp);
    CREATE INDEX IF NOT EXISTS idx_sync_runs_status ON follower_sync_runs(run_status);
'''


USER_INDICES = '''
    CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
    CREATE INDEX IF NOT EXISTS idx_users_telegram_username ON users(telegram_username);
    CREATE INDEX IF NOT EXISTS idx_users_twitter_username ON users(twitter_username);
    CREATE INDEX IF NOT EXISTS idx_users_solana_address ON users(solana_address);
    CREATE INDEX IF NOT EXISTS idx_users_eth_address ON users(eth_address);
'''

UPDATE_USER_TABLE = '''
    ALTER TABLE users ADD CONSTRAINT telegram_id_key UNIQUE (telegram_id);
'''

TELEGRAM_INDICES = '''
    CREATE INDEX IF NOT EXISTS idx_telegram_messages_chat_id ON telegram_messages(chat_id);
    CREATE INDEX IF NOT EXISTS idx_telegram_messages_sender_id ON telegram_messages(sender_id);
    CREATE INDEX IF NOT EXISTS idx_telegram_messages_reply_to ON telegram_messages(reply_to_message_id);
'''

# add a new column to the ducky_ai table
UPDATE_DUCKY_AI_POSTED = '''
    ALTER TABLE ducky_ai 
DROP CONSTRAINT IF EXISTS ducky_ai_tweet_id_key;
'''

ADD_SENTIMENT_ANALYSIS_COLUMNS = '''
    ALTER TABLE telegram_messages
    ADD COLUMN IF NOT EXISTS sentiment_positive FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_negative FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_helpful FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_sarcastic FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_analyzed BOOLEAN DEFAULT FALSE;

    CREATE INDEX IF NOT EXISTS idx_sentiment_positive ON telegram_messages(sentiment_positive);
    CREATE INDEX IF NOT EXISTS idx_sentiment_negative ON telegram_messages(sentiment_negative);
    CREATE INDEX IF NOT EXISTS idx_sentiment_helpful ON telegram_messages(sentiment_helpful);
    CREATE INDEX IF NOT EXISTS idx_sentiment_sarcastic ON telegram_messages(sentiment_sarcastic);
    CREATE INDEX IF NOT EXISTS idx_sentiment_analyzed ON telegram_messages(sentiment_analyzed);
'''

MENTION_TYPE = '''
    CREATE TYPE mention_type AS ENUM ('username', 'token', 'keyword');
'''

MENTIONED_TWEETS_INDICES = '''
-- Create indices for common query patterns
CREATE INDEX idx_mentioned_tweets_processed ON mentioned_tweets (processed) WHERE processed = FALSE;
CREATE INDEX idx_mentioned_tweets_created_at ON mentioned_tweets (created_at DESC);
CREATE INDEX idx_mentioned_tweets_author ON mentioned_tweets (author);
CREATE INDEX idx_mentioned_tweets_search_query ON mentioned_tweets (search_query);
CREATE INDEX idx_mentioned_tweets_mention_type ON mentioned_tweets (mention_type);
CREATE INDEX idx_mentioned_tweets_priority_score ON mentioned_tweets (priority_score DESC) WHERE processed = FALSE;

-- Create composite indices for common query combinations
CREATE INDEX idx_mentioned_tweets_processing ON mentioned_tweets (processed, priority_score DESC, created_at DESC);
CREATE INDEX idx_mentioned_tweets_metrics ON mentioned_tweets (engagement_score, sentiment_score, priority_score);

-- Create GIN index for text search
CREATE INDEX idx_mentioned_tweets_text_search ON mentioned_tweets USING gin(to_tsvector('english', text));
'''

ADD_TWEET_REPLIES_SENTIMENT = '''
ALTER TABLE tweet_replies
    ADD COLUMN IF NOT EXISTS sentiment_positive FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_negative FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_helpful FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_sarcastic FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_analyzed BOOLEAN DEFAULT FALSE;

    CREATE INDEX IF NOT EXISTS idx_sentiment_positive ON telegram_messages(sentiment_positive);
    CREATE INDEX IF NOT EXISTS idx_sentiment_negative ON telegram_messages(sentiment_negative);
    CREATE INDEX IF NOT EXISTS idx_sentiment_helpful ON telegram_messages(sentiment_helpful);
    CREATE INDEX IF NOT EXISTS idx_sentiment_sarcastic ON telegram_messages(sentiment_sarcastic);
    CREATE INDEX IF NOT EXISTS idx_sentiment_analyzed ON telegram_messages(sentiment_analyzed);
'''

ADD_TWEET_CONTENT_TO_REPLIES = '''
    ALTER TABLE tweet_replies
    ADD COLUMN IF NOT EXISTS content TEXT;
'''

ADD_TWEET_DUCKY_REPLY = '''
    ALTER TABLE tweet_replies
    ADD COLUMN IF NOT EXISTS ducky_reply TEXT;
'''


ADD_SENTIMENT_ANALYSIS_COLUMNS_TO_MENTIONED_TWEETS = '''
    ALTER TABLE mentioned_tweets
    ADD COLUMN IF NOT EXISTS sentiment_positive FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_negative FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_helpful FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_sarcastic FLOAT,
    ADD COLUMN IF NOT EXISTS sentiment_analyzed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS content TEXT,
    ADD COLUMN IF NOT EXISTS ducky_reply TEXT;

    CREATE INDEX IF NOT EXISTS idx_sentiment_positive ON mentioned_tweets(sentiment_positive);
    CREATE INDEX IF NOT EXISTS idx_sentiment_negative ON mentioned_tweets(sentiment_negative);
    CREATE INDEX IF NOT EXISTS idx_sentiment_helpful ON mentioned_tweets(sentiment_helpful);
    CREATE INDEX IF NOT EXISTS idx_sentiment_sarcastic ON mentioned_tweets(sentiment_sarcastic);
    CREATE INDEX IF NOT EXISTS idx_sentiment_analyzed ON mentioned_tweets(sentiment_analyzed);

'''