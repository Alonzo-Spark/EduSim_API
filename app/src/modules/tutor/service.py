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
from rag.vector_loader import vector_store
from rag.subject_router import detect_subject
import asyncio

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

def get_rag_components(subject: str = None):
    retriever = vector_store.get_retriever(subject)
    return retriever

async def analyze_with_llm_async(query: str, context: str) -> Dict[str, Any]:
    system_prompt = (
        "You are an intelligent tutor. Analyze query and context.\n"
        "1. Determine 'queryType': 'concept', 'formula', or 'mixed'.\n"
        "2. Extract 'concepts': topics.\n"
        "3. Extract 'formulas': [{formula, name, topic, meaning}]. Include fundamental ones if omitted in text.\n"
        "4. Generate a brief 'explanation'.\n"
        "Return ONLY valid JSON."
    )
    user_prompt = f"Context:\n{context}\n\nQuery:\n{query}"
    final_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    from rag.generator import generate_llm_text_async
    try:
        response_text = await generate_llm_text_async(final_prompt, temperature=0.1)
        if not response_text or "Error:" in response_text:
            return _empty_tutor_payload("AI failed to extract concepts.")
            
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                **parsed,
                "title": parsed.get("title", "AI Tutor"),
                "formula": parsed.get("formula", ""),
                "related_concepts": parsed.get("concepts", []),
                "related_formulas": parsed.get("formulas", []),
                "ai_explanation": parsed.get("explanation", ""),
            }
        return _empty_tutor_payload("Invalid JSON returned.")
    except Exception as e:
        return _empty_tutor_payload(f"AI error: {str(e)}")

async def generate_explanation_async(query: str, context: str, fallback_mode: bool = False) -> str:
    from rag.generator import generate_llm_text_async, get_tutor_prompt
    prompt = get_tutor_prompt(context, query, fallback_mode)
    res = await generate_llm_text_async(prompt, temperature=0.3)
    
    if not res:
        return "Failed to generate explanation."
        
    if fallback_mode:
        warning_msg = (
            "This topic is not available in the provided textbook context.\n\n"
            "The following explanation is AI-generated and may not exactly match your textbook.\n\n"
        )
        return warning_msg + res
    return res

async def analyze_tutor_query(query: str) -> Dict[str, Any]:
    request_started = time.perf_counter()
    
    # 1. Subject Routing & RAG Retrieval
    subject = detect_subject(query)
    retriever = get_rag_components(subject)
    
    rag_content = []
    context = ""
    retrieval_start = time.perf_counter()
    
    valid_docs = []
    if retriever:
        docs = retriever(query)
        valid_docs = [doc for doc in docs if doc.get('score', 0) > 0.35]
        
    fallback_mode = not bool(valid_docs)
    
    if not fallback_mode:
        for doc in valid_docs[:3]: # Optimized to 3
            source = os.path.basename(doc.get("source", "Textbook"))
            content = re.sub(r'\s+', ' ', doc.get("text", "")).strip()
            if len(content) > 400: content = content[:400] + "..."
            rag_content.append({"title": source, "content": content})
            context += f"{content}\n\n"
            
    retrieval_time = time.perf_counter() - retrieval_start
    print(f"[RAG] {retrieval_time:.2f}s (Subject: {subject})")
    
    if not context.strip():
        context = "No textbook context available."

    # 2. Async Parallel Execution
    llm_start = time.perf_counter()
    
    structured_task = asyncio.create_task(analyze_with_llm_async(query, context))
    explanation_task = asyncio.create_task(generate_explanation_async(query, context, fallback_mode))
    
    structured, rag_explanation = await asyncio.gather(structured_task, explanation_task)
    
    llm_time = time.perf_counter() - llm_start
    print(f"[LLM] {llm_time:.2f}s")
    
    total_time = time.perf_counter() - request_started
    print(f"[TOTAL] {total_time:.2f}s")
    
    formulas = structured.get("formulas", [])
    first_formula = formulas[0].get("formula", "") if formulas and isinstance(formulas[0], dict) else (formulas[0] if formulas else "")

    return {
        "title": structured.get("title", "AI Tutor Response"),
        "description": query,
        "formula": first_formula,
        "related_concepts": structured.get("related_concepts", []),
        "related_formulas": formulas,
        "ai_explanation": rag_explanation,
        "sources": rag_content,
        "queryType": structured.get("queryType", "concept"),
        "concepts": structured.get("related_concepts", []),
        "formulas": formulas,
        "explanation": rag_explanation,
        "ragContent": rag_content,
    }

async def analyze_tutor_query_stream(query: str):
    """
    Streaming SSE generator for ultra-fast first token.
    """
    request_started = time.perf_counter()
    
    subject = detect_subject(query)
    retriever = get_rag_components(subject)
    
    rag_content = []
    context = ""
    valid_docs = []
    
    if retriever:
        docs = retriever(query)
        valid_docs = [doc for doc in docs if doc.get('score', 0) > 0.35]
        
    fallback_mode = not bool(valid_docs)
    
    if not fallback_mode:
        for doc in valid_docs[:3]:
            source = os.path.basename(doc.get("source", "Textbook"))
            content = re.sub(r'\s+', ' ', doc.get("text", "")).strip()
            if len(content) > 400: content = content[:400] + "..."
            rag_content.append({"title": source, "content": content})
            context += f"{content}\n\n"
            
    if not context.strip():
        context = "No textbook context available."

    # Yield RAG Content immediately
    yield f"data: {json.dumps({'ragContent': rag_content})}\n\n"
    
    if fallback_mode:
        warning_msg = (
            "This topic is not available in the provided textbook context.\n\n"
            "The following explanation is AI-generated and may not exactly match your textbook.\n\n"
        )
        yield f"data: {json.dumps({'content': warning_msg})}\n\n"
    
    # Start structured task
    structured_task = asyncio.create_task(analyze_with_llm_async(query, context))
    
    # Stream explanation text
    from rag.generator import generate_llm_stream_async, get_tutor_prompt
    prompt = get_tutor_prompt(context, query, fallback_mode)
    
    async for chunk in generate_llm_stream_async(prompt):
        yield chunk
        
    # Wait for structured data to finish
    structured = await structured_task
    yield f"data: {json.dumps({'structured': structured})}\n\n"
    
    yield "data: [DONE]\n\n"


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
