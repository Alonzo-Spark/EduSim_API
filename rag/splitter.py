from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_docs(docs):
    """
    Split textbook documents into optimized chunks
    for educational RAG retrieval.
    """

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=700,

        chunk_overlap=120,

        separators=[
            "\n\n",
            "\nChapter",
            "\nDefinition",
            "\nFormula",
            "\nExample",
            "\nAdvantages",
            "\nDisadvantages",
            "\nApplications",
            "\n",
            ". ",
            " ",
            ""
        ]
    )

    chunks = splitter.split_documents(docs)

    print(f"✓ Total chunks created: {len(chunks)}")

    return chunks