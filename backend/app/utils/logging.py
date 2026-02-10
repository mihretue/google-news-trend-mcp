import logging
import json
from typing import Optional, Any, Dict
from datetime import datetime
import re

# Sensitive keys to redact from logs
SENSITIVE_KEYS = {
    'password', 'token', 'api_key', 'secret', 'authorization',
    'supabase_key', 'tavily_api_key', 'jwt_secret'
}


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log records."""
        if isinstance(record.msg, str):
            record.msg = self._redact_string(record.msg)
        
        if record.args:
            if isinstance(record.args, dict):
                record.args = self._redact_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._redact_value(arg) for arg in record.args
                )
        
        return True

    @staticmethod
    def _redact_string(text: str) -> str:
        """Redact sensitive patterns from string."""
        # Redact API keys
        text = re.sub(
            r'(api[_-]?key|token|password|secret)\s*[:=]\s*[^\s,}]+',
            r'\1=***REDACTED***',
            text,
            flags=re.IGNORECASE
        )
        # Redact Bearer tokens
        text = re.sub(
            r'Bearer\s+[^\s]+',
            'Bearer ***REDACTED***',
            text,
            flags=re.IGNORECASE
        )
        return text

    @staticmethod
    def _redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact sensitive keys from dictionary."""
        redacted = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
                redacted[key] = "***REDACTED***"
            elif isinstance(value, dict):
                redacted[key] = SensitiveDataFilter._redact_dict(value)
            else:
                redacted[key] = value
        return redacted

    @staticmethod
    def _redact_value(value: Any) -> Any:
        """Redact sensitive value."""
        if isinstance(value, dict):
            return SensitiveDataFilter._redact_dict(value)
        elif isinstance(value, str):
            return SensitiveDataFilter._redact_string(value)
        return value


class StructuredLogger:
    """Structured logging utility."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        # Add sensitive data filter
        self.logger.addFilter(SensitiveDataFilter())

    def log_request(
        self,
        method: str,
        path: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log incoming request."""
        self.logger.info(
            f"[{request_id}] {method} {path}",
            extra={
                "user_id": user_id,
                "request_id": request_id,
                "method": method,
                "path": path,
            }
        )

    def log_response(
        self,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log response."""
        self.logger.info(
            f"[{request_id}] Response {status_code} ({duration_ms:.1f}ms)",
            extra={
                "user_id": user_id,
                "request_id": request_id,
                "status_code": status_code,
                "duration_ms": duration_ms,
            }
        )

    def log_tool_invocation(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log tool invocation."""
        self.logger.info(
            f"[{request_id}] Tool invoked: {tool_name}",
            extra={
                "user_id": user_id,
                "request_id": request_id,
                "tool_name": tool_name,
                "input": input_data,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def log_tool_completion(
        self,
        tool_name: str,
        duration_ms: float,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log tool completion."""
        self.logger.info(
            f"[{request_id}] Tool completed: {tool_name} ({duration_ms:.1f}ms)",
            extra={
                "user_id": user_id,
                "request_id": request_id,
                "tool_name": tool_name,
                "duration_ms": duration_ms,
            }
        )

    def log_tool_error(
        self,
        tool_name: str,
        error: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log tool error."""
        self.logger.error(
            f"[{request_id}] Tool error: {tool_name} - {error}",
            extra={
                "user_id": user_id,
                "request_id": request_id,
                "tool_name": tool_name,
                "error": error,
            }
        )

    def log_error(
        self,
        message: str,
        error: Optional[Exception] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log error."""
        self.logger.error(
            f"[{request_id}] {message}",
            extra={
                "user_id": user_id,
                "request_id": request_id,
                "error": str(error) if error else None,
            },
            exc_info=error is not None,
        )
