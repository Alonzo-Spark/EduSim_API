import chromadb
import difflib
import re
import time
from app.config import settings
from app.rag.embedder import embed_query

# Simple thread-safe cache to eliminate latency on duplicate queries
_RETRIEVAL_CACHE = {}

def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower().strip())
    return re.sub(r"\s+", " ", normalized).strip()

def normalize_class_name(value: str | None) -> str:
    normalized = normalize_text(value)
    class_match = re.search(r"\bclass\s+(\d+)\b", normalized)
    if class_match:
        return f"class {class_match.group(1)}"
    roman_map = {
        "i": "1",
        "ii": "2",
        "iii": "3",
        "iv": "4",
        "v": "5",
        "vi": "6",
        "vii": "7",
        "viii": "8",
        "ix": "9",
        "x": "10",
    }
    if normalized in roman_map:
        return f"class {roman_map[normalized]}"
    return normalized

def metadata_match_score(candidate: dict, class_name: str, subject: str, chapter: str | None, topic: str | None) -> float:
    score = 0.0

    candidate_class = normalize_class_name(str(candidate.get("class", "")))
    candidate_subject = normalize_text(str(candidate.get("subject", "")))
    candidate_chapter = normalize_text(str(candidate.get("chapter", "")))
    candidate_topic = normalize_text(str(candidate.get("topic", "")))

    target_class = normalize_class_name(class_name)
    target_subject = normalize_text(subject)
    target_chapter = normalize_text(chapter)
    target_topic = normalize_text(topic)

    if target_class and candidate_class == target_class:
        score += 4.0
    elif target_class and target_class in candidate_class:
        score += 2.5

    if target_subject and candidate_subject == target_subject:
        score += 3.0
    elif target_subject and target_subject in candidate_subject:
        score += 2.0

    if target_chapter:
        chapter_ratio = difflib.SequenceMatcher(None, target_chapter, candidate_chapter).ratio() if candidate_chapter else 0.0
        if candidate_chapter == target_chapter:
            score += 2.5
        else:
            score += chapter_ratio * 2.0

    if target_topic:
        topic_ratio = difflib.SequenceMatcher(None, target_topic, candidate_topic).ratio() if candidate_topic else 0.0
        if candidate_topic == target_topic:
            score += 3.5
        elif target_topic in candidate_topic or candidate_topic in target_topic:
            score += 2.5
        else:
            score += topic_ratio * 3.0

    return score

def build_query_stages(class_name: str, subject: str, chapter: str | None, topic: str | None) -> list[tuple[str, dict | None]]:
    stages: list[tuple[str, dict | None]] = []

    base_filters = [
        {"class": {"$eq": class_name}},
        {"subject": {"$eq": subject}},
    ]

    if chapter:
        stages.append(("class+subject+chapter+topic", {"$and": base_filters + [{"chapter": {"$eq": chapter}}, {"topic": {"$eq": topic}}]} if topic else {"$and": base_filters + [{"chapter": {"$eq": chapter}}]}))
        stages.append(("class+subject+chapter", {"$and": base_filters + [{"chapter": {"$eq": chapter}}]}))

    stages.append(("class+subject", {"$and": base_filters}))
    stages.append(("global semantic search", None))
    return stages

def log_candidate_snapshot(results: dict) -> None:
    documents = results.get("documents", [[]])
    metadatas = results.get("metadatas", [[]])
    distances = results.get("distances", [[]])
    count = len(documents[0]) if documents else 0
    print(f"  [DEBUG] Retrieved chunk count: {count}")
    for index, (meta, distance) in enumerate(zip(metadatas[0][:3] if metadatas else [], distances[0][:3] if distances else []), start=1):
        print(f"  [DEBUG] Top {index} metadata: {meta}")
        print(f"  [DEBUG] Top {index} distance: {distance}")

def get_chroma_collection():
    client = chromadb.PersistentClient(path=settings.chroma_db_path)
    return client.get_collection("edusim_textbooks")

