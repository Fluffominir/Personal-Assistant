import os, openai, pinecone, json, requests
from datetime import datetime, timedelta
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import aiohttp
import urllib.parse

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

# Simple in-memory token storage (in production, use a database)
google_tokens = {}

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
# Auto-detect the redirect URI based on the environment
def get_redirect_uri():
    # Check if explicitly set
    if os.environ.get("GOOGLE_REDIRECT_URI"):
        return os.environ.get("GOOGLE_REDIRECT_URI")

    # Try to auto-detect from Replit environment
    repl_slug = os.environ.get("REPL_SLUG")
    repl_owner = os.environ.get("REPL_OWNER")

    if repl_slug and repl_owner:
        return f"https://{repl_slug}.{repl_owner}.repl.co/auth/google/callback"

    # Auto-detect from current domain
    repl_id = os.environ.get("REPL_ID")
    if repl_id:
        return f"https://{repl_id}.id.repl.co/auth/google/callback"

    # Fallback
    return "http://0.0.0.0:8000/auth/google/callback"

REDIRECT_URI = get_redirect_uri()

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

app = FastAPI(title="ATLAS - AI Companion", description="Michael's Personal AI Assistant")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Background sync task
sync_task = None

@app.on_event("startup")
async def start_background_tasks():
    global sync_task
    print("🚀 Starting ATLAS - Michael's AI Companion")
    
    # Check if we have Notion configuration (either NOTION_WORKSPACES or NOTION_API_KEY)
    has_notion = os.environ.get("NOTION_WORKSPACES") or os.environ.get("NOTION_API_KEY")
    has_required_keys = os.environ.get("OPENAI_API_KEY") and os.environ.get("PINECONE_API_KEY")

    print(f"🔍 Startup check - Notion: {bool(has_notion)}, Required keys: {bool(has_required_keys)}")
    
    # Test Notion API if configured
    if os.environ.get("NOTION_API_KEY"):
        print("🔍 Testing Notion API connection...")
        try:
            import aiohttp
            headers = {
                "Authorization": f"Bearer {os.environ.get('NOTION_API_KEY')}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.notion.com/v1/users/me", headers=headers) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        print(f"✅ Notion API connection successful - User: {user_data.get('name', 'Unknown')}")
                    else:
                        response_text = await response.text()
                        print(f"❌ Notion API test failed: {response.status} - {response_text}")
        except Exception as e:
            print(f"❌ Notion API test error: {e}")
    
    # Start background sync with improved error handling
    if has_notion and has_required_keys:
        try:
            from scripts.notion_sync import scheduler
            sync_task = asyncio.create_task(scheduler())
            print("🔄 Background Notion sync started")
            
            # Run an initial sync after a short delay
            asyncio.create_task(initial_sync())
            
        except ImportError as e:
            print(f"⚠️  Could not start background sync: {e}")
        except Exception as e:
            print(f"⚠️  Background sync startup error: {e}")
    else:
        missing = []
        if not has_notion:
            missing.append("NOTION_API_KEY or NOTION_WORKSPACES")
        if not os.environ.get("OPENAI_API_KEY"):
            missing.append("OPENAI_API_KEY")
        if not os.environ.get("PINECONE_API_KEY"):
            missing.append("PINECONE_API_KEY")
        print(f"⚠️  Background sync disabled - missing: {', '.join(missing)}")

async def initial_sync():
    """Run initial sync after startup"""
    await asyncio.sleep(5)  # Wait 5 seconds for server to fully start
    try:
        from scripts.notion_sync import full_sync
        print("🔄 Running initial Notion sync...")
        await full_sync()
        print("✅ Initial sync completed")
    except Exception as e:
        print(f"⚠️  Initial sync failed: {e}")

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
                elif response.status == 401:
                    print(f"❌ Notion API 401 Unauthorized - Check your NOTION_API_KEY token")
                    return {}
                else:
                    response_text = await response.text()
                    print(f"❌ Notion API error: {response.status} - {response_text}")
                    return {}
    except Exception as e:
        print(f"❌ Error fetching Notion data: {e}")
        return {}

