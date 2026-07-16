"""
Pipedrive read-only MCP server.

A small, self-contained Model Context Protocol (MCP) server that exposes
read-only Pipedrive data (deals, activities, notes, contacts/orgs, and deal
mail) to Claude as a custom connector.

Design notes
------------
* Self-contained: it does NOT import the rest of the quoter_sync project, so it
  can run on a newer Python (3.11) as a *separate* Render service without
  touching the existing Flask webhook app (which is pinned to Python 3.9).
* Reuses the same PIPEDRIVE_API_TOKEN secret you already store on Render.
* Read-only: every tool performs GET requests only. Nothing here can create,
  modify, or delete anything in Pipedrive.
* Access control: the MCP endpoint is mounted at a secret, hard-to-guess URL
  path (MCP_PATH_SECRET). Only someone who knows the full URL can reach it.
"""

import os
import logging

import requests
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pipedrive-mcp")

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
API_TOKEN = os.getenv("PIPEDRIVE_API_TOKEN")
BASE_URL = os.getenv("PIPEDRIVE_BASE_URL", "https://api.pipedrive.com/v1")

# Secret path segment that guards the MCP endpoint. Set this to a long random
# string on Render. The connector URL becomes:
#   https://<service>.onrender.com/<MCP_PATH_SECRET>/mcp
# If unset, the server falls back to a plain /mcp path (NOT recommended for
# anything other than local testing).
MCP_PATH_SECRET = os.getenv("MCP_PATH_SECRET", "").strip("/")
MCP_PATH = f"/{MCP_PATH_SECRET}/mcp" if MCP_PATH_SECRET else "/mcp"

HTTP_TIMEOUT = 30

mcp = FastMCP(
    name="Pipedrive (read-only)",
    instructions=(
        "Read-only access to a Pipedrive CRM. Use these tools to gather the "
        "full context around a deal (its activities, notes, participants, "
        "linked person/organization, and email) so you can summarize status "
        "and draft next steps. All tools are read-only."
    ),
)


