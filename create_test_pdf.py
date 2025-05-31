
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import pathlib

# Ensure data/raw directory exists
data_dir = pathlib.Path("data/raw")
data_dir.mkdir(parents=True, exist_ok=True)

# Create a test PDF
pdf_path = data_dir / "companion_memory_guide.pdf"

c = canvas.Canvas(str(pdf_path), pagesize=letter)
width, height = letter

# Title
c.setFont("Helvetica-Bold", 16)
c.drawString(50, height - 50, "Companion Memory System Guide")

# Content
c.setFont("Helvetica", 12)
y_position = height - 100

content = [
    "Overview:",
    "The Companion Memory system is a RAG (Retrieval Augmented Generation) application",
    "that allows users to upload PDF documents and ask questions about their content.",
    "",
    "Architecture:",
    "- FastAPI backend for web API",
    "- OpenAI for embeddings and chat completion",
    "- Pinecone for vector storage and similarity search",
    "- PyPDF for document text extraction",
    "- Tesseract OCR for image-based text extraction",
    "",
    "Key Components:",
    "1. ingest.py - Processes PDF files and stores embeddings",
    "2. main.py - FastAPI server with query endpoints",
    "3. /ask endpoint - Accepts questions and returns AI-generated answers",
    "4. /status endpoint - Shows system health and configuration",
    "",
    "Usage Flow:",
    "1. Place PDF files in data/raw/ directory",
    "2. Run python ingest.py to process documents",
    "3. Start the FastAPI server",
    "4. Send GET requests to /ask?q=your_question",
    "",
    "The system uses semantic search to find relevant document chunks",
    "and provides AI-generated answers with source citations."
]

for line in content:
    if y_position < 50:  # Start new page if needed
        c.showPage()
        y_position = height - 50
    c.drawString(50, y_position, line)
    y_position -= 20

c.save()
print(f"Created test PDF: {pdf_path}")
