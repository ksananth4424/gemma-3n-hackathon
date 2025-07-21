"""
Main Content Processor - Orchestrates all content processing with DI
"""

import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

from ..utils.dependency_injection import singleton, injectable
from ..utils.config_manager import ConfigManager
from ..service.ollama_service import OllamaService, ContentType

logger = logging.getLogger('accessibility_assistant.content_processor')


@singleton
@injectable  
class ContentProcessor:
    """
    Main content processor with dependency injection
    """
    
    def __init__(self, config_manager: ConfigManager, ollama_service: OllamaService):
        self.config = config_manager
        self.ollama_service = ollama_service
        
        # Lazy loading of processors to avoid circular dependencies
        self._pdf_processor = None
        self._video_processor = None
        self._text_processor = None
        
        # File type mapping
        self.processor_mapping = {
            '.pdf': ContentType.PDF,
            '.mp4': ContentType.VIDEO,
            '.avi': ContentType.VIDEO,
            '.mov': ContentType.VIDEO,
            '.mkv': ContentType.VIDEO,
            '.wmv': ContentType.VIDEO,
            '.txt': ContentType.TEXT,
            '.md': ContentType.TEXT,
            '.docx': ContentType.TEXT,
            '.rtf': ContentType.TEXT
        }
        
        logger.info("Content processor initialized with dependency injection")
    
    @property
    def pdf_processor(self):
        """Lazy load PDF processor"""
        if self._pdf_processor is None:
            from .pdf_processor import PDFProcessor
            self._pdf_processor = PDFProcessor(self.config)
        return self._pdf_processor
    
    @property
    def video_processor(self):
        """Lazy load video processor"""
        if self._video_processor is None:
            from .video_processor import VideoProcessor
            self._video_processor = VideoProcessor(self.config)
        return self._video_processor
    
    @property
    def text_processor(self):
        """Lazy load text processor"""
        if self._text_processor is None:
            from .text_processor import TextProcessor
            self._text_processor = TextProcessor(self.config)
        return self._text_processor
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process file and generate accessibility summary
        
        Args:
            file_path: Path to file to process
            
        Returns:
            Processing result dictionary
        """
        start_time = time.time()
        
        try:
            # Validate file
            if not self._validate_file(file_path):
                return self._create_error_result(
                    file_path, "Invalid file or file not found", start_time
                )
            
            # Get processor and content type
            content_type = self._get_content_type(file_path)
            if not content_type:
                return self._create_error_result(
                    file_path, "Unsupported file type", start_time
                )
            
            logger.info(f"Processing {file_path} as {content_type.value}")
            
            # Extract content using appropriate processor
            extracted_content = self._extract_content(file_path, content_type)
            
            if not extracted_content or not extracted_content.strip():
                return self._create_error_result(
                    file_path, "No content could be extracted from file", start_time
                )
            
            logger.debug(f"Extracted {len(extracted_content)} characters of content")
            
            # Generate AI summary
            summary_result = self.ollama_service.generate_summary(
                extracted_content, content_type
            )
            
            # Create successful result with structured summaries
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'file_path': file_path,
                'content_type': content_type.value,
                'summary': summary_result.get('paragraph', ''),  # For backward compatibility
                'structured_summary': summary_result,  # New structured format
                'content': extracted_content,  # Raw extracted content
                'metadata': {
                    'file_size': os.path.getsize(file_path),
                    'content_length': len(extracted_content),
                    'processing_time': processing_time
                }
            }
            
            logger.info(f"Successfully processed {file_path} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return self._create_error_result(file_path, str(e), start_time)
    
    def _extract_content(self, file_path: str, content_type: ContentType) -> str:
        """Extract content using appropriate processor"""
        if content_type == ContentType.PDF:
            return self.pdf_processor.extract_content(file_path)
        elif content_type == ContentType.VIDEO:
            return self.video_processor.extract_content(file_path)
        elif content_type == ContentType.TEXT:
            return self.text_processor.extract_content(file_path)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")
    
    def _validate_file(self, file_path: str) -> bool:
        """Validate file exists and is accessible"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return False
            
            if not os.path.isfile(file_path):
                logger.error(f"Path is not a file: {file_path}")
                return False
            
            file_size = os.path.getsize(file_path)
            max_size_mb = self.config.get('service', 'max_file_size_mb', 500)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                logger.error(f"File too large: {file_size} bytes > {max_size_bytes} bytes")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"File validation error: {e}")
            return False
    
    def _get_content_type(self, file_path: str) -> Optional[ContentType]:
        """Get content type for file"""
        file_extension = Path(file_path).suffix.lower()
        return self.processor_mapping.get(file_extension)
    
    def _create_error_result(self, file_path: str, error: str, start_time: float) -> Dict[str, Any]:
        """Create error result dictionary"""
        return {
            'success': False,
            'file_path': file_path,
            'error': error,
            'metadata': {
                'processing_time': time.time() - start_time
            }
        }
    
    def get_supported_formats(self) -> list:
        """Get list of supported file formats"""
        return list(self.processor_mapping.keys())
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file type is supported"""
        file_extension = Path(file_path).suffix.lower()
        return file_extension in self.processor_mapping
