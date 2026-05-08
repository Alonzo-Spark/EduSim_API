# Autonomous AI Simulation Generation Agent - Quick Start Guide

## What is the AI Agent?

The Autonomous AI Simulation Generation Agent is a system that converts natural language prompts into interactive educational simulations. Just describe what you want to learn, and the agent automatically:

1. **Analyzes** your prompt to understand the topic
2. **Retrieves** formulas and context from textbooks
3. **Generates** complete interactive HTML simulations
4. **Validates** safety and educational quality
5. **Renders** in the browser with full interactivity

## Quick Start

### For Users (Frontend)

1. **Navigate** to `http://localhost:5173/ai-agent`

2. **Enter a prompt**:
   ```
   "Create a projectile motion simulation showing trajectory"
   ```

3. **Choose complexity**: Beginner, Medium, or Advanced

4. **Click "Generate Simulation"**

5. **Watch progress** as the agent generates your simulation

6. **Interact** with the generated simulation using sliders and controls

### Example Prompts

**Physics**:
- "Create a projectile motion simulation with adjustable angle and velocity"
- "Show Newton's Third Law with collision demonstrations"
- "Generate a pendulum experiment with variable length"
- "Simulate momentum conservation in collisions"

**Chemistry**:
- "Visualize molecular bonding in water"
- "Show electron configuration in atoms"
- "Animate chemical reaction mechanism"

**Astronomy**:
- "Simulate planetary orbits around the sun"
- "Show gravitational force between objects"

**Biology**:
- "Visualize cell organelle structures"
- "Show photosynthesis process step-by-step"

**Mathematics**:
- "Graph polynomial functions with interactive coefficients"
- "Show derivative and slope visualization"

## For Developers

### Backend Setup

1. **Install dependencies**:
   ```bash
   pip install -r app/requirements.txt
   ```

2. **Set environment variables**:
   ```bash
   # .env file
   GOOGLE_API_KEY=your_gemini_api_key
   ```

3. **Start backend**:
   ```bash
   cd edusim
   uvicorn main:app --reload
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd EduSim_frontend
   npm install
   ```

2. **Set environment variables** (`.env.local`):
   ```
   VITE_API_URL=http://localhost:8000
   ```

3. **Start frontend**:
   ```bash
   npm run dev
   ```

### API Endpoints

#### Non-Streaming Generation
```bash
POST /api/simulations/agent/generate

{
  "prompt": "Create a projectile motion simulation",
  "complexity": "medium",
  "topic": null
}
```

#### Streaming Generation
```bash
POST /api/simulations/agent/generate-stream

{
  "prompt": "Create a projectile motion simulation",
  "complexity": "medium",
  "streaming": true
}
```

## Architecture

```
┌─────────────────────────────────────┐
│   User Prompt (Natural Language)    │
└────────────────┬────────────────────┘
                 │
         ┌───────▼────────┐
         │ Prompt Analysis│
         │ - Topic        │
         │ - Subject      │
         │ - Complexity   │
         └───────┬────────┘
                 │
      ┌──────────▼──────────┐
      │  RAG Context Query  │
      │ - Formulas          │
      │ - Constants         │
      │ - Laws              │
      │ - Definitions       │
      └──────────┬──────────┘
                 │
     ┌───────────▼───────────┐
     │ Enhanced Prompt Build │
     │ (Context-aware LLM)   │
     └───────────┬───────────┘
                 │
        ┌────────▼────────┐
        │ Gemini API Call │
        │ HTML Generation │
        └────────┬────────┘
                 │
    ┌────────────▼────────────┐
    │ Security Validation     │
    │ - Regex checks          │
    │ - BeautifulSoup sanitize│
    │ - CSP injection         │
    └────────────┬────────────┘
                 │
        ┌────────▼────────┐
        │ Persist & Store │
        │ Metadata + HTML │
        └────────┬────────┘
                 │
      ┌──────────▼──────────┐
      │ Return Response     │
      │ - HTML simulation   │
      │ - Metadata          │
      │ - Learning objects  │
      └──────────┬──────────┘
                 │
        ┌────────▼────────┐
        │  Render in      │
        │  iframe sandbox │
        └────────────────┘
```

