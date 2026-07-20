from typing import Optional

from pydantic import BaseModel, Field


class AssociateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    surnames: str = Field(..., min_length=1, max_length=100)
    telephones: Optional[list[str]] = Field(default=None)


class AssociatePatchSchema(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    surnames: Optional[str] = Field(default=None, min_length=1, max_length=100)
    telephones: Optional[list[str]] = Field(default=None)


class AssociateResponseSchema(BaseModel):
    id: int
    name: str
    surnames: str
    telephones: Optional[list[str]]

    model_config = {"from_attributes": True}
