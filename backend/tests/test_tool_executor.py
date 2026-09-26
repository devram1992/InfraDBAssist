import pytest

from backend.app.auth.authorization import AuthorizationService
from backend.app.tools.base import Tool
from backend.app.tools.executor import ToolExecutor
from backend.app.auth.user_context import UserContext


class DummyTool(Tool):
    name = "dummy"
    description = "Dummy tool"
    permission = "database.read"
    read_only = True
    parameters = {}

    async def execute(self, request: dict) -> dict:
        return {
            "status": "executed",
            "request": request,
        }


class InvalidRequestTool(DummyTool):
    def validate_request(self, request: dict) -> None:
        raise ValueError("Invalid request")


@pytest.mark.asyncio
async def test_executor_allows_authorized_tool():
    auth = AuthorizationService()
    executor = ToolExecutor(auth)
    tool = DummyTool()

    result = await executor.execute(
        tool=tool,
        request={"target": "TESTDB"},
        user_permissions={"database.read"},
    )

    assert result["status"] == "executed"
    assert result["request"]["target"] == "TESTDB"


@pytest.mark.asyncio
async def test_executor_denies_unauthorized_tool():
    auth = AuthorizationService()
    executor = ToolExecutor(auth)
    tool = DummyTool()

    with pytest.raises(PermissionError):
        await executor.execute(
            tool=tool,
            request={"target": "TESTDB"},
            user_permissions={"infrastructure.read"},
        )


@pytest.mark.asyncio
async def test_executor_validates_request_before_execution():
    auth = AuthorizationService()
    executor = ToolExecutor(auth)
    tool = InvalidRequestTool()

    with pytest.raises(ValueError, match="Invalid request"):
        await executor.execute(
            tool=tool,
            request={"target": "TESTDB"},
            user_permissions={"database.read"},
        )


@pytest.mark.asyncio
async def test_executor_rejects_non_tool():
    auth = AuthorizationService()
    executor = ToolExecutor(auth)

    with pytest.raises(TypeError):
        await executor.execute(
            tool=None,
            request={},
            user_permissions={"database.read"},
        )
@pytest.mark.asyncio
async def test_executor_rejects_missing_permissions():
    auth = AuthorizationService()
    executor = ToolExecutor(auth)
    tool = DummyTool()

    with pytest.raises(PermissionError, match="database.read"):
        await executor.execute(
            tool=tool,
            request={"target": "TESTDB"},
            user_permissions=set(),
        )


@pytest.mark.asyncio
async def test_executor_returns_tool_result():
    auth = AuthorizationService()
    executor = ToolExecutor(auth)
    tool = DummyTool()

    result = await executor.execute(
        tool=tool,
        request={"target": "TESTDB"},
        user_permissions={"database.read"},
    )

    assert result == {
        "status": "executed",
        "request": {"target": "TESTDB"},
    }
@pytest.mark.asyncio
async def test_executor_accepts_user_context():
    auth = AuthorizationService()
    executor = ToolExecutor(auth)
    tool = DummyTool()

    user_context = UserContext(
        user_id="user-001",
        username="engineer",
        permissions={"database.read"},
    )

    result = await executor.execute(
        tool=tool,
        request={"target": "TESTDB"},
        user_context=user_context,
    )

    assert result == {
        "status": "executed",
        "request": {"target": "TESTDB"},
    }


@pytest.mark.asyncio
async def test_executor_rejects_user_context_without_permission():
    auth = AuthorizationService()
    executor = ToolExecutor(auth)
    tool = DummyTool()

    user_context = UserContext(
        user_id="user-001",
        username="engineer",
        permissions={"infrastructure.read"},
    )

    with pytest.raises(
        PermissionError,
        match="database.read",
    ):
        await executor.execute(
            tool=tool,
            request={"target": "TESTDB"},
            user_context=user_context,
        )
