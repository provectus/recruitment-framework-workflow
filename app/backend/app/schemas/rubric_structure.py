from pydantic import BaseModel, model_validator


class RubricCriterion(BaseModel):
    name: str
    description: str | None = None
    weight: int
    sort_order: int


class RubricCategory(BaseModel):
    name: str
    description: str | None = None
    weight: int
    sort_order: int
    criteria: list[RubricCriterion]

    @model_validator(mode="after")
    def validate_criteria(self) -> "RubricCategory":
        if not self.criteria:
            raise ValueError("Each category must have at least one criterion")
        total = sum(c.weight for c in self.criteria)
        if total != 100:
            raise ValueError(
                f"Criterion weights in category '{self.name}' must sum to 100, "
                f"got {total}"
            )
        return self


class RubricStructure(BaseModel):
    categories: list[RubricCategory]

    @model_validator(mode="after")
    def validate_categories(self) -> "RubricStructure":
        if not self.categories:
            raise ValueError("Rubric must have at least one category")
        total = sum(c.weight for c in self.categories)
        if total != 100:
            raise ValueError(f"Category weights must sum to 100, got {total}")
        return self
