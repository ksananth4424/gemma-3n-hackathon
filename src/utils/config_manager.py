"""
Configuration Manager for Accessibility Assistant
Handles loading and managing configuration from JSON files
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class ConfigManager:
    """Manages configuration loading and access"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Optional path to configuration directory
        """
        if config_dir is None:
            # Default to config directory relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self._configs = {}
        self._load_configurations()
    
    def _load_configurations(self):
        """Load all configuration files"""
        config_files = {
            'service': 'service_config.json',
            'ai': 'ai_config.json', 
            'logging': 'logging_config.json'
        }
        
        for config_name, filename in config_files.items():
            config_path = self.config_dir / filename
            
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self._configs[config_name] = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading {filename}: {e}")
                    self._configs[config_name] = {}
            else:
                print(f"Configuration file not found: {config_path}")
                self._configs[config_name] = {}
    
    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            section: Configuration section (service, ai, logging)
            key: Specific key within section (optional)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if section not in self._configs:
            return default
        
        if key is None:
            return self._configs[section]
        
        return self._configs[section].get(key, default)
    
    def get_service_config(self) -> Dict[str, Any]:
        """Get service configuration"""
        return self._configs.get('service', {})
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI configuration"""
        return self._configs.get('ai', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self._configs.get('logging', {})
    
    def get_supported_formats(self) -> list:
        """Get list of supported file formats"""
        return self.get('service', 'supported_formats', [])
    
    def get_max_file_size_mb(self) -> int:
        """Get maximum file size in MB"""
        return self.get('service', 'max_file_size_mb', 100)
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """Get Ollama configuration"""
        return self.get('ai', 'ollama', {})
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration"""
        return self.get('ai', 'model', {})
    
    def reload(self):
        """Reload all configurations"""
        self._configs.clear()
        self._load_configurations()
