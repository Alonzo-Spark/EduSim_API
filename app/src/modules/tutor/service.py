import re
import json
import difflib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from rag.retriever import get_retriever
from rag.generator import generate_llm_text
import pickle
import faiss
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[4] / ".env")

# RAG Setup
_retriever = None
_embeddings_model = None

# Curriculum Index Cache
_curriculum_data = None
_curriculum_index = None


def _empty_tutor_payload(message: str):
    return {
        "title": "Generation Failed",
        "description": "",
        "formula": "",
        "related_concepts": [],
        "related_formulas": [],
        "ai_explanation": message,
        "sources": [],
        "queryType": "concept",
        "concepts": [],
        "formulas": [],
        "explanation": message,
        "ragContent": [],
    }

def get_rag_components():
    global _retriever, _embeddings_model
    if _retriever is None:
        try:
            # Load FAISS index and metadata
            index = faiss.read_index("faiss_index/index.faiss")
            with open("faiss_index/metadata.pkl", "rb") as f:
                metadata = pickle.load(f)
            
            _embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            _retriever = get_retriever(index, metadata, _embeddings_model)
        except Exception as e:
            print(f"⚠️ RAG Initialization Warning: {e}")
            return None, None
    return _retriever, _embeddings_model

def analyze_with_llm(query: str, context: str) -> Dict[str, Any]:
    """
    Uses LLM to extract physics concepts, formulas, query type, and explanation from the context.
    """
    system_prompt = (
        "You are an intelligent physics textbook tutor. Analyze the user's query and the provided Context.\n\n"
        "1. Determine the 'queryType': 'concept', 'formula', or 'mixed'.\n"
        "2. Extract 'concepts': list of related physics topics from the context.\n"
        "3. Extract 'formulas': find relevant formulas in the context. IF the query is a concept but has fundamental formulas (like F=ma for force) not present in context, you MUST include them from your knowledge. Provide formula, name, topic, meaning.\n"
        "4. Generate an 'explanation' answering the query based on the context.\n\n"
        "Return ONLY a valid JSON object:\n"
        "{\n"
        "  \"queryType\": \"string\",\n"
        "  \"concepts\": [\"string\"],\n"
        "  \"formulas\": [\n"
        "    {\"formula\": \"string\", \"name\": \"string\", \"topic\": \"string\", \"meaning\": \"string\"}\n"
        "  ],\n"
        "  \"explanation\": \"string\"\n"
        "}\n"
    )
    
    user_prompt = f"Context:\n{context}\n\nQuery:\n{query}"
    
    try:
        final_prompt = f"{system_prompt}\n\n{user_prompt}\n\nReturn only the JSON object."
        response_text = generate_llm_text(final_prompt, temperature=0.1)

        if not response_text or response_text.startswith("Error:"):
            return _empty_tutor_payload("AI returned an empty or error response.")

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            print("AI generation completed: tutor analysis")
            parsed = json.loads(json_match.group())
            return {
                **parsed,
                "title": parsed.get("title", "AI Tutor Response"),
                "description": parsed.get("description", ""),
                "formula": parsed.get("formula", ""),
                "related_concepts": parsed.get("concepts", []),
                "related_formulas": parsed.get("formulas", []),
                "ai_explanation": parsed.get("explanation", ""),
                "sources": parsed.get("sources", []),
            }

        return _empty_tutor_payload("AI returned an invalid JSON response.")
    except Exception as e:
        print("AI Generation Error:", str(e))
        return _empty_tutor_payload(f"AI generation failed: {str(e)}")

