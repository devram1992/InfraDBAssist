from abc import ABC, abstractmethod


class Tool(ABC):
    name: str
    description: str
    permission: str
    read_only: bool = True

    @abstractmethod
    async def execute(self, request: dict) -> dict:
        """Execute the tool and return a structured result."""
        pass

    def build_request(self, **kwargs) -> dict:
        """Build a request for tool execution."""
        return kwargs