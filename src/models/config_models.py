"""
Configuration models for the Windows Accessibility Assistant
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path
import json


class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ModelComplexity(Enum):
    """Model complexity levels"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class ModelConfig:
    """Configuration for a specific AI model"""
    name: str
    complexity: ModelComplexity
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    
    # Model-specific settings
    context_window: int = 8192
    supports_streaming: bool = True
    supports_vision: bool = False
    
    # Performance settings
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # Cost/resource considerations
    tokens_per_second: float = 50.0
    memory_mb: int = 1024
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'complexity': self.complexity.value,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'context_window': self.context_window,
            'supports_streaming': self.supports_streaming,
            'supports_vision': self.supports_vision,
            'timeout_seconds': self.timeout_seconds,
            'max_retries': self.max_retries,
            'retry_delay_seconds': self.retry_delay_seconds,
            'tokens_per_second': self.tokens_per_second,
            'memory_mb': self.memory_mb
        }


@dataclass
class OllamaConfig:
    """Configuration for Ollama service"""
    base_url: str = "http://localhost:11434"
    timeout_seconds: int = 300
    max_concurrent_requests: int = 3
    
    # Health check settings
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 10
    max_consecutive_failures: int = 3
    
    # Model management
    auto_pull_models: bool = False
    model_cache_size_gb: int = 10
    
    # Available models configuration
    models: List[ModelConfig] = field(default_factory=list)
    
    def get_model_by_name(self, name: str) -> Optional[ModelConfig]:
        """Get model configuration by name"""
        for model in self.models:
            if model.name == name:
                return model
        return None
    
    def get_models_by_complexity(self, complexity: ModelComplexity) -> List[ModelConfig]:
        """Get models filtered by complexity"""
        return [model for model in self.models if model.complexity == complexity]


@dataclass
class ProcessingLimits:
    """Limits for content processing"""
    # File size limits (in bytes)
    max_file_size_text: int = 50 * 1024 * 1024  # 50MB
    max_file_size_pdf: int = 100 * 1024 * 1024  # 100MB
    max_file_size_video: int = 1024 * 1024 * 1024  # 1GB
    
    # Content limits
    max_content_length: int = 1000000  # 1M characters
    max_summary_length: int = 10000    # 10K characters
    
    # Processing limits
    max_processing_time_seconds: int = 600  # 10 minutes
    max_concurrent_jobs: int = 5
    max_retry_attempts: int = 3
    
    # Memory limits
    max_memory_usage_mb: int = 2048  # 2GB
    
    def is_file_size_allowed(self, file_path: str, content_type: str) -> bool:
        """Check if file size is within limits"""
        file_size = Path(file_path).stat().st_size
        
        if content_type in ['text', 'document']:
            return file_size <= self.max_file_size_text
        elif content_type == 'pdf':
            return file_size <= self.max_file_size_pdf
        elif content_type in ['video', 'audio']:
            return file_size <= self.max_file_size_video
        
        return file_size <= self.max_file_size_text  # Default


@dataclass
class ADHDOptimizationConfig:
    """Configuration for ADHD-friendly features"""
    # Content structure
    max_bullet_points_per_section: int = 5
    max_sections: int = 6
    preferred_sentence_length: int = 15  # words
    
    # Visual formatting
    use_headers: bool = True
    use_bullet_points: bool = True
    use_numbered_lists: bool = False
    add_visual_separators: bool = True
    
    # Language simplification
    simplify_vocabulary: bool = True
    avoid_jargon: bool = True
    use_active_voice: bool = True
    target_reading_level: int = 8  # Grade level
    
    # Cognitive load reduction
    chunk_information: bool = True
    highlight_key_points: bool = True
    include_summary_boxes: bool = True
    
    # Time management
    include_reading_time: bool = True
    include_break_suggestions: bool = True


@dataclass
class LoggingConfig:
    """Configuration for logging"""
    level: LogLevel = LogLevel.INFO
    
    # File logging
    log_to_file: bool = True
    log_file_path: str = "logs/accessibility_assistant.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    
    # Console logging
    log_to_console: bool = True
    console_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Structured logging
    use_json_format: bool = False
    include_session_id: bool = True
    
    # Performance logging
    log_performance_metrics: bool = True
    log_sql_queries: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'level': self.level.value,
            'log_to_file': self.log_to_file,
            'log_file_path': self.log_file_path,
            'max_file_size_mb': self.max_file_size_mb,
            'backup_count': self.backup_count,
            'log_to_console': self.log_to_console,
            'console_format': self.console_format,
            'use_json_format': self.use_json_format,
            'include_session_id': self.include_session_id,
            'log_performance_metrics': self.log_performance_metrics,
            'log_sql_queries': self.log_sql_queries
        }


