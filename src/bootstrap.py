"""
Application Bootstrap - Sets up dependency injection container
"""

import logging
from pathlib import Path

from .utils.dependency_injection import container
from .utils.config_manager import ConfigManager
from .utils.logger_setup import setup_logging
from .service.ollama_service import OllamaService, OllamaServiceInterface
from .processors.content_processor import ContentProcessor

logger = logging.getLogger('accessibility_assistant.bootstrap')


class ApplicationBootstrap:
    """
    Bootstrap class for setting up the application with dependency injection
    """
    
    def __init__(self, config_dir: str = None):
        self.config_dir = config_dir
        self._setup_logging()
        self._register_dependencies()
        
    def _setup_logging(self):
        """Setup application logging"""
        try:
            # Setup logging first
            setup_logging()
            logger.info("Application bootstrap starting...")
            
        except Exception as e:
            print(f"Error setting up logging: {e}")
            # Continue with basic logging
            logging.basicConfig(level=logging.INFO)
            logger.info("Using basic logging configuration")
    
    def _register_dependencies(self):
        """Register all dependencies in the DI container"""
        try:
            # Register configuration manager as singleton
            container.register_singleton(ConfigManager, ConfigManager)
            
            # Register Ollama service interface and implementation
            container.register_singleton(OllamaServiceInterface, OllamaService)
            container.register_singleton(OllamaService, OllamaService)
            
            # Register content processor as singleton
            container.register_singleton(ContentProcessor, ContentProcessor)
            
            logger.info("Dependency injection container configured successfully")
            
        except Exception as e:
            logger.error(f"Error registering dependencies: {e}")
            raise
    
    def get_content_processor(self) -> ContentProcessor:
        """
        Get the main content processor instance
        
        Returns:
            Configured ContentProcessor instance
        """
        try:
            return container.get(ContentProcessor)
        except Exception as e:
            logger.error(f"Error getting content processor: {e}")
            raise
    
    def get_config_manager(self) -> ConfigManager:
        """
        Get the configuration manager instance
        
        Returns:
            ConfigManager instance
        """
        return container.get(ConfigManager)
    
    def get_ollama_service(self) -> OllamaService:
        """
        Get the Ollama service instance
        
        Returns:
            OllamaService instance
        """
        return container.get(OllamaService)
    
    def health_check(self) -> bool:
        """
        Perform application health check
        
        Returns:
            True if application is healthy, False otherwise
        """
        try:
            # Check if Ollama service is healthy
            ollama_service = self.get_ollama_service()
            if not ollama_service.is_healthy():
                logger.error("Ollama service health check failed")
                return False
            
            # Check if models are available
            models = ollama_service.get_available_models()
            if not models:
                logger.error("No models available in Ollama")
                return False
            
            logger.info(f"Health check passed. Available models: {len(models)}")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def shutdown(self):
        """Clean shutdown of the application"""
        try:
            logger.info("Application shutting down...")
            container.clear()
            logger.info("Application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Global bootstrap instance
_bootstrap = None


def get_bootstrap(config_dir: str = None) -> ApplicationBootstrap:
    """
    Get or create the application bootstrap instance
    
    Args:
        config_dir: Optional configuration directory path
        
    Returns:
        ApplicationBootstrap instance
    """
    global _bootstrap
    
    if _bootstrap is None:
        _bootstrap = ApplicationBootstrap(config_dir)
    
    return _bootstrap


def get_content_processor() -> ContentProcessor:
    """
    Convenience function to get content processor
    
    Returns:
        ContentProcessor instance
    """
    bootstrap = get_bootstrap()
    return bootstrap.get_content_processor()


def setup_ollama_models():
    """
    Setup custom Ollama models for accessibility
    """
    try:
        bootstrap = get_bootstrap()
        ollama_service = bootstrap.get_ollama_service()
        
        # This will trigger model setup in the service
        ollama_service.reload_models()
        
        logger.info("Ollama models setup completed")
        
    except Exception as e:
        logger.error(f"Error setting up Ollama models: {e}")
        raise
