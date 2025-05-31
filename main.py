import os, openai, pinecone
from fastapi import FastAPI, Query
from pydantic import BaseModel

EMBED_MD   = "text-embedding-3-small"
CHAT_MD    = os.getenv("COMPANION_VOICE_MODEL", "gpt-4o-mini")
INDEX_NM   = "companion-memory"
NS         = "v1"

openai_client = openai.OpenAI()
pc  = pinecone.Pinecone(api_key=os.environ["PINECONE_API_KEY"])
idx = pc.Index(INDEX_NM)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Companion Memory API", "endpoints": ["/ask"]}

class Answer(BaseModel):
    answer: str
    sources: list[str]

@app.get("/ask", response_model=Answer)
def ask(q: str = Query(..., description="Your question")):
    qvec = openai_client.embeddings.create(model=EMBED_MD, input=q)\
                                   .data[0].embedding
    hits = idx.query(vector=qvec, top_k=12, namespace=NS,
                     include_metadata=True).matches
    hits = [h for h in hits if h.score > 0.25][:6]
    ctx  = "\n\n".join(f"[{h.metadata['source']}] {h.metadata['text']}"
                       for h in hits)
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
