"""Custom exceptions for MCP Server"""


class MCPException(Exception):
    """Base exception for MCP Server"""
    pass


class ConnectorException(MCPException):
    """Exception raised by connectors"""

    def __init__(self, connector_name: str, message: str, original_error: Exception = None):
        self.connector_name = connector_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{connector_name}] {message}")


class AuthenticationException(ConnectorException):
    """Exception raised when authentication fails"""
    pass


class RateLimitException(ConnectorException):
    """Exception raised when rate limit is exceeded"""
    pass


class DataNotFoundException(MCPException):
    """Exception raised when requested data is not found"""
    pass


class ConfigurationException(MCPException):
    """Exception raised when configuration is invalid"""
    pass


class SnowflakeException(MCPException):
    """Exception raised by Snowflake service"""
    pass


class CacheException(MCPException):
    """Exception raised by cache operations"""
    pass
