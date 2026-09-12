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
                updated_at
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
                updated_at
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
                }

    def list_documents(self) -> list[dict]:
        query = """
            SELECT
                id,
                title,
                content,
                source_type,
                source_reference,
                metadata,
                created_at,
                updated_at
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