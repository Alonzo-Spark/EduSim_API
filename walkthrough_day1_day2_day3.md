# Walkthrough Report: Day 1, Day 2 & Day 3 Backend Refactor

This report documents the architectural setup, foundational curriculum retrievals, and completed retrieval intelligence layers across **Day 1**, **Day 1.5**, **Day 2**, and **Day 3** for the EduSim structured Educational Intelligence Engine.

---

## 📂 1. Directory Structure Implemented

The completed metadata-aware RAG retrieval system is isolated cleanly inside `app/src/rag/`:

```
app/src/rag/
├── __init__.py
├── controller.py          # FastAPI Routing
├── service.py             # Service Layer Aggregator (Topic Normalization integrated)
├── retriever.py           # Curriculum JSON Loader, Retrievers & Fallbacks
├── topic_classifier.py    # Topic Alias Normalization mapping
├── payload_builder.py     # Architecture Placeholder
│
├── registry/              # Semantic Relationship Store
│   └── relationship_registry.json
│
├── schemas/               # Pydantic Schemas
│   ├── __init__.py
│   ├── educational_payload.py
│   ├── formula_schema.py
│   ├── experiment_schema.py
│   ├── hint_schema.py
│   └── topic_request.py
│
└── curriculum/            # Static Curriculum Database
    ├── concepts/
    │   ├── default.json   # Safe fallback concept
    │   ├── gravity.json
    │   └── pendulum.json
    ├── formulas/
    │   ├── gravity.json
    │   └── pendulum.json
    ├── misconceptions/
    │   ├── gravity.json
    │   └── pendulum.json
    ├── experiments/
    │   ├── gravity.json
    │   └── pendulum.json
    └── hints/
        ├── gravity.json
        └── pendulum.json
```

---

## 🛠️ 2. Phase-by-Phase Implementation Details

### Day 1 & 1.5: Schema & Routing Foundations
1. **Pydantic Schemas**:
   * `FormulaSchema`, `ExperimentSchema`, `HintSchema`.
   * `TopicRequest`: Strictly types the incoming JSON request parameter `topic`.
   * `EducationalPayload`: Models the complete unified payload returned to the client.
2. **FastAPI Routing (`controller.py`)**:
   * Mapped `POST /educational/topic` using `response_model=EducationalPayload` for automatic validation and OpenAPI correctness.

### Day 2: Retrieval & Aggregation Foundations
1. **Curriculum Database**: Created filesystem sheets containing comprehensive structures for `gravity` and `pendulum`.
2. **Curriculum Loader & Service Layer**: Integrated retrievers in `retriever.py` and aggregated retrieved blocks in `service.py`.

### Day 3: Retrieval Intelligence + Metadata System
1. **Curriculum Metadata**: Appended rich parameters (`topic`, `aliases`, `difficulty`, `relationships`, `type`) across all curriculum files for gravity and pendulum.
2. **Topic Normalization (`topic_classifier.py`)**:
   * Maps alternative search strings (`free_fall`, `falling_objects`, `weight` -> `gravity`; `swing`, `oscillation` -> `pendulum`).
   * Resolves search inputs casing/whitespace variations safely.
3. **Safe Fallback Frameworks (`retriever.py` & default.json)**:
   * Created `default.json` holding fallback messages.
   * Configured all retrievers to return safe standard fallbacks instead of causing server exceptions when an unknown topic is requested.
4. **Relationship Registry**:
   * Created `/registry/relationship_registry.json` mapping relationship hooks.
5. **Metadata helper (`retriever.py`)**:
   * Created `build_metadata` mapping relationships/difficulty to future-proof adaptive tutoring engines.

---

## 🧪 3. Validation and Output Verification

Testing was performed directly in the FastAPI active workspace and verified using `curl`:

### 1. Alias Normalization Verification (free_fall -> gravity)
* **Request**:
  ```bash
  curl -X POST http://127.0.0.1:8000/educational/topic \
       -H "Content-Type: application/json" \
       -d '{"topic": "free_fall"}'
  ```
* **Output Response**:
  ```json
  {
    "topic": "gravity",
    "concept_explanation": "Gravity is a force that attracts objects toward Earth.",
    "formulas": [
      {
        "name": "Weight Formula",
        "latex": "F = mg",
        "explanation": "Weight equals mass multiplied by gravity."
      }
    ],
    "misconceptions": [
      "Heavier objects fall faster."
    ],
    "experiments": [
      {
        "title": "Free Fall Test",
        "description": "Drop two balls of different masses."
      }
    ],
    "observables": [
      "velocity",
      "acceleration"
    ],
    "hints": [
      {
        "text": "Observe how acceleration remains constant."
      }
    ],
    "assets": [
      "earth",
      "ball"
    ],
    "relationships": [
      "free_fall",
      "weight"
    ]
  }
  ```

### 2. Unknown Fallback Verification (quantum_banana -> default)
* **Request**:
  ```bash
  curl -X POST http://127.0.0.1:8000/educational/topic \
       -H "Content-Type: application/json" \
       -d '{"topic": "quantum_banana"}'
  ```
* **Output Response**:
  ```json
  {
    "topic": "quantum_banana",
    "concept_explanation": "Educational content is currently unavailable.",
    "formulas": [],
    "misconceptions": [],
    "experiments": [],
    "observables": [],
    "hints": [],
    "assets": [],
    "relationships": []
  }
  ```

---

> [!NOTE]
> The backend is now officially a metadata-aware educational intelligence engine.
