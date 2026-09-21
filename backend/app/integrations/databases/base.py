from abc import ABC, abstractmethod


class DatabaseConnection(ABC):
    """
    Common interface for read-only database connections.
    """

    name: str
    read_only: bool = True

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish the database connection.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close the database connection.
        """
        pass

    @abstractmethod
    async def execute(
        self,
        query: str,
        parameters: dict | None = None,
    ) -> list[dict]:
        """
        Execute a read-only query and return normalized rows.
        """
        pass

    @abstractmethod
    async def health_check(self) -> dict:
        """
        Check database connectivity and return status.
        """
        pass
