from typing import Generic, TypeVar, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.orm.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model, db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: str) -> Optional[ModelType]:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def list(self, limit: int = 20, offset: int = 0, **filters) -> List[ModelType]:
        q = select(self.model)
        for k, v in filters.items():
            q = q.where(getattr(self.model, k) == v)
        q = q.limit(limit).offset(offset)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id: str) -> bool:
        obj = await self.get(id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.commit()
        return True
