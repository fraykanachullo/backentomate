from app.models.orm.plot import Plot
from app.repositories.base_repository import BaseRepository

class PlotRepository(BaseRepository[Plot]):
    def __init__(self, db):
        super().__init__(Plot, db)