# Routes
@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/auth/google")
def google_auth():
    """Initiate Google OAuth flow"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        missing = []
        if not GOOGLE_CLIENT_ID:
            missing.append("GOOGLE_CLIENT_ID")
        if not GOOGLE_CLIENT_SECRET:
            missing.append("GOOGLE_CLIENT_SECRET")

        raise HTTPException(
            status_code=503, 
            detail=f"Google OAuth not configured. Missing: {', '.join(missing)}. Please set these in Secrets."
        )

    print(f"🔄 Initiating Google OAuth flow...")
    print(f"   Client ID: {GOOGLE_CLIENT_ID[:20]}...")
    print(f"   Redirect URI: {REDIRECT_URI}")
    print(f"   Scopes: {GOOGLE_SCOPES}")

    auth_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(GOOGLE_SCOPES),
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true"
    }

    url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    print(f"🔗 Generated OAuth URL: {url[:100]}...")

    return RedirectResponse(url=url)

@app.get("/auth/google/callback")
async def google_callback(code: str = None, error: str = None):
    """Handle Google OAuth callback"""
    if error:
        print(f"❌ OAuth error: {error}")
        return RedirectResponse(url="/?error=" + urllib.parse.quote(error))

    if not code:
        print("❌ No authorization code provided")
        return RedirectResponse(url="/?error=no_code")

    try:
        print(f"🔄 Processing OAuth callback with code: {code[:10]}...")

        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI
        }

        print(f"🔄 Exchanging code for tokens...")
        print(f"   Redirect URI: {REDIRECT_URI}")

        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data) as response:
                response_text = await response.text()

                if response.status == 200:
                    tokens = await response.json()
                    print(f"✅ Successfully received tokens")

                    # Store tokens (in production, associate with user ID)
                    google_tokens["access_token"] = tokens.get("access_token")
                    google_tokens["refresh_token"] = tokens.get("refresh_token")
                    google_tokens["expires_at"] = datetime.now() + timedelta(seconds=tokens.get("expires_in", 3600))

                    print(f"✅ Tokens stored successfully")
                    print(f"   Access token: {tokens.get('access_token', 'None')[:20]}...")
                    print(f"   Refresh token: {'Yes' if tokens.get('refresh_token') else 'No'}")

                    return RedirectResponse(url="/?auth=success")
                else:
                    print(f"❌ Token exchange failed: {response.status}")
                    print(f"   Response: {response_text}")
                    return RedirectResponse(url=f"/?error=token_exchange_failed_{response.status}")

    except Exception as e:
        print(f"❌ OAuth callback error: {str(e)}")
        return RedirectResponse(url="/?error=" + urllib.parse.quote(str(e)))

async def get_valid_google_token():
    """Get a valid Google access token, refreshing if necessary"""
    if not google_tokens.get("access_token"):
        return None

    # Check if token is expired
    if google_tokens.get("expires_at") and datetime.now() >= google_tokens["expires_at"]:
        # Try to refresh token
        if google_tokens.get("refresh_token"):
            try:
                refresh_url = "https://oauth2.googleapis.com/token"
                data = {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "refresh_token": google_tokens["refresh_token"],
                    "grant_type": "refresh_token"
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(refresh_url, data=data) as response:
                        if response.status == 200:
                            tokens = await response.json()
                            google_tokens["access_token"] = tokens.get("access_token")
                            google_tokens["expires_at"] = datetime.now() + timedelta(seconds=tokens.get("expires_in", 3600))
                            return google_tokens["access_token"]
            except Exception as e:
                print(f"Token refresh failed: {e}")
                return None
        else:
            return None

    return google_tokens.get("access_token")

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

    # Check Pinecone index stats
    index_stats = None
    if idx:
        try:
            index_stats = idx.describe_index_stats()
        except Exception as e:
            index_stats = f"Error: {str(e)}"

    return {
        "timestamp": datetime.now().isoformat(),
        "openai_api_key": "✓" if os.environ.get("OPENAI_API_KEY") else "✗ Missing",
        "pinecone_api_key": "✓" if os.environ.get("PINECONE_API_KEY") else "✗ Missing",
        "index_exists": "✓" if idx is not None else "✗ Missing or not accessible",
        "index_stats": index_stats,
        "pdf_files_found": len(pdf_files),
        "pdf_files": [f.name for f in pdf_files],
        "data_directory_exists": raw_dir.exists(),
        "google_configured": "✓" if os.environ.get("GOOGLE_CLIENT_ID") else "✗ Not configured",
        "google_authenticated": "✓" if google_tokens.get("access_token") else "✗ Not authenticated",
        "notion_configured": "✓" if os.environ.get("NOTION_API_KEY") else "✗ Not configured",
        "notion_workspaces": os.environ.get("NOTION_WORKSPACES", "Not set"),
        "system_ready": idx is not None and openai_client is not None,
        "background_sync_running": sync_task is not None and not sync_task.done() if sync_task else False
    }

@app.get("/integrations")
def get_integrations():
    """Get status of all integrations"""
    google_configured = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
    google_authenticated = bool(google_tokens.get("access_token"))

    google_status = "Authenticated" if google_authenticated else ("Ready to authenticate" if google_configured else "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in Secrets")

    integrations = [
        {
            "name": "Google Calendar",
            "connected": google_authenticated,
            "configured": google_configured,
            "status_message": google_status,
            "auth_url": "/auth/google" if google_configured and not google_authenticated else None
        },
        {
            "name": "Gmail",
            "connected": google_authenticated,
            "configured": google_configured,
            "status_message": google_status,
            "auth_url": "/auth/google" if google_configured and not google_authenticated else None
        },
        {
            "name": "Google Drive",
            "connected": google_authenticated,
            "configured": google_configured,
            "status_message": google_status,
            "auth_url": "/auth/google" if google_configured and not google_authenticated else None
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
    access_token = await get_valid_google_token()
    if not access_token:
        return {
            "error": "Not authenticated with Google",
            "auth_url": "/auth/google",
            "events": []
        }

    try:
        events = await get_google_calendar_events(access_token, days_ahead=1)
        return {
            "events": [
                {
                    "title": event.title,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "description": event.description
                }
                for event in events
            ],
            "count": len(events)
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch calendar: {str(e)}",
            "events": []
        }

@app.get("/calendar/week")
async def get_week_calendar():
    """Get this week's calendar events"""
    access_token = await get_valid_google_token()
    if not access_token:
        return {
            "error": "Not authenticated with Google",
            "auth_url": "/auth/google",
            "events": []
        }

    try:
        events = await get_google_calendar_events(access_token, days_ahead=7)
        return {
            "events": [
                {
                    "title": event.title,
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "description": event.description
                }
                for event in events
            ],
            "count": len(events)
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch calendar: {str(e)}",
            "events": []
        }

