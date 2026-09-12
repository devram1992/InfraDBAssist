import os


class DatabaseConfig:

    host: str = os.getenv("INFRADB_DB_HOST", "localhost")
    port: int = int(os.getenv("INFRADB_DB_PORT", "5433"))
    database: str = os.getenv("INFRADB_DB_NAME", "infradb")
    user: str = os.getenv("INFRADB_DB_USER", "infradb")
    password: str = os.getenv(
        "INFRADB_DB_PASSWORD",
        "infradb_dev_password",
    )

    @classmethod
    def connection_string(cls) -> str:
        """
        Return the PostgreSQL connection string.
        """

        return (
            f"host={cls.host} "
            f"port={cls.port} "
            f"dbname={cls.database} "
            f"user={cls.user} "
            f"password={cls.password}"
        )
