"""
Subject-specific synthesis prompt templates for EduSim Simulation Synthesis System.
Each template emphasizes different educational visualization approaches for its domain.
"""

import re
from typing import Literal

SubjectType = Literal["physics", "chemistry", "astronomy", "biology", "mathematics"]


def detect_subject(prompt: str) -> SubjectType:
    """
    Automatically detect the subject/domain from the user prompt.
    Returns the detected subject or 'physics' as default.
    """
    lowered = prompt.lower()

    # Physics keywords
    physics_keywords = [
        "motion", "velocity", "acceleration", "force", "newton", "momentum",
        "energy", "kinetic", "potential", "gravity", "gravitational",
        "pendulum", "projectile", "collision", "friction", "tension",
        "wave", "oscillation", "frequency", "amplitude", "drag",
        "momentum conservation", "elastic", "inelastic", "circular motion",
        "centripetal", "torque", "angular", "rotation", "lever",
        "simple harmonic", "spring", "hooke", "displacement", "vector",
    ]
    
    # Chemistry keywords
    chemistry_keywords = [
        "molecule", "atom", "chemical", "element", "bond", "reaction",
        "oxidation", "reduction", "electron", "ion", "orbital", "valence",
        "acid", "base", "ph", "salt", "compound", "mixture", "solution",
        "concentration", "molarity", "atomic structure", "periodic table",
        "isotope", "radioactive", "polymer", "hydrocarbon", "alcohol",
        "amine", "carboxylic", "ester", "amide", "protein", "nucleic",
    ]
    
    # Astronomy keywords
    astronomy_keywords = [
        "orbit", "orbital", "planet", "star", "galaxy", "moon", "comet",
        "asteroid", "celestial", "solar system", "universe", "space",
        "gravity", "gravitational", "sun", "earth", "mars", "jupiter",
        "supernova", "nebula", "black hole", "dark matter", "cosmic",
        "eclipse", "rotation", "revolution", "kepler", "astronomy",
    ]
    
    # Biology keywords
    biology_keywords = [
        "cell", "dna", "protein", "enzyme", "photosynthesis", "respiration",
        "mitochondria", "chloroplast", "organ", "tissue", "system",
        "evolution", "mutation", "gene", "chromosome", "reproduction",
        "immune", "nervous", "circulatory", "digestive", "endocrine",
        "organism", "species", "ecosystem", "metabolism", "homeostasis",
        "anatomy", "physiology", "cell division", "meiosis", "mitosis",
    ]
    
    # Mathematics keywords
    mathematics_keywords = [
        "function", "graph", "equation", "calculus", "integral", "derivative",
        "limit", "series", "vector", "matrix", "algebra", "geometry",
        "trigonometry", "sine", "cosine", "tangent", "polynomial",
        "parabola", "hyperbola", "ellipse", "circle", "line",
        "probability", "statistics", "distribution", "linear", "quadratic",
        "exponential", "logarithm", "transform", "fourier",
    ]

    # Score each subject based on keyword matches
    scores = {
        "physics": sum(1 for kw in physics_keywords if kw in lowered),
        "chemistry": sum(1 for kw in chemistry_keywords if kw in lowered),
        "astronomy": sum(1 for kw in astronomy_keywords if kw in lowered),
        "biology": sum(1 for kw in biology_keywords if kw in lowered),
        "mathematics": sum(1 for kw in mathematics_keywords if kw in lowered),
    }

    # Return subject with highest score, or physics as default
    detected = max(scores, key=scores.get)
    return detected if scores[detected] > 0 else "physics"


