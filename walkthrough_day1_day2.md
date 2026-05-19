# Walkthrough Report: Day 1 & Day 2 Backend Refactor

This report documents the architectural setup and foundational retrieval work completed during **Day 1**, **Day 1.5**, and **Day 2** for the EduSim structured Educational Intelligence Engine.

---

## 📂 1. Directory Structure Implemented

The new RAG and curriculum retrieval system is isolated cleanly inside `app/src/rag/`:

```
app/src/rag/
├── __init__.py
├── controller.py          # FastAPI Routing
├── service.py             # Service Layer Aggregator
├── retriever.py           # Curriculum JSON Loader & Retrievers
├── topic_classifier.py    # Architecture Placeholder
├── payload_builder.py     # Architecture Placeholder
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

## 🛠️ 2. Step-by-Step Implementation Details

### Day 1 & 1.5: Schema & Routing Foundations
1. **Pydantic Schemas**:
   * `FormulaSchema`: Holds `name`, `latex`, and `explanation`.
   * `ExperimentSchema`: Holds `title` and `description`.
   * `HintSchema`: Holds `text`.
   * `TopicRequest`: Strictly types the incoming JSON payload for request validation.
   * `EducationalPayload`: Models the final aggregated response payload as the main contract between the frontend and backend.
2. **FastAPI Routing (`controller.py`)**:
   * Registers the `/educational/topic` POST endpoint.
   * Configured `response_model=EducationalPayload` to enforce strict OpenAPI schema type definitions.
3. **Shadowing Resolution (`main.py`)**:
   * Integrated the new controller router into the main application.
   * Prioritized `app/src/modules/` search path over `app/src/` within `sys.path` to avoid naming namespace conflicts with legacy RAG imports.

### Day 2: Retrieval & Aggregation Foundations
1. **Curriculum Database**:
   * Populated structural concept definitions, formulas, misconceptions, sandbox experiments, and pedagogical hints for both **`gravity`** and **`pendulum`**.
2. **Curriculum Loader (`retriever.py`)**:
   * Implemented localized retrievers to read target JSON definitions dynamically from disk.
3. **Payload Aggregator (`service.py`)**:
   * Updated the service layer to coordinate element retrievals and bundle them into the expected `EducationalPayload` contract schema.

---

## 🧪 3. Validation and Output Verification

The API was fully validated using both direct `curl` commands and the live interactive **FastAPI Swagger UI (/docs)**.

### Gravity Topic Verification
* **Request**:
  ```bash
  curl -X POST http://127.0.0.1:8000/educational/topic \
       -H "Content-Type: application/json" \
       -d '{"topic": "gravity"}'
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
      "free_fall"
    ]
  }
  ```

### Pendulum Topic Verification
* **Request**:
  ```bash
  curl -X POST http://127.0.0.1:8000/educational/topic \
       -H "Content-Type: application/json" \
       -d '{"topic": "pendulum"}'
  ```
* **Output Response**:
  ```json
  {
    "topic": "pendulum",
    "concept_explanation": "A pendulum is a weight suspended from a pivot so that it can swing freely.",
    "formulas": [
      {
        "name": "Pendulum Period",
        "latex": "T = 2\\pi\\sqrt{\\frac{L}{g}}",
        "explanation": "The pendulum period depends on rope length and gravity."
      }
    ],
    "misconceptions": [
      "The period depends on the mass of the bob.",
      "A larger amplitude always increases the period significantly."
    ],
    "experiments": [
      {
        "title": "Period vs Length Experiment",
        "description": "Measure the period of the pendulum with different lengths of the string while keeping the mass constant."
      }
    ],
    "observables": [
      "period",
      "length",
      "angle"
    ],
    "hints": [
      {
        "text": "Notice how changes in the bob's mass do not alter the time taken for one full swing."
      }
    ],
    "assets": [
      "pivot",
      "string",
      "bob"
    ],
    "relationships": [
      "simple_harmonic_motion"
    ]
  }
  ```

---

> [!NOTE]
> The Educational Intelligence Engine has a solid retrieval base, complete payload compliance, and is fully configured for future semantic expansion!