# --------------------------------------------------------------------------
# Internal HTTP helper
# --------------------------------------------------------------------------
def _get(path: str, params: dict | None = None) -> dict:
    """Perform a GET against the Pipedrive API and return the parsed JSON.

    Returns a dict shaped like {"ok": bool, "data": ..., "error": ...}.
    Never raises for HTTP/network errors so the model gets a clean message.
    """
    if not API_TOKEN:
        return {"ok": False, "error": "PIPEDRIVE_API_TOKEN is not set on the server."}

    p = dict(params or {})
    p["api_token"] = API_TOKEN
    url = f"{BASE_URL}{path}"
    try:
        resp = requests.get(url, params=p, timeout=HTTP_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        logger.error("Request error for %s: %s", path, exc)
        return {"ok": False, "error": f"Request failed: {exc}"}

    if resp.status_code == 404:
        return {"ok": False, "error": "Not found", "status": 404}
    if resp.status_code == 401:
        return {"ok": False, "error": "Unauthorized - check PIPEDRIVE_API_TOKEN", "status": 401}
    if resp.status_code >= 400:
        return {"ok": False, "error": f"Pipedrive returned {resp.status_code}", "status": resp.status_code}

    try:
        body = resp.json()
    except ValueError:
        return {"ok": False, "error": "Non-JSON response from Pipedrive"}

    return {"ok": True, "data": body.get("data"), "additional_data": body.get("additional_data")}


# --------------------------------------------------------------------------
# Field trimming helpers (keep responses compact & useful)
# --------------------------------------------------------------------------
def _trim_activity(a: dict) -> dict:
    return {
        "id": a.get("id"),
        "type": a.get("type"),
        "subject": a.get("subject"),
        "done": a.get("done"),
        "due_date": a.get("due_date"),
        "due_time": a.get("due_time"),
        "marked_as_done_time": a.get("marked_as_done_time"),
        "add_time": a.get("add_time"),
        "note": a.get("note"),
        "owner_name": a.get("owner_name"),
        "person_name": a.get("person_name"),
        "org_name": a.get("org_name"),
    }


def _trim_note(n: dict) -> dict:
    return {
        "id": n.get("id"),
        "content": n.get("content"),
        "add_time": n.get("add_time"),
        "update_time": n.get("update_time"),
        "user_id": n.get("user_id"),
        "deal_id": n.get("deal_id"),
        "person_id": n.get("person_id"),
        "org_id": n.get("org_id"),
    }


def _trim_mail(m: dict) -> dict:
    return {
        "id": m.get("id"),
        "subject": m.get("subject"),
        "snippet": m.get("snippet"),
        "from": m.get("from"),
        "to": m.get("to"),
        "message_time": m.get("message_time"),
        "has_body": bool(m.get("has_body")),
        "read_flag": m.get("read_flag"),
    }


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------
@mcp.tool
def search_deals(term: str, status: str | None = None, limit: int = 20) -> dict:
    """Search deals by title/keyword.

    Args:
        term: Text to search for in deal titles (and related fields).
        status: Optional filter - one of "open", "won", "lost", "deleted".
        limit: Max results (default 20).
    """
    res = _get("/deals/search", {"term": term, "limit": limit})
    if not res["ok"]:
        return res
    items = (res.get("data") or {}).get("items", [])
    deals = []
    for it in items:
        d = it.get("item", {})
        if status and (d.get("status") != status):
            continue
        deals.append({
            "id": d.get("id"),
            "title": d.get("title"),
            "status": d.get("status"),
            "value": d.get("value"),
            "currency": d.get("currency"),
            "stage": (d.get("stage") or {}).get("name") if isinstance(d.get("stage"), dict) else d.get("stage"),
            "person": (d.get("person") or {}).get("name") if isinstance(d.get("person"), dict) else None,
            "organization": (d.get("organization") or {}).get("name") if isinstance(d.get("organization"), dict) else None,
        })
    return {"ok": True, "count": len(deals), "deals": deals}


@mcp.tool
def list_deals(status: str = "open", limit: int = 30) -> dict:
    """List deals, optionally filtered by status.

    Args:
        status: "open" (default), "won", "lost", "deleted", or "all_not_deleted".
        limit: Max results (default 30).
    """
    return _get("/deals", {"status": status, "limit": limit})


@mcp.tool
def get_deal(deal_id: int) -> dict:
    """Get full details for a single deal by its ID."""
    return _get(f"/deals/{deal_id}")


@mcp.tool
def get_deal_activities(deal_id: int, limit: int = 50) -> dict:
    """Get activities (meetings, calls, tasks, emails logged as activities) for a deal."""
    res = _get(f"/deals/{deal_id}/activities", {"limit": limit})
    if not res["ok"]:
        return res
    data = res.get("data") or []
    return {"ok": True, "count": len(data), "activities": [_trim_activity(a) for a in data]}


@mcp.tool
def get_deal_notes(deal_id: int, limit: int = 50) -> dict:
    """Get notes attached to a deal."""
    res = _get("/notes", {"deal_id": deal_id, "limit": limit})
    if not res["ok"]:
        return res
    data = res.get("data") or []
    return {"ok": True, "count": len(data), "notes": [_trim_note(n) for n in data]}


@mcp.tool
def get_deal_participants(deal_id: int) -> dict:
    """Get the people (participants) associated with a deal."""
    res = _get(f"/deals/{deal_id}/participants")
    if not res["ok"]:
        return res
    data = res.get("data") or []
    people = []
    for row in data:
        person = row.get("person") if isinstance(row, dict) else None
        if isinstance(person, dict):
            people.append({
                "id": person.get("id"),
                "name": person.get("name"),
                "email": person.get("email"),
                "phone": person.get("phone"),
            })
    return {"ok": True, "count": len(people), "participants": people}


@mcp.tool
def get_deal_mail(deal_id: int, limit: int = 50) -> dict:
    """Get email messages linked to a deal (Pipedrive email sync)."""
    res = _get(f"/deals/{deal_id}/mailMessages", {"limit": limit})
    if not res["ok"]:
        return res
    data = res.get("data") or []
    mails = []
    for row in data:
        # mailMessages rows sometimes wrap the message under a "data" key
        m = row.get("data") if isinstance(row, dict) and "data" in row else row
        if isinstance(m, dict):
            mails.append(_trim_mail(m))
    return {"ok": True, "count": len(mails), "mail": mails}


@mcp.tool
def get_person(person_id: int) -> dict:
    """Get a person/contact by ID."""
    return _get(f"/persons/{person_id}")


@mcp.tool
def get_organization(org_id: int) -> dict:
    """Get an organization by ID."""
    return _get(f"/organizations/{org_id}")


@mcp.tool
def search_persons(term: str, limit: int = 20) -> dict:
    """Search for people/contacts by name, email, or phone."""
    res = _get("/persons/search", {"term": term, "limit": limit})
    if not res["ok"]:
        return res
    items = (res.get("data") or {}).get("items", [])
    return {"ok": True, "count": len(items), "persons": [it.get("item") for it in items]}


@mcp.tool
def search_organizations(term: str, limit: int = 20) -> dict:
    """Search for organizations by name."""
    res = _get("/organizations/search", {"term": term, "limit": limit})
    if not res["ok"]:
        return res
    items = (res.get("data") or {}).get("items", [])
    return {"ok": True, "count": len(items), "organizations": [it.get("item") for it in items]}


@mcp.tool
def get_deal_context(deal_id: int) -> dict:
    """Get EVERYTHING about a deal in one call: the deal, its linked person and
    organization, activities, notes, participants, and email. This is the best
    tool for preparing a next-steps summary for a deal.
    """
    out: dict = {"ok": True, "deal_id": deal_id}

    deal_res = _get(f"/deals/{deal_id}")
    if not deal_res["ok"]:
        return deal_res
    deal = deal_res.get("data") or {}
    out["deal"] = deal

    # Linked person / organization
    person_id = (deal.get("person_id") or {}).get("value") if isinstance(deal.get("person_id"), dict) else deal.get("person_id")
    org_id = (deal.get("org_id") or {}).get("value") if isinstance(deal.get("org_id"), dict) else deal.get("org_id")
    if person_id:
        pr = _get(f"/persons/{person_id}")
        out["person"] = pr.get("data") if pr["ok"] else {"error": pr.get("error")}
    if org_id:
        orr = _get(f"/organizations/{org_id}")
        out["organization"] = orr.get("data") if orr["ok"] else {"error": orr.get("error")}

    # Activities
    act = _get(f"/deals/{deal_id}/activities", {"limit": 50})
    out["activities"] = [_trim_activity(a) for a in (act.get("data") or [])] if act["ok"] else []

    # Notes
    notes = _get("/notes", {"deal_id": deal_id, "limit": 50})
    out["notes"] = [_trim_note(n) for n in (notes.get("data") or [])] if notes["ok"] else []

    # Participants
    part = _get(f"/deals/{deal_id}/participants")
    if part["ok"]:
        ppl = []
        for row in (part.get("data") or []):
            person = row.get("person") if isinstance(row, dict) else None
            if isinstance(person, dict):
                ppl.append({"id": person.get("id"), "name": person.get("name"), "email": person.get("email")})
        out["participants"] = ppl
    else:
        out["participants"] = []

    # Mail
    mail = _get(f"/deals/{deal_id}/mailMessages", {"limit": 50})
    if mail["ok"]:
        mails = []
        for row in (mail.get("data") or []):
            m = row.get("data") if isinstance(row, dict) and "data" in row else row
            if isinstance(m, dict):
                mails.append(_trim_mail(m))
        out["mail"] = mails
    else:
        out["mail"] = []

    return out


@mcp.tool
def whoami() -> dict:
    """Return basic info about the connected Pipedrive account (sanity check)."""
    return _get("/users/me")


# --------------------------------------------------------------------------
# ASGI app + entrypoint
# --------------------------------------------------------------------------
# Build the ASGI app so it can be served by uvicorn:  `uvicorn server:app`
# allowed_hosts/allowed_origins are relaxed because Render terminates TLS at its
# proxy and forwards the public onrender.com host header; Anthropic connects
# from its own cloud, not localhost.
app = mcp.http_app(
    path=MCP_PATH,
    allowed_hosts=["*"],
    allowed_origins=["*"],
)

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    logger.info("Starting Pipedrive MCP server on port %s at path %s", port, MCP_PATH)
    uvicorn.run(app, host="0.0.0.0", port=port)
