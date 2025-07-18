"""
Comprehensive error handling system for the Windows Accessibility Assistant
"""

import sys
import traceback
import logging
import functools
from typing import Any, Callable, Dict, Optional, Type, Union
from datetime import datetime
from pathlib import Path

from src.models.response_models import ProcessingError, ErrorCode


class AccessibilityAssistantException(Exception):
    """Base exception for the Accessibility Assistant"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INVALID_REQUEST,
        details: Optional[str] = None,
        original_exception: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details
        self.original_exception = original_exception
        self.timestamp = datetime.now()
    
    def to_processing_error(self) -> ProcessingError:
        """Convert to ProcessingError model"""
        details = self.details
        if self.original_exception:
            details = f"{details}\nOriginal: {str(self.original_exception)}" if details else str(self.original_exception)
        
        return ProcessingError(
            code=self.error_code,
            message=self.message,
            details=details,
            timestamp=self.timestamp
        )


class FileProcessingError(AccessibilityAssistantException):
    """Errors related to file processing"""
    
    def __init__(self, message: str, file_path: str, **kwargs):
        super().__init__(message, **kwargs)
        self.file_path = file_path


class ModelError(AccessibilityAssistantException):
    """Errors related to AI model operations"""
    
    def __init__(self, message: str, model_name: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.model_name = model_name


class ConfigurationError(AccessibilityAssistantException):
    """Errors related to configuration"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key


class DependencyError(AccessibilityAssistantException):
    """Errors related to missing dependencies"""
    
    def __init__(self, message: str, dependency_name: str, **kwargs):
        super().__init__(message, error_code=ErrorCode.DEPENDENCY_MISSING, **kwargs)
        self.dependency_name = dependency_name


class ProcessingTimeoutError(AccessibilityAssistantException):
    """Errors related to processing timeouts"""
    
    def __init__(self, message: str, timeout_seconds: int, **kwargs):
        super().__init__(message, error_code=ErrorCode.PROCESSING_TIMEOUT, **kwargs)
        self.timeout_seconds = timeout_seconds


class ErrorHandler:
    """Centralized error handling and logging"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._error_counts: Dict[str, int] = {}
        self._last_errors: Dict[str, datetime] = {}
    
    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = True
    ) -> ProcessingError:
        """Handle any exception and convert to ProcessingError"""
        
        # Convert known exceptions
        if isinstance(exception, AccessibilityAssistantException):
            error = exception.to_processing_error()
        else:
            error = self._convert_standard_exception(exception)
        
        # Add context information
        if context:
            if error.details:
                error.details += f"\nContext: {context}"
            else:
                error.details = f"Context: {context}"
        
        # Log the error
        self._log_error(error, exception, context)
        
        # Update error tracking
        self._track_error(error.code.value)
        
        # Re-raise if requested
        if reraise and not isinstance(exception, AccessibilityAssistantException):
            raise AccessibilityAssistantException(
                error.message,
                error.code,
                error.details,
                exception
            )
        elif reraise:
            raise
        
        return error
    
    def _convert_standard_exception(self, exception: Exception) -> ProcessingError:
        """Convert standard Python exceptions to ProcessingError"""
        
        error_code = ErrorCode.INVALID_REQUEST
        message = str(exception)
        details = None
        
        if isinstance(exception, FileNotFoundError):
            error_code = ErrorCode.FILE_NOT_FOUND
            message = f"File not found: {exception.filename if hasattr(exception, 'filename') else 'Unknown file'}"
        
        elif isinstance(exception, PermissionError):
            error_code = ErrorCode.FILE_ACCESS_DENIED
            message = f"Access denied: {exception.filename if hasattr(exception, 'filename') else 'Unknown file'}"
        
        elif isinstance(exception, ImportError):
            error_code = ErrorCode.DEPENDENCY_MISSING
            message = f"Missing dependency: {exception.name if hasattr(exception, 'name') else 'Unknown module'}"
        
        elif isinstance(exception, TimeoutError):
            error_code = ErrorCode.PROCESSING_TIMEOUT
            message = "Operation timed out"
        
        elif isinstance(exception, MemoryError):
            error_code = ErrorCode.INSUFFICIENT_MEMORY
            message = "Insufficient memory to complete operation"
        
        elif isinstance(exception, (ConnectionError, OSError)):
            error_code = ErrorCode.OLLAMA_CONNECTION_FAILED
            message = "Failed to connect to Ollama service"
        
        # Add traceback as details
        details = traceback.format_exc()
        
        return ProcessingError(
            code=error_code,
            message=message,
            details=details
        )
    
    def _log_error(
        self,
        error: ProcessingError,
        exception: Exception,
        context: Optional[Dict[str, Any]]
    ):
        """Log error with appropriate level"""
        
        log_data = {
            'error_code': error.code.value,
            'message': error.message,
            'exception_type': type(exception).__name__,
            'timestamp': error.timestamp.isoformat()
        }
        
        if context:
            log_data['context'] = context
        
        if error.details:
            log_data['details'] = error.details
        
        # Determine log level based on error type
        if error.code in [ErrorCode.OLLAMA_CONNECTION_FAILED, ErrorCode.INSUFFICIENT_MEMORY]:
            self.logger.critical("Critical error occurred", extra=log_data)
        elif error.code in [ErrorCode.PROCESSING_TIMEOUT, ErrorCode.DEPENDENCY_MISSING]:
            self.logger.error("Processing error occurred", extra=log_data)
        elif error.code in [ErrorCode.FILE_NOT_FOUND, ErrorCode.UNSUPPORTED_FORMAT]:
            self.logger.warning("File processing warning", extra=log_data)
        else:
            self.logger.error("Error occurred", extra=log_data)
    
    def _track_error(self, error_code: str):
        """Track error frequency for monitoring"""
        self._error_counts[error_code] = self._error_counts.get(error_code, 0) + 1
        self._last_errors[error_code] = datetime.now()
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            'error_counts': self._error_counts.copy(),
            'last_errors': {
                code: timestamp.isoformat()
                for code, timestamp in self._last_errors.items()
            },
            'total_errors': sum(self._error_counts.values())
        }
    
    def reset_statistics(self):
        """Reset error tracking statistics"""
        self._error_counts.clear()
        self._last_errors.clear()


def handle_errors(
    default_error_code: ErrorCode = ErrorCode.INVALID_REQUEST,
    reraise: bool = False,
    log_errors: bool = True
):
    """Decorator for automatic error handling"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger = logging.getLogger(func.__module__)
                    handler = ErrorHandler(logger)
                    
                    context = {
                        'function': func.__name__,
                        'args': str(args),
                        'kwargs': str(kwargs)
                    }
                    
                    handler.handle_exception(e, context, reraise)
                
                if not reraise:
                    # Return a ProcessingError instead of raising
                    if isinstance(e, AccessibilityAssistantException):
                        return e.to_processing_error()
                    else:
                        return ProcessingError(
                            code=default_error_code,
                            message=str(e),
                            details=traceback.format_exc()
                        )
                raise
        
        return wrapper
    return decorator


