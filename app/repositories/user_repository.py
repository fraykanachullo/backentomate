from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.orm.user import User
from app.repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str):
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalars().first()
