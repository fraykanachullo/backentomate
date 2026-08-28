from app.models.orm.diagnostic import Diagnostic
from app.repositories.base_repository import BaseRepository

class DiagnosticRepository(BaseRepository[Diagnostic]):
    def __init__(self, db):
        super().__init__(Diagnostic, db)
