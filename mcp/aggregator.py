"""Tasks 10, 11: MCP aggregator — combines multiple MCP servers with tool prefixes and Resources/Prompts."""
import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """Minimal in-process MCP client that spawns a server subprocess."""

    def __init__(self, name: str, cmd: list[str], prefix: str):
        self.name = name
        self.cmd = cmd
        self.prefix = prefix
        self._process: Optional[subprocess.Popen] = None
        self._tools: list[dict] = []

    async def connect(self):
        try:
            self._process = await asyncio.create_subprocess_exec(
                *self.cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            # Send MCP initialize
            await self._send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "aggregator", "version": "1.0"},
            }})
            await self._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            # Get tools list
            await self._send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            resp = await self._recv()
            self._tools = resp.get("result", {}).get("tools", [])
            logger.info(f"MCP client '{self.name}' connected, tools: {[t['name'] for t in self._tools]}")
        except Exception as e:
            logger.warning(f"MCP client '{self.name}' connect failed: {e}")

    async def _send(self, msg: dict):
        import json
        data = (json.dumps(msg) + "\n").encode()
        if self._process and self._process.stdin:
            self._process.stdin.write(data)
            await self._process.stdin.drain()

    async def _recv(self) -> dict:
        import json
        if self._process and self._process.stdout:
            try:
                line = await asyncio.wait_for(self._process.stdout.readline(), timeout=5.0)
                return json.loads(line)
            except Exception:
                pass
        return {}

    def get_tools(self) -> list[dict]:
        return [{"name": f"{self.prefix}__{t['name']}", "original": t["name"], "client": self} for t in self._tools]

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        import json
        await self._send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                          "params": {"name": tool_name, "arguments": arguments}})
        resp = await self._recv()
        content = resp.get("result", {}).get("content", [])
        if content:
            return content[0].get("text", "")
        return str(resp)

    async def disconnect(self):
        if self._process:
            self._process.terminate()


class MCPAggregator:
    """Task 10: Aggregates tools from multiple MCP servers with prefix routing.
       Task 11: Exposes Resources and Prompts."""

    RESOURCES = [
        {"uri": "template://essay_ru", "name": "Шаблон эссе (RU)", "description": "Структура академического эссе"},
        {"uri": "template://essay_kz", "name": "Үлгі эссе (KZ)", "description": "Академиялық эссенің құрылымы"},
    ]

    PROMPTS = [
        {"name": "write_essay", "description": "Написать академическое эссе", "arguments": [{"name": "topic", "required": True}]},
        {"name": "explain_concept", "description": "Объяснить концепцию простым языком", "arguments": [{"name": "concept", "required": True}]},
    ]

    RESOURCE_CONTENTS = {
        "template://essay_ru": (
            "# Структура эссе\n1. Введение (тезис)\n2. Основная часть (3 аргумента)\n3. Заключение"
        ),
        "template://essay_kz": (
            "# Эссенің құрылымы\n1. Кіріспе (тезис)\n2. Негізгі бөлім (3 дәлел)\n3. Қорытынды"
        ),
    }

    def __init__(self, settings):
        python = sys.executable
        self._clients: list[MCPClient] = [
            MCPClient("filesystem", [python, str(Path(__file__).parent / "filesystem_server.py")], "fs"),
            MCPClient("postgres", [python, str(Path(__file__).parent / "postgres_server.py"), "admin"], "pg"),
        ]

    async def connect_all(self):
        await asyncio.gather(*[c.connect() for c in self._clients], return_exceptions=True)

    def list_tools(self) -> list[dict]:
        tools = []
        for client in self._clients:
            tools.extend(client.get_tools())
        return tools

    async def call_tool(self, prefixed_name: str, arguments: dict) -> str:
        """Route tool call to correct server by prefix."""
        for client in self._clients:
            for tool in client.get_tools():
                if tool["name"] == prefixed_name:
                    return await client.call_tool(tool["original"], arguments)
        # Fallback: try direct name
        for client in self._clients:
            for tool in client.get_tools():
                if tool["original"] == prefixed_name:
                    return await client.call_tool(tool["original"], arguments)
        return f"Tool not found: {prefixed_name}"

    def list_resources(self) -> list[dict]:
        """Task 11: resources/list."""
        return self.RESOURCES

    def read_resource(self, uri: str) -> str:
        """Task 11: resources/read."""
        return self.RESOURCE_CONTENTS.get(uri, "Resource not found")

    def list_prompts(self) -> list[dict]:
        """Task 11: prompts/list."""
        return self.PROMPTS

    def get_prompt(self, name: str, arguments: dict) -> str:
        """Task 11: prompts/get."""
        if name == "write_essay":
            topic = arguments.get("topic", "")
            return f"Напиши развернутое академическое эссе на тему: '{topic}'. Структура: введение, 3 аргумента, заключение."
        if name == "explain_concept":
            concept = arguments.get("concept", "")
            return f"Объясни концепцию '{concept}' простым языком для студента первого курса."
        return f"Prompt '{name}' not found"

    async def disconnect_all(self):
        await asyncio.gather(*[c.disconnect() for c in self._clients], return_exceptions=True)
