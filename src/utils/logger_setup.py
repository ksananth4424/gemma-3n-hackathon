"""
Logging setup for Accessibility Assistant
Configures logging based on configuration files
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional
import json


def setup_logging(log_level: int = logging.INFO, config_path: Optional[str] = None):
    """
    Setup logging configuration
    
    Args:
        log_level: Default log level
        config_path: Path to logging configuration file
    """
    
    if config_path is None:
        # Default to logging config in project
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "logging_config.json"
    
    # Create logs directory if it doesn't exist
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Try to load logging configuration
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update file paths to be absolute
            for handler_name, handler_config in config.get('handlers', {}).items():
                if 'filename' in handler_config:
                    filename = handler_config['filename']
                    if not os.path.isabs(filename):
                        handler_config['filename'] = str(logs_dir / filename)
            
            logging.config.dictConfig(config)
            
        except (json.JSONDecodeError, KeyError) as e:
            # Fall back to basic configuration
            setup_basic_logging(log_level, logs_dir)
            logging.warning(f"Error loading logging config, using basic setup: {e}")
    else:
        # Fall back to basic configuration
        setup_basic_logging(log_level, logs_dir)
        logging.info("No logging config found, using basic setup")


def setup_basic_logging(log_level: int, logs_dir: Path):
    """
    Setup basic logging configuration as fallback
    
    Args:
        log_level: Log level to use
        logs_dir: Directory for log files
    """
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(
        logs_dir / "accessibility_assistant.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler(
        logs_dir / "errors.log",
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with specified name
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
