import os, openai, pinecone
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel

EMBED_MD   = "text-embedding-3-small"
CHAT_MD    = os.getenv("COMPANION_VOICE_MODEL", "gpt-4o-mini")
INDEX_NM   = "companion-memory"
NS         = "v1"

# Validate environment variables
if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not os.environ.get("PINECONE_API_KEY"):
    raise ValueError("PINECONE_API_KEY environment variable is required")

try:
    openai_client = openai.OpenAI()
    pc  = pinecone.Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    
    # Check if index exists
    if INDEX_NM not in pc.list_indexes().names():
        raise ValueError(f"Pinecone index '{INDEX_NM}' does not exist. Run ingest.py first.")
    
    idx = pc.Index(INDEX_NM)
except Exception as e:
    raise ValueError(f"Failed to initialize Pinecone: {str(e)}")

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Companion Memory API", "endpoints": ["/ask"]}

class Answer(BaseModel):
    answer: str
    sources: list[str]

@app.get("/ask", response_model=Answer)
def ask(q: str = Query(..., description="Your question")):
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