@app.get("/email/priority")
async def get_priority_emails():
    """Get priority emails"""
    access_token = await get_valid_google_token()
    if not access_token:
        return {
            "error": "Not authenticated with Google",
            "auth_url": "/auth/google",
            "emails": []
        }

    try:
        emails = await get_gmail_summary(access_token, max_results=10)
        return {
            "emails": [
                {
                    "sender": email.sender,
                    "subject": email.subject,
                    "snippet": email.snippet,
                    "importance": email.importance,
                    "timestamp": email.timestamp.isoformat()
                }
                for email in emails
            ],
            "count": len(emails)
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch emails: {str(e)}",
            "emails": []
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

@app.post("/notion/sync")
async def manual_notion_sync():
    """Manually trigger a Notion sync"""
    try:
        from scripts.notion_sync import full_sync
        await full_sync()
        return {"message": "Notion sync completed successfully"}
    except Exception as e:
        return {"error": f"Sync failed: {str(e)}"}

@app.get("/notion/status")
async def notion_sync_status():
    """Get Notion sync status and data"""
    if not idx:
        return {"error": "Pinecone not configured"}

    try:
        # Check how many Notion items we have
        stats = idx.describe_index_stats()
        notion_count = stats.namespaces.get("notion", {}).get("vector_count", 0)

        return {
            "notion_vectors_stored": notion_count,
            "notion_api_key_configured": bool(os.environ.get("NOTION_API_KEY")),
            "notion_workspaces_configured": bool(os.environ.get("NOTION_WORKSPACES")),
            "last_sync": "Check logs for sync activity"
        }
    except Exception as e:
        return {"error": f"Failed to get status: {str(e)}"}

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

        # Query Pinecone - search both main documents and Notion data with more results
        main_hits = idx.query(vector=qvec, top_k=10, namespace=NS, include_metadata=True).matches
        notion_hits = idx.query(vector=qvec, top_k=10, namespace="notion", include_metadata=True).matches

        # Combine and filter by relevance score with more permissive threshold
        all_hits = main_hits + notion_hits
        # Much lower threshold to actually find relevant content
        hits = [h for h in all_hits if h.score > 0.25][:8]
        print(f"✓ Found {len(hits)} relevant matches ({len(main_hits)} from docs, {len(notion_hits)} from Notion)")
        print(f"✓ Relevance scores: {[f'{h.score:.3f}' for h in hits]}")

        # Debug: Show all scores even if below threshold
        all_scores = [f'{h.score:.3f}' for h in all_hits[:5]]
        print(f"✓ Top 5 raw scores: {all_scores}")

        # Handle questions without specific context - be more conversational
        if not hits:
            print("⚠️  No relevant context found, providing general response")
            # For general questions, still answer but note the lack of personal context
            msgs = [
                {"role": "system", "content": """You are Michael Slusher's personal AI companion and executive assistant. Michael is the founder of Rocket Launch Studio, a creative professional with ADHD who values efficiency and clear communication.

You can answer general questions, provide explanations, give advice, help with coding, etc. However, you don't have specific personal information about Michael available for this question.

Be conversational, helpful, and supportive. If this seems like a question that would benefit from Michael's personal information, let him know that you could provide more personalized help if he adds relevant documents to his knowledge base."""},
                {"role": "user", "content": q}
            ]

            try:
                response = openai_client.chat.completions.create(
                    model=CHAT_MD,
                    messages=msgs,
                    temperature=0.7,
                    max_tokens=1000
                )

                ans = response.choices[0].message.content.strip()

                # Add a note about personal context if the question seems personal
                personal_keywords = ['my', 'i am', 'i have', 'my family', 'my business', 'my schedule', 'my email', 'my calendar']
                if any(keyword in q.lower() for keyword in personal_keywords):
                    ans += "\n\n💡 *For more personalized assistance with your specific information, you can add relevant documents to data/raw/ and run ingest.py, or update your Notion pages.*"

                return {"answer": ans, "sources": []}
            except Exception as openai_error:
                print(f"❌ OpenAI API error: {str(openai_error)}")
                raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(openai_error)}")

        # Build context
        ctx_pieces = []
        for h in hits:
            source = h.metadata.get('source', 'Unknown')
            text = h.metadata.get('text', '')
            ctx_pieces.append(f"Source: {source}\nContent: {text}")

        ctx = "\n\n---\n\n".join(ctx_pieces)
        print(f"✓ Built context from {len(hits)} sources")

        # System prompt based on Michael's training data
        system_prompt = f"""You are Michael's personal creative and productivity assistant. Speak with direct kindness, give step-by-step structure, and never use emojis.

KEY CONTEXT ABOUT MICHAEL:
- You are speaking directly to Michael Slusher, founder of Rocket Launch Studio
- He has ADHD and autism (RAADS-R score 107) and benefits from clear, structured communication
- He's a creative professional specializing in video production and content creation
- Brand colors: Spruce Blue and Olive Green
- Ultimate comfort movie: Stranger Than Fiction
- Primary love language: Quality Time
- Mother's birthday: May 12
- He's a lifelong twin and red panda enthusiast from Atlanta

YOUR COMMUNICATION STYLE:
- Speak with direct kindness and clarity
- Provide step-by-step structure for complex tasks
- Never use emojis in responses
- Be concise but thorough
- Offer actionable micro-plans when he's in task paralysis
- Support his neurodivergent needs with structured guidance

ROCKET LAUNCH STUDIO CONTEXT:
- Mission: Deliver striking, polished photo and video content that helps clients stand out
- Core values: Creativity, Professionalism, Collaboration, Growth, Support
- Services: Creative Development, Filming & Production, Editing & Post-Production
- Tools: DaVinci Resolve, Adobe Suite, Sony FX6/FX3 cameras
- Current projects: Focus on quality over quantity

TECHNICAL PREFERENCES:
- Camera setup: Sony FX6 A-cam, FX3 B-cam
- Color workflow: ACES 1.3 pipeline, S-Log3 to Rec.709
- File naming: ProjectName_Client_MMDDYYYY_Format_Final.mp4
- Review tool: Frame.io for client feedback

When Michael is experiencing overwhelm or task paralysis, break things into micro-steps with clear next actions.

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



@app.get("/debug/search")
def debug_search(q: str = Query(..., description="Search term to debug")):
    """Debug endpoint to see what's actually in the knowledge base"""
    if not openai_client or not idx:
        raise HTTPException(status_code=503, detail="System not configured")

    try:
        # Get embeddings
        qvec = openai_client.embeddings.create(model=EMBED_MD, input=q).data[0].embedding

        # Query both namespaces
        main_hits = idx.query(vector=qvec, top_k=10, namespace=NS, include_metadata=True).matches
        notion_hits = idx.query(vector=qvec, top_k=10, namespace="notion", include_metadata=True).matches

        return {
            "query": q,
            "main_namespace_results": [
                {
                    "score": h.score,
                    "source": h.metadata.get("source", "Unknown"),
                    "text_preview": h.metadata.get("text", "")[:200] + "..."
                }
                for h in main_hits
            ],
            "notion_namespace_results": [
                {
                    "score": h.score,
                    "source": h.metadata.get("source", "Unknown"),
                    "text_preview": h.metadata.get("text", "")[:200] + "..."
                }
                for h in notion_hits
            ],
            "high_relevance_count": len([h for h in main_hits + notion_hits if h.score > 0.75])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug search failed: {str(e)}")

@app.get("/weather")
async def get_weather():
    """Get current weather information"""
    try:
        # In a real implementation, you'd use a weather API
        # For now, return mock data
        return {
            "temperature": 22,
            "condition": "Partly Cloudy",
            "location": "Current Location",
            "humidity": 65,
            "wind_speed": 8
        }
    except Exception as e:
        return {
            "error": f"Weather service unavailable: {str(e)}",
            "temperature": "--",
            "condition": "Unknown",
            "location": "Unknown"
        }

@app.get("/dashboard")
async def get_dashboard():
    """Get comprehensive dashboard data"""
    try:
        # Get calendar events
        calendar_events = []
        emails = []
        
        access_token = await get_valid_google_token()
        if access_token:
            calendar_events = await get_google_calendar_events(access_token, days_ahead=1)
            emails = await get_gmail_summary(access_token, max_results=5)

        # System health calculation
        health_factors = []
        health_factors.append(100 if openai_client else 0)
        health_factors.append(100 if idx else 0)
        health_factors.append(100 if google_tokens.get("access_token") else 50)
        health_factors.append(100 if os.environ.get("NOTION_API_KEY") else 50)

        system_health = sum(health_factors) / len(health_factors)

        # Knowledge base stats
        kb_stats = {"total_vectors": 0, "namespaces": []}
        if idx:
            try:
                stats = idx.describe_index_stats()
                kb_stats["total_vectors"] = stats.total_vector_count
                kb_stats["namespaces"] = list(stats.namespaces.keys())
            except:
                pass

        return {
            "system_health": round(system_health),
            "active_integrations": len([
                1 for token in [
                    google_tokens.get("access_token"),
                    os.environ.get("NOTION_API_KEY"),
                    os.environ.get("DUBSADO_API_KEY")
                ] if token
            ]),
            "last_sync": datetime.now().isoformat(),
            "calendar_events_today": len(calendar_events),
            "unread_emails": len(emails),
            "knowledge_base_vectors": kb_stats["total_vectors"],
            "namespaces": kb_stats["namespaces"],
            "background_sync_active": sync_task is not None and not sync_task.done() if sync_task else False,
            "recent_events": [
                {
                    "title": event.title,
                    "start_time": event.start_time.strftime("%H:%M"),
                    "end_time": event.end_time.strftime("%H:%M")
                }
                for event in calendar_events[:3]
            ],
            "priority_emails": [
                {
                    "sender": email.sender.split('<')[0].strip(),
                    "subject": email.subject[:50] + "..." if len(email.subject) > 50 else email.subject
                }
                for email in emails[:3]
            ]
        }
    except Exception as e:
        return {
            "system_health": 0,
            "active_integrations": 0,
            "last_sync": None,
            "error": str(e)
        }

@app.get("/metrics/dashboard")
def get_dashboard_metrics():
    """Get comprehensive dashboard metrics (legacy endpoint)"""
    try:
        # System health calculation
        health_factors = []
        health_factors.append(100 if openai_client else 0)
        health_factors.append(100 if idx else 0)
        health_factors.append(100 if google_tokens.get("access_token") else 50)
        health_factors.append(100 if os.environ.get("NOTION_API_KEY") else 50)

        system_health = sum(health_factors) / len(health_factors)

        return {
            "system_health": round(system_health),
            "active_integrations": len([
                1 for token in [
                    google_tokens.get("access_token"),
                    os.environ.get("NOTION_API_KEY"),
                    os.environ.get("DUBSADO_API_KEY")
                ] if token
            ]),
            "last_sync": datetime.now().isoformat(),
            "uptime": "Running",
            "total_queries_today": 42,
            "knowledge_base_size": "Ready"
        }
    except Exception as e:
        return {
            "system_health": 0,
            "active_integrations": 0,
            "last_sync": None,
            "error": str(e)
        }

@app.get("/metrics/work")
async def get_work_metrics():
    """Get business/work-related metrics"""
    try:
        # Get real data from integrations
        calendar_events = []
        emails = []
        
        access_token = await get_valid_google_token()
        if access_token:
            calendar_events = await get_google_calendar_events(access_token, days_ahead=1)
            emails = await get_gmail_summary(access_token, max_results=20)

        # Analyze calendar for work metrics
        work_events = [e for e in calendar_events if any(keyword in e.title.lower() 
                      for keyword in ['meeting', 'call', 'project', 'client', 'work'])]
        
        client_emails = [e for e in emails if any(keyword in e.sender.lower() 
                        for keyword in ['client', '@company', 'business'])]

        return {
            "active_projects": 3,  # This would come from Notion/project management
            "projects_on_track": 2,
            "projects_at_risk": 1,
            "monthly_revenue": 12450,  # This would come from QuickBooks/accounting
            "revenue_growth": 18,
            "active_clients": 8,
            "new_clients_this_week": 2,
            "tasks_today": len(work_events),
            "tasks_completed": 0,
            "tasks_remaining": len(work_events),
            "calendar_events_today": len(calendar_events),
            "work_events_today": len(work_events),
            "unread_emails": len(emails),
            "client_emails": len(client_emails),
            "next_meeting": work_events[0].title if work_events else None,
            "next_meeting_time": work_events[0].start_time.strftime("%H:%M") if work_events else None
        }
    except Exception as e:
        return {
            "error": f"Work metrics unavailable: {str(e)}",
            "active_projects": 0,
            "monthly_revenue": 0
        }

@app.post("/tasks")
async def create_task(task_data: dict):
    """Create a new task"""
    try:
        # In a real implementation, this would integrate with task management systems
        task = {
            "id": f"task_{int(datetime.now().timestamp())}",
            "title": task_data.get("title", "Untitled Task"),
            "description": task_data.get("description", ""),
            "priority": task_data.get("priority", "medium"),
            "due_date": task_data.get("due_date"),
            "created_at": datetime.now().isoformat(),
            "completed": False
        }
        
        # For now, return the task (in production, store in database)
        return {"message": "Task created successfully", "task": task}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@app.get("/tasks/today")
async def get_todays_tasks():
    """Get today's tasks and schedule"""
    try:
        access_token = await get_valid_google_token()
        tasks = []
        
        if access_token:
            calendar_events = await get_google_calendar_events(access_token, days_ahead=1)
            
            # Convert calendar events to task format
            for event in calendar_events:
                tasks.append({
                    "id": event.id,
                    "title": event.title,
                    "type": "calendar_event",
                    "start_time": event.start_time.isoformat(),
                    "end_time": event.end_time.isoformat(),
                    "description": event.description
                })
        
        return {
            "tasks": tasks,
            "total_count": len(tasks),
            "completed_count": 0,
            "remaining_count": len(tasks)
        }
    except Exception as e:
        return {
            "error": f"Failed to get tasks: {str(e)}",
            "tasks": []
        }

@app.post("/ai/context")
async def add_context(context_data: dict):
    """Add contextual information to the AI's knowledge"""
    try:
        if not openai_client or not idx:
            raise HTTPException(status_code=503, detail="AI services not configured")
        
        content = context_data.get("content", "")
        source = context_data.get("source", "User Input")
        context_type = context_data.get("type", "general")
        
        if not content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        # Generate embedding
        embedding_response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=content
        )
        
        embedding = embedding_response.data[0].embedding
        
        # Store in Pinecone
        metadata = {
            "source": source,
            "text": content,
            "type": context_type,
            "added_at": datetime.now().isoformat()
        }
        
        vector_id = f"context_{int(datetime.now().timestamp())}"
        idx.upsert(
            vectors=[(vector_id, embedding, metadata)],
            namespace="user_context"
        )
        
        return {"message": "Context added successfully", "vector_id": vector_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add context: {str(e)}")

@app.get("/ai/personality")
def get_ai_personality():
    """Get AI personality and preferences"""
    return {
        "name": "ATLAS",
        "role": "Personal AI Companion and Executive Assistant",
        "personality_traits": [
            "Direct and kind communication",
            "Structured and organized",
            "Neurodivergent-friendly",
            "Professional yet supportive",
            "Solution-oriented"
        ],
        "communication_style": {
            "tone": "Direct kindness",
            "structure": "Step-by-step when needed",
            "emojis": False,
            "length": "Concise but thorough"
        },
        "specializations": [
            "Creative project management",
            "Video production workflows",
            "ADHD-friendly task organization",
            "Business intelligence",
            "Calendar and email management"
        ],
        "owner_context": {
            "name": "Michael Slusher",
            "company": "Rocket Launch Studio",
            "focus": "Video production and creative services",
            "neurodivergent_support": True
        }
    }