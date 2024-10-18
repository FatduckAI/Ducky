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
}
