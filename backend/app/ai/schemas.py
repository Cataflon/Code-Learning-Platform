"""What the model must answer, checked with Pydantic after the structured-output constraint."""

from pydantic import BaseModel, Field, field_validator


class GeneratedTest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    input: str = Field(max_length=64 * 1024)
    concepts: list[str] = Field(default_factory=list, max_length=10)
    hidden: bool = False
    weight: int = 1
    rationale: str = Field(default="", max_length=1000)

    @field_validator("name", "rationale")
    @classmethod
    def _strip(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("weight")
    @classmethod
    def _weight_in_range(cls, value: int) -> int:
        return max(1, min(10, value))


class GenerationResult(BaseModel):
    reference_solution: str = Field(min_length=1, max_length=64 * 1024)
    tests: list[GeneratedTest] = Field(min_length=1, max_length=20)


class MaterialChoice(BaseModel):
    material_id: int | None = None
    pages: str = Field(default="", max_length=200)
