# Pipedrive MCP Connection — Technical Manual

This manual documents the read-only Pipedrive MCP server that lets Claude pull
deal context (deals, activities, notes, contacts/orgs, email) to prepare
next-steps documents. It covers the architecture, the exact steps to recreate
the connection, the key decisions and gotchas, and ongoing maintenance.

> This is an **infrastructure** integration, not an application. There is no
> user manual: "using" it means asking Claude in natural language once the
> connector is enabled.

---

## 1. Architecture at a glance

```
Claude (desktop / web)
      │  MCP over HTTPS (streamable HTTP)
      ▼
Anthropic cloud  ──►  https://pipedrive-mcp-<id>.onrender.com/<SECRET>/mcp
      │                         │  (Render web service: uvicorn + FastMCP)
      │                         ▼
      │                 mcp_server/server.py  ──►  Pipedrive REST API v1
      │                         (api_token from env)      api.pipedrive.com
```

Key facts:

- **Two separate Render services, one repo.**
  - `quoter-webhook-server` — the existing Flask webhook/sync app (Python 3.9→3.11).
  - `pipedrive-mcp` — this MCP server (Python 3.11), Root Directory `mcp_server/`.
- **Claude connects from Anthropic's cloud**, not your laptop. The server must
  be reachable on the public internet (Render's public URL satisfies this).
- **Read-only.** Every tool issues HTTP GET only; nothing writes to Pipedrive.
- **Access control = a secret URL path.** There is no OAuth; the unguessable
  path segment (`MCP_PATH_SECRET`) is the shared secret.

---

## 2. Repository layout (`mcp_server/`)

| File | Purpose |
|------|---------|
| `server.py` | FastMCP server + self-contained Pipedrive client + tool definitions |
| `requirements.txt` | Pinned deps: `fastmcp`, `uvicorn`, `requests` |
| `.python-version` | Pins Python `3.11.9` |
| `.env.example` | Template for local env vars (never commit a real `.env`) |
| `render.yaml` | Reference service definition (dashboard setup is primary) |
| `README.md` | Quickstart deploy + connect guide |
| `TECHNICAL_MANUAL.md` | This document |

The server is deliberately **self-contained** — it does not import the rest of
`quoter_sync`, so it runs on a newer Python as its own service without touching
the Flask app.

---

## 3. Steps to (re)create the MCP connection

### 3.1 Prerequisites
- A Pipedrive **API token** (Pipedrive → Settings → Personal preferences → API).
- A GitHub repo Render can deploy from.
- A Claude plan that supports custom connectors (Pro/Max/Team/Enterprise/Free-1).

### 3.2 Generate the secret path
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```
Save the output — it becomes `MCP_PATH_SECRET`.

### 3.3 Deploy the Render service
1. Push `mcp_server/` to GitHub.
2. Render → **New + → Web Service** → select the repo.
3. Configure:
   - **Root Directory:** `mcp_server`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Starter (always-on) recommended; Free works but cold-starts.
4. Environment variables (mark secrets as such):
   - `PYTHON_VERSION` = `3.11.9`
   - `PIPEDRIVE_API_TOKEN` = *your token*
   - `MCP_PATH_SECRET` = *the string from 3.2*
5. Leave **Health Check Path** blank (the app has no GET health route; blank =
   Render just checks the port opens).
6. Create the service and wait for "Your service is live."

### 3.4 Verify the endpoint (from a machine with open internet)
```bash
curl -i -X POST "https://<service>.onrender.com/<SECRET>/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}'
```
Expect `HTTP/2 200` and an `event: message` line with `serverInfo:"Pipedrive (read-only)"`.
A wrong path returns `404`.

### 3.5 Connect in Claude
1. **Settings/Customize → Connectors → + → Add custom connector.**
2. URL: `https://<service>.onrender.com/<SECRET>/mcp`
3. Leave OAuth Client ID/Secret **blank**. Add.
4. In a chat, **+ → Connectors** → enable **Pipedrive (read-only)**.
5. Sanity check: ask Claude to run `whoami` — it should return your Pipedrive
   account (name, email, company).

---

## 4. Available tools

| Tool | Returns |
|------|---------|
| `search_deals` / `list_deals` | Find/list deals by keyword or status |
| `get_deal` | Full detail for one deal |
| `get_deal_activities` | Meetings, calls, tasks |
| `get_deal_notes` | Notes |
| `get_deal_participants` | People on the deal |
| `get_deal_mail` | Linked emails |
| `get_person` / `get_organization` | Contact / org detail |
| `search_persons` / `search_organizations` | Find contacts / orgs |
| `get_deal_context` | **Deal + person + org + activities + notes + participants + mail in one call** (best for prep docs) |
| `whoami` | Connection/token sanity check |

---

## 5. Key decisions & gotchas (learned the hard way)

- **Separate service, not shared.** The MCP libraries need Python ≥3.10; the
  Flask app was pinned to 3.9. Isolating avoids version conflicts and means an
  MCP restart never disturbs the webhook/sync flow.
- **Local Python ≠ Render Python.** Upgrading Python locally (brew) and pushing
  does **not** change Render's runtime. Render reads the version from the repo
  pin (`PYTHON_VERSION` env var / `.python-version`), and the local `venv/` is
  gitignored so it never deploys.
- **`host_origin_protection` must be `False`.** FastMCP's DNS-rebinding guard
  is for browsers. Passing `allowed_hosts=["*"]` does *not* mean "allow all" —
  `*` is treated as a literal host, which *enables* strict checking and then
  403s the real onrender.com host. The fix in `server.py`:
  ```python
  app = mcp.http_app(path=MCP_PATH, host_origin_protection=False)
  ```
  This is safe here: it's a server-to-server API, and the secret path is the guard.
- **Root Directory limits auto-deploy.** Because the service's Root Directory is
  `mcp_server`, Render only auto-deploys when files **inside** `mcp_server/`
  change. If a deploy doesn't fire, use **Manual Deploy → Deploy latest commit**.
- **404 vs 403.** Wrong secret path → `404` (route not found). `403` with header
  `X-Proxy-Error: blocked-by-allowlist` is an *outbound firewall* on the caller's
  side (e.g., a sandbox), not the server.

---

## 6. Maintenance

### Rotate the Pipedrive token
1. Generate a new token in Pipedrive.
2. Update `PIPEDRIVE_API_TOKEN` on **both** Render services (webhook + MCP).
3. Redeploy. Verify with `whoami`.

### Rotate the secret URL
1. Change `MCP_PATH_SECRET` in the `pipedrive-mcp` service env vars; redeploy.
2. In Claude, remove and re-add the custom connector with the new URL
   (connectors can't be edited in place — remove then re-add).

### Add or change a tool
1. Add a `@mcp.tool`-decorated function in `server.py` (GET-only to stay read-only).
2. Commit and push; confirm the `pipedrive-mcp` service redeploys.
3. New tools appear in Claude after the connector reconnects.

### Dependency updates
`requirements.txt` is pinned for reproducible builds. Bump versions
deliberately, then redeploy and re-run the `whoami` check.

### Interaction with `sync.sh` / `retrieve.sh`
- `sync.sh` (`git add -A` → commit → push) carries `mcp_server/` changes to
  GitHub. Render then auto-deploys **if** the change is inside `mcp_server/`;
  otherwise deploy manually.
- The chain is **local → GitHub → (auto-deploy) → Render**. GitHub can be ahead
  of what's actually running if a deploy misfires — confirm the deploy after syncing.
- Safety: only `.env.example` is tracked; the real `.env` and `venv/` stay
  gitignored, so the `sync.sh` guards pass.

---

## 7. Security notes

- The secret URL is effectively a password — anyone with the full URL can read
  the CRM. Treat it accordingly; rotate if exposed.
- Least privilege: the internet-facing MCP service holds **only** the Pipedrive
  token, not the Slack/Gmail/QBO secrets used by the webhook service.
- Read-only by design: no tool can create, modify, or delete Pipedrive data.
- Optional hardening: OAuth for per-user auth, or firewall allowlisting of
  Anthropic's published IP ranges (requires a paid tier + network controls).

---

## 8. Quick troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| `403 Forbidden` from Claude | `host_origin_protection` re-enabled, or wrong config — ensure `host_origin_protection=False`. |
| `403` + `X-Proxy-Error: blocked-by-allowlist` | Caller's outbound firewall blocks onrender.com — test from an unrestricted network. |
| `404` on the endpoint | Secret path mismatch between the URL and `MCP_PATH_SECRET`. |
| `whoami` returns an auth error | `PIPEDRIVE_API_TOKEN` missing/invalid on the service. |
| Changes not live | Root-Directory auto-deploy didn't fire — Manual Deploy. |
| First call slow (Free tier) | Service cold-started after idle; upgrade to Starter for always-on. |
