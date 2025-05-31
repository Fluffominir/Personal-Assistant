
import os, json, time, asyncio, aiohttp
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec
from openai import AsyncOpenAI

# ---------- Load env ------------
try:
    workspaces = json.loads(os.getenv("NOTION_WORKSPACES", "{}"))
except json.JSONDecodeError:
    workspaces = {}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    print("⚠️  Missing required API keys for sync")
    exit(1)

# ---------- Init clients ----------
pc = Pinecone(api_key=PINECONE_API_KEY)
if "notion-cache" not in [i["name"] for i in pc.list_indexes()]:
    print("Creating notion-cache index...")
    pc.create_index("notion-cache", dimension=1536, metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"))
index = pc.Index("notion-cache")

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
            # 1. discover ALL databases
            dbs = await fetch_json(session, "https://api.notion.com/v1/search", token,
                                   {"filter":{"property":"object","value":"database"}})
            
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
                        # Extract page title/content
                        title_prop = None
                        for prop_name, prop_data in page["properties"].items():
                            if prop_data.get("type") == "title":
                                title_prop = prop_data
                                break
                        
                        if title_prop and title_prop.get("title"):
                            plain = title_prop["title"][0].get("plain_text", "") if title_prop["title"] else ""
                        else:
                            plain = ""
                        
                        content = plain or f"Page in {db_title}" or page["url"]
                        
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
