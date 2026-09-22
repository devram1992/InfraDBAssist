from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from backend.app.tools.base import Tool


CommandRunner = Callable[
    [list[str]],
    Awaitable[tuple[int, str, str]],
]


class LinuxTool(Tool):
    """
    Read-only Linux server diagnostics.

    For the current POC, commands execute on the machine/container
    where InfraDB Assist is running. Remote Linux access can later
    be implemented behind the same tool contract using SSH.
    """

    name = "linux"

    description = "Read-only Linux server diagnostics"

    permission = "infrastructure.read"

    read_only = True

    parameters = {
        "server": {
            "type": "string",
            "description": "Linux server hostname",
            "required": True,
        },
        "filesystem": {
            "type": "string",
            "description": (
                "Optional filesystem or mount point to inspect, "
                "for example /, /u01, or /data"
            ),
            "required": False,
        },
    }

    def __init__(
        self,
        command_runner: CommandRunner | None = None,
    ):
        self.command_runner = (
            command_runner
            or self._run_command
        )

    @staticmethod
    async def _run_command(
        command: list[str],
    ) -> tuple[int, str, str]:
        """
        Execute a fixed read-only command without using a shell.

        Using create_subprocess_exec avoids shell interpretation
        and command injection through request parameters.
        """
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        return (
            process.returncode,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )

    @staticmethod
    def _parse_df_output(
        output: str,
    ) -> list[dict]:
        """
        Parse POSIX df output.

        Expected columns:

        Filesystem
        1024-blocks
        Used
        Available
        Capacity
        Mounted on
        """
        lines = [
            line.strip()
            for line in output.splitlines()
            if line.strip()
        ]

        if not lines:
            return []

        filesystems = []

        for line in lines[1:]:
            parts = line.split(
                maxsplit=5
            )

            if len(parts) != 6:
                continue

            (
                filesystem,
                total_blocks,
                used_blocks,
                available_blocks,
                capacity,
                mount_point,
            ) = parts

            try:
                total_kb = float(total_blocks)
                used_kb = float(used_blocks)
                available_kb = float(
                    available_blocks
                )

                used_percent = float(
                    capacity.rstrip("%")
                )
            except ValueError:
                continue

            if (
                used_percent < 0
                or used_percent > 100
            ):
                continue

            filesystems.append(
                {
                    "filesystem": filesystem,
                    "mount_point": mount_point,
                    "total_mb": round(
                        total_kb / 1024,
                        2,
                    ),
                    "used_mb": round(
                        used_kb / 1024,
                        2,
                    ),
                    "available_mb": round(
                        available_kb / 1024,
                        2,
                    ),
                    "used_percent": used_percent,
                }
            )

        return filesystems

    def build_request(
        self,
        **kwargs,
    ) -> dict:
        """
        Build a Linux server request.
        """
        request = {
            "server": (
                kwargs.get("server")
                or "localhost"
            ),
        }

        filesystem = kwargs.get(
            "filesystem"
        )

        if filesystem:
            request["filesystem"] = (
                filesystem.strip()
            )

        return request

    def validate_request(
        self,
        request: dict,
    ) -> None:
        """
        Validate a Linux diagnostic request.
        """
        super().validate_request(request)

        server = request.get("server")

        if not isinstance(server, str) or not server.strip():
            raise ValueError(
                "Linux server must be a non-empty string."
            )

        filesystem = request.get(
            "filesystem"
        )

        if filesystem is not None:
            if not isinstance(
                filesystem,
                str,
            ):
                raise ValueError(
                    "Linux filesystem must be a string."
                )

            if not filesystem.strip():
                raise ValueError(
                    "Linux filesystem cannot be empty."
                )

    async def execute(
        self,
        request: dict,
    ) -> dict:
        """
        Execute read-only df capacity collection.
        """
        self.validate_request(request)

        server = request["server"]
        filesystem = request.get(
            "filesystem"
        )

        command = [
            "df",
            "-P",
            "-k",
        ]

        if filesystem:
            command.append(filesystem)

        return_code, stdout, stderr = (
            await self.command_runner(command)
        )

        if return_code != 0:
            return {
                "tool": self.name,
                "status": "error",
                "message": (
                    stderr.strip()
                    or "Linux df command failed."
                ),
                "data": {
                    "server": server,
                },
            }

        filesystems = (
            self._parse_df_output(stdout)
        )

        if not filesystems:
            return {
                "tool": self.name,
                "status": "error",
                "message": (
                    "No filesystem data was returned "
                    "by the df command."
                ),
                "data": {
                    "server": server,
                },
            }

        root_filesystem = next(
            (
                item
                for item in filesystems
                if item["mount_point"] == "/"
            ),
            filesystems[0],
        )

        return {
            "tool": self.name,
            "status": "success",
            "data": {
                "server": server,
                "disk_usage": (
                    f'{root_filesystem["used_percent"]}%'
                ),
                "filesystems": filesystems,
                "execution_mode": "local",
            },
        }