def analyze_query(query: str) -> dict:
    """
    Query Intent Analyzer:
    Identifies if a student is asking for a definition, formula, example, derivation,
    or a numerical computation, and outputs semantic term boosts.
    """
    query_lower = query.lower()
    
    intent = "conceptual"
    boost_keywords = []
    
    if any(k in query_lower for k in ["formula", "equation", "express", "relation", "constant", "value", "=", "+", "-", "/"]):
        intent = "formula-based"
        boost_keywords = ["formula", "equation", "derive", "expression", "constant", "equal"]
    elif any(k in query_lower for k in ["calculate", "find", "solve", "numerical", "problem", "value", "speed of", "velocity of", "mass"]):
        intent = "numerical"
        boost_keywords = ["example", "solve", "numerical", "problem", "value", "calculate"]
    elif any(k in query_lower for k in ["derive", "derivation", "proof", "prove", "step by step", "how to get", "obtain"]):
        intent = "derivation"
        boost_keywords = ["derivation", "proof", "step", "derive", "obtain", "equations"]
    elif any(k in query_lower for k in ["define", "definition", "what is", "meaning of", "state"]):
        intent = "definition"
        boost_keywords = ["define", "definition", "stated as", "refers to", "called"]
    elif any(k in query_lower for k in ["example", "illustration", "real life", "demonstrate", "show"]):
        intent = "example-based"
        boost_keywords = ["example", "illustration", "consider", "case", "demonstrates"]
        
    return {
        "intent": intent,
        "boost_keywords": boost_keywords
    }

def calculate_keyword_score(text: str, query: str, intent_info: dict) -> float:
    """
    Textbook Phrase & Math Expression Matcher:
    - Calculates term frequency overlaps with log-scaled frequency normalization
    - Detects exact phrase matching
    - Runs mathematical equation structural comparisons (ignoring spacing)
    - Boosts text aligning with analyzed intent keywords
    """
    text_lower = text.lower()
    query_lower = query.lower()
    
    # 1. Exact phrase match
    phrase_score = 0.0
    if query_lower in text_lower:
        phrase_score = 1.0
        
    # Clean query into keywords
    query_words = [w for w in re.sub(r'[^\w\s\=\+\-\*/\^]', ' ', query_lower).split() if len(w) > 2]
    if not query_words:
        return phrase_score
        
    # 2. Term frequency matching with log scaling
    matches = 0
    tf_sum = 0
    for word in query_words:
        count = text_lower.count(word)
        if count > 0:
            matches += 1
            tf_sum += (1.0 + count**0.5) / 2.0
            
    overlap_ratio = matches / len(query_words)
    tf_score = tf_sum / len(query_words)
    
    # 3. Exact equation structural matcher (removes spaces to compare syntax)
    formula_score = 0.0
    formula_matches = re.findall(r'([a-zA-Z0-9\s_]{1,5}\s*=\s*[a-zA-Z0-9\s_\*\+\-\(\)\^/]{1,10})', query_lower)
    if formula_matches:
        for f in formula_matches:
            f_clean = re.sub(r'\s+', '', f)
            t_clean = re.sub(r'\s+', '', text_lower)
            if f_clean in t_clean:
                formula_score += 1.0
                
    # 4. Intent keyword boosting
    intent_boost = 0.0
    for kw in intent_info["boost_keywords"]:
        if kw in text_lower:
            intent_boost += 0.2
            
    # Combine scores
    combined = (0.4 * phrase_score) + (0.3 * overlap_ratio) + (0.2 * tf_score) + (0.1 * min(1.0, formula_score + intent_boost))
    return min(1.0, combined)

def calculate_educational_boost(text: str, metadata: dict, query_intent: str, active_topic: str = None) -> float:
    """
    Educational Structure Booster:
    Examines chunks to reward high-value educational assets like definitions,
    formulas, steps, and examples, relative to the student's intent.
    """
    boost = 0.0
    text_lower = text.lower()
    
    # Active topic match boost
    if active_topic and metadata.get("topic") == active_topic:
        boost += 0.2
        
    # Formulas/Equations boost
    if "[equation/formula]" in text_lower or "formula" in text_lower or "equation" in text_lower:
        if query_intent in ["formula-based", "numerical"]:
            boost += 0.25
        else:
            boost += 0.1
            
    # Definition boost
    is_definition = any(marker in text_lower for marker in ["defined as", "refers to", "stated as", "is known as", "meaning of"])
    if is_definition:
        if query_intent == "definition":
            boost += 0.25
        else:
            boost += 0.1
            
    # Examples boost
    if "[example]" in text_lower or "example" in text_lower or "illustration" in text_lower:
        if query_intent in ["example-based", "numerical"]:
            boost += 0.2
        else:
            boost += 0.05
            
    # Steps / lists / derivations boost
    has_steps = any(marker in text_lower for marker in ["step 1", "step 2", "first step", "finally", "therefore", "proof", "derivation"])
    if has_steps or len(re.findall(r'^\s*(\d+[\.\)]|\*|\-|•)\s+', text, re.MULTILINE)) >= 2:
        if query_intent == "derivation":
            boost += 0.2
        else:
            boost += 0.05
            
    return boost

