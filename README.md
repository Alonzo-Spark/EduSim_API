# RAG System - Gemini API

A clean, lightweight Retrieval-Augmented Generation (RAG) system using Gemini API for LLM inference.

## Features

- **PDF Processing**: Load and chunk PDF documents
- **Lightweight Embeddings**: Uses sentence-transformers `all-MiniLM-L6-v2` (25MB, very fast)
- **FAISS Vector Database**: Fast similarity search with persistence
- **Gemini API**: Uses `gemini-1.5-flash` model
- **Error Handling**: Graceful error handling for API failures
- **No Large Model Downloads**: No need to download large LLMs locally

## Architecture

```
rag_app.py             - Main application
├── rag/
│   ├── loader.py      - PDF loading (PyPDFLoader)
│   ├── splitter.py    - Text splitting (RecursiveCharacterTextSplitter)
│   ├── embedder.py    - Embeddings (sentence-transformers)
│   ├── vector_store.py - FAISS vector database
│   ├── retriever.py   - Document retriever (top 3 chunks)
│   └── generator.py   - Gemini API calls (google.generativeai)
├── .env               - Configuration (API keys)
└── requirements.txt   - Dependencies
```

## Installation

### 1. Clone and Setup

```bash
cd c:\edu-sample
python -m venv venv
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Gemini API

1. Get your API key from Google AI Studio or your Gemini provider setup
2. Edit `.env` file:

```env
GOOGLE_API_KEY=your_api_key_here
PDF_PATH=data/Projectile Motion.pdf
```

### 4. Prepare PDF

Place your PDF file in the `data/` folder and update `PDF_PATH` in `.env`.

## Usage

### Run the RAG System

```bash
python rag_app.py
```

### Example Interaction

```
Question: What is projectile motion?
🔍 Retrieving context...
✓ Found 3 relevant chunks

💭 Generating response...

📝 Answer:
Projectile motion is the motion of an object thrown or projected into the air...
```

### Exit

Type `exit` or `quit` to exit the application.

## Configuration

### .env Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Your Gemini API key | Yes |
| `PDF_PATH` | Path to PDF file | Yes |
| `FORCE_REBUILD` | Force rebuild of FAISS index | No |

### Customization

#### Change LLM Model

Edit `rag/generator.py`:

```python
GEMINI_MODEL = "gemini-1.5-flash"  # Change this if needed
```

#### Change Number of Retrieved Chunks

Edit `rag_app.py`:

```python
retriever = get_retriever(index, metadata, embeddings_model, k=5)  # Changed from 3
```

#### Adjust Chunking

Edit `rag/splitter.py`:

```python
RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Larger chunks
    chunk_overlap=200     # More overlap
)
```

## API Response Parsing

The system correctly handles Gemini API responses:

```json
{
  "text": "Generated response..."
}
```

**Important**: Response is accessed as:
```python
response.json()["choices"][0]["message"]["content"]
```

NOT `.content` attribute!

## Error Handling

The system handles:

- ❌ Missing PDF file
- ❌ Invalid API key
- ❌ Network timeouts
- ❌ API errors
- ❌ Invalid JSON responses

## Performance

| Component | Size | Speed |
|-----------|------|-------|
| Embeddings Model | ~25 MB | Very fast (<1s) |
| FAISS Index | Depends on PDF | Near-instant |
| API Call | - | ~2-5s |

## Troubleshooting

### "No module named 'faiss'"

```bash
pip install faiss-cpu
```

### "GOOGLE_API_KEY not found"

Make sure `.env` exists in the project root and contains your API key.

### "PDF file not found"

Update `PDF_PATH` in `.env` to the correct path.

### API returns "Invalid request"

Check:
- API key is valid and has credits
- Model name is correct
- Request format matches Gemini generation expectations

## Example Files

- **PDF**: `data/Projectile Motion.pdf` (or your own PDF)
- **Vector Store**: `faiss_index/` (auto-created)
- **Config**: `.env` (auto-created, update with your key)

## Dependencies Overview

| Package | Purpose |
|---------|---------|
| `langchain-community` | PDF loading & text splitting |
| `PyPDF2` | PDF parsing (alternative) |
| `sentence-transformers` | Embeddings (all-MiniLM-L6-v2) |
| `faiss-cpu` | Vector similarity search |
| `requests` | HTTP API calls |
| `python-dotenv` | Environment variables |

## Next Steps

1. Set up Gemini API key
2. Place a PDF in `data/` folder
3. Update `.env` with PDF path
4. Run `python rag_app.py`
5. Ask questions about your document!

## License

MIT License
