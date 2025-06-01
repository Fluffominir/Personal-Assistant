
import os
import asyncio
import aiohttp
import json
import openai
import pinecone
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import schedule
import time

# Configuration
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_WORKSPACES = os.environ.get("NOTION_WORKSPACES", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")

# Initialize clients
openai_client = None
pc = None
idx = None

if OPENAI_API_KEY and PINECONE_API_KEY:
    try:
        openai_client = openai.OpenAI()
        pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
        
        # Get or create index
        index_name = "companion-memory"
        if index_name not in pc.list_indexes().names():
            print(f"⚠️  Creating Pinecone index '{index_name}'...")
            pc.create_index(
                name=index_name,
                dimension=1536,  # text-embedding-3-small dimension
                metric="cosine"
            )
        
        idx = pc.Index(index_name)
    except Exception as e:
        print(f"❌ Failed to initialize Notion sync: {e}")

class NotionSync:
    def __init__(self):
        self.api_key = NOTION_API_KEY
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    async def get_databases(self) -> List[Dict]:
        """Get all accessible databases"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/search",
                    headers=self.headers,
                    json={"filter": {"property": "object", "value": "database"}}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
                    else:
                        print(f"❌ Failed to get databases: {response.status}")
                        return []
        except Exception as e:
            print(f"❌ Error getting databases: {e}")
            return []
    
    async def get_pages(self) -> List[Dict]:
        """Get all accessible pages"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/search",
                    headers=self.headers,
                    json={"filter": {"property": "object", "value": "page"}}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
                    else:
                        print(f"❌ Failed to get pages: {response.status}")
                        return []
        except Exception as e:
            print(f"❌ Error getting pages: {e}")
            return []
    
    async def get_database_content(self, database_id: str) -> List[Dict]:
        """Get content from a specific database"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/databases/{database_id}/query",
                    headers=self.headers,
                    json={}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("results", [])
                    else:
                        print(f"❌ Failed to get database content: {response.status}")
                        return []
        except Exception as e:
            print(f"❌ Error getting database content: {e}")
            return []
    
    async def get_page_content(self, page_id: str) -> Dict:
        """Get content from a specific page"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get page properties
                async with session.get(
                    f"{self.base_url}/pages/{page_id}",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        return {}
                    
                    page_data = await response.json()
                
                # Get page blocks (content)
                async with session.get(
                    f"{self.base_url}/blocks/{page_id}/children",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        blocks_data = await response.json()
                        page_data["blocks"] = blocks_data.get("results", [])
                    
                    return page_data
        except Exception as e:
            print(f"❌ Error getting page content: {e}")
            return {}
    
    def extract_text_from_page(self, page_data: Dict) -> str:
        """Extract readable text from a Notion page"""
        text_parts = []
        
        # Extract title
        if "properties" in page_data:
            for prop_name, prop_data in page_data["properties"].items():
                if prop_data.get("type") == "title" and prop_data.get("title"):
                    title_text = " ".join([t.get("plain_text", "") for t in prop_data["title"]])
                    text_parts.append(f"Title: {title_text}")
        
        # Extract blocks content
        if "blocks" in page_data:
            for block in page_data["blocks"]:
                block_type = block.get("type", "")
                
                if block_type == "paragraph" and block.get("paragraph", {}).get("rich_text"):
                    text = " ".join([t.get("plain_text", "") for t in block["paragraph"]["rich_text"]])
                    if text.strip():
                        text_parts.append(text)
                
                elif block_type == "heading_1" and block.get("heading_1", {}).get("rich_text"):
                    text = " ".join([t.get("plain_text", "") for t in block["heading_1"]["rich_text"]])
                    if text.strip():
                        text_parts.append(f"# {text}")
                
                elif block_type == "heading_2" and block.get("heading_2", {}).get("rich_text"):
                    text = " ".join([t.get("plain_text", "") for t in block["heading_2"]["rich_text"]])
                    if text.strip():
                        text_parts.append(f"## {text}")
                
                elif block_type == "heading_3" and block.get("heading_3", {}).get("rich_text"):
                    text = " ".join([t.get("plain_text", "") for t in block["heading_3"]["rich_text"]])
                    if text.strip():
                        text_parts.append(f"### {text}")
                
                elif block_type == "bulleted_list_item" and block.get("bulleted_list_item", {}).get("rich_text"):
                    text = " ".join([t.get("plain_text", "") for t in block["bulleted_list_item"]["rich_text"]])
                    if text.strip():
                        text_parts.append(f"• {text}")
                
                elif block_type == "numbered_list_item" and block.get("numbered_list_item", {}).get("rich_text"):
                    text = " ".join([t.get("plain_text", "") for t in block["numbered_list_item"]["rich_text"]])
                    if text.strip():
                        text_parts.append(f"1. {text}")
        
        return "\n".join(text_parts)

async def sync_notion_to_pinecone():
    """Sync Notion content to Pinecone"""
    if not all([NOTION_API_KEY, openai_client, idx]):
        print("⚠️  Notion sync skipped - missing configuration")
        return
    
    print("🔄 Starting Notion sync...")
    
    notion = NotionSync()
    
    try:
        # Get all pages
        pages = await notion.get_pages()
        print(f"📄 Found {len(pages)} pages")
        
        # Get all databases
        databases = await notion.get_databases()
        print(f"🗃️  Found {len(databases)} databases")
        
        vectors_to_upsert = []
        
        # Process pages
        for page in pages[:10]:  # Limit to 10 pages for now
            page_id = page["id"]
            page_content = await notion.get_page_content(page_id)
            
            if page_content:
                text = notion.extract_text_from_page(page_content)
                
                if text and len(text.strip()) > 10:  # Only process pages with substantial content
                    try:
                        # Generate embedding
                        embedding_response = openai_client.embeddings.create(
                            model="text-embedding-3-small",
                            input=text[:8000]  # Limit text length
                        )
                        
                        embedding = embedding_response.data[0].embedding
                        
                        # Prepare metadata
                        metadata = {
                            "source": f"Notion Page: {page.get('url', page_id)}",
                            "text": text[:1000],  # Store first 1000 chars in metadata
                            "type": "notion_page",
                            "page_id": page_id,
                            "synced_at": datetime.now().isoformat()
                        }
                        
                        vectors_to_upsert.append((f"notion_page_{page_id}", embedding, metadata))
                        
                    except Exception as e:
                        print(f"❌ Error processing page {page_id}: {e}")
        
        # Process database entries
        for database in databases[:5]:  # Limit to 5 databases
            db_id = database["id"]
            db_entries = await notion.get_database_content(db_id)
            
            for entry in db_entries[:20]:  # Limit entries per database
                entry_content = await notion.get_page_content(entry["id"])
                
                if entry_content:
                    text = notion.extract_text_from_page(entry_content)
                    
                    if text and len(text.strip()) > 10:
                        try:
                            # Generate embedding
                            embedding_response = openai_client.embeddings.create(
                                model="text-embedding-3-small",
                                input=text[:8000]
                            )
                            
                            embedding = embedding_response.data[0].embedding
                            
                            # Prepare metadata
                            metadata = {
                                "source": f"Notion DB Entry: {database.get('title', [{}])[0].get('plain_text', 'Unknown')}",
                                "text": text[:1000],
                                "type": "notion_database_entry",
                                "page_id": entry["id"],
                                "database_id": db_id,
                                "synced_at": datetime.now().isoformat()
                            }
                            
                            vectors_to_upsert.append((f"notion_db_{entry['id']}", embedding, metadata))
                            
                        except Exception as e:
                            print(f"❌ Error processing database entry {entry['id']}: {e}")
        
        # Upsert vectors to Pinecone
        if vectors_to_upsert:
            print(f"📤 Upserting {len(vectors_to_upsert)} vectors to Pinecone...")
            
            # Batch upsert (Pinecone supports up to 100 vectors per batch)
            batch_size = 50
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                idx.upsert(vectors=batch, namespace="notion")
            
            print(f"✅ Notion sync completed - {len(vectors_to_upsert)} items synced")
        else:
            print("⚠️  No content to sync")
    
    except Exception as e:
        print(f"❌ Notion sync failed: {e}")

async def full_sync():
    """Run a full Notion sync"""
    await sync_notion_to_pinecone()

async def scheduler():
    """Background scheduler for Notion sync"""
    print("🔄 Notion sync scheduler started")
    
    # Run initial sync after 30 seconds
    await asyncio.sleep(30)
    await sync_notion_to_pinecone()
    
    # Then sync every 6 hours
    while True:
        await asyncio.sleep(6 * 60 * 60)  # 6 hours
        await sync_notion_to_pinecone()

if __name__ == "__main__":
    # For testing
    asyncio.run(full_sync())
