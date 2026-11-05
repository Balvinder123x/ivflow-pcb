"""Talk to the Fusion 360 MCP server directly over HTTP (used when the Claude Code
extension does not load the server).

    python scripts/fusion_mcp.py script FILE.py            run a Fusion API script (must define run(context))
    python scripts/fusion_mcp.py screenshot OUT.png [DIR]  save a view (DIR: front, iso-top-right, ...)
    python scripts/fusion_mcp.py call TOOL '{"json": "args"}'

Fusion must be open with its MCP add-in running (default http://127.0.0.1:27182/mcp).
"""
import base64
import json
import os
import sys
import urllib.request

URL = os.environ.get("FUSION_MCP_URL", "http://127.0.0.1:27182/mcp")
HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def _post(payload, sid=None, timeout=600):
    h = dict(HEADERS)
    if sid:
        h["Mcp-Session-Id"] = sid
    req = urllib.request.Request(URL, json.dumps(payload).encode(), h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", "replace")
        sid = r.headers.get("Mcp-Session-Id") or sid
    # Streamable HTTP may answer as an SSE stream: take the last "data:" JSON message
    if body.lstrip().startswith("event:") or "\ndata:" in body or body.startswith("data:"):
        datas = [line[5:].strip() for line in body.splitlines() if line.startswith("data:")]
        body = datas[-1] if datas else "{}"
    return (json.loads(body) if body.strip() else {}), sid


def session():
    _, sid = _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                               "clientInfo": {"name": "ivflow-scripts", "version": "1"}}})
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    return sid


def call(tool, args, sid=None):
    sid = sid or session()
    res, _ = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": tool, "arguments": args}}, sid)
    if "error" in res:
        raise SystemExit(f"MCP error: {res['error']}")
    return res.get("result", {})


def text_of(result):
    return "\n".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "script":
        src = open(sys.argv[2], encoding="utf-8").read()
        r = call("fusion_mcp_execute", {"featureType": "script", "object": {"script": src}})
        print(text_of(r))
        if r.get("isError"):
            sys.exit(1)
    elif cmd == "screenshot":
        args = {"queryType": "screenshot", "direction": sys.argv[3] if len(sys.argv) > 3 else "iso-top-right",
                "width": 1400, "height": 1000, "transparentBackground": False}
        r = call("fusion_mcp_read", args)
        saved = False
        for c in r.get("content", []):
            if c.get("type") == "image":
                open(sys.argv[2], "wb").write(base64.b64decode(c["data"]))
                saved = True
        txt = text_of(r)
        if not saved:
            # Some servers return a signed URL instead of inline image data
            try:
                info = json.loads(txt)
            except ValueError:
                info = {}
            url = info.get("signed_url") or info.get("url")
            if url:
                urllib.request.urlretrieve(url, sys.argv[2])
                saved = True
        print(f"saved {sys.argv[2]}" if saved else txt[:2000])
    elif cmd == "call":
        print(json.dumps(call(sys.argv[2], json.loads(sys.argv[3])), indent=1)[:5000])
