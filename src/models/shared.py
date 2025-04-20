"""Generic Util Models."""

from pydantic import BaseModel


class DTO[T](BaseModel):
    data: T
