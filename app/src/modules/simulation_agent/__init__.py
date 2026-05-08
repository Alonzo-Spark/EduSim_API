"""
Autonomous AI Simulation Generation Agent

This module provides autonomous generation of interactive physics, chemistry,
and mathematics simulations from natural language prompts.

Architecture:
- Prompt Analysis: Detect topic, subject, complexity, grade level
- Context Retrieval: Fetch textbook formulas, laws, definitions via RAG
- Enhanced Prompt Building: Create context-aware instructions for LLM
- HTML Generation: Use Gemini to synthesize complete interactive simulations
- Validation & Sanitization: Multi-layer security checks
- Storage & Serving: Persist generated content with metadata

Features:
✓ Autonomous prompt understanding
✓ Educational context awareness
✓ Interactive control generation
✓ Multi-subject support (physics, chemistry, astronomy, biology, mathematics)
✓ Streaming generation with progress updates
✓ HTML sanitization and security validation
✓ Metadata extraction and storage
✓ Educational annotations and formulas
"""

from .models import (
    SimulationTopic,
    SimulationInteraction,
    SimulationContext,
    AgentGenerateRequest,
    AgentGenerateResponse,
    AgentStreamingProgress,
)

from .analyzer import (
    analyze_prompt,
    generate_title_from_topic,
    extract_learning_objectives,
    extract_related_concepts,
)

from .context_builder import (
    retrieve_context,
    build_enhanced_context_prompt,
    extract_interaction_hints,
)

from .generator import (
    generate_simulation_with_agent,
    build_agent_response,
    store_agent_response,
)

from .controller import (
    agent_generate_controller,
    agent_generate_stream_controller,
)

from .agentic_models import (
    AgenticGenerateRequest,
    AgenticGenerateResponse,
    AgenticRegenerateRequest,
    SimulationBlueprint,
)

from .controller_v2 import (
    agentic_generate_controller,
    agentic_regenerate_controller,
    marketplace_list_controller,
)

__all__ = [
    # Models
    "SimulationTopic",
    "SimulationInteraction",
    "SimulationContext",
    "AgentGenerateRequest",
    "AgentGenerateResponse",
    "AgentStreamingProgress",
    # Analyzer
    "analyze_prompt",
    "generate_title_from_topic",
    "extract_learning_objectives",
    "extract_related_concepts",
    # Context Builder
    "retrieve_context",
    "build_enhanced_context_prompt",
    "extract_interaction_hints",
    # Generator
    "generate_simulation_with_agent",
    "build_agent_response",
    "store_agent_response",
    # Controller
    "agent_generate_controller",
    "agent_generate_stream_controller",
    # Multi-agent v2
    "AgenticGenerateRequest",
    "AgenticGenerateResponse",
    "AgenticRegenerateRequest",
    "SimulationBlueprint",
    "agentic_generate_controller",
    "agentic_regenerate_controller",
    "marketplace_list_controller",
]
