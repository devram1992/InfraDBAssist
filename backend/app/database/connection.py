import psycopg

from backend.app.database.config import DatabaseConfig


def get_connection():
    """
    Create and return a PostgreSQL database connection.
    """

    return psycopg.connect(
        DatabaseConfig.connection_string()
    )