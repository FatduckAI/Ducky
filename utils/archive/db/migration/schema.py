# schema.py

SCHEMA = {
    'edgelord': '''
        CREATE TABLE IF NOT EXISTS edgelord (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tweet_id TEXT UNIQUE,
            timestamp TEXT NOT NULL
        )
    ''',
    'edgelord_oneoff': '''
        CREATE TABLE IF NOT EXISTS edgelord_oneoff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tweet_id TEXT UNIQUE,
            timestamp TEXT NOT NULL
        )
    ''',
    'hitchiker_conversations': '''
        CREATE TABLE IF NOT EXISTS hitchiker_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            content TEXT,
            summary TEXT,
            tweet_url TEXT
        )
    ''',
    'hitchiker_personalities': '''
        CREATE TABLE IF NOT EXISTS hitchiker_personalities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT,
            openness INTEGER,
            conscientiousness INTEGER,
            extraversion INTEGER,
            agreeableness INTEGER,
            neuroticism INTEGER
        )
    ''',
    'hitchiker_personality_changes': '''
        CREATE TABLE IF NOT EXISTS hitchiker_personality_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT,
            change_type TEXT,
            change_value INTEGER,
            timestamp TEXT
        )
    ''',
    'hitchiker_personality_grades': '''
        CREATE TABLE IF NOT EXISTS hitchiker_personality_grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT,
            openness TEXT,
            conscientiousness TEXT,
            extraversion TEXT,
            agreeableness TEXT,
            neuroticism TEXT,
            overall TEXT,
            timestamp TEXT
        )
    ''',
    'hitchiker_personality_changes': '''
        CREATE TABLE IF NOT EXISTS hitchiker_personality_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor TEXT,
        change_type TEXT,
        change_value INTEGER,
        timestamp TEXT
    )
    ''',
    'hitchiker_personality_grades': '''
        CREATE TABLE IF NOT EXISTS hitchiker_personality_grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT,
            openness TEXT,
            conscientiousness TEXT,
            extraversion TEXT,
            agreeableness TEXT,
            neuroticism TEXT,
            overall TEXT,
            timestamp TEXT
        )
    ''',
    'narratives': '''
        CREATE TABLE IF NOT EXISTS narratives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            content TEXT,
            summary TEXT
        )
    ''',
    'coin_info': '''
        CREATE TABLE IF NOT EXISTS coin_info (
            id TEXT PRIMARY KEY,
            symbol TEXT,
            name TEXT,
            image TEXT
        )
    ''',
    'price_data': '''
        CREATE TABLE IF NOT EXISTS price_data (
            id TEXT,
            timestamp TEXT,
            current_price REAL,
            market_cap REAL,
            market_cap_rank INTEGER,
            fully_diluted_valuation REAL,
            total_volume REAL,
            high_24h REAL,
            low_24h REAL,
            price_change_24h REAL,
            price_change_percentage_24h REAL,
            market_cap_change_24h REAL,
            market_cap_change_percentage_24h REAL,
            circulating_supply REAL,
            total_supply REAL,
            max_supply REAL,
            ath REAL,
            ath_change_percentage REAL,
            ath_date TEXT,
            atl REAL,
            atl_change_percentage REAL,
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
