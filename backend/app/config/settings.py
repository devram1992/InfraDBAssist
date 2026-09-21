import os


class Settings:
    """
    Central application configuration.

    Values are loaded from environment variables so that
    configuration remains separate from application code.
    """

    # Application
    app_name: str = os.getenv(
        "INFRADB_APP_NAME",
        "InfraDB Assist",
    )

    environment: str = os.getenv(
        "INFRADB_ENVIRONMENT",
        "development",
    )

    # RAG
    rag_similarity_threshold: float = float(
        os.getenv(
            "INFRADB_RAG_SIMILARITY_THRESHOLD",
            "0.60",
        )
    )

    rag_default_limit: int = int(
        os.getenv(
            "INFRADB_RAG_DEFAULT_LIMIT",
            "5",
        )
    )
