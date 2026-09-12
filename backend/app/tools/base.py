from abc import ABC, abstractmethod


class Tool(ABC):
    name: str
    description: str
    permission: str
    read_only: bool = True
    parameters: dict = {}

    def get_metadata(self) -> dict:
        """
        Return standardized metadata for the tool.
        """

        return {
            "name": self.name,
            "description": self.description,
            "permission": self.permission,
            "read_only": self.read_only,
            "parameters": self.parameters,
        }

    def validate_request(self, request: dict) -> None:
        """
        Validate a tool request before execution.

        Tools can override this method when they require
        specific validation rules.
        """

        if not isinstance(request, dict):
            raise ValueError("Tool request must be a dictionary.")

    @abstractmethod
    async def execute(self, request: dict) -> dict:
        """
        Execute the tool and return a structured result.
        """
        pass

    def build_request(self, **kwargs) -> dict:
        """
        Build a request for tool execution.
        """

        return kwargs

