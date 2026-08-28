from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.orm.plot import Plot

router = APIRouter()

class PlotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_m2: Optional[float] = None
    crop_type: str = "tomate"

@router.post("", status_code=201)
async def create_plot(req: PlotCreate, db: AsyncSession = Depends(get_db), payload: dict = Depends(get_current_user)):
    plot = Plot(
        name=req.name,
        description=req.description,
        latitude=req.latitude,
        longitude=req.longitude,
        area_m2=req.area_m2,
        crop_type=req.crop_type,
        owner_user_id=payload["user_id"],
    )
    db.add(plot)
    await db.commit()
    await db.refresh(plot)
    return {"id": plot.id, "name": plot.name, "owner_user_id": plot.owner_user_id, "created_at": plot.created_at.isoformat() if plot.created_at else None}

@router.get("")
async def list_plots(db: AsyncSession = Depends(get_db), payload: dict = Depends(get_current_user)):
    # Ver todos si ADMIN, sino solo propios
    q = select(Plot).order_by(desc(Plot.created_at))
    if payload.get("role") != "ADMIN":
        q = q.where(Plot.owner_user_id == payload["user_id"])
    result = await db.execute(q)
    plots = result.scalars().all()
    return [{"id": p.id, "name": p.name, "description": p.description, "latitude": p.latitude, "longitude": p.longitude, "crop_type": p.crop_type} for p in plots]

@router.get("/{plot_id}")
async def get_plot(plot_id: str, db: AsyncSession = Depends(get_db), payload: dict = Depends(get_current_user)):
    result = await db.execute(select(Plot).where(Plot.id == plot_id))
    plot = result.scalars().first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot no encontrado")
    return {"id": plot.id, "name": plot.name, "description": plot.description, "latitude": plot.latitude, "longitude": plot.longitude}
