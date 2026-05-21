
from sqlmodel import SQLModel
from typing import Optional

class ProjectBase(SQLModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    template: Optional[str] = None

class ProjectRead(ProjectBase):
    id: int

class ProjectUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
