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

# Notion API headers
def get_notion_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

async def full_sync():
    """Full sync of all Notion workspaces"""
    print("🔄 Starting full Notion sync...")

    for workspace_name, config in workspaces.items():
        token = config.get("token")
        if not token:
            print(f"⚠️  No token for workspace {workspace_name}")
            continue

        print(f"📝 Syncing workspace: {workspace_name}")

        # Test the connection first
        headers = get_notion_headers(token)
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.notion.com/v1/users/me", headers=headers) as response:
                if response.status != 200:
                    print(f"❌ Failed to authenticate workspace {workspace_name}")
                    continue

        print(f"✅ {workspace_name} authentication successful")

async def scheduler():
    """Background scheduler for regular syncs"""
    while True:
        try:
            await full_sync()
            await asyncio.sleep(3600)  # Wait 1 hour
        except Exception as e:
            print(f"⚠️  Scheduler error: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error

if __name__ == "__main__":
    asyncio.run(full_sync())