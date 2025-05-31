
import os, openai, pinecone, json, requests
from datetime import datetime, timedelta
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import aiohttp

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Constants
EMBED_MD = "text-embedding-3-small"
CHAT_MD = os.getenv("COMPANION_VOICE_MODEL", "gpt-4o-mini")
INDEX_NM = "companion-memory"
NS = "v1"

# Google APIs setup
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/drive.readonly'
]

print("🔍 Checking environment variables...")
required_vars = ["OPENAI_API_KEY", "PINECONE_API_KEY"]
optional_vars = ["GOOGLE_CLIENT_ID", "NOTION_API_KEY", "DUBSADO_API_KEY", "QUICKBOOKS_CLIENT_ID"]

for var in required_vars + optional_vars:
    status = "✓ Set" if os.environ.get(var) else "✗ Missing"
    print(f"   {var}: {status}")

# Initialize OpenAI and Pinecone
openai_client = None
pc = None
idx = None

if os.environ.get("OPENAI_API_KEY") and os.environ.get("PINECONE_API_KEY"):
    try:
        openai_client = openai.OpenAI()
        pc = pinecone.Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        
        if INDEX_NM not in pc.list_indexes().names():
            print(f"⚠️  Pinecone index '{INDEX_NM}' does not exist. Run ingest.py first.")
            idx = None
        else:
            idx = pc.Index(INDEX_NM)
    except Exception as e:
        print(f"❌ Failed to initialize: {str(e)}")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Background sync task
sync_task = None

@app.on_event("startup")
async def start_background_tasks():
    global sync_task
    # Only start if we have the required configuration
    if os.environ.get("NOTION_WORKSPACES") and os.environ.get("OPENAI_API_KEY") and os.environ.get("PINECONE_API_KEY"):
        try:
            from scripts.notion_sync import scheduler
            sync_task = asyncio.create_task(scheduler())
            print("🔄 Background Notion sync started")
        except ImportError as e:
            print(f"⚠️  Could not start background sync: {e}")
    else:
        print("⚠️  Background sync disabled - missing configuration")

@app.on_event("shutdown")
async def shutdown_background_tasks():
    global sync_task
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass

# Models
class Answer(BaseModel):
    answer: str
    sources: list[str]

