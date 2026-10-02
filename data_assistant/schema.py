from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Filter(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    column: str
    op: Literal["eq", "ne", "gt", "ge", "lt", "le", "contains", "is_null", "not_null"]
    value: str | float | bool | None


class AnalysisPlan(BaseModel):
    """Only supported dataframe operations. No code or expressions."""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    operation: Literal["profile", "aggregate", "rows", "unsupported"]
    group_by: list[str] = Field(max_length=2)
    metric: str | None
    aggregation: Literal["sum", "mean", "min", "max", "count", "nunique"] | None
    filters: list[Filter] = Field(max_length=5)
    columns: list[str] = Field(max_length=20)
    sort_by: str | None
    descending: bool
    limit: int = Field(ge=1, le=1000)
    chart: Literal["none", "bar", "line"]
    explanation: str = Field(max_length=1500)