def analyze_tutor_query(query: str) -> Dict[str, Any]:
    # 1. RAG Retrieval First
    request_started = time.perf_counter()
    print("AI request started: tutor retrieval")
    retriever, _ = get_rag_components()
    rag_content = []
    context = ""
    retrieval_started = time.perf_counter()
    
    if retriever:
        docs = retriever(query)
        # Format RAG content for frontend
        for doc in docs[:5]: # Top 5
            source = os.path.basename(doc.get("source", "Textbook"))
            content = doc.get("text", "").strip()
            
            # Clean up text
            content = re.sub(r'\s+', ' ', content)
            if len(content) > 400:
                content = content[:400] + "..."

            rag_content.append({
                "title": source,
                "content": content
            })
            
            context += f"{content}\n\n"
        print(f"RAG retrieval completed: {len(rag_content)} chunks")
    else:
        context = "No textbook context available."

    retrieval_time = time.perf_counter() - retrieval_started
    print(f"Retrieval time: {retrieval_time:.2f}s")
    print("Retrieved Context:", context)

    if not query or len(query.strip()) < 2:
        return _empty_tutor_payload("Query is too short for AI generation.")

    # 2. Use LLM for intelligent extraction based on context
    structured = analyze_with_llm(query, context)

    if not context.strip():
        context = "No textbook context available."

    # 3. Generate the explanation with AI using the same textbook context
    explanation_prompt = (
        "You are an intelligent physics textbook tutor. Use the retrieved textbook context to answer the student's query. "
        "Keep the explanation accurate, concise, and educational.\n\n"
        f"Context:\n{context}\n\n"
        f"Query:\n{query}\n\n"
        "Respond with a clear explanation and include relevant formulas when appropriate."
    )
    try:
        explanation_started = time.perf_counter()
        print("AI request started: tutor explanation")
        rag_explanation = generate_llm_text(explanation_prompt, temperature=0.2)

        if not rag_explanation or rag_explanation.startswith("Error:"):
            rag_explanation = "AI returned an empty or error response."
        else:
            print("AI generation completed: tutor explanation")

        explanation_time = time.perf_counter() - explanation_started
        print(f"AI generation time: {explanation_time:.2f}s")
    except Exception as e:
        print("AI Generation Error:", str(e))
        rag_explanation = f"AI generation failed: {str(e)}"

    total_time = time.perf_counter() - request_started
    print(f"Total request time: {total_time:.2f}s")

    concepts = structured.get("concepts", [])
    formulas = structured.get("formulas", [])
    if isinstance(formulas, list) and formulas and isinstance(formulas[0], dict):
        first_formula = formulas[0].get("formula", "")
    elif isinstance(formulas, list) and formulas:
        first_formula = formulas[0]
    else:
        first_formula = ""

    explanation_text = rag_explanation or structured.get("explanation", "")
    
    return {
        "title": structured.get("title", "AI Tutor Response"),
        "description": structured.get("description", query),
        "formula": first_formula,
        "related_concepts": concepts,
        "related_formulas": formulas,
        "ai_explanation": explanation_text,
        "sources": rag_content[:3],
        "queryType": structured.get("queryType", "concept"),
        "concepts": concepts,
        "formulas": formulas,
        "explanation": explanation_text,
        "ragContent": rag_content[:3], # Send top 3 to frontend
    }


# --- Comprehensive Curriculum Search System ---

_TYPE_PRIORITY = {"topic": 0, "chapter": 1, "subject": 2, "class": 3}

_QUERY_HINTS = {
    "ele": ["electric", "electro", "electromag", "current", "charge", "voltage", "resistance"],
    "newton": ["newton", "laws of motion", "force", "acceleration"],
    "grav": ["gravitation", "gravity", "centre of gravity"],
    "proj": ["projectile", "projectiles", "projectile motion"],
}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip().lower()


def _format_class_name(value: Any) -> str:
    text = str(value).strip()
    if text.lower().startswith("class "):
        return text[:6].capitalize() + text[6:]
    return f"Class {text}"


