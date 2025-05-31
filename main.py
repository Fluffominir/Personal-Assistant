import os, openai, pinecone
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, environment variables should come from system
    pass

# Load environment variables from .env file if it exists
load_dotenv()

EMBED_MD   = "text-embedding-3-small"
CHAT_MD    = os.getenv("COMPANION_VOICE_MODEL", "gpt-4o-mini")
INDEX_NM   = "companion-memory"
NS         = "v1"

# Check environment variables
print("🔍 Checking environment variables...")
openai_key = os.environ.get("OPENAI_API_KEY")
pinecone_key = os.environ.get("PINECONE_API_KEY")

print(f"   OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Missing'}")
print(f"   PINECONE_API_KEY: {'✓ Set' if pinecone_key else '✗ Missing'}")

missing_vars = []
if not openai_key:
    missing_vars.append("OPENAI_API_KEY")
if not pinecone_key:
    missing_vars.append("PINECONE_API_KEY")

if missing_vars:
    print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
    print("   Please check the Secrets tool in your Replit workspace")
    # Initialize with dummy clients to allow app to start
    openai_client = None
    pc = None
    idx = None
else:
    try:
        openai_client = openai.OpenAI()
        pc = pinecone.Pinecone(api_key=os.environ["PINECONE_API_KEY"])
        
        # Check if index exists
        if INDEX_NM not in pc.list_indexes().names():
            print(f"⚠️  Pinecone index '{INDEX_NM}' does not exist. Run ingest.py first.")
            idx = None
        else:
            idx = pc.Index(INDEX_NM)
    except Exception as e:
        print(f"❌ Failed to initialize: {str(e)}")
        openai_client = None
        pc = None
        idx = None

app = FastAPI()

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    # Serve the main HTML interface
    return FileResponse("static/index.html")

@app.get("/api")
def api_root():
    status = {
        "message": "Companion Memory API",
        "endpoints": ["/ask", "/status"],
        "openai_configured": openai_client is not None,
        "pinecone_configured": pc is not None,
        "index_ready": idx is not None
    }
    return status

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
        "ready": idx is not None and openai_client is not None
    }

class Answer(BaseModel):
    answer: str
    sources: list[str]

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
        qvec = openai_client.embeddings.create(model=EMBED_MD, input=q)\
                                       .data[0].embedding
        print(f"✓ Generated embedding vector")
        
        # Query Pinecone
        hits = idx.query(vector=qvec, top_k=12, namespace=NS,
                         include_metadata=True).matches
        print(f"✓ Found {len(hits)} initial matches")
        
        # Filter by relevance score
        hits = [h for h in hits if h.score > 0.25][:6]
        print(f"✓ Filtered to {len(hits)} relevant matches")
        
        if not hits:
            return {"answer": "I don't have enough information to answer that question. This could mean:\n1. The PDFs haven't been processed yet\n2. Your question is about topics not covered in the documents\n3. Try rephrasing your question with different keywords", "sources": []}
        
        # Build context with better formatting
        ctx_pieces = []
        for h in hits:
            source = h.metadata.get('source', 'Unknown')
            text = h.metadata.get('text', '')
            ctx_pieces.append(f"Source: {source}\nContent: {text}")
        
        ctx = "\n\n---\n\n".join(ctx_pieces)
        print(f"✓ Built context from {len(hits)} sources")
        
        # Generate answer with better system prompt
        msgs = [
            {"role": "system", "content": "You are a helpful AI assistant that answers questions based on the provided document context. Always provide accurate, helpful answers and cite your sources. If the information isn't in the context, say so clearly."},
            {"role": "system", "content": f"Context from documents:\n\n{ctx}"},
            {"role": "user", "content": q}
        ]
        
        response = openai_client.chat.completions.create(
            model=CHAT_MD, 
            messages=msgs, 
            temperature=0.2,
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
