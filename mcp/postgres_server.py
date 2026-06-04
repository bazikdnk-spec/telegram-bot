"""Tasks 8, 9: MCP PostgreSQL server with role-based auth."""
import csv
import io
import json
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

try:
    import asyncpg
    _PG_AVAILABLE = True
except ImportError:
    _PG_AVAILABLE = False

app = Server("postgres-server")

# Roles: student < teacher < admin
ROLE_TOOLS = {
    "student": ["query_users"],
    "teacher": ["query_users", "get_user_stats"],
    "admin": ["query_users", "get_user_stats", "export_to_csv"],
}

_pool = None
_current_role = "student"


async def get_pool():
    global _pool
    if _pool is None and _PG_AVAILABLE:
        dsn = os.environ.get("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/botdb")
        _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
    return _pool


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    allowed = ROLE_TOOLS.get(_current_role, [])
    all_tools = [
        types.Tool(
            name="query_users",
            description="Query users from the database",
            inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}}},
        ),
        types.Tool(
            name="get_user_stats",
            description="Get user statistics (teacher+)",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="export_to_csv",
            description="Export data to CSV (admin only)",
            inputSchema={"type": "object", "properties": {"table": {"type": "string"}}},
        ),
    ]
    return [t for t in all_tools if t.name in allowed]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    allowed = ROLE_TOOLS.get(_current_role, [])
    # Task 9: Role-based access control
    if name not in allowed:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": -32603, "message": f"Недостаточно прав. Требуется роль выше '{_current_role}'."})
        )]

    pool = await get_pool()
    if not pool:
        return [types.TextContent(type="text", text="PostgreSQL недоступен")]

    try:
        async with pool.acquire() as conn:
            if name == "query_users":
                limit = arguments.get("limit", 10)
                rows = await conn.fetch("SELECT user_id, role, content FROM history LIMIT $1", limit)
                result = [dict(r) for r in rows]
                return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

            if name == "get_user_stats":
                rows = await conn.fetch(
                    "SELECT user_id, COUNT(*) as messages FROM history GROUP BY user_id ORDER BY messages DESC LIMIT 20"
                )
                result = [{"user_id": r["user_id"], "messages": r["messages"]} for r in rows]
                return [types.TextContent(type="text", text=json.dumps(result))]

            if name == "export_to_csv":
                table = arguments.get("table", "history")
                rows = await conn.fetch(f"SELECT * FROM {table} LIMIT 1000")
                buf = io.StringIO()
                if rows:
                    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows([dict(r) for r in rows])
                return [types.TextContent(type="text", text=buf.getvalue())]

    except Exception as e:
        return [types.TextContent(type="text", text=f"DB error: {e}")]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def run(role: str = "student"):
    global _current_role
    _current_role = role
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    import sys
    role = sys.argv[1] if len(sys.argv) > 1 else "student"
    asyncio.run(run(role))
