from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_docs(docs):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        separators=[
            "\n\n",
            "\nFormula:",
            "\nDerivation:",
            "\n=",
            "\n",
            ". ",
            "=",
            " ",
            ""
        ]
    )

    chunks = splitter.split_documents(docs)

    print(f"✓ Total chunks created: {len(chunks)}")

    return chunks