## Key Features

### Automatic Prompt Understanding
- Detects physics, chemistry, astronomy, biology, mathematics topics
- Identifies complexity level (beginner/medium/advanced)
- Infers grade level from context
- Suggests interactive controls

### Educational Context
- RAG-powered formula retrieval
- Textbook law and principle extraction
- Constant and definition lookup
- Source attribution and citations

### Multi-Layer Security
- Regex validation (18 security patterns)
- BeautifulSoup HTML sanitization
- Content-Security-Policy injection
- iframe sandbox isolation

### Interactive Controls
- Automatic parameter detection
- Slider generation with ranges
- Play/pause/reset buttons
- Real-time value displays
- Unit-aware inputs

### Streaming Progress
- Real-time progress updates
- Stage-by-stage visualization
- Percentage indicator
- Detailed status messages

## Project Structure

### Backend
```
app/src/modules/simulation_agent/
├── __init__.py          # Module exports
├── models.py            # Pydantic data models
├── analyzer.py          # Prompt analysis
├── context_builder.py   # RAG context retrieval
├── generator.py         # HTML generation
└── controller.py        # FastAPI handlers
```

### Frontend
```
EduSim_frontend/src/
├── services/
│   └── agentSimulationService.ts  # API client
├── hooks/
│   └── useAgentSimulation.ts      # State management
└── routes/
    └── ai-agent.tsx               # UI component
```

## Response Format

### Successful Generation
```json
{
  "success": true,
  "id": "uuid-string",
  "title": "Projectile Motion Simulation",
  "description": "AI-synthesized interactive simulation...",
  "topic": {
    "topic": "projectile motion",
    "subject": "physics",
    "complexity": "medium"
  },
  "html": "<!DOCTYPE html>...",
  "formulas": ["v = u + at", "s = ut + 0.5at²"],
  "learning_objectives": [
    "Understand projectile motion",
    "Apply kinematic equations"
  ],
  "related_concepts": [
    "Kinematics",
    "Vectors",
    "Gravity"
  ],
  "interactions": [
    {
      "name": "angle",
      "label": "Launch Angle",
      "type": "slider",
      "min": 0,
      "max": 90,
      "unit": "°"
    }
  ],
  "context": {
    "topic": "projectile motion",
    "formulas": [...],
    "constants": [...],
    "laws": [...],
    "sources": [...]
  },
  "timestamp": "2026-05-08T...",
  "generation_stages": [...]
}
```

## Troubleshooting

### "Generation failed"
- Check that `GOOGLE_API_KEY` is set in `.env`
- Verify RAG index files exist in `faiss_index/`
- Check backend logs for detailed errors

### "HTML failed safety validation"
- The generated HTML contains blocked patterns
- Check browser console for safety violations
- Verify CSP headers are present

### "Streaming not working"
- Check browser compatibility (needs ReadableStream support)
- Verify CORS settings in FastAPI
- Check network tab for failed requests

### Simulation doesn't render
- Check that iframe content is visible
- Verify srcDoc attribute is set
- Check browser security warnings

## Performance Tips

- **Use Streaming Mode** for real-time progress visibility
- **Beginner Complexity** generates faster (~3s)
- **Medium Complexity** takes ~4-5s
- **Advanced Complexity** takes ~5-6s
- Streaming adds ~500ms overhead

## Limitations

- Requires active GOOGLE_API_KEY for generation
- RAG requires pre-built FAISS index
- HTML must be self-contained (no external resources)
- Sandbox limits network access
- Canvas-based simulations only

## Future Enhancements

- [ ] Database persistence of simulations
- [ ] Advanced search and filtering
- [ ] Simulation remix/regeneration
- [ ] Thumbnail generation
- [ ] Curriculum linking
- [ ] Multi-language support
- [ ] Performance analytics

## Support

For issues or feature requests, refer to:
- Backend logs: `edusim/logs/`
- Frontend console: Browser DevTools
- API documentation: Interactive Swagger at `http://localhost:8000/docs`

## License

Part of EduSim Odyssey educational platform.
