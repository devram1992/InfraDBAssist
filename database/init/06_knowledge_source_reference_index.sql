CREATE UNIQUE INDEX IF NOT EXISTS knowledge_documents_source_reference_uidx
ON knowledge_documents (source_reference)
WHERE source_reference IS NOT NULL;	
