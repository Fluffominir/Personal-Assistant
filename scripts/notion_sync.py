# Applying the provided changes to enhance Notion API authentication and error handling.
import os, json, time, asyncio, aiohttp
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec
from openai import AsyncOpenAI

# ---------- Load env ------------
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
try:
    workspaces_str = os.getenv("NOTION_WORKSPACES", "{}")
    workspaces = json.loads(workspaces_str)
    print(f"📝 Loaded workspaces: {list(workspaces.keys())}")
except json.JSONDecodeError:
    print("⚠️  Invalid NOTION_WORKSPACES JSON, falling back to API key")
    workspaces = {}
    if NOTION_API_KEY:
        workspaces = {"default": {"token": NOTION_API_KEY}}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    print("⚠️  Missing required API keys for sync")
    exit(1)

if not workspaces:
    print("⚠️  No Notion workspaces configured")
    exit(1)

# ---------- Init clients ----------
pc = Pinecone(api_key=PINECONE_API_KEY)

# Use the main index instead of creating a separate one
index_name = "companion-memory"
if index_name not in [i["name"] for i in pc.list_indexes()]:
    print(f"⚠️  Main index '{index_name}' not found. Please run ingest.py first.")
    exit(1)

index = pc.Index(index_name)

oai = AsyncOpenAI(api_key=OPENAI_API_KEY)
NOTION_VER = "2022-06-28"

# ---------- Helpers --------------
async def embed(text: str):
    resp = await oai.embeddings.create(
        model="text-embedding-3-small", input=text[:8191])
    return resp.data[0].embedding

async def fetch_json(session, url, token, payload=None):
    hdrs = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VER,
        "Content-Type": "application/json"
    }
    method = "POST" if payload is not None else "GET"
    async with session.request(method, url, headers=hdrs, json=payload) as r:
        r.raise_for_status()
        return await r.json()

async def sync_workspace(key, ws):
    token = ws["token"]
    print(f"🔄 Syncing workspace: {key}")

    async with aiohttp.ClientSession() as session:
        try:
            # 1. discover ALL databases with better error handling
            try:
                dbs = await fetch_json(session, "https://api.notion.com/v1/search", token,
                                       {"filter":{"property":"object","value":"database"}})
            except Exception as e:
                print(f"  ❌ Database search failed for {key}: {e}")
                return

            db_count = 0
            page_count = 0

            for db in dbs["results"]:
                db_id = db["id"].replace("-", "")
                db_title = db.get("title", [{}])[0].get("plain_text", "Untitled")
                print(f"  📋 Processing database: {db_title}")

                cursor = None
                while True:
                    qry = {"page_size": 100}
                    if cursor:
                        qry["start_cursor"] = cursor

                    res = await fetch_json(session, f"https://api.notion.com/v1/databases/{db_id}/query", token, qry)

                    for page in res["results"]:
                        # Extract page title and all text properties
                        content_parts = []

                        # Get page title
                        for prop_name, prop_data in page["properties"].items():
                            if prop_data.get("type") == "title" and prop_data.get("title"):
                                title_text = prop_data["title"][0].get("plain_text", "") if prop_data["title"] else ""
                                if title_text:
                                    content_parts.append(f"Title: {title_text}")
                            elif prop_data.get("type") == "rich_text" and prop_data.get("rich_text"):
                                rich_text = " ".join([rt.get("plain_text", "") for rt in prop_data["rich_text"]])
                                if rich_text.strip():
                                    content_parts.append(f"{prop_name}: {rich_text}")
                            elif prop_data.get("type") == "select" and prop_data.get("select"):
                                select_text = prop_data["select"].get("name", "")
                                if select_text:
                                    content_parts.append(f"{prop_name}: {select_text}")
                            elif prop_data.get("type") == "multi_select" and prop_data.get("multi_select"):
                                multi_select_text = ", ".join([ms.get("name", "") for ms in prop_data["multi_select"]])
                                if multi_select_text:
                                    content_parts.append(f"{prop_name}: {multi_select_text}")

                        content = "\n".join(content_parts) if content_parts else f"Page in {db_title}"

                        if content.strip():
                            vec = await embed(content)
                            uid = f"notion_{page['id'].replace('-', '')}"
                            meta = {
                                "workspace": key, 
                                "database": db_id, 
                                "database_title": db_title,
                                "url": page["url"], 
                                "text": content,
                                "source": f"Notion: {db_title}",
                                "last_sync": datetime.utcnow().isoformat()
                            }
                            index.upsert([(uid, vec, meta)], namespace="notion")
                            page_count += 1

                    if res.get("has_more"):
                        cursor = res["next_cursor"]
                    else:
                        break

                db_count += 1

            print(f"  ✅ {key}: {db_count} databases, {page_count} pages synced")

        except Exception as e:
            print(f"  ❌ Error syncing {key}: {e}")

