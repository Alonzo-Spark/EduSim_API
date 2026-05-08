import os
from langchain_community.document_loaders import PyPDFLoader

def load_pdf(pdf_path: str):
    """Load a single PDF document."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"File not found: {pdf_path}")
    
    try:
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        print(f"[LOADER] Loaded {len(docs)} pages from {os.path.basename(pdf_path)}")
        return docs
    except Exception as e:
        raise Exception(f"Error loading {pdf_path}: {e}")

def load_all_pdfs(directory_path: str):
    """Load all PDF documents from a directory."""
    all_docs = []
    if not os.path.isdir(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
        
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(directory_path, filename)
            try:
                docs = load_pdf(pdf_path)
                all_docs.extend(docs)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                
    if not all_docs:
        print("[LOADER] Warning: No PDFs found or loaded in the directory.")
        
    return all_docs

# Alias for backward compatibility if needed
load_pdfs = load_all_pdfs