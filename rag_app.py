import os
from dotenv import load_dotenv

from rag.loader import load_pdf
from rag.splitter import split_docs
from rag.embedder import get_embeddings
from rag.vector_store import create_vector_store
from rag.retriever import get_retriever
from rag.generator import generate_response

# Load environment variables
load_dotenv()


# =========================================================
# MAIN APPLICATION
# =========================================================
def main():
    """Main RAG application loop."""

    # Load PDF
    pdf_path = os.getenv("PDF_PATH", "data/physics.pdf")

    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        print("Please update PDF_PATH in .env or ensure the file exists.")
        return

    print("=" * 60)
    print("RAG System - OpenRouter API")
    print("=" * 60)
    print(f"\n📄 Loading PDF: {pdf_path}")

    try:

        # =====================================================
        # LOAD PDF
        # =====================================================
        docs = load_pdf(pdf_path)

        # =====================================================
        # SPLIT DOCUMENTS
        # =====================================================
        print(f"\n📑 Splitting into chunks...")
        chunks = split_docs(docs)

        print(f"✓ Total chunks created: {len(chunks)}")

        # =====================================================
        # LOAD EMBEDDINGS
        # =====================================================
        print("\n🔗 Loading embeddings model...")
        embeddings_model = get_embeddings()

        # =====================================================
        # CREATE / LOAD VECTOR STORE
        # =====================================================
        force_rebuild = (
            os.getenv("FORCE_REBUILD", "false").lower() == "true"
        )

        print("\n🗂️ Setting up vector store...")

        index, metadata = create_vector_store(
            chunks,
            embeddings_model,
            force_rebuild=force_rebuild
        )[:2]

        print(f"✓ Vector DB ready with {len(metadata)} chunks")

        # =====================================================
        # CREATE RETRIEVER
        # =====================================================
        retriever = get_retriever(
            index,
            metadata,
            embeddings_model,
            k=8
        )

        # =====================================================
        # READY
        # =====================================================
        print("\n" + "=" * 60)
        print("✅ RAG System Ready!")
        print("=" * 60)
        print("Commands:")
        print("  - Ask any question")
        print("  - Type 'exit' or 'quit' to exit")
        print("=" * 60 + "\n")

        # =====================================================
        # CHAT LOOP
        # =====================================================
        while True:

            try:

                query = input("❓ Question: ").strip()

                if not query:
                    continue

                # Exit command
                if query.lower() in ["exit", "quit"]:
                    print("\n👋 Goodbye!")
                    break

                # =================================================
                # RETRIEVE CONTEXT
                # =================================================
                print("\n🔍 Retrieving context...")

                results = retriever(query)

                if not results:
                    print("⚠️ No relevant documents found.")
                    continue

                print(f"✓ Found {len(results)} relevant chunks")

                # =================================================
                # BUILD CONTEXT
                # =================================================
                context = "\n\n".join([
                    f"[Page {doc['page']}]\n{doc['text']}"
                    for doc in results
                ])

                # =================================================
                # GENERATE RESPONSE
                # =================================================
                print("\n💭 Generating response...")

                response = generate_response(
                    context=context,
                    question=query
                )

                # =================================================
                # PRINT RESPONSE
                # =================================================
                print(f"\n📝 Answer:\n")

                print(response)

                print("\n" + "-" * 60)

            except KeyboardInterrupt:

                print("\n\n⏹️ Interrupted by user")
                break

            except Exception as e:

                print(f"\n❌ Error: {str(e)}")
                print("Please check your API key and try again.\n")

    except Exception as e:

        print(f"\n❌ Fatal error: {str(e)}")
        return


# =========================================================
# ENTRY POINT
# =====================================================
if __name__ == "__main__":
    main()