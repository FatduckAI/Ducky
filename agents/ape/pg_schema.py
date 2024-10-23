PG_SCHEMA = {
    'ape': '''
        CREATE TABLE IF NOT EXISTS ape (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL,
            tweet_id TEXT,
            postTime TEXT,
            posted BOOLEAN DEFAULT FALSE,
            timestamp TEXT NOT NULL
        )
    '''
}