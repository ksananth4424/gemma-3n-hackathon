"""
Enhanced configuration management with support for data models
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import logging

from src.models.config_models import ApplicationConfig, LogLevel
from src.utils.logger_setup import setup_logging


class EnhancedConfigManager:
    """Enhanced configuration manager with data model support"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to config directory relative to project root
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        
        self.config_dir.mkdir(exist_ok=True)
        
        # Configuration files
        self.main_config_file = self.config_dir / "main_config.json"
        self.service_config_file = self.config_dir / "service_config.json"
        self.ai_config_file = self.config_dir / "ai_config.json"
        self.logging_config_file = self.config_dir / "logging_config.json"
        
        # Cached configuration
        self._config: Optional[ApplicationConfig] = None
        self._config_loaded = False
    
    def get_config(self) -> ApplicationConfig:
        """Get the complete application configuration"""
        if not self._config_loaded:
            self._load_configuration()
        return self._config
    
    def _load_configuration(self):
        """Load configuration from files or create defaults"""
        try:
            # Try to load main configuration
            if self.main_config_file.exists():
                self._config = ApplicationConfig.load_from_file(str(self.main_config_file))
                self.logger.info(f"Configuration loaded from {self.main_config_file}")
            else:
                # Create default configuration
                self._config = ApplicationConfig()
                self.save_configuration()
                self.logger.info("Created default configuration")
            
            # Load additional configurations and merge
            self._merge_additional_configs()
            
            self._config_loaded = True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Fall back to default configuration
            self._config = ApplicationConfig()
            self._config_loaded = True
    
    def _merge_additional_configs(self):
        """Merge additional configuration files"""
        
        # Load service configuration
        if self.service_config_file.exists():
            try:
                with open(self.service_config_file, 'r', encoding='utf-8') as f:
                    service_data = json.load(f)
                
                # Update Ollama configuration
                if 'ollama' in service_data:
                    ollama_data = service_data['ollama']
                    if 'base_url' in ollama_data:
                        self._config.ollama.base_url = ollama_data['base_url']
                    if 'timeout_seconds' in ollama_data:
                        self._config.ollama.timeout_seconds = ollama_data['timeout_seconds']
                
                # Update processing limits
                if 'processing_limits' in service_data:
                    limits_data = service_data['processing_limits']
                    for key, value in limits_data.items():
                        if hasattr(self._config.processing_limits, key):
                            setattr(self._config.processing_limits, key, value)
                
                self.logger.debug("Service configuration merged")
                
            except Exception as e:
                self.logger.warning(f"Failed to load service configuration: {e}")
        
        # Load AI configuration
        if self.ai_config_file.exists():
            try:
                with open(self.ai_config_file, 'r', encoding='utf-8') as f:
                    ai_data = json.load(f)
                
                # Update ADHD optimization settings
                if 'adhd_optimization' in ai_data:
                    adhd_data = ai_data['adhd_optimization']
                    for key, value in adhd_data.items():
                        if hasattr(self._config.adhd_optimization, key):
                            setattr(self._config.adhd_optimization, key, value)
                
                self.logger.debug("AI configuration merged")
                
            except Exception as e:
                self.logger.warning(f"Failed to load AI configuration: {e}")
    
    def save_configuration(self):
        """Save the current configuration to files"""
        try:
            if self._config is None:
                self.logger.warning("No configuration to save")
                return
            
            # Save main configuration
            self._config.save_to_file(str(self.main_config_file))
            
            # Save individual configuration files for easier editing
            self._save_service_config()
            self._save_ai_config()
            self._save_logging_config()
            
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def _save_service_config(self):
        """Save service-specific configuration"""
        service_config = {
            "ollama": {
                "base_url": self._config.ollama.base_url,
                "timeout_seconds": self._config.ollama.timeout_seconds,
                "max_concurrent_requests": self._config.ollama.max_concurrent_requests,
                "health_check_interval_seconds": self._config.ollama.health_check_interval_seconds,
                "models": [model.to_dict() for model in self._config.ollama.models]
            },
            "processing_limits": {
                "max_file_size_text": self._config.processing_limits.max_file_size_text,
                "max_file_size_pdf": self._config.processing_limits.max_file_size_pdf,
                "max_file_size_video": self._config.processing_limits.max_file_size_video,
                "max_content_length": self._config.processing_limits.max_content_length,
                "max_summary_length": self._config.processing_limits.max_summary_length,
                "max_processing_time_seconds": self._config.processing_limits.max_processing_time_seconds,
                "max_concurrent_jobs": self._config.processing_limits.max_concurrent_jobs,
                "max_retry_attempts": self._config.processing_limits.max_retry_attempts,
                "max_memory_usage_mb": self._config.processing_limits.max_memory_usage_mb
            }
        }
        
        with open(self.service_config_file, 'w', encoding='utf-8') as f:
            json.dump(service_config, f, indent=2)
    
    def _save_ai_config(self):
        """Save AI-specific configuration"""
        ai_config = {
            "adhd_optimization": {
                "max_bullet_points_per_section": self._config.adhd_optimization.max_bullet_points_per_section,
                "max_sections": self._config.adhd_optimization.max_sections,
                "use_bullet_points": self._config.adhd_optimization.use_bullet_points,
                "simplify_vocabulary": self._config.adhd_optimization.simplify_vocabulary,
                "target_reading_level": self._config.adhd_optimization.target_reading_level,
                "include_reading_time": self._config.adhd_optimization.include_reading_time
            },
            "model_prompts": {
                "adhd_summary_prompt": '''Create an ADHD-friendly summary that:
1. Uses clear, simple language (grade 8 reading level)
2. Organizes information with headers and bullet points
3. Limits each section to 3-5 key points maximum
4. Avoids jargon and complex sentences
5. Highlights the most important takeaways
6. Uses active voice and concrete examples

Focus on making the content easy to scan and understand for someone with ADHD.''',
                "text_processing_prompt": "Summarize this text content in an accessible, ADHD-friendly format.",
                "pdf_processing_prompt": "Extract and summarize the key information from this PDF in an ADHD-friendly format.",
                "video_processing_prompt": "Create an ADHD-friendly summary of this video transcript, focusing on main points and actionable information."
            }
        }
        
        with open(self.ai_config_file, 'w', encoding='utf-8') as f:
            json.dump(ai_config, f, indent=2)
    
    def _save_logging_config(self):
        """Save logging configuration"""
        logging_config = self._config.logging.to_dict()
        
        with open(self.logging_config_file, 'w', encoding='utf-8') as f:
            json.dump(logging_config, f, indent=2)
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """Get Ollama-specific configuration"""
        config = self.get_config()
        return {
            'base_url': config.ollama.base_url,
            'timeout_seconds': config.ollama.timeout_seconds,
            'max_concurrent_requests': config.ollama.max_concurrent_requests,
            'models': [model.to_dict() for model in config.ollama.models]
        }
    
    def get_processing_limits(self) -> Dict[str, Any]:
        """Get processing limits configuration"""
        config = self.get_config()
        return {
            'max_file_size_text': config.processing_limits.max_file_size_text,
            'max_file_size_pdf': config.processing_limits.max_file_size_pdf,
            'max_file_size_video': config.processing_limits.max_file_size_video,
            'max_content_length': config.processing_limits.max_content_length,
            'max_summary_length': config.processing_limits.max_summary_length,
            'max_processing_time_seconds': config.processing_limits.max_processing_time_seconds,
            'max_concurrent_jobs': config.processing_limits.max_concurrent_jobs,
            'max_retry_attempts': config.processing_limits.max_retry_attempts,
            'max_memory_usage_mb': config.processing_limits.max_memory_usage_mb
        }
    
    def get_adhd_optimization_config(self) -> Dict[str, Any]:
        """Get ADHD optimization configuration"""
        config = self.get_config()
        return {
            'max_bullet_points_per_section': config.adhd_optimization.max_bullet_points_per_section,
            'max_sections': config.adhd_optimization.max_sections,
            'use_bullet_points': config.adhd_optimization.use_bullet_points,
            'simplify_vocabulary': config.adhd_optimization.simplify_vocabulary,
            'target_reading_level': config.adhd_optimization.target_reading_level,
            'include_reading_time': config.adhd_optimization.include_reading_time
        }
    
    def setup_logging(self):
        """Setup logging based on configuration"""
        config = self.get_config()
        setup_logging(
            level=config.logging.level.value,
            log_file=config.logging.log_file_path if config.logging.log_to_file else None,
            console_output=config.logging.log_to_console,
            json_format=config.logging.use_json_format
        )


