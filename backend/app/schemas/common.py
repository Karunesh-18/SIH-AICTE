from pydantic import BaseModel, ConfigDict


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: str
    role: str
    institution_id: str | None
    region_id: str | None
    bureau_id: str | None
    language: str


class InstitutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    aicte_code: str
    name: str
    type: str
    state: str
    city: str
    region_id: str
    contact_email: str
    status: str
    established_year: int


class ProgramOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    level: str
    approved_intake: int
    start_year: int


class InstitutionDetail(InstitutionOut):
    programs: list[ProgramOut]
