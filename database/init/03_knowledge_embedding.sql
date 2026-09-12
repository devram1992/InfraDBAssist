ALTER TABLE knowledge_documents
ADD COLUMN IF NOT EXISTS embedding VECTOR(1024);
