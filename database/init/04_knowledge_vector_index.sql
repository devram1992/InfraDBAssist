CREATE INDEX IF NOT EXISTS knowledge_documents_embedding_idx
ON knowledge_documents
USING hnsw (embedding vector_cosine_ops);