def _load_curriculum() -> Dict[str, Any]:
    """Load curriculum data from the generated JSON file."""
    global _curriculum_data
    if _curriculum_data is not None:
        return _curriculum_data

    curriculum_path = Path(__file__).resolve().parents[2] / "data" / "curriculum.json"
    try:
        with open(curriculum_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if isinstance(loaded, dict) and "classes" in loaded:
            _curriculum_data = loaded
        else:
            _curriculum_data = {"classes": []}
    except Exception as e:
        print(f"Failed to load curriculum: {e}")
        _curriculum_data = {"classes": []}
    return _curriculum_data


def _iter_class_records() -> List[Dict[str, Any]]:
    data = _load_curriculum()
    classes = data.get("classes", []) if isinstance(data, dict) else []
    if not isinstance(classes, list):
        return []
    return classes


def _flatten_curriculum() -> List[Dict[str, Any]]:
    """Flatten the nested curriculum into searchable records."""
    entries: List[Dict[str, Any]] = []
    seen = set()

    for class_record in _iter_class_records():
        class_name = _format_class_name(class_record.get("name", ""))
        class_id = class_record.get("id")
        class_description = class_record.get("description", "")
        subjects = class_record.get("subjects", []) or []

        class_search_parts = [class_name, class_description]
        for subject in subjects:
            class_search_parts.extend([
                subject.get("name", ""),
                subject.get("description", ""),
            ])
            chapters = subject.get("chapters", []) or []
            if isinstance(chapters, list):
                for chapter in chapters:
                    chapter_name = chapter.get("name", "")
                    class_search_parts.append(chapter_name)
                    topics = chapter.get("topics", []) or []
                    for topic in topics:
                        class_search_parts.append(topic.get("name", ""))

        class_key = ("class", class_name)
        if class_key not in seen:
            seen.add(class_key)
            entries.append(
                {
                    "type": "class",
                    "class_id": class_id,
                    "class_name": class_name,
                    "subject": None,
                    "chapter": None,
                    "topic": None,
                    "search_text": _normalize_text(" ".join(class_search_parts)),
                    "display": class_name,
                }
            )

        for subject in subjects:
            subject_name = subject.get("name", "")
            subject_id = subject.get("id", "")
            subject_description = subject.get("description", "")
            chapters = subject.get("chapters", []) or []

            subject_search_parts = [
                class_name,
                subject_name,
                subject_id,
                subject_description,
            ]

            if isinstance(chapters, list):
                chapter_names = [chapter.get("name", "") for chapter in chapters]
                subject_search_parts.extend(chapter_names)
            else:
                subject_search_parts.append(str(chapters))

            subject_key = ("subject", class_name, subject_name)
            if subject_key not in seen:
                seen.add(subject_key)
                entries.append(
                    {
                        "type": "subject",
                        "class_id": class_id,
                        "class_name": class_name,
                        "subject_id": subject_id,
                        "subject": subject_name,
                        "chapter": None,
                        "topic": None,
                        "search_text": _normalize_text(" ".join(subject_search_parts)),
                        "display": f"{subject_name} • {class_name}",
                    }
                )

            if not isinstance(chapters, list):
                continue

            for chapter in chapters:
                chapter_name = chapter.get("name", "")
                topics = chapter.get("topics", []) or []
                chapter_search_parts = [
                    class_name,
                    subject_name,
                    chapter_name,
                ]
                chapter_search_parts.extend(topic.get("name", "") for topic in topics)

                chapter_key = ("chapter", class_name, subject_name, chapter_name)
                if chapter_key not in seen:
                    seen.add(chapter_key)
                    entries.append(
                        {
                            "type": "chapter",
                            "class_id": class_id,
                            "class_name": class_name,
                            "subject_id": subject_id,
                            "subject": subject_name,
                            "chapter": chapter_name,
                            "topic": None,
                            "topics": [topic.get("name", "") for topic in topics],
                            "search_text": _normalize_text(" ".join(chapter_search_parts)),
                            "display": f"{subject_name} • {class_name}\n{chapter_name}",
                        }
                    )

                for topic in topics:
                    topic_name = topic.get("name", "")
                    topic_key = ("topic", class_name, subject_name, chapter_name, topic_name)
                    if topic_key in seen:
                        continue
                    seen.add(topic_key)
                    entries.append(
                        {
                            "type": "topic",
                            "class_id": class_id,
                            "class_name": class_name,
                            "subject_id": subject_id,
                            "subject": subject_name,
                            "chapter": chapter_name,
                            "topic": topic_name,
                            "search_text": _normalize_text(
                                f"{class_name} {subject_name} {chapter_name} {topic_name}"
                            ),
                            "display": f"{subject_name} • {class_name}\n{chapter_name} → {topic_name}",
                        }
                    )

    return entries


def _build_curriculum_index() -> List[Dict[str, Any]]:
    global _curriculum_index
    if _curriculum_index is None:
        _curriculum_index = _flatten_curriculum()
    return _curriculum_index


def _score_value(query: str, value: str, exact_score: int, prefix_score: int, substring_score: int, fuzzy_score: int) -> float:
    if not value:
        return 0.0

    q = _normalize_text(query)
    v = _normalize_text(value)
    if not q or not v:
        return 0.0

    if q == v:
        return float(exact_score)
    if v.startswith(q):
        return float(prefix_score + min(len(q) / max(len(v), 1), 1.0) * 25)
    if q in v:
        return float(substring_score + min(len(q) / max(len(v), 1), 1.0) * 25)

    if len(q) < 4:
        return 0.0

    ratio = difflib.SequenceMatcher(None, q, v).ratio()
    if ratio >= 0.6:
        return float(fuzzy_score + ratio * 50)
    return 0.0


def _score_match(query: str, entry: Dict[str, Any]) -> Tuple[float, int]:
    q = _normalize_text(query)
    if not q:
        return (0.0, 999)

    score = 0.0
    search_text = entry.get("search_text", "")
    if entry.get("type") == "topic":
        score = max(
            _score_value(q, entry.get("topic", ""), 1200, 1100, 1000, 850),
            _score_value(q, entry.get("chapter", ""), 900, 850, 760, 650),
            _score_value(q, entry.get("subject", ""), 750, 700, 650, 550),
            _score_value(q, entry.get("class_name", ""), 600, 550, 500, 450),
        )
    elif entry.get("type") == "chapter":
        score = max(
            _score_value(q, entry.get("chapter", ""), 1100, 1000, 920, 760),
            _score_value(q, entry.get("subject", ""), 800, 760, 700, 580),
            _score_value(q, entry.get("class_name", ""), 650, 600, 540, 460),
        )
    elif entry.get("type") == "subject":
        score = max(
            _score_value(q, entry.get("subject", ""), 1000, 920, 860, 720),
            _score_value(q, entry.get("class_name", ""), 700, 650, 600, 500),
        )
    else:
        score = max(
            _score_value(q, entry.get("class_name", ""), 900, 840, 780, 650),
            _score_value(q, search_text, 500, 460, 420, 350),
        )

    for hint_key, hint_terms in _QUERY_HINTS.items():
        if q.startswith(hint_key):
            if any(term in search_text for term in hint_terms):
                score += 220
            break

    if score <= 0:
        return (0.0, 999)

    return (score, _TYPE_PRIORITY.get(entry.get("type", "class"), 999))


def search_curriculum(query: str, max_results: int = 30) -> List[Dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []

    scored_results: List[Tuple[float, int, Dict[str, Any]]] = []
    for entry in _build_curriculum_index():
        score, type_rank = _score_match(q, entry)
        if score > 0:
            scored_results.append((score, type_rank, entry))

    scored_results.sort(key=lambda item: (-item[0], item[1], item[2].get("display", "")))

    results = []
    seen = set()
    for score, _, entry in scored_results:
        key = (
            entry.get("type"),
            entry.get("class_name"),
            entry.get("subject"),
            entry.get("chapter"),
            entry.get("topic"),
        )
        if key in seen:
            continue
        seen.add(key)
        results.append(entry)
        if len(results) >= max_results:
            break
    return results


def autocomplete_curriculum(query: str, max_suggestions: int = 15) -> List[Dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []

    ranked = search_curriculum(q, max_results=max_suggestions * 3)
    suggestions: List[Dict[str, Any]] = []
    seen = set()

    for entry in ranked:
        key = (
            entry.get("type"),
            entry.get("class_name"),
            entry.get("subject"),
            entry.get("chapter"),
            entry.get("topic"),
        )
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(
            {
                "type": entry.get("type"),
                "class_name": entry.get("class_name"),
                "subject": entry.get("subject"),
                "chapter": entry.get("chapter"),
                "topic": entry.get("topic"),
                "display": entry.get("display"),
                "priority": _TYPE_PRIORITY.get(entry.get("type", "class"), 999),
            }
        )
        if len(suggestions) >= max_suggestions:
            break

    return suggestions


def get_topic_content(subject: str, class_name: str, chapter: str, topic: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve curriculum content for a selected class/subject/chapter/topic."""
    data = _load_curriculum()
    classes = data.get("classes", []) if isinstance(data, dict) else []

    class_record = None
    for candidate in classes:
        if _normalize_text(candidate.get("name", "")) == _normalize_text(class_name):
            class_record = candidate
            break

    if not class_record:
        return {"error": "class_not_found"}

    subject_record = None
    for candidate in class_record.get("subjects", []) or []:
        candidate_name = candidate.get("name", "")
        candidate_id = candidate.get("id", "")
        if _normalize_text(candidate_name) == _normalize_text(subject) or _normalize_text(candidate_id) == _normalize_text(subject):
            subject_record = candidate
            break

    if not subject_record:
        return {"error": "subject_not_found"}

    chapters = subject_record.get("chapters", []) or []
    chapter_record = None
    if isinstance(chapters, list):
        for candidate in chapters:
            if _normalize_text(candidate.get("name", "")) == _normalize_text(chapter):
                chapter_record = candidate
                break

    if not chapter_record:
        return {"error": "chapter_not_found"}

    topic_list = [item.get("name", "") for item in chapter_record.get("topics", []) or []]
    matched_topic = topic
    if topic:
        matched_topic = None
        for candidate in topic_list:
            if _normalize_text(candidate) == _normalize_text(topic):
                matched_topic = candidate
                break
        if not matched_topic:
            return {"error": "topic_not_found"}

    response: Dict[str, Any] = {
        "class_name": class_record.get("name", class_name),
        "subject": subject_record.get("name", subject),
        "chapter": chapter_record.get("name", chapter),
        "topic": matched_topic or "",
        "outcomes": chapter_record.get("outcomes", []) or [],
        "prerequisites": chapter_record.get("prerequisites", []) or [],
        "topics": topic_list,
        "ai_explanation": "",
        "related_concepts": topic_list,
        "related_formulas": [],
        "textbook_content": {
            "outcomes": chapter_record.get("outcomes", []) or [],
            "prerequisites": chapter_record.get("prerequisites", []) or [],
            "topics": topic_list,
        },
        "simulation_prompt": None,
    }

    if matched_topic:
        try:
            sims_path = Path(__file__).resolve().parents[4] / "data" / "generated_simulations.json"
            if sims_path.exists():
                with open(sims_path, "r", encoding="utf-8") as f:
                    sims = json.load(f)
                for sim in sims:
                    sim_topic = sim.get("topic") or {}
                    sim_topic_name = sim_topic.get("topic") if isinstance(sim_topic, dict) else None
                    if sim_topic_name and _normalize_text(sim_topic_name) == _normalize_text(matched_topic):
                        response["simulation_prompt"] = sim.get("description") or sim.get("dsl")
                        response["stored_simulation"] = sim
                        break
        except Exception:
            pass

    return response
