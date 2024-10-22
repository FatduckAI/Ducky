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
    '''
}