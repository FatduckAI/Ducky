# Configuration constants for message filtering
IGNORED_COMMANDS = {
    # Basic raid-related commands
    '/raid',
    '/RAID',
    '/report',
    '/Report',
    '/REPORT',
    
    # Common spam variations
    '/spam',
    '/SPAM',
    '/Spam',
    
    # Common bot commands that might be spam
    '/verify',
    '/airdrop',
    '/claim',
    '/free',
    
    # Miscellaneous
    '/pin',
    '/unpin',
    '/contest',
    '/giveaway'
}

# Words or phrases to ignore (case-insensitive)
IGNORED_PHRASES = {
    'raid',
    'spam',
    'scam',
    'report',
    'fake',
    'bot',
    'verify here',
    'claim your',
    'free tokens',
    'airdrop',
    'giveaway',
    'win free',
    'double your',
    '100x',
    '1000x',
    'investment opportunity',
    'private sale',
    'presale',
    'whitelist spot'
}