async def full_sync():
    print(f"🚀 Starting full Notion sync at {datetime.utcnow().isoformat()}")

    if not workspaces:
        print("⚠️  No workspaces configured in NOTION_WORKSPACES")
        return

    for key, ws in workspaces.items():
        await sync_workspace(key, ws)

    print("✅ Notion sync finished", datetime.utcnow().isoformat())

# ---------- Scheduler ------------
async def scheduler():
    interval = int(os.getenv("SYNC_INTERVAL_MIN", "240")) * 60
    print(f"📅 Notion sync scheduler started (interval: {interval//60} minutes)")

    while True:
        try:
            await full_sync()
        except Exception as e:
            print("❌ Sync error:", e)

        print(f"⏰ Next sync in {interval//60} minutes...")
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(full_sync())
```

Here's the corrected and complete code:

```python
import os, json, time, asyncio, aiohttp
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec
from openai import AsyncOpenAI

# ---------- Load env ------------
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
try:
    workspaces_str = os.getenv("NOTION_WORKSPACES", "{}")
    workspaces = json.loads(workspaces_str)
    print(f"📝 Loaded workspaces: {list(workspaces.keys())}")
except json.JSONDecodeError:
    print("⚠️  Invalid NOTION_WORKSPACES JSON, falling back to API key")
    workspaces = {}
    if NOTION_API_KEY:
        workspaces = {"default": {"token": NOTION_API_KEY}}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    print("⚠️  Missing required API keys for sync")
    exit(1)

if not workspaces:
    print("⚠️  No Notion workspaces configured")
    exit(1)

# ---------- Init clients ----------
pc = Pinecone(api_key=PINECONE_API_KEY)

# Use the main index instead of creating a separate one
index_name = "companion-memory"
if index_name not in [i["name"] for i in pc.list_indexes()]:
    print(f"⚠️  Main index '{index_name}' not found. Please run ingest.py first.")
    exit(1)

index = pc.Index(index_name)

oai = AsyncOpenAI(api_key=OPENAI_API_KEY)
NOTION_VER = "2022-06-28"

# ---------- Helpers --------------
async def embed(text: str):
    resp = await oai.embeddings.create(
        model="text-embedding-3-small", input=text[:8191])
    return resp.data[0].embedding

async def fetch_json(session, url, token, payload=None):
    hdrs = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VER,
        "Content-Type": "application/json"
    }
    method = "POST" if payload is not None else "GET"
    async with session.request(method, url, headers=hdrs, json=payload) as r:
        r.raise_for_status()
        return await r.json()