def retrieve_chunks(
    query: str,
    class_name: str,
    subject: str,
    chapter: str = None,
    topic: str = None,
    n_results: int = 6,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.3
) -> list[dict]:
    """
    Production-grade hybrid retriever combining semantic vector search
    with query-intent keyword matching, reranking, and educational structure boosting.
    
    Automatically infers curriculum context coordinates for unstructured queries!
    """
    start_time = time.time()
    
    # 0. Curriculum Context Inference Fallback
    from app.rag.topic_classifier import infer_curriculum_context
    inferred = infer_curriculum_context(query)
    
    resolved_class = class_name or inferred.get("class") or "Class 9"
    resolved_subject = subject or inferred.get("subject") or "Science"
    resolved_chapter = chapter or inferred.get("chapter")
    resolved_topic = topic or inferred.get("topic")

    # Cache lookup
    cache_key = (query, resolved_class, resolved_subject, resolved_chapter, resolved_topic, n_results)
    if cache_key in _RETRIEVAL_CACHE:
        return _RETRIEVAL_CACHE[cache_key]

    try:
        collection = get_chroma_collection()
    except Exception as e:
        print(f"[ERROR] Opening ChromaDB collection failed: {e}")
        return []

    # 1. Intent & Query Analysis
    intent_info = analyze_query(query)

    # Generate query embedding vector
    query_embedding = embed_query(query)

    # Query a wider pool of candidates to run in-memory reranking
    candidate_limit = max(n_results * 3, 20)

    print("[INFO] Retrieval request received")
    print(f"  [DEBUG] incoming query: {query}")
    print(f"  [DEBUG] resolved class: {resolved_class}")
    print(f"  [DEBUG] resolved subject: {resolved_subject}")
    print(f"  [DEBUG] resolved chapter: {resolved_chapter}")
    print(f"  [DEBUG] resolved topic: {resolved_topic}")

    try:
        snapshot = collection.get(limit=3, include=["metadatas", "documents"])
        print("  [DEBUG] Stored chunk metadata sample:")
        for index, meta in enumerate(snapshot.get("metadatas", [])[:3], start=1):
            print(f"    {index}. {meta}")
    except Exception as e:
        print(f"  [DEBUG] Unable to sample stored chunk metadata: {e}")

    final_results: list[dict] = []
    normalized_stage = {
        "class": normalize_class_name(resolved_class),
        "subject": normalize_text(resolved_subject),
        "chapter": normalize_text(resolved_chapter),
        "topic": normalize_text(resolved_topic),
    }

    for stage_name, where_filter in build_query_stages(resolved_class, resolved_subject, resolved_chapter, resolved_topic):
        try:
            print(f"  [DEBUG] Retrieval stage: {stage_name}")
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=candidate_limit,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            print(f"  [DEBUG] Stage {stage_name} failed: {e}")
            continue

        if not results or not results.get("documents") or not results["documents"][0]:
            print(f"  [DEBUG] Stage {stage_name} returned 0 chunks")
            continue

        log_candidate_snapshot(results)

        raw_candidates = []
        seen_texts = set()

        for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            if doc in seen_texts:
                continue
            seen_texts.add(doc)

            semantic_score = max(0.0, 1.0 - (dist / 2.0))
            keyword_score = calculate_keyword_score(doc, query, intent_info)
            hybrid_score = (semantic_weight * semantic_score) + (keyword_weight * keyword_score)
            boost = calculate_educational_boost(doc, meta, intent_info["intent"], resolved_topic)
            metadata_boost = metadata_match_score(meta, resolved_class, resolved_subject, resolved_chapter, resolved_topic) / 12.0
            final_score = min(1.0, hybrid_score + boost + metadata_boost)

            raw_candidates.append({
                "text": doc,
                "metadata": meta,
                "relevance_score": round(final_score, 3),
                "semantic_score": round(semantic_score, 3),
                "keyword_score": round(keyword_score, 3),
                "hybrid_score": round(hybrid_score, 3),
                "query_intent": intent_info["intent"],
                "metadata_match_score": round(metadata_boost, 3),
            })

        raw_candidates.sort(key=lambda x: (x["metadata_match_score"], x["relevance_score"]), reverse=True)
        final_results = raw_candidates[:n_results]

        if final_results:
            print(f"  [DEBUG] Stage {stage_name} yielded {len(final_results)} chunk(s)")
            break

    if not final_results:
        try:
            print("  [DEBUG] No staged results found; falling back to global semantic search")
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=candidate_limit,
                include=["documents", "metadatas", "distances"],
            )
            log_candidate_snapshot(results)
            raw_candidates = []
            seen_texts = set()
            for doc, meta, dist in zip(results.get("documents", [[]])[0], results.get("metadatas", [[]])[0], results.get("distances", [[]])[0]):
                if doc in seen_texts:
                    continue
                seen_texts.add(doc)
                semantic_score = max(0.0, 1.0 - (dist / 2.0))
                keyword_score = calculate_keyword_score(doc, query, intent_info)
                hybrid_score = (semantic_weight * semantic_score) + (keyword_weight * keyword_score)
                boost = calculate_educational_boost(doc, meta, intent_info["intent"], resolved_topic)
                metadata_boost = metadata_match_score(meta, resolved_class, resolved_subject, resolved_chapter, resolved_topic) / 12.0
                raw_candidates.append({
                    "text": doc,
                    "metadata": meta,
                    "relevance_score": round(min(1.0, hybrid_score + boost + metadata_boost), 3),
                    "semantic_score": round(semantic_score, 3),
                    "keyword_score": round(keyword_score, 3),
                    "hybrid_score": round(hybrid_score, 3),
                    "query_intent": intent_info["intent"],
                    "metadata_match_score": round(metadata_boost, 3),
                })
            raw_candidates.sort(key=lambda x: (x["metadata_match_score"], x["relevance_score"]), reverse=True)
            final_results = raw_candidates[:n_results]
        except Exception as e:
            print(f"[ERROR] Global semantic fallback failed: {e}")
            final_results = []

    elapsed = round((time.time() - start_time) * 1000, 2)
    
    # Clean ASCII log summaries for timing audits
    print(f"[INFO] Hybrid search complete in {elapsed}ms! Intent: {intent_info['intent']}")
    if final_results:
        print(f"  - Top match score: {final_results[0]['relevance_score']} (Sem: {final_results[0]['semantic_score']}, Key: {final_results[0]['keyword_score']}, Meta: {final_results[0].get('metadata_match_score', 0)})")

    # Add to in-memory cache (limit cache size to prevent memory leaks)
    if len(_RETRIEVAL_CACHE) < 150:
        _RETRIEVAL_CACHE[cache_key] = final_results
    else:
        _RETRIEVAL_CACHE.clear()
        _RETRIEVAL_CACHE[cache_key] = final_results

    return final_results

def build_rag_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a structured context string for the LLM.
    Includes source labels so the LLM can cite textbook references.
    """
    if not chunks:
        return "No textbook content available."

    parts = []
    for chunk in chunks:
        meta = chunk["metadata"]
        label = (
            f"[SOURCE: {meta.get('class','')} > {meta.get('subject','')} > "
            f"{meta.get('chapter','')} | Page {meta.get('page','')} | "
            f"Hybrid Score: {chunk['relevance_score']} (Vector: {chunk.get('semantic_score', 0)}, Keyword: {chunk.get('keyword_score', 0)})]"
        )
        parts.append(f"{label}\n{chunk['text']}")

    separator = "\n\n" + "="*60 + "\n\n"
    return separator.join(parts)
