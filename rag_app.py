import os
from dotenv import load_dotenv

from rag.loader import load_all_pdfs
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

    print("=" * 60)
    print("EduSim Multi-PDF RAG System")
    print("=" * 60)

    # =====================================================
    # LOAD ALL PDFs
    # =====================================================
    data_path = "data"

    print(f"\n[RAG] Loading PDFs from: {data_path}")

    docs = load_all_pdfs(data_path)

    if not docs:
        print("❌ No PDFs found in data folder")
        return

    print(f"✓ Total pages loaded: {len(docs)}")

    try:

        # =====================================================
        # SPLIT DOCUMENTS
        # =====================================================
        print(f"\n[RAG] Splitting into chunks...")

        chunks = split_docs(docs)

        print(f"✓ Total chunks created: {len(chunks)}")

        # =====================================================
        # LOAD EMBEDDINGS
        # =====================================================
        print("\n🔗 Loading embeddings model...")

        embeddings_model = get_embeddings()

        # =====================================================
        # VECTOR STORE
        # =====================================================
        force_rebuild = (
            os.getenv("FORCE_REBUILD", "false").lower() == "true"
        )

        print("\n[RAG] Setting up vector store...")

        index, metadata = create_vector_store(
            chunks,
            embeddings_model,
            force_rebuild=force_rebuild
        )[:2]

        print(f"✓ Vector DB ready with {len(metadata)} chunks")

        # =====================================================
        # RETRIEVER
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
        print("✅ EduSim RAG Ready!")
        print("=" * 60)

        while True:

            try:

                query = input("\n[?] Question: ").strip()

                if not query:
                    continue

                if query.lower() in ["exit", "quit"]:
                    print("\n👋 Goodbye!")
                    break

                # =================================================
                # RETRIEVE DOCUMENTS
                # =================================================
                print("\n🔍 Retrieving context...")

                results = retriever(query)

                if not results:
                    print("⚠️ No relevant documents found.")
                    continue

                # =================================================
                # DEBUG RETRIEVAL
                # =================================================
                print("\n===== RETRIEVED DOCUMENTS =====")

                for r in results:

                    print(f"Source  : {r.get('source')}")
                    print(f"Page    : {r.get('page')}")
                    print(f"Score   : {r.get('score')}")
                    print("-" * 40)

                # =================================================
                # FILTER LOW SCORES
                # =================================================
                results = [
                    r for r in results
                    if r["score"] > 0.35
                ]

                # =================================================
                # BUILD CONTEXT
                # =================================================
                context = "\n\n".join([
                    f"""
[SUBJECT]: {r.get('subject', 'unknown')}
[SOURCE]: {r.get('source', 'unknown')}
[PAGE]: {r.get('page', 0)}

{r['text']}
"""
                    for r in results
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
                print("\n📝 Answer:\n")

                print(response)

                print("\n" + "-" * 60)

            except KeyboardInterrupt:

                print("\n\n⏹️ Interrupted by user")
                break

            except Exception as e:

                print(f"\n❌ Error: {str(e)}")

    except Exception as e:

        print(f"\n❌ Fatal error: {str(e)}")


# =====================================================
# ENTRY POINT
# =====================================================
if __name__ == "__main__":
    main()