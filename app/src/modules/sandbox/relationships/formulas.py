"""
formulas.py
===========
Canonical educational physics formulas system for EduSim.

This module defines the formula representations used across the relationships, 
observables, and tutoring systems. It represents educational physics formulas as
reusable primitives, complete with symbolic metadata, LaTeX representations, 
SymPy expressions, and tutor-friendly explanations.

ARCHITECTURE AND DESIGN
-----------------------
1. Decoupled Primitives: Formulas do not execute physics. They are symbolic 
   declarations of mathematical relationships.
2. Symbolic Grounding: Every variable in a formula is bound to an explicit symbol 
   (e.g., 'm', 'v', 'a') and carries metadata like SI units, name, and role.
3. Extensible Design: Adding a new formula requires only defining a new instance
   of the `PhysicsFormula` model and adding it to the registry.
4. SymPy Integration: Formulas carry a `sympy_expr` or `formula_sympy` string,
   enabling computer-algebraic verification, derivative chaining (e.g., d(KE)/dv = mv),
   and algebraic rewriting (e.g., solving F=ma for a).

BEST PRACTICES
--------------
- Always provide clear default LaTeX strings for standard rendering.
- Specify units clearly in SI notation.
- Ensure that variable symbols in the formula map 1-to-1 with the `variables` metadata.

ANTI-PATTERNS TO AVOID
----------------------
- Hardcoding simulation-specific objects within a formula.
- Mixing runtime Matter.js step calculations into formula structures.
- Storing dynamic values/observables directly inside the static formula template.

FUTURE-PROOFING DECISIONS
-------------------------
- Extra parameters bag `extra_metadata` accommodates domain-specific needs
  (e.g., relativistic corrections or quantum bounds).
- Fully validated with Pydantic for automated serialization/deserialization.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class FormulaVariable(BaseModel):
    """
    Symbolic variable definition within a physics formula.
    """
    symbol: str = Field(..., description="Variable symbol, e.g. 'm', 'F', 'v'")
    name: str = Field(..., description="Human-readable variable name, e.g. 'Mass'")
    unit: str = Field(..., description="SI unit, e.g. 'kg', 'm/s', 'N'")
    description: str = Field(..., description="Educational explanation of the variable's physical meaning")
    is_dependent: bool = Field(
        default=False, 
        description="True if this is the default subject variable (left-hand side of the equation)"
    )


class PhysicsFormula(BaseModel):
    """
    canonical physics formula definition with symbolic and educational metadata.
    """
    id: str = Field(..., description="Unique formula ID, e.g. 'newtons_second_law'")
    name: str = Field(..., description="Human-readable formula name, e.g. 'Newton\\'s Second Law'")
    formula_latex: str = Field(..., description="LaTeX representation, e.g. 'F = m a'")
    formula_sympy: str = Field(..., description="SymPy-parseable formula string, e.g. 'F - m * a'")
    description: str = Field(..., description="Plain-English explanation of what this formula explains")
    variables: List[FormulaVariable] = Field(..., description="Metadata for all symbols in the formula")
    concept_tags: List[str] = Field(default_factory=list, description="Curriculum concept tags")
    extra_metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata bag")

    def get_variable(self, symbol: str) -> Optional[FormulaVariable]:
        """Retrieve a variable definition by its symbol."""
        for var in self.variables:
            if var.symbol == symbol:
                return var
        return None

    def get_dependent_variable(self) -> Optional[FormulaVariable]:
        """Retrieve the primary dependent variable (subject of the formula)."""
        for var in self.variables:
            if var.is_dependent:
                return var
        return next((var for var in self.variables), None)


# ===========================================================================
# Canonical Physics Formulas Library
# ===========================================================================

FORMULA_LIBRARY: Dict[str, PhysicsFormula] = {
    # --- Newton's Laws ---
    "newtons_second_law": PhysicsFormula(
        id="newtons_second_law",
        name="Newton's Second Law of Motion",
        formula_latex="F = m a",
        formula_sympy="F - m * a",
        description="The force applied to an object is equal to its mass multiplied by its acceleration.",
        variables=[
            FormulaVariable(symbol="F", name="Net Force", unit="N", description="Total vector force acting on the body", is_dependent=True),
            FormulaVariable(symbol="m", name="Mass", unit="kg", description="Inertial mass of the body"),
            FormulaVariable(symbol="a", name="Acceleration", unit="m/s^2", description="Rate of change of velocity")
        ],
        concept_tags=["forces", "dynamics", "motion", "newtons_laws"]
    ),
    "newtons_law_of_gravitation": PhysicsFormula(
        id="newtons_law_of_gravitation",
        name="Newton's Law of Universal Gravitation",
        formula_latex="F = G \\frac{m_1 m_2}{r^2}",
        formula_sympy="F - G * m_1 * m_2 / r**2",
        description="Every particle attracts every other particle in the universe with a force proportional to the product of their masses and inversely proportional to the square of the distance between them.",
        variables=[
            FormulaVariable(symbol="F", name="Gravitational Force", unit="N", description="Attractive force between the two masses", is_dependent=True),
            FormulaVariable(symbol="G", name="Gravitational Constant", unit="N*m^2/kg^2", description="Universal gravitational constant"),
            FormulaVariable(symbol="m_1", name="Mass 1", unit="kg", description="Mass of the first body"),
            FormulaVariable(symbol="m_2", name="Mass 2", unit="kg", description="Mass of the second body"),
            FormulaVariable(symbol="r", name="Distance", unit="m", description="Distance between the centers of mass of the two bodies")
        ],
        concept_tags=["gravity", "forces", "orbital_motion"]
    ),

    # --- Hooke's Law ---
    "hookes_law": PhysicsFormula(
        id="hookes_law",
        name="Hooke's Law",
        formula_latex="F = -k x",
        formula_sympy="F + k * x",
        description="The force needed to extend or compress a spring by some distance is proportional to that distance.",
        variables=[
            FormulaVariable(symbol="F", name="Restoring Force", unit="N", description="Force exerted by the spring", is_dependent=True),
            FormulaVariable(symbol="k", name="Spring Constant", unit="N/m", description="Stiffness of the spring"),
            FormulaVariable(symbol="x", name="Displacement", unit="m", description="Displacement of the spring from its equilibrium position")
        ],
        concept_tags=["springs", "simple_harmonic_motion", "forces"]
    ),

    # --- Energy ---
    "kinetic_energy": PhysicsFormula(
        id="kinetic_energy",
        name="Kinetic Energy",
        formula_latex="KE = \\frac{1}{2} m v^2",
        formula_sympy="KE - 0.5 * m * v**2",
        description="The energy that an object possesses due to its motion.",
        variables=[
            FormulaVariable(symbol="KE", name="Kinetic Energy", unit="J", description="Energy of motion", is_dependent=True),
            FormulaVariable(symbol="m", name="Mass", unit="kg", description="Mass of the moving object"),
            FormulaVariable(symbol="v", name="Velocity", unit="m/s", description="Speed of the moving object")
        ],
        concept_tags=["energy", "dynamics", "kinematics"]
    ),
    "gravitational_potential_energy": PhysicsFormula(
        id="gravitational_potential_energy",
        name="Gravitational Potential Energy",
        formula_latex="PE = m g h",
        formula_sympy="PE - m * g * h",
        description="The energy stored in an object as a result of its vertical position or height.",
        variables=[
            FormulaVariable(symbol="PE", name="Potential Energy", unit="J", description="Energy of position", is_dependent=True),
            FormulaVariable(symbol="m", name="Mass", unit="kg", description="Mass of the body"),
            FormulaVariable(symbol="g", name="Gravitational Acceleration", unit="m/s^2", description="Local acceleration due to gravity"),
            FormulaVariable(symbol="h", name="Height", unit="m", description="Height above a reference point")
        ],
        concept_tags=["energy", "gravity"]
    ),

    # --- Circular & Pendulum Motion ---
    "circular_acceleration": PhysicsFormula(
        id="circular_acceleration",
        name="Centripetal Acceleration",
        formula_latex="a_c = \\frac{v^2}{r}",
        formula_sympy="a_c - v**2 / r",
        description="The acceleration of an object moving in a circle of radius r at a constant speed v.",
        variables=[
            FormulaVariable(symbol="a_c", name="Centripetal Acceleration", unit="m/s^2", description="Acceleration directed toward the center of curvature", is_dependent=True),
            FormulaVariable(symbol="v", name="Linear Velocity", unit="m/s", description="Tangential speed of the object"),
            FormulaVariable(symbol="r", name="Radius", unit="m", description="Radius of the circular path")
        ],
        concept_tags=["circular_motion", "kinematics"]
    ),
    "pendulum_period": PhysicsFormula(
        id="pendulum_period",
        name="Simple Pendulum Period",
        formula_latex="T = 2 \\pi \\sqrt{\\frac{L}{g}}",
        formula_sympy="T - 2 * pi * sqrt(L / g)",
        description="The time for one complete cycle of a simple pendulum is determined solely by its length and gravitational acceleration.",
        variables=[
            FormulaVariable(symbol="T", name="Period", unit="s", description="Time for one complete oscillation", is_dependent=True),
            FormulaVariable(symbol="L", name="Length", unit="m", description="Length of the pendulum string/arm"),
            FormulaVariable(symbol="g", name="Gravitational Acceleration", unit="m/s^2", description="Local acceleration due to gravity")
        ],
        concept_tags=["pendulum", "simple_harmonic_motion", "oscillation"]
    ),

    # --- Momentum ---
    "momentum": PhysicsFormula(
        id="momentum",
        name="Linear Momentum",
        formula_latex="p = m v",
        formula_sympy="p - m * v",
        description="The product of the mass and velocity of an object.",
        variables=[
            FormulaVariable(symbol="p", name="Momentum", unit="kg*m/s", description="Linear momentum vector", is_dependent=True),
            FormulaVariable(symbol="m", name="Mass", unit="kg", description="Mass of the body"),
            FormulaVariable(symbol="v", name="Velocity", unit="m/s", description="Velocity of the body")
        ],
        concept_tags=["momentum", "collisions", "dynamics"]
    ),

    # --- Drag & Resistance ---
    "drag_force": PhysicsFormula(
        id="drag_force",
        name="Fluid Drag Force",
        formula_latex="F_d = \\frac{1}{2} \\rho v^2 C_d A",
        formula_sympy="F_d - 0.5 * rho * v**2 * C_d * A",
        description="The force acting opposite to the relative motion of any object moving with respect to a surrounding fluid.",
        variables=[
            FormulaVariable(symbol="F_d", name="Drag Force", unit="N", description="Resistive force of the fluid", is_dependent=True),
            FormulaVariable(symbol="rho", name="Fluid Density", unit="kg/m^3", description="Density of the surrounding fluid"),
            FormulaVariable(symbol="v", name="Relative Velocity", unit="m/s", description="Velocity of the object relative to the fluid"),
            FormulaVariable(symbol="C_d", name="Drag Coefficient", unit="dimensionless", description="Dimensionless coefficient representing shape resistance"),
            FormulaVariable(symbol="A", name="Cross-sectional Area", unit="m^2", description="Orthogonal projected cross-sectional area of the body")
        ],
        concept_tags=["drag", "fluids", "aerodynamics", "forces"]
    ),

    # --- Angular Motion ---
    "angular_torque": PhysicsFormula(
        id="angular_torque",
        name="Rotational Second Law",
        formula_latex="\\tau = I \\alpha",
        formula_sympy="tau - I * alpha",
        description="The net torque acting on a rotating rigid body is equal to its moment of inertia times its angular acceleration.",
        variables=[
            FormulaVariable(symbol="tau", name="Torque", unit="N*m", description="Rotational force or torque", is_dependent=True),
            FormulaVariable(symbol="I", name="Moment of Inertia", unit="kg*m^2", description="Rotational mass of the body"),
            FormulaVariable(symbol="alpha", name="Angular Acceleration", unit="rad/s^2", description="Rate of change of angular velocity")
        ],
        concept_tags=["angular_motion", "dynamics", "rotation"]
    ),
}
