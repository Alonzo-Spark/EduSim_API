TOPIC_ALIASES = {
    # Gravity
    "free_fall": "gravity",
    "falling_objects": "gravity",
    "weight": "gravity",
    
    # Collisions
    "impact": "collisions",
    "crash": "collisions",
    "collision": "collisions",
    
    # Projectile Motion
    "projectile": "projectile_motion",
    "trajectory": "projectile_motion",
    "launch": "projectile_motion",
    
    # Hooke's Law & Springs
    "spring": "hookes_law",
    "elasticity": "hookes_law",
    "oscillation": "hookes_law",
    
    # Pendulum
    "swing": "pendulum",
    
    # Friction
    "sliding": "friction",
    "rough_surface": "friction",
    
    # Inclined Plane
    "ramp": "inclined_plane",
    "slope": "inclined_plane",
    "incline": "inclined_plane",
    
    # Momentum & Impulse
    "momentum": "momentum",
    "impulse": "impulse",
    
    # Energy Conservation
    "energy": "energy_conservation",
    "kinetic_energy": "energy_conservation",
    "potential_energy": "energy_conservation",
    
    # Rotational & Circular Motion
    "orbit": "circular_motion",
    "spinning": "circular_motion",
    "rotation": "rotational_motion",
    "torque": "rotational_motion",
    
    # Buoyancy
    "floating": "buoyancy",
    "sinking": "buoyancy",
    
    # Wave Motion
    "wave": "wave_motion",
    "ripple": "wave_motion",
    
    # Electricity
    "charge": "electricity",
    "circuit": "electricity",
    "electrostatic": "electricity"
}

def normalize_topic(topic: str):
    topic = topic.lower().strip()
    return TOPIC_ALIASES.get(topic, topic)
