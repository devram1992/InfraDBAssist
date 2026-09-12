CREATE TABLE IF NOT EXISTS knowledge_documents (

    id BIGSERIAL PRIMARY KEY,

    title TEXT NOT NULL,

    content TEXT NOT NULL,

    source_type VARCHAR(50) NOT NULL,

    source_reference TEXT,

    content_hash VARCHAR(64),

    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);
