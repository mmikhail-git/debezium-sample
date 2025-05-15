CREATE SCHEMA outbox;

CREATE TABLE outbox.outbox_message (
    id UUID PRIMARY KEY,
    aggregate_type VARCHAR(255) NOT NULL,
    aggregate_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Включение логической репликации
ALTER SYSTEM SET wal_level = logical;