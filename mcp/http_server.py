"""Task 12: MCP server with HTTP/SSE transport + Bearer token auth."""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from mcp.server import Server
from mcp import types
import json
import asyncio

BEARER_TOKEN = os.environ.get("MCP_BEARER_TOKEN", "secret-mcp-token")
ALLOWED_DIR = Path(".").resolve()

app_mcp = Server("filesystem-http-server")
app = FastAPI(title="MCP HTTP Server")
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid Bearer token")
    return credentials


@app_mcp.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_directory",
            description="List files in the allowed directory",
            inputSchema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
            },
        ),
    ]


@app_mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "list_directory":
        rel = arguments.get("path", ".")
        target = (ALLOWED_DIR / rel).resolve()
        if not str(target).startswith(str(ALLOWED_DIR)):
            return [types.TextContent(type="text", text="Access denied")]
        items = [item.name for item in target.iterdir()]
        return [types.TextContent(type="text", text=json.dumps(items))]
    return [types.TextContent(type="text", text="Unknown tool")]


@app.get("/tools/list", dependencies=[Depends(verify_token)])
async def http_list_tools():
    """Task 12: HTTP endpoint for tools/list."""
    tools = await list_tools()
    return {"tools": [{"name": t.name, "description": t.description} for t in tools]}


@app.post("/tools/call", dependencies=[Depends(verify_token)])
async def http_call_tool(request: Request):
    """Task 12: HTTP endpoint for tools/call."""
    body = await request.json()
    name = body.get("name", "")
    arguments = body.get("arguments", {})
    results = await call_tool(name, arguments)
    return {"content": [{"type": r.type, "text": r.text} for r in results]}


@app.get("/sse", dependencies=[Depends(verify_token)])
async def sse_endpoint():
    """Task 12: SSE stream for real-time events."""
    async def event_generator():
        for i in range(5):
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'event': 'heartbeat', 'seq': i})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("MCP_HTTP_PORT", 8080)))
