"""Generic Util Models."""

from .model_config import ConfiguredBaseModel


class DTO[T](ConfiguredBaseModel):
    data: T
