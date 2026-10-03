import pytest



from backend.app.audit.service import AuditService

from backend.app.auth.authorization import AuthorizationService

from backend.app.auth.role_permissions import RolePermissionMapper

from backend.app.auth.user_context import UserContext

from backend.app.tools.base import Tool

from backend.app.tools.executor import ToolExecutor





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





class FailingTool(DummyTool):

    async def execute(self, request: dict) -> dict:

        raise RuntimeError("Tool execution failed")





def database_user_context() -> UserContext:

    return UserContext(

        user_id="user-001",

        username="database-engineer",

        roles={"database_engineer"},

        permissions={"database.read"},

    )





def create_executor() -> tuple[ToolExecutor, AuditService]:

    auth = AuthorizationService()

    audit_service = AuditService()

    executor = ToolExecutor(

        authorization=auth,

        audit_service=audit_service,

    )

    return executor, audit_service





@pytest.mark.asyncio

async def test_executor_allows_authorized_tool():

    executor, audit_service = create_executor()

    tool = DummyTool()



    result = await executor.execute(

        tool=tool,

        request={"target": "TESTDB"},

        user_context=database_user_context(),

    )



    assert result["status"] == "executed"



    events = audit_service.list_events()



    assert len(events) == 1

    assert events[0].status == "success"

    assert events[0].user_id == "user-001"

    assert events[0].username == "database-engineer"

    assert events[0].tool_name == "dummy"

    assert events[0].permission == "database.read"

    assert events[0].request == {"target": "TESTDB"}

    assert events[0].error is None





@pytest.mark.asyncio

async def test_executor_denies_unauthorized_tool():

    executor, audit_service = create_executor()

    tool = DummyTool()



    user_context = UserContext(

        user_id="user-001",

        username="infrastructure-engineer",

        roles={"infrastructure_engineer"},

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



    events = audit_service.list_events()



    assert len(events) == 1

    assert events[0].status == "denied"

    assert events[0].user_id == "user-001"

    assert events[0].tool_name == "dummy"

    assert events[0].permission == "database.read"

    assert events[0].error == (

        "Permission denied: database.read"

    )





@pytest.mark.asyncio

async def test_executor_validates_request_before_execution():

    executor, audit_service = create_executor()

    tool = InvalidRequestTool()



    with pytest.raises(

        ValueError,

        match="Invalid request",

    ):

        await executor.execute(

            tool=tool,

            request={"target": "TESTDB"},

            user_context=database_user_context(),

        )



    events = audit_service.list_events()



    assert len(events) == 1

    assert events[0].status == "validation_failed"

    assert events[0].error == "Invalid request"





@pytest.mark.asyncio

async def test_executor_rejects_non_tool():

    executor, audit_service = create_executor()



    with pytest.raises(TypeError):

        await executor.execute(

            tool=None,

            request={},

            user_context=database_user_context(),

        )



    assert audit_service.list_events() == []





@pytest.mark.asyncio

async def test_executor_rejects_missing_user_context():

    executor, audit_service = create_executor()

    tool = DummyTool()



    with pytest.raises(

        ValueError,

        match="User context is required",

    ):

        await executor.execute(

            tool=tool,

            request={"target": "TESTDB"},

        )



    assert audit_service.list_events() == []





@pytest.mark.asyncio

async def test_executor_returns_tool_result():

    executor, audit_service = create_executor()

    tool = DummyTool()



    result = await executor.execute(

        tool=tool,

        request={"target": "TESTDB"},

        user_context=database_user_context(),

    )



    assert result == {

        "status": "executed",

        "request": {"target": "TESTDB"},

    }



    assert len(audit_service.list_events()) == 1

    assert audit_service.list_events()[0].status == "success"





@pytest.mark.asyncio

async def test_executor_accepts_user_context():

    executor, audit_service = create_executor()

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



    events = audit_service.list_events()



    assert len(events) == 1

    assert events[0].username == "engineer"

    assert events[0].status == "success"





@pytest.mark.asyncio

async def test_executor_rejects_user_context_without_permission():

    executor, audit_service = create_executor()

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



    events = audit_service.list_events()



    assert len(events) == 1

    assert events[0].status == "denied"





@pytest.mark.asyncio

async def test_executor_records_tool_execution_error():

    executor, audit_service = create_executor()

    tool = FailingTool()



    with pytest.raises(

        RuntimeError,

        match="Tool execution failed",

    ):

        await executor.execute(

            tool=tool,

            request={"target": "TESTDB"},

            user_context=database_user_context(),

        )



    events = audit_service.list_events()



    assert len(events) == 1

    assert events[0].status == "error"

    assert events[0].error == "Tool execution failed"





@pytest.mark.asyncio

async def test_database_engineer_can_execute_database_tool():

    executor, audit_service = create_executor()

    tool = DummyTool()



    mapper = RolePermissionMapper()



    user_context = UserContext(

        user_id="user-001",

        username="database-engineer",

        roles={"database_engineer"},

        permissions=mapper.get_permissions(

            {"database_engineer"}

        ),

    )



    result = await executor.execute(

        tool=tool,

        request={"target": "TESTDB"},

        user_context=user_context,

    )



    assert result["status"] == "executed"



    events = audit_service.list_events()



    assert len(events) == 1

    assert events[0].status == "success"





@pytest.mark.asyncio

async def test_database_engineer_cannot_execute_kubernetes_tool():

    executor, audit_service = create_executor()



    class KubernetesDummyTool(Tool):

        name = "kubernetes_dummy"

        description = "Dummy Kubernetes tool"

        permission = "kubernetes.read"

        read_only = True

        parameters = {}



        async def execute(

            self,

            request: dict,

        ) -> dict:

            return {

                "status": "executed",

            }



    tool = KubernetesDummyTool()



    mapper = RolePermissionMapper()



    user_context = UserContext(

        user_id="user-001",

        username="database-engineer",

        roles={"database_engineer"},

        permissions=mapper.get_permissions(

            {"database_engineer"}

        ),

    )



    with pytest.raises(

        PermissionError,

        match="kubernetes.read",

    ):

        await executor.execute(

            tool=tool,

            request={},

            user_context=user_context,

        )



    events = audit_service.list_events()



    assert len(events) == 1

    assert events[0].status == "denied"

    assert events[0].tool_name == "kubernetes_dummy"

    assert events[0].permission == "kubernetes.read"

@pytest.mark.asyncio

async def test_executor_sanitizes_audit_request_without_modifying_tool_request():

    executor, audit_service = create_executor()

    tool = DummyTool()



    request = {

        "action": "connect",

        "username": "db-user",

        "password": "super-secret",

    }



    result = await executor.execute(

        tool=tool,

        request=request,

        user_context=database_user_context(),

    )



    # The actual tool receives the original request.

    assert result["request"] == request

    assert result["request"]["password"] == "super-secret"



    # The audit record receives the sanitized request.

    events = audit_service.list_events()



    assert len(events) == 1

    assert events[0].status == "success"

    assert events[0].request["action"] == "connect"

    assert events[0].request["username"] == "db-user"

    assert events[0].request["password"] == "[REDACTED]"



    # The caller's original request remains unchanged.

    assert request["password"] == "super-secret"
