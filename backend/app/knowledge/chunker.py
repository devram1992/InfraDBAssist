class DocumentChunker:

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
    ):
        if chunk_size <= 0:
            raise ValueError(
                "Chunk size must be greater than zero."
            )

        if chunk_overlap < 0:
            raise ValueError(
                "Chunk overlap cannot be negative."
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "Chunk overlap must be smaller than chunk size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, content: str) -> list[str]:
        """
        Split document content into overlapping chunks.
        """

        if not content or not content.strip():
            raise ValueError(
                "Document content cannot be empty."
            )

        content = content.strip()

        if len(content) <= self.chunk_size:
            return [content]

        chunks = []

        start = 0
        content_length = len(content)

        while start < content_length:
            end = min(
                start + self.chunk_size,
                content_length,
            )

            chunk = content[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= content_length:
                break

            start = end - self.chunk_overlap

        return chunks

