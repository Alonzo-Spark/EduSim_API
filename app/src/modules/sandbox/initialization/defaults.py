"""
defaults.py
===========
Centralized repository for default physical, rendering, camera, and simulation values 
across all EduSim scenarios.

These defaults ensure that when the AI synthesis or user configuration provides a partial 
specification, the system safely falls back to standard, stable, and educational values.
"""

from typing import Dict, Any

# --- Physical Defaults ---
DEFAULT_GRAVITY_X: float = 0.0
DEFAULT_GRAVITY_Y: float = 9.81
DEFAULT_GRAVITY_SCALE: float = 1.0

DEFAULT_FRICTION: float = 0.1
DEFAULT_FRICTION_STATIC: float = 0.05
DEFAULT_RESTITUTION: float = 0.5
DEFAULT_DENSITY: float = 0.001   # kg/px^2 in local space normalization
DEFAULT_MASS: float = 1.0
DEFAULT_GRAVITY_SCALE_BODY: float = 1.0
DEFAULT_AIR_RESISTANCE: float = 0.01

# --- Geometric & Scaling Defaults ---
DEFAULT_PIXELS_PER_METER: float = 100.0
DEFAULT_CANVAS_WIDTH: int = 1280
DEFAULT_CANVAS_HEIGHT: int = 720

# --- Camera & Rendering Defaults ---
DEFAULT_CAMERA_ZOOM: float = 1.0
DEFAULT_CAMERA_OFFSET_X: float = 0.0
DEFAULT_CAMERA_OFFSET_Y: float = 0.0

DEFAULT_COLOR_CIRCLE: str = "#FF5733"      # Vibrant Orange
DEFAULT_COLOR_RECTANGLE: str = "#3A86FF"   # Sleek Blue
DEFAULT_COLOR_POLYGON: str = "#8338EC"     # Deep Purple
DEFAULT_COLOR_STATIC: str = "#4A4E69"      # Steel Slate
DEFAULT_COLOR_SENSOR: str = "#38B000"      # Translucent Green

# --- Simulation Controls & Timesteps ---
DEFAULT_SIMULATION_SPEED: float = 1.0
DEFAULT_MAX_FPS: int = 60
DEFAULT_SUBSTEPS: int = 1
DEFAULT_SHOW_DEBUG_OVERLAY: bool = False
DEFAULT_ENABLE_SLEEPING: bool = True

# --- Default Aggregate Payload Bags ---
DEFAULT_PHYSICS_PROPERTIES: Dict[str, Any] = {
    "mass": DEFAULT_MASS,
    "restitution": DEFAULT_RESTITUTION,
    "friction": DEFAULT_FRICTION,
    "friction_static": DEFAULT_FRICTION_STATIC,
    "density": None,
    "is_sensor": False,
    "gravity_scale": DEFAULT_GRAVITY_SCALE_BODY,
    "drag_coefficient": 0.47,
    "cross_sectional_area": 0.1
}

DEFAULT_VISUAL_HINTS: Dict[str, Any] = {
    "color": None,
    "tint": None,
    "texture_key": None,
    "z_index": 0,
    "visible": True,
    "opacity": 1.0,
    "label": None
}

DEFAULT_RUNTIME_METADATA: Dict[str, Any] = {
    "initial_velocity": {"x": 0.0, "y": 0.0},
    "initial_angle": 0.0,
    "initial_angular_vel": 0.0,
    "air_resistance": DEFAULT_AIR_RESISTANCE,
    "is_sleeping": False,
    "collision_filter": {"category": 0x0001, "mask": 0xFFFF, "group": 0}
}
