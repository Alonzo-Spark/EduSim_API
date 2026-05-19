from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user
from app.models.simulation import Simulation
from app.schemas.simulation import SimulationCreateRequest
from app.tutor.simulation_generator import generate_simulation_config
from app.rag.retriever import retrieve_chunks
from app.services.asset_service import get_assets_for_topic
from app.services.gamification_service import award_xp, check_and_award_badges
import uuid

router = APIRouter(prefix="/simulations", tags=["Simulations"])

@router.post("/generate")
async def generate_simulation(
    request: SimulationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from app.services.simulation_service import generate_and_save_simulation
    res = await generate_and_save_simulation(
        user_id=current_user.id,
        topic=request.topic,
        class_name=request.class_name,
        subject=request.subject,
        chapter=request.chapter,
        topic_id=request.topic_id,
        db=db
    )
    return res

@router.get("/my")
async def get_my_simulations(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(Simulation)
        .where(Simulation.user_id == current_user.id)
        .order_by(Simulation.created_at.desc())
    )
    sims = result.scalars().all()
    return [
        {
            "id": str(s.id), "topic_name": s.topic_name,
            "class_name": s.class_name, "subject": s.subject,
            "is_saved": s.is_saved, "created_at": s.created_at.isoformat(),
            "config": s.config
        }
        for s in sims
    ]

@router.patch("/{sim_id}/save")
async def toggle_save(
    sim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    sim = await db.get(Simulation, uuid.UUID(sim_id))
    if not sim or sim.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Simulation not found")
    sim.is_saved = not sim.is_saved
    await db.commit()
    if sim.is_saved:
        await award_xp(current_user.id, "simulation_saved", db)
    return {"is_saved": sim.is_saved}

@router.delete("/{sim_id}")
async def delete_simulation(
    sim_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    sim = await db.get(Simulation, uuid.UUID(sim_id))
    if sim and sim.user_id == current_user.id:
        await db.delete(sim)
        await db.commit()
    return {"deleted": True}