def validate_file_access(file_path: str) -> None:
    """Validate file access and throw appropriate errors"""
    path = Path(file_path)
    
    if not path.exists():
        raise FileProcessingError(
            f"File does not exist: {file_path}",
            file_path=file_path,
            error_code=ErrorCode.FILE_NOT_FOUND
        )
    
    if not path.is_file():
        raise FileProcessingError(
            f"Path is not a file: {file_path}",
            file_path=file_path,
            error_code=ErrorCode.FILE_NOT_FOUND
        )
    
    try:
        # Try to open the file to check permissions
        with open(path, 'rb') as f:
            pass
    except PermissionError:
        raise FileProcessingError(
            f"Access denied to file: {file_path}",
            file_path=file_path,
            error_code=ErrorCode.FILE_ACCESS_DENIED
        )
    except OSError as e:
        raise FileProcessingError(
            f"Cannot access file: {file_path}. {str(e)}",
            file_path=file_path,
            error_code=ErrorCode.FILE_ACCESS_DENIED,
            original_exception=e
        )


def validate_dependencies() -> Dict[str, bool]:
    """Validate that all required dependencies are available"""
    dependencies = {
        'ollama': False,
        'fitz': False,  # PyMuPDF
        'whisper': False,
        'cv2': False,  # opencv-python
        'docx': False,  # python-docx
        'spacy': False
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
        except ImportError:
            dependencies[dep] = False
    
    return dependencies


def check_system_resources() -> Dict[str, Any]:
    """Check system resources and return status"""
    import psutil
    
    return {
        'memory': {
            'total_gb': psutil.virtual_memory().total / (1024**3),
            'available_gb': psutil.virtual_memory().available / (1024**3),
            'percent_used': psutil.virtual_memory().percent
        },
        'disk': {
            'total_gb': psutil.disk_usage('/').total / (1024**3),
            'free_gb': psutil.disk_usage('/').free / (1024**3),
            'percent_used': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
        },
        'cpu': {
            'percent': psutil.cpu_percent(interval=1),
            'cores': psutil.cpu_count()
        }
    }


# Global error handler instance
_global_error_handler = ErrorHandler()

def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    return _global_error_handler


def setup_error_handling(logger: Optional[logging.Logger] = None):
    """Setup global error handling"""
    global _global_error_handler
    _global_error_handler = ErrorHandler(logger)
    
    # Setup global exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupts to pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        _global_error_handler.handle_exception(
            exc_value,
            context={'type': 'unhandled_exception'},
            reraise=False
        )
    
    sys.excepthook = handle_exception