# Keep the original ConfigManager for backward compatibility
# but make it use the enhanced version internally
class ConfigManager(EnhancedConfigManager):
    """Backward compatible configuration manager"""
    
    def get_service_config(self) -> Dict[str, Any]:
        """Get service configuration (backward compatibility)"""
        config = self.get_config()
        return {
            "ollama": {
                "base_url": config.ollama.base_url,
                "timeout_seconds": config.ollama.timeout_seconds,
                "max_retries": config.ollama.max_concurrent_requests,
                "health_check_enabled": True,
                "health_check_interval": config.ollama.health_check_interval_seconds
            },
            "file_processing": {
                "max_file_size_mb": config.processing_limits.max_file_size_text // (1024 * 1024),
                "supported_formats": config.security.allowed_file_extensions,
                "temp_directory": config.temp_directory,
                "cleanup_temp_files": True
            },
            "performance": {
                "max_concurrent_jobs": config.processing_limits.max_concurrent_jobs,
                "processing_timeout_seconds": config.processing_limits.max_processing_time_seconds,
                "memory_limit_mb": config.processing_limits.max_memory_usage_mb
            }
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI configuration (backward compatibility)"""
        config = self.get_config()
        return {
            "models": {
                "text_model": "gemma3n:e2b",
                "video_model": "gemma3n:e4b", 
                "fallback_model": "gemma3n:e2b"
            },
            "summarization": {
                "max_length": config.processing_limits.max_summary_length,
                "style": "bullet_points" if config.adhd_optimization.use_bullet_points else "paragraph",
                "focus": "accessibility",
                "language_level": "simple" if config.adhd_optimization.simplify_vocabulary else "normal"
            },
            "adhd_optimization": {
                "use_headers": config.adhd_optimization.use_headers,
                "max_points_per_section": config.adhd_optimization.max_bullet_points_per_section,
                "include_reading_time": config.adhd_optimization.include_reading_time,
                "visual_separators": config.adhd_optimization.add_visual_separators
            }
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration (backward compatibility)"""
        config = self.get_config()
        return {
            "level": config.logging.level.value,
            "file_logging": {
                "enabled": config.logging.log_to_file,
                "file": config.logging.log_file_path,
                "max_size_mb": config.logging.max_file_size_mb,
                "backup_count": config.logging.backup_count
            },
            "console_logging": {
                "enabled": config.logging.log_to_console,
                "colored": True,
                "format": config.logging.console_format
            }
        }
