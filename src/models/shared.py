"""Generic Util Models."""

from src.models.model_config import ConfiguredBaseModel


class DTO[T](ConfiguredBaseModel):
    data: T
