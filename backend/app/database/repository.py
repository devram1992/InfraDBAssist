import json

from backend.app.database.connection import get_connection


class KnowledgeRepository:

    def create_document(
        self,
        title: str,
        content: str,
        source_type: str,
        source_reference: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        metadata = json.dumps(metadata or {})

        query = """
            INSERT INTO knowledge_documents (
                title,
                content,
                source_type,
                source_reference,
                metadata
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        title,
                        content,
                        source_type,
                        source_reference,
                        metadata,
                    ),
                )

                document_id = cursor.fetchone()[0]

                conn.commit()

                return document_id

    def update_document(
        self,
        document_id: int,
        title: str,
        content: str,
        source_type: str,
        metadata: dict | None = None,
        content_hash: str | None = None,
    ) -> None:
        metadata = json.dumps(metadata or {})

        query = """
            UPDATE knowledge_documents
            SET
                title = %s,
                content = %s,
                source_type = %s,
                metadata = %s,
                content_hash = %s,
                updated_at = NOW()
            WHERE id = %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        title,
                        content,
                        source_type,
                        metadata,
                        content_hash,
                        document_id,
                    ),
                )

                if cursor.rowcount == 0:
                    raise ValueError(
                        f"Knowledge document not found: {document_id}"
                    )

                conn.commit()

    def replace_document(
        self,
        document_id: int,
        title: str,
        content: str,
        source_type: str,
        metadata: dict | None,
        content_hash: str,
        chunks: list[dict],
    ) -> None:
        """
        Atomically update a document and replace all of its chunks.

        The document update, old chunk deletion, and new chunk
        insertion happen in a single PostgreSQL transaction.
        """

        metadata_json = json.dumps(metadata or {})

        document_query = """
            UPDATE knowledge_documents
            SET
                title = %s,
                content = %s,
                source_type = %s,
                metadata = %s,
                content_hash = %s,
                updated_at = NOW()
            WHERE id = %s;
        """

        delete_chunks_query = """
            DELETE FROM knowledge_chunks
            WHERE document_id = %s;
        """

        insert_chunk_query = """
            INSERT INTO knowledge_chunks (
                document_id,
                chunk_index,
                content,
                metadata,
                embedding
            )
            VALUES (%s, %s, %s, %s, %s);
        """

        with get_connection() as conn:
            try:
                with conn.cursor() as cursor:

                    cursor.execute(
                        document_query,
                        (
                            title,
                            content,
                            source_type,
                            metadata_json,
                            content_hash,
                            document_id,
                        ),
                    )

                    if cursor.rowcount == 0:
                        raise ValueError(
                            f"Knowledge document not found: {document_id}"
                        )

                    cursor.execute(
                        delete_chunks_query,
                        (document_id,),
                    )

                    for chunk in chunks:

                        chunk_metadata = json.dumps(
                            chunk.get("metadata") or {}
                        )

                        cursor.execute(
                            insert_chunk_query,
                            (
                                document_id,
                                chunk["chunk_index"],
                                chunk["content"],
                                chunk_metadata,
                                chunk["embedding"],
                            ),
                        )

                conn.commit()

            except Exception:
                conn.rollback()
                raise

    def replace_document_chunks(
        self,
        document_id: int,
        chunks: list[dict],
    ) -> None:
        """
        Atomically replace all chunks for a document.

        Used when a newly created document has already been inserted
        and its chunks and embeddings need to be persisted together.
        """

        delete_chunks_query = """
            DELETE FROM knowledge_chunks
            WHERE document_id = %s;
        """

        insert_chunk_query = """
            INSERT INTO knowledge_chunks (
                document_id,
                chunk_index,
                content,
                metadata,
                embedding
            )
            VALUES (%s, %s, %s, %s, %s);
        """

        with get_connection() as conn:
            try:
                with conn.cursor() as cursor:

                    cursor.execute(
                        delete_chunks_query,
                        (document_id,),
                    )

                    for chunk in chunks:

                        chunk_metadata = json.dumps(
                            chunk.get("metadata") or {}
                        )

                        cursor.execute(
                            insert_chunk_query,
                            (
                                document_id,
                                chunk["chunk_index"],
                                chunk["content"],
                                chunk_metadata,
                                chunk["embedding"],
                            ),
                        )

                conn.commit()

            except Exception:
                conn.rollback()
                raise

    def update_content_hash(
        self,
        document_id: int,
        content_hash: str,
    ) -> None:
        if len(content_hash) != 64:
            raise ValueError(
                "Content hash must be a 64-character SHA-256 hash."
            )

        query = """
            UPDATE knowledge_documents
            SET
                content_hash = %s,
                updated_at = NOW()
            WHERE id = %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        content_hash,
                        document_id,
                    ),
                )

                if cursor.rowcount == 0:
                    raise ValueError(
                        f"Knowledge document not found: {document_id}"
                    )

                conn.commit()

    def delete_document(
        self,
        document_id: int,
    ) -> None:
        query = """
            DELETE FROM knowledge_documents
            WHERE id = %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (document_id,),
                )

                if cursor.rowcount == 0:
                    raise ValueError(
                        f"Knowledge document not found: {document_id}"
                    )

                conn.commit()

    def update_embedding(
        self,
        document_id: int,
        embedding: list[float],
    ) -> None:
        if len(embedding) != 1024:
            raise ValueError(
                f"Expected 1024 dimensions, received {len(embedding)}."
            )

        query = """
            UPDATE knowledge_documents
            SET embedding = %s
            WHERE id = %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        embedding,
                        document_id,
                    ),
                )

                if cursor.rowcount == 0:
                    raise ValueError(
                        f"Knowledge document not found: {document_id}"
                    )

                conn.commit()

    def get_document(
        self,
        document_id: int,
    ) -> dict | None:
        query = """
            SELECT
                id,
                title,
                content,
                source_type,
                source_reference,
                metadata,
                created_at,
                updated_at,
                content_hash
            FROM knowledge_documents
            WHERE id = %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (document_id,),
                )

                row = cursor.fetchone()

                if row is None:
                    return None

                return {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "source_type": row[3],
                    "source_reference": row[4],
                    "metadata": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                    "content_hash": row[8],
                }

    def get_document_by_source_reference(
        self,
        source_reference: str,
    ) -> dict | None:
        query = """
            SELECT
                id,
                title,
                content,
                source_type,
                source_reference,
                metadata,
                created_at,
                updated_at,
                content_hash
            FROM knowledge_documents
            WHERE source_reference = %s
            LIMIT 1;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (source_reference,),
                )

                row = cursor.fetchone()

                if row is None:
                    return None

                return {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "source_type": row[3],
                    "source_reference": row[4],
                    "metadata": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                    "content_hash": row[8],
                }

    def list_documents(
        self,
    ) -> list[dict]:
        query = """
            SELECT
                id,
                title,
                content,
                source_type,
                source_reference,
                metadata,
                created_at,
                updated_at,
                content_hash
            FROM knowledge_documents
            ORDER BY id;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)

                rows = cursor.fetchall()

                return [
                    {
                        "id": row[0],
                        "title": row[1],
                        "content": row[2],
                        "source_type": row[3],
                        "source_reference": row[4],
                        "metadata": row[5],
                        "created_at": row[6],
                        "updated_at": row[7],
                        "content_hash": row[8],
                    }
                    for row in rows
                ]

    def search_similar(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> list[dict]:
        if len(embedding) != 1024:
            raise ValueError(
                f"Expected 1024 dimensions, received {len(embedding)}."
            )

        if limit < 1:
            raise ValueError(
                "Limit must be greater than zero."
            )

        query = """
            SELECT
                id,
                title,
                content,
                source_type,
                source_reference,
                metadata,
                1 - (embedding <=> %s::vector) AS similarity
            FROM knowledge_documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        embedding,
                        embedding,
                        limit,
                    ),
                )

                rows = cursor.fetchall()

                return [
                    {
                        "id": row[0],
                        "title": row[1],
                        "content": row[2],
                        "source_type": row[3],
                        "source_reference": row[4],
                        "metadata": row[5],
                        "similarity": float(row[6]),
                    }
                    for row in rows
                ]

    def create_chunk(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        metadata: dict | None = None,
    ) -> int:
        if chunk_index < 0:
            raise ValueError(
                "Chunk index cannot be negative."
            )

        if not content or not content.strip():
            raise ValueError(
                "Chunk content cannot be empty."
            )

        metadata = json.dumps(metadata or {})

        query = """
            INSERT INTO knowledge_chunks (
                document_id,
                chunk_index,
                content,
                metadata
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        document_id,
                        chunk_index,
                        content,
                        metadata,
                    ),
                )

                chunk_id = cursor.fetchone()[0]

                conn.commit()

                return chunk_id

    def create_chunk_with_embedding(
        self,
        document_id: int,
        chunk_index: int,
        content: str,
        embedding: list[float],
        metadata: dict | None = None,
    ) -> int:
        if chunk_index < 0:
            raise ValueError(
                "Chunk index cannot be negative."
            )

        if not content or not content.strip():
            raise ValueError(
                "Chunk content cannot be empty."
            )

        if len(embedding) != 1024:
            raise ValueError(
                f"Expected 1024 dimensions, received {len(embedding)}."
            )

        metadata = json.dumps(metadata or {})

        query = """
            INSERT INTO knowledge_chunks (
                document_id,
                chunk_index,
                content,
                metadata,
                embedding
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        document_id,
                        chunk_index,
                        content,
                        metadata,
                        embedding,
                    ),
                )

                chunk_id = cursor.fetchone()[0]

                conn.commit()

                return chunk_id

    def update_chunk_embedding(
        self,
        chunk_id: int,
        embedding: list[float],
    ) -> None:
        if len(embedding) != 1024:
            raise ValueError(
                f"Expected 1024 dimensions, received {len(embedding)}."
            )

        query = """
            UPDATE knowledge_chunks
            SET embedding = %s
            WHERE id = %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        embedding,
                        chunk_id,
                    ),
                )

                if cursor.rowcount == 0:
                    raise ValueError(
                        f"Knowledge chunk not found: {chunk_id}"
                    )

                conn.commit()

    def delete_chunks(
        self,
        document_id: int,
    ) -> None:
        query = """
            DELETE FROM knowledge_chunks
            WHERE document_id = %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (document_id,),
                )

                conn.commit()

    def search_similar_chunks(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> list[dict]:
        if len(embedding) != 1024:
            raise ValueError(
                f"Expected 1024 dimensions, received {len(embedding)}."
            )

        if limit < 1:
            raise ValueError(
                "Limit must be greater than zero."
            )

        query = """
            SELECT
                c.id,
                c.document_id,
                d.title,
                c.chunk_index,
                c.content,
                d.source_type,
                d.source_reference,
                c.metadata,
                1 - (c.embedding <=> %s::vector) AS similarity
            FROM knowledge_chunks c
            JOIN knowledge_documents d
                ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s;
        """

        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    query,
                    (
                        embedding,
                        embedding,
                        limit,
                    ),
                )

                rows = cursor.fetchall()

                return [
                    {
                        "id": row[0],
                        "document_id": row[1],
                        "title": row[2],
                        "chunk_index": row[3],
                        "content": row[4],
                        "source_type": row[5],
                        "source_reference": row[6],
                        "metadata": row[7],
                        "similarity": float(row[8]),
                    }
                    for row in rows
                ]