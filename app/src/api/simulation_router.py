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

#InclinedPane
from app.src.modules.physics.Motion.inclinedPlane.controller import (
    inclined_plane_controller,
    SimulationRequest as InclinedPlaneRequest
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

#Optical Fiber
from app.src.modules.physics.Refraction.OpticalFibre.controller import (
    optical_fibre_controller,
    OpticalFibreRequest,
    optical_fibre_controller
)

#EchoRanging
from app.src.modules.physics.Sounds.EchoRanging.controller import (
    echo_ranging_controller,
    EchoRangingRequest
)

#Pitch and Loudness
from app.src.modules.physics.Sounds.PitchAndLoudness.controller import (
    pitch_and_loudness_controller,
    PitchAndLoudnessRequest
)

#Visualizing Waves
from app.src.modules.physics.Sounds.VisualizingWaves.controller import (
    wave_visualization_controller,
    WaveVisualizationRequest
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

#Inclined Plane
@simulation_router.post("/inclined-plane")
async def simulate_inclined_plane(
    request: InclinedPlaneRequest
):

    return await inclined_plane_controller(
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

# Optical Fiber
@simulation_router.post("/optical-fiber")
async def simulate_optical_fibre(
    request: OpticalFibreRequest
):

    return await optical_fibre_controller(
        request
    )

# Echo Ranging
@simulation_router.post("/echo-ranging")
async def simulate_echo_ranging(
    request: EchoRangingRequest
):

    return await echo_ranging_controller(
        request
    )

# Pitch and Loudness
@simulation_router.post("/pitch-and-loudness")
async def simulate_pitch_and_loudness(
    request: PitchAndLoudnessRequest
):

    return await pitch_and_loudness_controller(
        request
    )

# Visualizing Waves
@simulation_router.post("/visualizing-waves")
async def simulate_visualizing_waves(
    request: WaveVisualizationRequest
):

    return await wave_visualization_controller(
        request
    )