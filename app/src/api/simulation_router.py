from fastapi import APIRouter

# Action Reaction
from app.src.modules.physics.Motion.actionReaction.controller import (
    action_reaction_controller,
    SimulationRequest
)

# Projectile Motion
from app.src.modules.physics.Motion.projectileMotion.controller import (
    projectile_controller,
    SimulationRequest as ProjectileRequest
)

# Bending Light
from app.src.modules.physics.Refraction.BendingLight.controller import (
    bending_light_controller,
    RefractionRequest
)

# Total Internal Reflection
from app.src.modules.physics.Refraction.TotalInternalReflection.controller import (
    total_internal_reflection_controller,
    TIRRequest
)

simulation_router = APIRouter()


# Action Reaction
@simulation_router.post("/action-reaction")
async def simulate_action_reaction(
    request: SimulationRequest
):

    return await action_reaction_controller(
        request
    )


# Projectile Motion
@simulation_router.post("/projectile-motion")
async def simulate_projectile_motion(
    request: ProjectileRequest
):

    return await projectile_controller(
        request
    )


# Bending Light
@simulation_router.post("/bending-light")
async def simulate_bending_light(
    request: RefractionRequest
):

    return await bending_light_controller(
        request
    )


# Total Internal Reflection
@simulation_router.post(
    "/total-internal-reflection"
)
async def simulate_tir(
    request: TIRRequest
):

    return await total_internal_reflection_controller(
        request
    )