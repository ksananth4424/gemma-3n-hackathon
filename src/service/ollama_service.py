"""
Ollama Service for AI model interaction
Handles model selection, initialization, and inference
"""

import ollama
import logging
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
import threading
from abc import ABC, abstractmethod

from ..utils.dependency_injection import singleton, injectable
from ..utils.config_manager import ConfigManager

logger = logging.getLogger('accessibility_assistant.ollama')


class ContentType(Enum):
    """Content types for model selection"""
    TEXT = "text"
    PDF = "pdf" 
    VIDEO = "video"
    AUDIO = "audio"


@dataclass
class ModelInfo:
    """Information about available models"""
    name: str
    size: str
    id: str
    modified: str
    complexity_score: int  # Higher score for more complex content


class OllamaServiceInterface(ABC):
    """Interface for Ollama service"""
    
    @abstractmethod
    def generate_summary(self, content: str, content_type: ContentType, **kwargs) -> str:
        pass
    
    @abstractmethod
    def is_healthy(self) -> bool:
        pass


@singleton
@injectable
class OllamaService(OllamaServiceInterface):
    """
    Ollama service with intelligent model selection and caching
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.client = None
        self._models_cache: Dict[str, ModelInfo] = {}
        self._model_lock = threading.RLock()
        self._initialize_client()
        self._setup_models()
        
    def _initialize_client(self):
        """Initialize Ollama client"""
        try:
            ollama_config = self.config.get_ollama_config()
            host = ollama_config.get('host', 'http://localhost:11434')
            
            self.client = ollama.Client(host=host)
            logger.info(f"Ollama client initialized with host: {host}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise
    
    def _setup_models(self):
        """Setup and cache available models"""
        try:
            # Get available models
            models_response = self.client.list()
            logger.debug(f"Raw models response: {models_response}")
            
            # Handle both dict format and object format
            if hasattr(models_response, 'models'):
                models_list = models_response.models
            else:
                models_list = models_response.get('models', [])
            
            logger.info(f"Found {len(models_list)} models in response")
            
            for model_data in models_list:
                logger.debug(f"Processing model data: {model_data}")
                
                # Handle both dict and object formats
                if hasattr(model_data, 'model'):
                    name = model_data.model
                    size = getattr(model_data, 'size', 0)
                    digest = getattr(model_data, 'digest', '')
                    modified_at = getattr(model_data, 'modified_at', '')
                else:
                    name = model_data.get('name') or model_data.get('model')
                    size = model_data.get('size', 0)
                    digest = model_data.get('digest', model_data.get('id', ''))
                    modified_at = model_data.get('modified_at', model_data.get('modified', ''))
                
                if not name:
                    logger.warning(f"Model data missing name: {model_data}")
                    continue
                
                # Create model info with complexity scoring
                model_info = ModelInfo(
                    name=name,
                    size=str(size),
                    id=str(digest),
                    modified=str(modified_at),
                    complexity_score=self._calculate_complexity_score(name)
                )
                
                self._models_cache[name] = model_info
                logger.info(f"Cached model: {name} (complexity: {model_info.complexity_score})")
            
            # Setup custom models if not exist (temporarily disabled)
            # self._ensure_custom_models()
            
        except Exception as e:
            logger.error(f"Error setting up models: {e}")
            # Log more details for debugging
            logger.debug(f"Full error details: {e}", exc_info=True)
    
    def _calculate_complexity_score(self, model_name: str) -> int:
        """Calculate complexity score based on model name/size"""
        if 'e4b' in model_name or '8b' in model_name.lower():
            return 100  # High complexity model
        elif 'e2b' in model_name or '5.6b' in model_name.lower():
            return 75   # Medium complexity model
        elif '2b' in model_name.lower():
            return 50   # Low complexity model
        else:
            return 60   # Default medium-low
    
    def _ensure_custom_models(self):
        """Ensure our custom accessibility models exist"""
        custom_models = {
            'accessibility-e4b': 'src/models/Modelfile.e4b',
            'accessibility-e2b': 'src/models/Modelfile.e2b'
        }
        
        for model_name, modelfile_path in custom_models.items():
            if model_name not in self._models_cache:
                try:
                    # Read the modelfile
                    with open(modelfile_path, 'r') as f:
                        modelfile_content = f.read()
                    
                    # Create custom model using correct API
                    self.client.create(model=model_name, modelfile=modelfile_content)
                    logger.info(f"Created custom model: {model_name}")
                    
                    # Add to cache
                    base_model = 'gemma3n:e4b' if 'e4b' in model_name else 'gemma3n:e2b'
                    complexity = 100 if 'e4b' in model_name else 75
                    
                    self._models_cache[model_name] = ModelInfo(
                        name=model_name,
                        size="custom",
                        id="custom",
                        modified=str(time.time()),
                        complexity_score=complexity
                    )
                    
                except FileNotFoundError:
                    logger.warning(f"Modelfile not found: {modelfile_path}")
                except Exception as e:
                    logger.warning(f"Could not create custom model {model_name}: {e}")
                    # Continue with base models if custom creation fails
    
    def _select_model(self, content_type: ContentType, content_length: int = 0) -> str:
        """
        Intelligently select model based on content type and complexity
        
        Args:
            content_type: Type of content being processed
            content_length: Length of content (chars)
            
        Returns:
            Best model name for the task
        """
        with self._model_lock:
            # Define model selection rules - use base models for now
            if content_type in [ContentType.VIDEO, ContentType.AUDIO]:
                # Use larger model for complex audio/video content
                preferred_models = ['gemma3n:e4b', 'accessibility-e4b']
            elif content_type == ContentType.PDF and content_length > 10000:
                # Use larger model for long PDFs
                preferred_models = ['gemma3n:e4b', 'accessibility-e4b']
            else:
                # Use smaller, faster model for text and short content
                preferred_models = ['gemma3n:e2b', 'accessibility-e2b']
            
            # Find first available model from preferred list
            for model_name in preferred_models:
                if model_name in self._models_cache:
                    logger.debug(f"Selected model {model_name} for {content_type.value}")
                    return model_name
            
            # Fallback to any available model
            available_models = list(self._models_cache.keys())
            if available_models:
                fallback = available_models[0]
                logger.warning(f"Using fallback model {fallback} for {content_type.value}")
                return fallback
            
            raise RuntimeError("No models available")
    
    def generate_summary(self, content: str, content_type: ContentType, **kwargs) -> str:
        """
        Generate ADHD-friendly summary using appropriate model
        
        Args:
            content: Content to summarize
            content_type: Type of content
            **kwargs: Additional parameters
            
        Returns:
            Generated summary
        """
        try:
            # Select appropriate model
            model_name = self._select_model(content_type, len(content))
            
            # Get AI configuration
            ai_config = self.config.get_ai_config()
            
            # Build prompt based on content type
            prompt = self._build_prompt(content, content_type)
            
            # Generate response
            response = self.client.chat(
                model=model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': ai_config.get('prompts', {}).get('system_prompt', '')
                    },
                    {
                        'role': 'user', 
                        'content': prompt
                    }
                ],
                options={
                    'temperature': ai_config.get('model', {}).get('temperature', 0.3),
                    'top_p': ai_config.get('model', {}).get('top_p', 0.9),
                    'top_k': ai_config.get('model', {}).get('top_k', 40),
                    'num_predict': ai_config.get('model', {}).get('max_tokens', 500)
                }
            )
            
            summary = response['message']['content']
            logger.info(f"Generated summary using {model_name} ({len(summary)} chars)")
            
            return self._format_summary(summary)
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise
    
    def _build_prompt(self, content: str, content_type: ContentType) -> str:
        """Build appropriate prompt for content type"""
        ai_config = self.config.get_ai_config()
        prompts = ai_config.get('prompts', {})
        
        # Get template based on content type
        if content_type == ContentType.PDF:
            template = prompts.get('pdf_prompt_template', 'Summarize this PDF: {content}')
        elif content_type in [ContentType.VIDEO, ContentType.AUDIO]:
            template = prompts.get('video_prompt_template', 'Summarize this video transcript: {content}')
        else:
            template = prompts.get('text_prompt_template', 'Summarize this text: {content}')
        
        # Truncate content if too long
        max_content_length = 4000  # Leave room for prompt structure
        if len(content) > max_content_length:
            content = content[:max_content_length] + "...\n[Content truncated for processing]"
        
        return template.format(content=content)
    
    def _format_summary(self, summary: str) -> str:
        """Format summary for ADHD-friendly presentation"""
        lines = summary.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Ensure bullet points are consistent
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    if not line.startswith('• '):
                        line = '• ' + line.lstrip('•-* ')
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def is_healthy(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            # Try to list models as health check
            models = self.client.list()
            return len(models.get('models', [])) > 0
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models"""
        return list(self._models_cache.values())
    
    def reload_models(self):
        """Reload available models"""
        self._models_cache.clear()
        self._setup_models()