class CalendarEvent(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None

class EmailSummary(BaseModel):
    sender: str
    subject: str
    snippet: str
    importance: str
    timestamp: datetime

class IntegrationStatus(BaseModel):
    name: str
    connected: bool
    last_sync: Optional[str] = None
    status_message: str = "Not configured"

# Helper functions for integrations
async def get_google_calendar_events(access_token: str, days_ahead: int = 7) -> List[CalendarEvent]:
    """Get calendar events from Google Calendar"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events"
        params = {
            'timeMin': time_min,
            'timeMax': time_max,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    events = []
                    for item in data.get('items', []):
                        start = item['start'].get('dateTime', item['start'].get('date'))
                        end = item['end'].get('dateTime', item['end'].get('date'))
                        events.append(CalendarEvent(
                            id=item['id'],
                            title=item.get('summary', 'No title'),
                            start_time=datetime.fromisoformat(start.replace('Z', '+00:00')),
                            end_time=datetime.fromisoformat(end.replace('Z', '+00:00')),
                            description=item.get('description', '')
                        ))
                    return events
                else:
                    print(f"Calendar API error: {response.status}")
                    return []
    except Exception as e:
        print(f"Error fetching calendar: {e}")
        return []

async def get_gmail_summary(access_token: str, max_results: int = 10) -> List[EmailSummary]:
    """Get recent important emails from Gmail"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        url = "https://www.googleapis.com/gmail/v1/users/me/messages"
        params = {
            'q': 'is:unread OR is:important',
            'maxResults': max_results
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    emails = []
                    
                    for message in data.get('messages', []):
                        msg_url = f"https://www.googleapis.com/gmail/v1/users/me/messages/{message['id']}"
                        async with session.get(msg_url, headers=headers) as msg_response:
                            if msg_response.status == 200:
                                msg_data = await msg_response.json()
                                payload = msg_data.get('payload', {})
                                headers_list = payload.get('headers', [])
                                
                                sender = next((h['value'] for h in headers_list if h['name'] == 'From'), 'Unknown')
                                subject = next((h['value'] for h in headers_list if h['name'] == 'Subject'), 'No subject')
                                date_str = next((h['value'] for h in headers_list if h['name'] == 'Date'), '')
                                
                                emails.append(EmailSummary(
                                    sender=sender,
                                    subject=subject,
                                    snippet=msg_data.get('snippet', ''),
                                    importance='high' if 'IMPORTANT' in msg_data.get('labelIds', []) else 'normal',
                                    timestamp=datetime.now()  # Simplified for now
                                ))
                    
                    return emails
                else:
                    print(f"Gmail API error: {response.status}")
                    return []
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []

async def get_notion_data(notion_token: str, database_id: str) -> Dict[str, Any]:
    """Get data from Notion database"""
    try:
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json={}) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Notion API error: {response.status}")
                    return {}
    except Exception as e:
        print(f"Error fetching Notion data: {e}")
        return {}

# Routes
@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/api")
def api_root():
    integrations = {
        "google": bool(os.environ.get("GOOGLE_CLIENT_ID")),
        "notion": bool(os.environ.get("NOTION_API_KEY")),
        "dubsado": bool(os.environ.get("DUBSADO_API_KEY")),
        "quickbooks": bool(os.environ.get("QUICKBOOKS_CLIENT_ID"))
    }
    
    return {
        "message": "Michael's AI Companion API",
        "endpoints": ["/ask", "/status", "/calendar", "/emails", "/integrations"],
        "openai_configured": openai_client is not None,
        "pinecone_configured": pc is not None,
        "index_ready": idx is not None,
        "integrations_configured": integrations
    }

@app.get("/status")
def status():
    import pathlib
    raw_dir = pathlib.Path("data/raw")
    pdf_files = list(raw_dir.glob("*.pdf")) if raw_dir.exists() else []
    
    return {
        "openai_api_key": "✓" if os.environ.get("OPENAI_API_KEY") else "✗ Missing",
        "pinecone_api_key": "✓" if os.environ.get("PINECONE_API_KEY") else "✗ Missing",
        "index_exists": "✓" if idx is not None else "✗ Missing or not accessible",
        "pdf_files_found": len(pdf_files),
        "pdf_files": [f.name for f in pdf_files],
        "data_directory_exists": raw_dir.exists(),
        "google_configured": "✓" if os.environ.get("GOOGLE_CLIENT_ID") else "✗ Not configured",
        "notion_configured": "✓" if os.environ.get("NOTION_API_KEY") else "✗ Not configured",
        "ready": idx is not None and openai_client is not None
    }

@app.get("/integrations")
def get_integrations():
    """Get status of all integrations"""
    integrations = [
        {
            "name": "Google Calendar",
            "connected": bool(os.environ.get("GOOGLE_CLIENT_ID")),
            "status_message": "Configured" if os.environ.get("GOOGLE_CLIENT_ID") else "Set GOOGLE_CLIENT_ID in Secrets"
        },
        {
            "name": "Gmail",
            "connected": bool(os.environ.get("GOOGLE_CLIENT_ID")),
            "status_message": "Configured" if os.environ.get("GOOGLE_CLIENT_ID") else "Set GOOGLE_CLIENT_ID in Secrets"
        },
        {
            "name": "Google Drive",
            "connected": bool(os.environ.get("GOOGLE_CLIENT_ID")),
            "status_message": "Configured" if os.environ.get("GOOGLE_CLIENT_ID") else "Set GOOGLE_CLIENT_ID in Secrets"
        },
        {
            "name": "Notion",
            "connected": bool(os.environ.get("NOTION_API_KEY")),
            "status_message": "Configured" if os.environ.get("NOTION_API_KEY") else "Set NOTION_API_KEY in Secrets"
        },
        {
            "name": "Dubsado",
            "connected": bool(os.environ.get("DUBSADO_API_KEY")),
            "status_message": "Configured" if os.environ.get("DUBSADO_API_KEY") else "Set DUBSADO_API_KEY in Secrets"
        },
        {
            "name": "QuickBooks",
            "connected": bool(os.environ.get("QUICKBOOKS_CLIENT_ID")),
            "status_message": "Configured" if os.environ.get("QUICKBOOKS_CLIENT_ID") else "Set QUICKBOOKS_CLIENT_ID in Secrets"
        },
        {
            "name": "Synology NAS",
            "connected": False,
            "status_message": "Manual configuration required"
        },
        {
            "name": "Slack",
            "connected": False,
            "status_message": "Set SLACK_BOT_TOKEN in Secrets"
        },
        {
            "name": "Zoom",
            "connected": False,
            "status_message": "Set ZOOM_API_KEY in Secrets"
        },
        {
            "name": "Zapier",
            "connected": False,
            "status_message": "Configure webhooks manually"
        }
    ]
    return {"integrations": integrations}

@app.get("/calendar/today")
async def get_today_calendar():
    """Get today's calendar events"""
    # This would use stored OAuth token in production
    # For now, return placeholder
    return {
        "message": "Calendar integration configured but needs OAuth token",
        "events": [],
        "setup_required": "Complete OAuth flow to access calendar"
    }

@app.get("/email/priority")
async def get_priority_emails():
    """Get priority emails"""
    # This would use stored OAuth token in production
    return {
        "message": "Email integration configured but needs OAuth token",
        "emails": [],
        "setup_required": "Complete OAuth flow to access Gmail"
    }

@app.get("/notion/projects")
async def get_notion_projects():
    """Get current projects from Notion"""
    notion_token = os.environ.get("NOTION_API_KEY")
    if not notion_token:
        return {"error": "Notion API key not configured"}
    
    # This would use actual database ID from configuration
    return {
        "message": "Notion integration ready",
        "setup_required": "Add NOTION_DATABASE_IDS to Secrets with your database IDs"
    }

@app.get("/ask", response_model=Answer)
def ask(q: str = Query(..., description="Your question")):
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI API not configured. Please set OPENAI_API_KEY in Secrets.")
    
    if not idx:
        raise HTTPException(status_code=503, detail="Pinecone index not available. Please set PINECONE_API_KEY and run ingest.py.")
    
    try:
        if not q.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        print(f"🔍 Processing question: {q}")
        
        # Get embeddings
        qvec = openai_client.embeddings.create(model=EMBED_MD, input=q).data[0].embedding
        print(f"✓ Generated embedding vector")
        
        # Query Pinecone - search both main documents and Notion data
        main_hits = idx.query(vector=qvec, top_k=6, namespace=NS, include_metadata=True).matches
        notion_hits = idx.query(vector=qvec, top_k=6, namespace="notion", include_metadata=True).matches
        
        # Combine and filter by relevance score
        all_hits = main_hits + notion_hits
        hits = [h for h in all_hits if h.score > 0.25][:8]
        print(f"✓ Found {len(hits)} relevant matches ({len(main_hits)} from docs, {len(notion_hits)} from Notion)")
        
        if not hits:
            return {
                "answer": "I don't have enough information to answer that question based on your uploaded documents. However, I can help you with:\n\n1. Calendar management\n2. Email prioritization\n3. Project tracking\n4. General questions about your business\n\nTry asking something like 'What's my schedule like?' or 'Help me plan my week.'",
                "sources": []
            }
        
        # Build context
        ctx_pieces = []
        for h in hits:
            source = h.metadata.get('source', 'Unknown')
            text = h.metadata.get('text', '')
            ctx_pieces.append(f"Source: {source}\nContent: {text}")
        
        ctx = "\n\n---\n\n".join(ctx_pieces)
        print(f"✓ Built context from {len(hits)} sources")
        
        # Enhanced system prompt for Michael
        system_prompt = f"""You are Michael Slusher's personal AI companion and executive assistant. You know Michael intimately and should respond as his trusted advisor and helper.

KEY CONTEXT ABOUT MICHAEL:
- You are speaking directly to Michael Slusher, founder of Rocket Launch Studio
- He has ADHD and benefits from clear, organized communication
- He's a creative professional in video production and content creation
- He values efficiency, creativity, and personal growth
- When he asks first-person questions like "who is my mother" or "what's my schedule", HE is Michael

YOUR ROLE:
- Act as Michael's personal assistant, not a generic AI
- Provide personalized advice based on his personality and preferences
- Help him stay organized and on track with his goals
- Be encouraging and supportive, understanding his neurodivergent needs
- Suggest improvements to his workflow and business

COMMUNICATION STYLE:
- Be direct but warm and supportive
- Break down complex information into digestible chunks
- Offer actionable advice and next steps
- Reference his goals and values when relevant
- Don't just recite information - provide insights and suggestions

Context from Michael's documents:
{ctx}"""
        
        msgs = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": q}
        ]
        
        response = openai_client.chat.completions.create(
            model=CHAT_MD,
            messages=msgs,
            temperature=0.3,
            max_tokens=1000
        )
        
        ans = response.choices[0].message.content.strip()
        print(f"✓ Generated answer: {ans[:100]}...")
        
        # Extract unique sources
        srcs = list({h.metadata["source"].replace("#", " p") for h in hits})
        
        return {"answer": ans, "sources": srcs}
        
    except Exception as e:
        print(f"❌ Error processing question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
