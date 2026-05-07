import os
from langchain_community.document_loaders import PyPDFLoader

def load_all_pdfs(directory_path: str):
    """Load all PDF documents from a directory."""
    all_docs = []
    if not os.path.isdir(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")
        
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(directory_path, filename)
            try:
                loader = PyPDFLoader(pdf_path)
                docs = loader.load()
                print(f"✓ Loaded {len(docs)} pages from {filename}")
                all_docs.extend(docs)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                
    if not all_docs:
        print("⚠ No PDFs found or loaded in the directory.")
        
    return all_docs