"""Task 7: MCP filesystem server using official MCP Python SDK."""
import os
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

ALLOWED_DIR = Path(".").resolve()

app = Server("filesystem-server")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_directory",
            description="List files in the allowed directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path (default: '.')"}
                },
            },
        ),
        types.Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"}
                },
                "required": ["path"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "list_directory":
        rel_path = arguments.get("path", ".")
        target = (ALLOWED_DIR / rel_path).resolve()
        if not str(target).startswith(str(ALLOWED_DIR)):
            return [types.TextContent(type="text", text="Access denied")]
        items = []
        try:
            for item in target.iterdir():
                prefix = "📁" if item.is_dir() else "📄"
                items.append(f"{prefix} {item.name}")
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {e}")]
        return [types.TextContent(type="text", text="\n".join(sorted(items)))]

    if name == "read_file":
        rel_path = arguments.get("path", "")
        target = (ALLOWED_DIR / rel_path).resolve()
        if not str(target).startswith(str(ALLOWED_DIR)):
            return [types.TextContent(type="text", text="Access denied")]
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            return [types.TextContent(type="text", text=content[:8000])]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {e}")]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