@dataclass
class SecurityConfig:
    """Security configuration"""
    # File access
    allowed_file_extensions: List[str] = field(default_factory=lambda: [
        '.txt', '.md', '.pdf', '.docx', '.doc', '.rtf',
        '.mp4', '.avi', '.mov', '.mkv', '.wmv',
        '.mp3', '.wav', '.flac', '.aac'
    ])
    
    blocked_directories: List[str] = field(default_factory=lambda: [
        'C:\\Windows\\System32',
        'C:\\Program Files',
        'C:\\Program Files (x86)',
        '%APPDATA%\\Microsoft'
    ])
    
    # Content scanning
    scan_for_malware: bool = False
    max_scan_time_seconds: int = 30
    
    # Privacy
    anonymize_content: bool = False
    remove_metadata: bool = False
    
    def is_file_allowed(self, file_path: str) -> bool:
        """Check if file is allowed to be processed"""
        path = Path(file_path)
        
        # Check extension
        if path.suffix.lower() not in self.allowed_file_extensions:
            return False
        
        # Check directory
        for blocked_dir in self.blocked_directories:
            try:
                if path.is_relative_to(blocked_dir):
                    return False
            except (ValueError, OSError):
                continue
        
        return True


@dataclass
class ApplicationConfig:
    """Main application configuration"""
    # Core settings
    app_name: str = "Windows Accessibility Assistant"
    version: str = "1.0.0"
    debug_mode: bool = False
    
    # Service configurations
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    processing_limits: ProcessingLimits = field(default_factory=ProcessingLimits)
    adhd_optimization: ADHDOptimizationConfig = field(default_factory=ADHDOptimizationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # Directories
    temp_directory: str = "temp"
    cache_directory: str = "cache"
    output_directory: str = "output"
    
    # Performance
    enable_caching: bool = True
    cache_timeout_minutes: int = 60
    enable_monitoring: bool = True
    
    def __post_init__(self):
        """Initialize default models if none provided"""
        if not self.ollama.models:
            self.ollama.models = [
                ModelConfig(
                    name="gemma3n:e2b",
                    complexity=ModelComplexity.SIMPLE,
                    max_tokens=2048,
                    context_window=4096,
                    memory_mb=512
                ),
                ModelConfig(
                    name="gemma3n:e4b",
                    complexity=ModelComplexity.COMPLEX,
                    max_tokens=4096,
                    context_window=8192,
                    memory_mb=1024
                )
            ]
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'ApplicationConfig':
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except FileNotFoundError:
            # Return default configuration if file doesn't exist
            return cls()
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationConfig':
        """Create configuration from dictionary"""
        # This is a simplified version - in practice, you'd want
        # more sophisticated nested object creation
        config = cls()
        
        # Update basic fields
        for key, value in data.items():
            if hasattr(config, key) and not isinstance(getattr(config, key), (OllamaConfig, ProcessingLimits, ADHDOptimizationConfig, LoggingConfig, SecurityConfig)):
                setattr(config, key, value)
        
        return config
    
    def save_to_file(self, config_path: str):
        """Save configuration to JSON file"""
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'app_name': self.app_name,
            'version': self.version,
            'debug_mode': self.debug_mode,
            'ollama': {
                'base_url': self.ollama.base_url,
                'timeout_seconds': self.ollama.timeout_seconds,
                'max_concurrent_requests': self.ollama.max_concurrent_requests,
                'models': [model.to_dict() for model in self.ollama.models]
            },
            'processing_limits': {
                'max_file_size_text': self.processing_limits.max_file_size_text,
                'max_file_size_pdf': self.processing_limits.max_file_size_pdf,
                'max_file_size_video': self.processing_limits.max_file_size_video,
                'max_content_length': self.processing_limits.max_content_length,
                'max_summary_length': self.processing_limits.max_summary_length,
                'max_processing_time_seconds': self.processing_limits.max_processing_time_seconds,
                'max_concurrent_jobs': self.processing_limits.max_concurrent_jobs,
                'max_retry_attempts': self.processing_limits.max_retry_attempts,
                'max_memory_usage_mb': self.processing_limits.max_memory_usage_mb
            },
            'adhd_optimization': {
                'max_bullet_points_per_section': self.adhd_optimization.max_bullet_points_per_section,
                'max_sections': self.adhd_optimization.max_sections,
                'use_bullet_points': self.adhd_optimization.use_bullet_points,
                'simplify_vocabulary': self.adhd_optimization.simplify_vocabulary,
                'target_reading_level': self.adhd_optimization.target_reading_level
            },
            'logging': self.logging.to_dict(),
            'security': {
                'allowed_file_extensions': self.security.allowed_file_extensions,
                'blocked_directories': self.security.blocked_directories,
                'scan_for_malware': self.security.scan_for_malware
            },
            'temp_directory': self.temp_directory,
            'cache_directory': self.cache_directory,
            'output_directory': self.output_directory,
            'enable_caching': self.enable_caching,
            'cache_timeout_minutes': self.cache_timeout_minutes,
            'enable_monitoring': self.enable_monitoring
        }
