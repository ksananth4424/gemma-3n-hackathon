"""
Dependency Injection Container for Accessibility Assistant
Manages service lifecycle and dependencies efficiently
"""

from typing import Dict, Any, Type, TypeVar, Callable, Optional
import threading
import logging
from functools import wraps

T = TypeVar('T')

logger = logging.getLogger('accessibility_assistant.di')


class DIContainer:
    """
    Dependency Injection Container with singleton support
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._lock = threading.RLock()
        
    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a singleton service"""
        with self._lock:
            service_name = interface.__name__
            self._factories[service_name] = implementation
            logger.debug(f"Registered singleton: {service_name}")
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register a transient service (new instance each time)"""
        with self._lock:
            service_name = interface.__name__
            self._services[service_name] = implementation
            logger.debug(f"Registered transient: {service_name}")
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a specific instance"""
        with self._lock:
            service_name = interface.__name__
            self._singletons[service_name] = instance
            logger.debug(f"Registered instance: {service_name}")
    
    def get(self, interface: Type[T]) -> T:
        """Get service instance"""
        service_name = interface.__name__
        
        # Check if we have a singleton instance
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Check if we need to create a singleton
        if service_name in self._factories:
            with self._lock:
                if service_name not in self._singletons:
                    factory = self._factories[service_name]
                    instance = self._create_instance(factory)
                    self._singletons[service_name] = instance
                    logger.debug(f"Created singleton instance: {service_name}")
                return self._singletons[service_name]
        
        # Check for transient service
        if service_name in self._services:
            implementation = self._services[service_name]
            instance = self._create_instance(implementation)
            logger.debug(f"Created transient instance: {service_name}")
            return instance
        
        raise ValueError(f"Service not registered: {service_name}")
    
    def _create_instance(self, implementation_class: Type[T]) -> T:
        """Create instance with dependency injection"""
        try:
            # Try to get constructor parameters
            import inspect
            from typing import get_origin, get_args
            
            sig = inspect.signature(implementation_class.__init__)
            
            # Skip 'self' parameter
            params = list(sig.parameters.values())[1:]
            
            if not params:
                # No dependencies
                return implementation_class()
            
            # Resolve dependencies
            args = []
            for param in params:
                if param.annotation != param.empty:
                    # Handle Optional types
                    origin = get_origin(param.annotation)
                    if origin is not None:
                        # This is a generic type like Optional[str]
                        if hasattr(param, 'default') and param.default is not param.empty:
                            # Has default value, skip injection
                            continue
                        else:
                            logger.warning(f"Cannot resolve generic type {param.annotation} for {param.name}")
                            continue
                    
                    try:
                        dependency = self.get(param.annotation)
                        args.append(dependency)
                    except ValueError:
                        # If we can't resolve and there's a default, skip it
                        if hasattr(param, 'default') and param.default is not param.empty:
                            continue
                        else:
                            raise
                else:
                    # Can't resolve without type annotation
                    logger.warning(f"Cannot resolve dependency without type annotation: {param.name}")
            
            return implementation_class(*args)
            
        except Exception as e:
            logger.error(f"Error creating instance of {implementation_class}: {e}")
            # Fallback to simple instantiation
            return implementation_class()
    
    def clear(self):
        """Clear all registrations"""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()


# Global container instance
container = DIContainer()


def inject(interface: Type[T]) -> T:
    """Decorator for dependency injection"""
    return container.get(interface)


def singleton(cls):
    """Class decorator to mark as singleton"""
    container.register_singleton(cls, cls)
    return cls


def transient(cls):
    """Class decorator to mark as transient"""
    container.register_transient(cls, cls)
    return cls


def injectable(cls):
    """Class decorator to enable dependency injection in methods"""
    
    def wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs)
        return inner
    
    # Mark class as injectable
    cls._injectable = True
    return cls
