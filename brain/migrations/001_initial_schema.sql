-- Create conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    platform TEXT NOT NULL,
    priority TEXT NOT NULL,
    thread_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for better query performance
CREATE INDEX idx_conversations_user_platform ON conversations(user_id, platform);
CREATE INDEX idx_conversations_active ON conversations(is_active) WHERE is_active = true;
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_messages_thread ON messages(thread_id) WHERE thread_id IS NOT NULL;

-- Add constraints
ALTER TABLE conversations 
    ADD CONSTRAINT check_ended_at_after_started 
    CHECK (ended_at IS NULL OR ended_at >= started_at);

ALTER TABLE conversations 
    ADD CONSTRAINT check_started_at_not_future 
    CHECK (started_at <= CURRENT_TIMESTAMP);

-- Add useful views
CREATE VIEW active_conversations AS
    SELECT *
    FROM conversations
    WHERE is_active = true;

CREATE VIEW recent_messages AS
    SELECT m.*, c.user_id as conversation_user_id
    FROM messages m
    JOIN conversations c ON m.conversation_id = c.id
    WHERE c.is_active = true
    ORDER BY m.created_at DESC;

-- Comments for documentation
COMMENT ON TABLE conversations IS 'Stores conversation metadata and lifecycle information';
COMMENT ON TABLE messages IS 'Stores individual messages within conversations';
COMMENT ON COLUMN conversations.metadata IS 'Additional platform-specific conversation data';
COMMENT ON COLUMN messages.metadata IS 'Additional platform-specific message data';
COMMENT ON COLUMN messages.thread_id IS 'Optional thread identifier for platforms that support threading';


-- Optional: Add trigger for automatically setting ended_at when is_active becomes false
CREATE OR REPLACE FUNCTION set_ended_at() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_active = false AND OLD.is_active = true THEN
        NEW.ended_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_set_ended_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    WHEN (OLD.is_active = true AND NEW.is_active = false)
    EXECUTE FUNCTION set_ended_at();