# Pipedrive MCP Server

A small, **read-only** MCP server that lets Claude pull Pipedrive context
(deals, activities, notes, contacts/orgs, and email) so it can prepare
next-steps documents for a deal or event.

It runs as a **separate Render web service** from your existing Flask webhook
app, reuses the same `PIPEDRIVE_API_TOKEN` secret, and never writes to
Pipedrive.

---

## What Claude gets (tools)

| Tool | Purpose |
|------|---------|
| `search_deals` | Find deals by keyword |
| `list_deals` | List deals by status (open/won/lost) |
| `get_deal` | Full detail for one deal |
| `get_deal_activities` | Meetings, calls, tasks on a deal |
| `get_deal_notes` | Notes on a deal |
| `get_deal_participants` | People attached to a deal |
| `get_deal_mail` | Emails linked to a deal |
| `get_person` / `get_organization` | Contact / org detail |
| `search_persons` / `search_organizations` | Find contacts / orgs |
| `get_deal_context` | **Everything about a deal in one call** (best for prep docs) |
| `whoami` | Sanity check the token/connection |

---

## Deploy to Render

### 1. Generate your secret path

The MCP endpoint lives at a hard-to-guess URL. Generate a random secret:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

Copy the output (e.g. `k3Jh...`). This is your `MCP_PATH_SECRET`.

### 2. Create the service (dashboard route — recommended)

1. Push this `mcp_server/` folder to your existing GitHub repo.
2. In Render: **New +  →  Web Service  →** pick the same repo.
3. Settings:
   - **Root Directory:** `mcp_server`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free is fine
4. **Environment variables** (Environment tab):
   - `PYTHON_VERSION` = `3.11.9`
   - `PIPEDRIVE_API_TOKEN` = *your Pipedrive token* (mark as secret)
   - `MCP_PATH_SECRET` = *the string from step 1* (mark as secret)
5. Create the service and wait for the first deploy to go green.

> Render stores these values encrypted at rest and injects them only into the
> running service. The token never lives in the repo and is never sent to
> Claude.

### 3. Confirm it's up

Your connector URL is:

```
https://<your-service-name>.onrender.com/<MCP_PATH_SECRET>/mcp
```

Quick check from a terminal (should return an SSE `initialize` result):

```bash
curl -i -X POST "https://<your-service>.onrender.com/<MCP_PATH_SECRET>/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"1"}}}'
```

A `200` with `event: message` means it's live. Any other path returns `404`.

---

## Connect it to Claude

1. In Claude, go to **Customize → Connectors**.
2. Click **+ → Add custom connector**.
3. Paste the full URL: `https://<your-service>.onrender.com/<MCP_PATH_SECRET>/mcp`
4. Leave OAuth fields blank (this server has no OAuth; the secret path is the
   guard). Click **Add**.
5. In a chat, open the **+ → Connectors** menu and enable **Pipedrive
   (read-only)**.

Then just ask, e.g. *"Use the Pipedrive connector to pull the context for deal
2530 and draft next steps."*

---

## Security notes

- **Read-only:** every tool is a GET. Nothing can change Pipedrive.
- **Access control is the secret URL.** Anyone with the full URL can read your
  CRM, so treat it like a password. Rotate it any time by changing
  `MCP_PATH_SECRET` in Render (then update the connector URL in Claude).
- **Hardening options (optional):** Render's paid tiers + a firewall let you
  allowlist [Anthropic's IP ranges](https://platform.claude.com/docs/en/api/ip-addresses),
  or you can add full OAuth later for per-user auth.
- Free Render services sleep after inactivity; the first call after idle takes
  ~30s to wake. Fine for occasional prep-doc use.

---

## Local testing

```bash
cd mcp_server
cp .env.example .env      # fill in your token + a secret
pip install -r requirements.txt
python3 server.py         # serves on http://localhost:8000/<secret>/mcp
```
