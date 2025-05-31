import os, openai, pinecone
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel

EMBED_MD   = "text-embedding-3-small"
CHAT_MD    = os.getenv("COMPANION_VOICE_MODEL", "gpt-4o-mini")
INDEX_NM   = "companion-memory"
NS         = "v1"

# Check environment variables
missing_vars = []
if not os.environ.get("OPENAI_API_KEY"):
    missing_vars.append("OPENAI_API_KEY")
if not os.environ.get("PINECONE_API_KEY"):
    missing_vars.append("PINECONE_API_KEY")

if missing_vars:
    print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
    print("   Please set these in the Secrets tool")
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

@app.get("/")
def root():
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
    return {
        "openai_api_key": "✓" if os.environ.get("OPENAI_API_KEY") else "✗ Missing",
        "pinecone_api_key": "✓" if os.environ.get("PINECONE_API_KEY") else "✗ Missing",
        "index_exists": "✓" if idx is not None else "✗ Missing or not accessible",
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
        
        # Get embeddings
        qvec = openai_client.embeddings.create(model=EMBED_MD, input=q)\
                                       .data[0].embedding
        
        # Query Pinecone
        hits = idx.query(vector=qvec, top_k=12, namespace=NS,
                         include_metadata=True).matches
        hits = [h for h in hits if h.score > 0.25][:6]
        
        if not hits:
            return {"answer": "I don't have enough information to answer that question. Please check if data has been ingested.", "sources": []}
        
        # Build context
        ctx  = "\n\n".join(f"[{h.metadata['source']}] {h.metadata['text']}"
                           for h in hits)
        
        # Generate answer
        msgs = [
            {"role":"system","content":"Answer accurately and cite source."},
            {"role":"system","content":ctx},
            {"role":"user","content":q}
        ]
        ans = openai_client.chat.completions.create(
                model=CHAT_MD, messages=msgs, temperature=0.2
              ).choices[0].message.content.strip()
        
        srcs = list({h.metadata["source"].replace("#"," p") for h in hits})
        return {"answer": ans, "sources": srcs}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