def get_system_prompt(subject: SubjectType) -> str:
    """
    Return subject-specific system prompt for Gemini LLM synthesis.
    Each template emphasizes domain-specific visualization and interaction patterns.
    """
    
    base_requirements = (
        "You are Simulation Synthesis System for EduSim. "
        "Generate ONLY raw HTML (single self-contained document) for an interactive educational simulation. "
        "Do not return markdown, code fences, or explanation text.\n"
        "Base Requirements:\n"
        "- Use Canvas-based animation and plain HTML/CSS/JavaScript only.\n"
        "- Dark futuristic UI with clear educational overlays, labels, formulas, and controls.\n"
        "- Responsive layout for desktop and mobile.\n"
        "- Include sliders/playback controls and real-time updates.\n"
        "- No external dependencies and no network access.\n"
        "- Avoid eval, new Function, fetch, XMLHttpRequest, WebSocket, window.open, top navigation.\n"
        "- Use textbook terminology and keep equations/models accurate.\n"
        "- Add short educational annotations near visual elements.\n"
        "- Include a concise title and one-line concept summary in the UI.\n"
    )

    subject_prompts = {
        "physics": (
            base_requirements +
            "Physics-Specific Requirements:\n"
            "- Animate motion with velocity vectors and acceleration arrows.\n"
            "- Use color-coded force vectors (red=applied, blue=gravity, green=friction).\n"
            "- Show trajectory paths and collision detection visually.\n"
            "- Include real-time measurements: velocity, displacement, energy, momentum.\n"
            "- Use Canvas 2D with smooth requestAnimationFrame animations.\n"
            "- Emphasize Newton's laws, energy conservation, momentum conservation in labels.\n"
            "- Add interactive sliders for initial conditions (angle, velocity, mass).\n"
            "- Display equations of motion and calculated values prominently.\n"
            "- Show reference grids and scale indicators for spatial accuracy.\n"
        ),
        
        "chemistry": (
            base_requirements +
            "Chemistry-Specific Requirements:\n"
            "- Render atoms as circles with nucleus + electron shells/orbits.\n"
            "- Use color-coding for different elements (H=white, C=black, O=red, N=blue).\n"
            "- Animate electron orbitals and bonding interactions.\n"
            "- Show molecular structure with bonds (single=line, double=parallel lines).\n"
            "- Display atomic number, mass, electrons, and valence clearly.\n"
            "- Animate reaction sequences: reactants → products with energy visualization.\n"
            "- Include oxidation state labels and electron transfer arrows.\n"
            "- Use Canvas to draw 3D-like ball-and-stick or space-filling models.\n"
            "- Add pH scale, molarity, concentration sliders as interactive parameters.\n"
        ),
        
        "astronomy": (
            base_requirements +
            "Astronomy-Specific Requirements:\n"
            "- Render orbital mechanics with gravity field visualization.\n"
            "- Use circular orbits or Kepler ellipse paths with accurate scaling.\n"
            "- Color stars/planets realistically and show scale references.\n"
            "- Animate orbital motion with angular velocity calculated from Kepler's laws.\n"
            "- Display orbital parameters: semi-major axis, eccentricity, period, inclination.\n"
            "- Show gravitational force vectors and acceleration toward central body.\n"
            "- Include time-stepping controls (pause, play, speed-up).\n"
            "- Add constellation or solar system context.\n"
            "- Use Canvas with filled circles and rotation transforms for smooth animation.\n"
        ),
        
        "biology": (
            base_requirements +
            "Biology-Specific Requirements:\n"
            "- Render cell structures with organelles: nucleus, mitochondria, chloroplast, ER, etc.\n"
            "- Use color-coding for different cellular components.\n"
            "- Animate cellular processes: photosynthesis, respiration, cell division, protein synthesis.\n"
            "- Show molecular flow: glucose → ATP, CO2 fixation, DNA replication.\n"
            "- Display anatomical systems with organ connectivity (circulatory, nervous, digestive).\n"
            "- Include interactive controls to show/hide layers or cellular structures.\n"
            "- Add legend and labels for all biological components.\n"
            "- Use Canvas to draw organelles, cells, and tissue structures.\n"
            "- Emphasize biological accuracy and textbook terminology.\n"
        ),
        
        "mathematics": (
            base_requirements +
            "Mathematics-Specific Requirements:\n"
            "- Plot functions as curves on a Cartesian coordinate system.\n"
            "- Show axes with tick marks, labels, and gridlines.\n"
            "- Animate transformations: translation, scaling, rotation of functions.\n"
            "- Display equation in standard form near the graph (y = mx + b, etc.).\n"
            "- Include interactive sliders for coefficients (a, b, c) to modify functions in real-time.\n"
            "- Show key points: roots, vertex, asymptotes, inflection points.\n"
            "- Use color-coding for different functions if comparing multiple graphs.\n"
            "- Add derivative/integral visualization for calculus topics.\n"
            "- Use Canvas for smooth curve rendering with anti-aliasing.\n"
            "- Include numerical values and formulas prominently.\n"
        ),
    }

    return subject_prompts.get(subject, subject_prompts["physics"])


def get_user_content_enhancement(subject: SubjectType, extracted: dict) -> str:
    """
    Return subject-specific enhancement to the user content message.
    Guides the LLM to prioritize certain extracted features.
    """
    
    enhancements = {
        "physics": (
            "Subject Context: Physics/Mechanics\n"
            "Prioritize visualization of: motion, vectors, forces, energy conservation.\n"
            f"Key formulas to use prominently: {extracted.get('formulas', [])}\n"
            f"Constants: {extracted.get('constants', [])}\n"
            f"Laws: {extracted.get('laws', [])}\n"
            "Render interactive sliders for initial conditions.\n"
        ),
        
        "chemistry": (
            "Subject Context: Chemistry/Molecular Structure\n"
            "Prioritize visualization of: atoms, bonds, electron configuration, reactions.\n"
            f"Molecular components: {extracted.get('formulas', [])}\n"
            f"Constants (atomic weights, charges): {extracted.get('constants', [])}\n"
            f"Chemical principles: {extracted.get('definitions', [])}\n"
            "Use color-coded atoms and animated bonding.\n"
        ),
        
        "astronomy": (
            "Subject Context: Astronomy/Orbital Mechanics\n"
            "Prioritize visualization of: orbits, gravity, celestial motion, Kepler's laws.\n"
            f"Orbital parameters: {extracted.get('formulas', [])}\n"
            f"Constants (G, masses, distances): {extracted.get('constants', [])}\n"
            f"Laws of motion: {extracted.get('laws', [])}\n"
            "Animate smooth orbital paths with accurate physics.\n"
        ),
        
        "biology": (
            "Subject Context: Biology/Cell/Organism Structure\n"
            "Prioritize visualization of: cells, organelles, biological processes, anatomy.\n"
            f"Biological components/processes: {extracted.get('formulas', [])}\n"
            f"Biological parameters: {extracted.get('constants', [])}\n"
            f"Key definitions: {extracted.get('definitions', [])}\n"
            "Use color-coded organelles and animated processes.\n"
        ),
        
        "mathematics": (
            "Subject Context: Mathematics/Functions/Calculus\n"
            "Prioritize visualization of: graphs, functions, transformations, key points.\n"
            f"Functions and equations: {extracted.get('formulas', [])}\n"
            f"Key values (slopes, intercepts, roots): {extracted.get('constants', [])}\n"
            f"Mathematical principles: {extracted.get('laws', [])}\n"
            "Use interactive sliders to explore parameter changes in real-time.\n"
        ),
    }

    return enhancements.get(subject, enhancements["physics"])
