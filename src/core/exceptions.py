"""Custom Exceptions."""


class ResourceNotFoundError(Exception):
    """Exception raised when a specific resource is not found."""

    def __init__(
        self, resource_type: str, resource_id: str | int | None = None
    ) -> None:
        """Construct instance with resource_type and resource_id."""
        self.resource_id = resource_id
        self.resource_type = resource_type
        message = f"{self.resource_type} not found"
        if self.resource_id is not None:
            message += f" with ID: {self.resource_id}"
        super().__init__(message)


class InvalidTokenError(Exception):
    """Raised when a token is considered expired or invalid."""

    def __init__(
        self, resource_type: str = "Resource", request_id: str | None = None
    ) -> None:
        """Construct instance with resource_type and request_id."""
        self.resource_type = resource_type
        self.request_id = request_id
        message = "Invalid or expired authentication token"
        if self.request_id is not None:
            message += f" with ID: {request_id}"
        super().__init__(message)


class PartialSmsError(Exception):
    """Exception Raised Raised when not all messages were sent successfully."""


class SmsError(Exception):
    """Exception Raised when SMS error occurs."""

    def __init__(
        self, resource_type: str = "Resource", request_id: str | None = None
    ) -> None:
        """Consructs instance of SMS error with resource type and request id."""
        self.resource_type = resource_type
        self.request_id = request_id
        message = f"{resource_type} Error"
        if self.request_id is not None:
            message += f" with ID: {request_id}"
        super().__init__(message)
