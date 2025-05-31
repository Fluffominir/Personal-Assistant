import os, io, re, uuid, pathlib
from pypdf import PdfReader
from PIL import Image
import pytesseract, openai, pinecone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

RAW       = pathlib.Path("data/raw")
EMBED_MD  = "text-embedding-3-small"
INDEX_NM  = "companion-memory"
NS        = "v1"
CHUNK_W   = 400
OVERLAP_W = 200

# Validate environment variables
if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not os.environ.get("PINECONE_API_KEY"):
    raise ValueError("PINECONE_API_KEY environment variable is required")

# Ensure data directory exists
RAW.mkdir(parents=True, exist_ok=True)

print(f"Looking for PDFs in: {RAW.absolute()}")
pdf_files = list(RAW.glob("*.pdf"))
if not pdf_files:
    print("⚠️  No PDF files found in data/raw/ directory")
    print("   Please add PDF files to data/raw/ before running ingest")
    exit(1)

print(f"Found {len(pdf_files)} PDF files to process")

try:
    openai_client = openai.OpenAI()
    pc = pinecone.Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    
    if INDEX_NM not in pc.list_indexes().names():
        print(f"Creating Pinecone index: {INDEX_NM}")
        pc.create_index(INDEX_NM, dimension=1536, metric="cosine")
    
    idx = pc.Index(INDEX_NM)
except Exception as e:
    print(f"❌ Failed to initialize: {str(e)}")
    exit(1)

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

total_chunks = 0
for pdf in pdf_files:
    try:
        print(f"Processing: {pdf.name}")
        reader = PdfReader(str(pdf))
        
        for pnum, page in enumerate(reader.pages, 1):
            try:
                page_chunks = list(chunks(page_text(page)))
                if not page_chunks:
                    print(f"  Page {pnum}: No text chunks extracted")
                    continue
                
                for ch in page_chunks:
                    cid = f"{pdf.stem}_p{pnum}_{uuid.uuid4().hex[:6]}"
                    vec = openai_client.embeddings.create(model=EMBED_MD, input=ch)\
                                                  .data[0].embedding
                    idx.upsert([{
                        "id": cid,
                        "values": vec,
                        "metadata": {"text": ch[:250], "source": f"{pdf.name}#p{pnum}"}
                    }], namespace=NS)
                    total_chunks += 1
                
                print(f"  Page {pnum}: {len(page_chunks)} chunks")
                
            except Exception as e:
                print(f"  ❌ Error processing page {pnum}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"❌ Error processing {pdf.name}: {str(e)}")
        continue

print(f"✓ Ingest complete - {total_chunks} total chunks processed")