async def sync_workspace(key, ws):
    token = ws["token"]
    print(f"🔄 Syncing workspace: {key}")

    async with aiohttp.ClientSession() as session:
        try:
            # 1. discover ALL databases with better error handling
            try:
                async def search_databases(session, headers, workspace_name):
                    """Search for databases in a workspace"""
                    url = "https://api.notion.com/v1/search"
                    data = {
                        "filter": {
                            "value": "database",
                            "property": "object"
                        }
                    }

                    try:
                        async with session.post(url, headers=headers, json=data) as response:
                            if response.status == 200:
                                result = await response.json()
                                return result.get('results', [])
                            elif response.status == 401:
                                print(f"  ❌ Notion API authentication failed for {workspace_name}")
                                print(f"     Check if NOTION_API_KEY is valid and has proper permissions")
                                return []
                            else:
                                error_text = await response.text()
                                print(f"  ❌ Database search failed for {workspace_name}: {response.status} - {error_text}")
                                return []
                    except Exception as e:
                        print(f"  ❌ Exception during database search for {workspace_name}: {str(e)}")
                        return []
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": NOTION_VER,
                    "Content-Type": "application/json",
                }
                dbs = await search_databases(session, headers, key)
            except Exception as e:
                print(f"  ❌ Database search failed for {key}: {e}")
                return

            db_count = 0
            page_count = 0

            for db in dbs:
                db_id = db["id"].replace("-", "")
                db_title = db.get("title", [{}])[0].get("plain_text", "Untitled")
                print(f"  📋 Processing database: {db_title}")

                cursor = None
                while True:
                    qry = {"page_size": 100}
                    if cursor:
                        qry["start_cursor"] = cursor

                    res = await fetch_json(session, f"https://api.notion.com/v1/databases/{db_id}/query", token, qry)

                    for page in res["results"]:
                        # Extract page title and all text properties
                        content_parts = []

                        # Get page title
                        for prop_name, prop_data in page["properties"].items():
                            if prop_data.get("type") == "title" and prop_data.get("title"):
                                title_text = prop_data["title"][0].get("plain_text", "") if prop_data["title"] else ""
                                if title_text:
                                    content_parts.append(f"Title: {title_text}")
                            elif prop_data.get("type") == "rich_text" and prop_data.get("rich_text"):
                                rich_text = " ".join([rt.get("plain_text", "") for rt in prop_data["rich_text"]])
                                if rich_text.strip():
                                    content_parts.append(f"{prop_name}: {rich_text}")
                            elif prop_data.get("type") == "select" and prop_data.get("select"):
                                select_text = prop_data["select"].get("name", "")
                                if select_text:
                                    content_parts.append(f"{prop_name}: {select_text}")
                            elif prop_data.get("type") == "multi_select" and prop_data.get("multi_select"):
                                multi_select_text = ", ".join([ms.get("name", "") for ms in prop_data["multi_select"]])
                                if multi_select_text:
                                    content_parts.append(f"{prop_name}: {multi_select_text}")

                        content = "\n".join(content_parts) if content_parts else f"Page in {db_title}"

                        if content.strip():
                            vec = await embed(content)
                            uid = f"notion_{page['id'].replace('-', '')}"
                            meta = {
                                "workspace": key, 
                                "database": db_id, 
                                "database_title": db_title,
                                "url": page["url"], 
                                "text": content,
                                "source": f"Notion: {db_title}",
                                "last_sync": datetime.utcnow().isoformat()
                            }
                            index.upsert([(uid, vec, meta)], namespace="notion")
                            page_count += 1

                    if res.get("has_more"):
                        cursor = res["next_cursor"]
                    else:
                        break

                db_count += 1

            print(f"  ✅ {key}: {db_count} databases, {page_count} pages synced")

        except Exception as e:
            print(f"  ❌ Error syncing {key}: {e}")

async def full_sync():
    print(f"🚀 Starting full Notion sync at {datetime.utcnow().isoformat()}")

    if not workspaces:
        print("⚠️  No workspaces configured in NOTION_WORKSPACES")
        return

    for key, ws in workspaces.items():
        await sync_workspace(key, ws)

    print("✅ Notion sync finished", datetime.utcnow().isoformat())

# ---------- Scheduler ------------
async def scheduler():
    interval = int(os.getenv("SYNC_INTERVAL_MIN", "240")) * 60
    print(f"📅 Notion sync scheduler started (interval: {interval//60} minutes)")

    while True:
        try:
            await full_sync()
        except Exception as e:
            print("❌ Sync error:", e)

        print(f"⏰ Next sync in {interval//60} minutes...")
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(full_sync())