# RAG Setup Guide

## Quick Start

### 1. Configure Environment

Edit `.env`:
```env
GOOGLE_API_KEY=your_gemini_api_key

# Google Drive shared links
GOOGLE_DRIVE_LINK_DR_WILLI_BEDNA=https://drive.google.com/file/d/.../view
GOOGLE_DRIVE_LINK_DR_TERRY_KLOCK=https://drive.google.com/file/d/.../view
GOOGLE_DRIVE_LINK_DR_JACKI_SENGE=https://drive.google.com/file/d/.../view
GOOGLE_DRIVE_LINK_DR_DALLA_MCDER=https://drive.google.com/file/d/.../view
GOOGLE_DRIVE_LINK_PATIENT_DATA=https://drive.google.com/file/d/.../view
```

### 2. Load Data

```bash
pip install -r requirements.txt
python load_rag_data.py
```

### 3. Run Chatbot

```bash
python chatbot.bat
```

## How It Works

1. **Download** - Fetches documents from Google Drive shared links
2. **Extract** - Parses text from .txt, .csv, .pdf, .docx, .pptx files
3. **Embed** - Creates vector embeddings using Gemini
4. **Store** - Saves in local Chroma database (`.vector_db/`)
5. **Search** - Retrieves relevant context on user queries
6. **Inject** - Adds context to LLM prompts for personalized responses

## File Format Support

- `.txt` - Text files
- `.csv` - Data files
- `.pdf` - PDF documents
- `.docx` - Word documents
- `.pptx` - PowerPoint presentations

## Update Data

When you modify documents in Google Drive:

```bash
python load_rag_data.py
```

To force a full reload:

```bash
python load_rag_data.py --force
```

## Performance

- First load: 2-3 minutes
- Subsequent startups: ~1-2 seconds (cached)
- Per-query overhead: ~1-2 seconds

## Architecture

```
Google Drive (shared links)
    ↓ (download)
load_rag_data.py (extract text)
    ↓
rag_vector_db.py (create embeddings)
    ↓
.vector_db/ (Chroma local database)
    ↓ (semantic search)
response_generator.py (inject context)
    ↓
Chatbot (personalized responses)
```

## Core Files

- `load_rag_data.py` - Load Google Drive data into vector DB
- `rag_vector_db.py` - Vector database operations
- `response_generator.py` - RAG context injection
- `.vector_db/` - Local Chroma database (in repository)
