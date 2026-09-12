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
        """
        Create a knowledge document and return its ID.
        """

        metadata = json.dumps(metadata or {})

        query = """
            INSERT INTO knowledge_documents (
                title,
                content,
                source_type,
                source_reference,
                metadata
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s
            )
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

    def update_embedding(
        self,
        document_id: int,
        embedding: list[float],
    ) -> None:
        """
        Store the embedding for a knowledge document.
        """

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

    def get_document(self, document_id: int) -> dict | None:
        """
        Retrieve a knowledge document by ID.
        """

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
                cursor.execute(query, (document_id,))

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
        """
        Return all knowledge documents.
        """

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
        """
        Search knowledge documents using vector similarity.
        """

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