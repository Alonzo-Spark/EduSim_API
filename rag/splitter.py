from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_docs(docs):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    chunks = splitter.split_documents(docs)

    print(f"✓ Total chunks created: {len(chunks)}")

    return chunks