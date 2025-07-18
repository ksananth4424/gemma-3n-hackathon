"""
Request models for the Windows Accessibility Assistant
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path
import json


class OutputFormat(Enum):
    """Supported output formats"""
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class ProcessingPriority(Enum):
    """Processing priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ContentType(Enum):
    """Content types for processing"""
    TEXT = "text"
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"


@dataclass
class ProcessingOptions:
    """Options for content processing"""
    # Output configuration
    output_format: OutputFormat = OutputFormat.TEXT
    output_file: Optional[str] = None
    
    # Processing behavior
    priority: ProcessingPriority = ProcessingPriority.NORMAL
    max_summary_length: int = 500
    include_timestamps: bool = False
    
    # ADHD-specific options
    use_bullet_points: bool = True
    include_key_takeaways: bool = True
    simplify_language: bool = True
    max_points_per_section: int = 5
    
    # Advanced options
    force_model: Optional[str] = None
    enable_ocr: bool = True
    extract_metadata: bool = False
    
    # Performance options
    timeout_seconds: int = 300
    chunk_size: int = 4096
    parallel_processing: bool = False


@dataclass
class ProcessingRequest:
    """Main request for content processing"""
    file_path: str
    options: ProcessingOptions = field(default_factory=ProcessingOptions)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate request after initialization"""
        if not self.file_path:
            raise ValueError("file_path is required")
        
        file_path = Path(self.file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        # Generate session ID if not provided
        if not self.session_id:
            import uuid
            self.session_id = str(uuid.uuid4())
    
    @property
    def content_type(self) -> ContentType:
        """Determine content type from file extension"""
        suffix = Path(self.file_path).suffix.lower()
        
        if suffix in ['.txt', '.md', '.rtf']:
            return ContentType.TEXT
        elif suffix == '.pdf':
            return ContentType.PDF
        elif suffix in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
            return ContentType.VIDEO
        elif suffix in ['.mp3', '.wav', '.flac', '.aac']:
            return ContentType.AUDIO
        elif suffix in ['.docx', '.doc', '.odt']:
            return ContentType.DOCUMENT
        elif suffix in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            return ContentType.IMAGE
        else:
            return ContentType.TEXT  # Default fallback
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'file_path': self.file_path,
            'content_type': self.content_type.value,
            'options': {
                'output_format': self.options.output_format.value,
                'output_file': self.options.output_file,
                'priority': self.options.priority.value,
                'max_summary_length': self.options.max_summary_length,
                'include_timestamps': self.options.include_timestamps,
                'use_bullet_points': self.options.use_bullet_points,
                'include_key_takeaways': self.options.include_key_takeaways,
                'simplify_language': self.options.simplify_language,
                'max_points_per_section': self.options.max_points_per_section,
                'force_model': self.options.force_model,
                'enable_ocr': self.options.enable_ocr,
                'extract_metadata': self.options.extract_metadata,
                'timeout_seconds': self.options.timeout_seconds,
                'chunk_size': self.options.chunk_size,
                'parallel_processing': self.options.parallel_processing
            },
            'user_id': self.user_id,
            'session_id': self.session_id,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingRequest':
        """Create from dictionary"""
        options_data = data.get('options', {})
        options = ProcessingOptions(
            output_format=OutputFormat(options_data.get('output_format', 'text')),
            output_file=options_data.get('output_file'),
            priority=ProcessingPriority(options_data.get('priority', 'normal')),
            max_summary_length=options_data.get('max_summary_length', 500),
            include_timestamps=options_data.get('include_timestamps', False),
            use_bullet_points=options_data.get('use_bullet_points', True),
            include_key_takeaways=options_data.get('include_key_takeaways', True),
            simplify_language=options_data.get('simplify_language', True),
            max_points_per_section=options_data.get('max_points_per_section', 5),
            force_model=options_data.get('force_model'),
            enable_ocr=options_data.get('enable_ocr', True),
            extract_metadata=options_data.get('extract_metadata', False),
            timeout_seconds=options_data.get('timeout_seconds', 300),
            chunk_size=options_data.get('chunk_size', 4096),
            parallel_processing=options_data.get('parallel_processing', False)
        )
        
        return cls(
            file_path=data['file_path'],
            options=options,
            user_id=data.get('user_id'),
            session_id=data.get('session_id'),
            metadata=data.get('metadata', {})
        )


@dataclass
class BatchProcessingRequest:
    """Request for processing multiple files"""
    file_paths: List[str]
    options: ProcessingOptions = field(default_factory=ProcessingOptions)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    batch_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate batch request"""
        if not self.file_paths:
            raise ValueError("file_paths cannot be empty")
        
        # Check all files exist
        for file_path in self.file_paths:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate IDs if not provided
        if not self.session_id:
            import uuid
            self.session_id = str(uuid.uuid4())
        
        if not self.batch_id:
            import uuid
            self.batch_id = str(uuid.uuid4())
    
    def get_individual_requests(self) -> List[ProcessingRequest]:
        """Convert to individual processing requests"""
        requests = []
        for file_path in self.file_paths:
            request = ProcessingRequest(
                file_path=file_path,
                options=self.options,
                user_id=self.user_id,
                session_id=self.session_id,
                metadata={'batch_id': self.batch_id}
            )
            requests.append(request)
        return requests
