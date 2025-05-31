import os, io, re, uuid, pathlib
from pypdf import PdfReader
from PIL import Image
import pytesseract, openai, pinecone

RAW       = pathlib.Path("data/raw")
EMBED_MD  = "text-embedding-3-small"
INDEX_NM  = "companion-memory"
NS        = "v1"
CHUNK_W   = 400
OVERLAP_W = 200

openai_client = openai.OpenAI()
pc = pinecone.Pinecone(api_key=os.environ["PINECONE_API_KEY"],
                       environment=os.environ["PINECONE_ENVIRONMENT"])
if INDEX_NM not in pc.list_indexes().names():
    pc.create_index(INDEX_NM, dimension=1536, metric="cosine")
idx = pc.Index(INDEX_NM)

def page_text(pg):
    txt = pg.extract_text() or ""
    if len(txt.strip()) < 40 and pg.images:
        txt = pytesseract.image_to_string(Image.open(io.BytesIO(pg.images[0].data)))
    return txt.replace("\r", "\n")

def chunks(txt):
    words = txt.split()
    for i in range(0, len(words), CHUNK_W - OVERLAP_W):
        slice = words[i:i + CHUNK_W]
        if len(slice) > 50:
            yield " ".join(slice)

for pdf in RAW.glob("*.pdf"):
    for pnum, page in enumerate(PdfReader(str(pdf)).pages, 1):
        for ch in chunks(page_text(page)):
            cid = f"{pdf.stem}_p{pnum}_{uuid.uuid4().hex[:6]}"
            vec = openai_client.embeddings.create(model=EMBED_MD, input=ch)\
                                          .data[0].embedding
            idx.upsert([{
                "id": cid,
                "values": vec,
                "metadata": {"text": ch[:250], "source": f"{pdf.name}#p{pnum}"}
            }], namespace=NS)
print("✓ Ingest complete")
