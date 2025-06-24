from typing import TypeVar, Generic, List

from pydantic import BaseModel

T = TypeVar('T')

class Pagination(BaseModel):
    page_number: int
    page_size: int
    num_pages: int
    total_results: int

class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: Pagination