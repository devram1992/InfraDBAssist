from backend.app.tools.base import Tool


class ToolRegistry:

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def has(self, name: str) -> bool:
        return name in self._tools

    def get_tool_metadata(self) -> list[dict]:
        """
        Return standardized metadata for all registered tools.
        """

        return [
            tool.get_metadata()
            for tool in self._tools.values()
        ]