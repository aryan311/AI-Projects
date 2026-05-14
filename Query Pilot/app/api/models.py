from typing import Any, Dict, List
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(..., description="The natural language question to ask against the database.", example="Show the top 5 customers by revenue")

class QueryResponse(BaseModel):
    sql: str = Field(..., description="The generated SQL query.")
    rows: List[Dict[str, Any]] = Field(..., description="The rows returned by the query execution.")
    summary: str = Field(..., description="A plain English summary of the results.")
    warnings: List[str] = Field(default_factory=list, description="Any warnings such as truncation or timeouts.")

class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message details.")
