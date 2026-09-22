import pytest

from backend.app.tools.linux.tool import LinuxTool


DF_OUTPUT = """\
Filesystem 1024-blocks Used Available Capacity Mounted on
/dev/root 104857600 73400320 31457280 70% /
/dev/data 209715200 104857600 104857600 50% /data
/dev/u01 52428800 41943040 10485760 80% /u01
"""


async def fake_runner(
    command: list[str],
) -> tuple[int, str, str]:
    return (
        0,
        DF_OUTPUT,
        "",
    )


async def failing_runner(
    command: list[str],
) -> tuple[int, str, str]:
    return (
        1,
        "",
        "df: /missing: No such file or directory",
    )


def test_build_request_defaults_to_localhost():
    tool = LinuxTool()

    request = tool.build_request()

    assert request == {
        "server": "localhost",
    }


def test_build_request_supports_filesystem():
    tool = LinuxTool()

    request = tool.build_request(
        server="DEV-SERVER-01",
        filesystem="/data",
    )

    assert request == {
        "server": "DEV-SERVER-01",
        "filesystem": "/data",
    }


@pytest.mark.asyncio
async def test_execute_returns_filesystem_capacity():
    tool = LinuxTool(
        command_runner=fake_runner,
    )

    result = await tool.execute(
        {
            "server": "DEV-SERVER-01",
        }
    )

    assert result["status"] == "success"
    assert result["tool"] == "linux"
    assert result["data"]["server"] == "DEV-SERVER-01"
    assert result["data"]["disk_usage"] == "70.0%"
    assert result["data"]["execution_mode"] == "local"

    filesystems = result["data"]["filesystems"]

    assert len(filesystems) == 3

    assert filesystems[0] == {
        "filesystem": "/dev/root",
        "mount_point": "/",
        "total_mb": 102400.0,
        "used_mb": 71680.0,
        "available_mb": 30720.0,
        "used_percent": 70.0,
    }


@pytest.mark.asyncio
async def test_execute_returns_multiple_filesystems():
    tool = LinuxTool(
        command_runner=fake_runner,
    )

    result = await tool.execute(
        {
            "server": "DEV-SERVER-01",
        }
    )

    mount_points = [
        item["mount_point"]
        for item in result["data"]["filesystems"]
    ]

    assert mount_points == [
        "/",
        "/data",
        "/u01",
    ]


@pytest.mark.asyncio
async def test_execute_can_filter_filesystem():
    captured_command = {}

    async def filtered_runner(
        command: list[str],
    ) -> tuple[int, str, str]:
        captured_command["command"] = command

        return (
            0,
            """\
Filesystem 1024-blocks Used Available Capacity Mounted on
/dev/data 209715200 104857600 104857600 50% /data
""",
            "",
        )

    tool = LinuxTool(
        command_runner=filtered_runner,
    )

    result = await tool.execute(
        {
            "server": "DEV-SERVER-01",
            "filesystem": "/data",
        }
    )

    assert captured_command["command"] == [
        "df",
        "-P",
        "-k",
        "/data",
    ]

    assert (
        result["data"]["filesystems"][0]["mount_point"]
        == "/data"
    )


@pytest.mark.asyncio
async def test_execute_returns_error_when_df_fails():
    tool = LinuxTool(
        command_runner=failing_runner,
    )

    result = await tool.execute(
        {
            "server": "DEV-SERVER-01",
            "filesystem": "/missing",
        }
    )

    assert result["status"] == "error"
    assert (
        "No such file or directory"
        in result["message"]
    )


@pytest.mark.asyncio
async def test_execute_returns_error_when_df_returns_no_data():
    async def empty_runner(
        command: list[str],
    ) -> tuple[int, str, str]:
        return (
            0,
            "",
            "",
        )

    tool = LinuxTool(
        command_runner=empty_runner,
    )

    result = await tool.execute(
        {
            "server": "DEV-SERVER-01",
        }
    )

    assert result["status"] == "error"
    assert (
        "No filesystem data"
        in result["message"]
    )


def test_validate_request_rejects_missing_server():
    tool = LinuxTool()

    with pytest.raises(
        ValueError,
        match="Linux server must be a non-empty string",
    ):
        tool.validate_request(
            {
                "server": "",
            }
        )


def test_validate_request_rejects_invalid_filesystem():
    tool = LinuxTool()

    with pytest.raises(
        ValueError,
        match="Linux filesystem must be a string",
    ):
        tool.validate_request(
            {
                "server": "DEV-SERVER-01",
                "filesystem": 123,
            }
        )
