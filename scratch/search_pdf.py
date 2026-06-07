import fitz  # PyMuPDF

def search_pdf():
    pdf_path = "data/IX Physics EM 2025-26.pdf"
    doc = fitz.open(pdf_path)
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        if "second law" in text.lower():
            print(f"--- PAGE {i+1} ---")
            # Print the paragraph containing the word
            lines = text.split('\n')
            for j, line in enumerate(lines):
                if "second law" in line.lower():
                    start = max(0, j-3)
                    end = min(len(lines), j+4)
                    print("\n".join(lines[start:end]))
                    print("-------------------")

if __name__ == "__main__":
    search_pdf()
