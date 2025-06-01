import os, json, time, asyncio, aiohttp
from datetime import datetime
from pinecone import Pinecone, ServerlessSpec
from openai import AsyncOpenAI

# ---------- Load env ------------
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
try:
    workspaces_str = os.getenv("NOTION_WORKSPACES", "{}")
    if workspaces_str and workspaces_str != "{}":
        workspaces = json.loads(workspaces_str)
        print(f"📝 Loaded workspaces: {list(workspaces.keys())}")
    else:
        workspaces = {}
except json.JSONDecodeError:
    print("⚠️  Invalid NOTION_WORKSPACES JSON, falling back to API key")
    workspaces = {}

# Always add default workspace if we have an API key
if NOTION_API_KEY and "default" not in workspaces:
    workspaces["default"] = {"token": NOTION_API_KEY}
    print("📝 Added default workspace using NOTION_API_KEY")

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

    if not workspaces:
        print("⚠️  No Notion workspaces configured")
        return

    for workspace_name, config in workspaces.items():
        token = config.get("token")
        if not token:
            print(f"⚠️  No token for workspace {workspace_name}")
            continue

        print(f"📝 Syncing workspace: {workspace_name}")

        # Test the connection first
        headers = get_notion_headers(token)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.notion.com/v1/users/me", headers=headers) as response:
                    if response.status == 200:
                        print(f"✅ {workspace_name} authentication successful")
                        # Here you would add the actual sync logic
                        await sync_workspace_pages(session, headers, workspace_name)
                    else:
                        response_text = await response.text()
                        print(f"❌ Failed to authenticate workspace {workspace_name}: {response.status} - {response_text}")
        except Exception as e:
            print(f"❌ Error syncing workspace {workspace_name}: {e}")

async def sync_workspace_pages(session, headers, workspace_name):
    """Sync pages from a workspace"""
    try:
        # Get all pages the bot has access to
        async with session.post("https://api.notion.com/v1/search", 
                               headers=headers, 
                               json={"filter": {"property": "object", "value": "page"}}) as response:
            if response.status == 200:
                data = await response.json()
                pages = data.get("results", [])
                print(f"📄 Found {len(pages)} pages in {workspace_name}")
                
                # Process each page
                for page in pages[:5]:  # Limit to avoid rate limits
                    await process_notion_page(session, headers, page, workspace_name)
            else:
                print(f"⚠️  Failed to search pages in {workspace_name}")
    except Exception as e:
        print(f"❌ Error syncing pages for {workspace_name}: {e}")

async def process_notion_page(session, headers, page, workspace_name):
    """Process a single Notion page"""
    try:
        page_id = page["id"]
        title = ""
        
        # Extract title
        if "properties" in page:
            for prop_name, prop_data in page["properties"].items():
                if prop_data.get("type") == "title" and prop_data.get("title"):
                    title = "".join([t.get("plain_text", "") for t in prop_data["title"]])
                    break
        
        if not title:
            title = f"Untitled Page ({page_id[:8]})"
        
        print(f"  📃 Processing: {title}")
        
        # Get page content
        blocks_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        async with session.get(blocks_url, headers=headers) as response:
            if response.status == 200:
                blocks_data = await response.json()
                content = extract_page_content(blocks_data.get("results", []))
                
                # Create embedding and store in Pinecone
                if content.strip() and len(content) > 50:  # Only process meaningful content
                    await store_notion_content(title, content, workspace_name, page_id)
            else:
                print(f"    ⚠️  Failed to get content for {title}")
                
    except Exception as e:
        print(f"❌ Error processing page: {e}")

def extract_page_content(blocks):
    """Extract text content from Notion blocks"""
    content = []
    
    for block in blocks:
        block_type = block.get("type", "")
        
        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
            rich_text = block.get(block_type, {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            if text.strip():
                content.append(text.strip())
        elif block_type == "bulleted_list_item":
            rich_text = block.get("bulleted_list_item", {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            if text.strip():
                content.append(f"• {text.strip()}")
        elif block_type == "numbered_list_item":
            rich_text = block.get("numbered_list_item", {}).get("rich_text", [])
            text = "".join([t.get("plain_text", "") for t in rich_text])
            if text.strip():
                content.append(f"- {text.strip()}")
    
    return "\n".join(content)

async def store_notion_content(title, content, workspace, page_id):
    """Store Notion content in Pinecone"""
    try:
        # Generate embedding
        embedding_response = await oai.embeddings.create(
            model="text-embedding-3-small",
            input=content
        )
        
        embedding = embedding_response.data[0].embedding
        
        # Store in Pinecone with notion namespace
        metadata = {
            "source": f"Notion - {workspace} - {title}",
            "text": content,
            "workspace": workspace,
            "page_id": page_id,
            "type": "notion_page"
        }
        
        index.upsert(
            vectors=[(f"notion_{workspace}_{page_id}", embedding, metadata)],
            namespace="notion"
        )
        
        print(f"    ✅ Stored embedding for {title}")
        
    except Exception as e:
        print(f"    ❌ Failed to store {title}: {e}")

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