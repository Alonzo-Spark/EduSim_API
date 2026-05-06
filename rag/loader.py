from langchain_community.document_loaders import PyPDFLoader

def load_pdf(pdf_path: str):
    """Load PDF document using PyPDFLoader."""
    try:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        print(f"✓ Loaded {len(docs)} pages from {pdf_path}")
        return docs
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    except Exception as e:
        raise Exception(f"Error loading PDF: {e}")