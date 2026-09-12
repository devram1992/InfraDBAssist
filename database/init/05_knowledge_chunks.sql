CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id BIGSERIAL PRIMARY KEY,

    document_id BIGINT NOT NULL
        REFERENCES knowledge_documents(id)
        ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,

    content TEXT NOT NULL,

    metadata JSONB DEFAULT '{}'::jsonb,

    embedding VECTOR(1024),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_idx
ON knowledge_chunks
USING hnsw (embedding vector_cosine_ops);
