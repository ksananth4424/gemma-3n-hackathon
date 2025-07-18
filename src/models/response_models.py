"""
Response models for the Windows Accessibility Assistant
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import json


class ProcessingStatus(Enum):
    """Status of processing operations"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ErrorCode(Enum):
    """Error codes for different failure types"""
    # File errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_ACCESS_DENIED = "FILE_ACCESS_DENIED"
    FILE_CORRUPTED = "FILE_CORRUPTED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    
    # Processing errors
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    SUMMARIZATION_FAILED = "SUMMARIZATION_FAILED"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    PROCESSING_TIMEOUT = "PROCESSING_TIMEOUT"
    
    # System errors
    OLLAMA_CONNECTION_FAILED = "OLLAMA_CONNECTION_FAILED"
    INSUFFICIENT_MEMORY = "INSUFFICIENT_MEMORY"
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    
    # Configuration errors
    INVALID_CONFIGURATION = "INVALID_CONFIGURATION"
    INVALID_REQUEST = "INVALID_REQUEST"


@dataclass
class ProcessingError:
    """Error information for failed operations"""
    code: ErrorCode
    message: str
    details: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'code': self.code.value,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ProcessingMetrics:
    """Performance metrics for processing operations"""
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # File metrics
    file_size_bytes: int = 0
    content_length_chars: int = 0
    
    # Processing metrics
    model_used: Optional[str] = None
    tokens_processed: int = 0
    chunks_processed: int = 0
    
    # Resource usage
    peak_memory_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    def complete(self, end_time: Optional[datetime] = None):
        """Mark processing as complete and calculate duration"""
        if end_time is None:
            end_time = datetime.now()
        
        self.end_time = end_time
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration_seconds,
            'file_size_bytes': self.file_size_bytes,
            'content_length_chars': self.content_length_chars,
            'model_used': self.model_used,
            'tokens_processed': self.tokens_processed,
            'chunks_processed': self.chunks_processed,
            'peak_memory_mb': self.peak_memory_mb,
            'cpu_usage_percent': self.cpu_usage_percent
        }


@dataclass
class SummarySection:
    """A section of the generated summary"""
    title: str
    content: str
    bullet_points: List[str] = field(default_factory=list)
    importance_score: float = 0.0
    word_count: int = 0
    
    def __post_init__(self):
        """Calculate word count"""
        if not self.word_count:
            self.word_count = len(self.content.split())


@dataclass
class ProcessingSummary:
    """The generated summary content"""
    # Main content
    title: str
    overview: str
    sections: List[SummarySection] = field(default_factory=list)
    key_takeaways: List[str] = field(default_factory=list)
    
    # Metadata
    original_length: int = 0
    summary_length: int = 0
    compression_ratio: float = 0.0
    readability_score: float = 0.0
    
    # ADHD-specific features
    estimated_reading_time_minutes: float = 0.0
    cognitive_load_score: float = 0.0  # Lower is better for ADHD
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if not self.summary_length:
            self.summary_length = len(self.overview) + sum(
                len(section.content) for section in self.sections
            )
        
        if self.original_length > 0:
            self.compression_ratio = self.summary_length / self.original_length
        
        # Estimate reading time (200 WPM average)
        word_count = len(self.overview.split()) + sum(
            len(section.content.split()) for section in self.sections
        )
        self.estimated_reading_time_minutes = word_count / 200.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'title': self.title,
            'overview': self.overview,
            'sections': [
                {
                    'title': section.title,
                    'content': section.content,
                    'bullet_points': section.bullet_points,
                    'importance_score': section.importance_score,
                    'word_count': section.word_count
                }
                for section in self.sections
            ],
            'key_takeaways': self.key_takeaways,
            'original_length': self.original_length,
            'summary_length': self.summary_length,
            'compression_ratio': self.compression_ratio,
            'readability_score': self.readability_score,
            'estimated_reading_time_minutes': self.estimated_reading_time_minutes,
            'cognitive_load_score': self.cognitive_load_score
        }
    
    def to_formatted_text(self, adhd_friendly: bool = True) -> str:
        """Convert to formatted text output"""
        lines = []
        
        if adhd_friendly:
            lines.append("=" * 60)
            lines.append("ACCESSIBILITY SUMMARY")
            lines.append("=" * 60)
        
        lines.append(f"## {self.title}")
        lines.append("")
        lines.append("### Overview:")
        lines.append(self.overview)
        lines.append("")
        
        if self.sections:
            for i, section in enumerate(self.sections, 1):
                lines.append(f"### {i}. {section.title}")
                if section.bullet_points and adhd_friendly:
                    for point in section.bullet_points:
                        lines.append(f"• {point}")
                else:
                    lines.append(section.content)
                lines.append("")
        
        if self.key_takeaways:
            lines.append("### Key Takeaways:")
            for takeaway in self.key_takeaways:
                lines.append(f"• {takeaway}")
            lines.append("")
        
        if adhd_friendly:
            lines.append(f"📖 Estimated reading time: {self.estimated_reading_time_minutes:.1f} minutes")
            lines.append(f"📊 Content reduced by {(1-self.compression_ratio)*100:.0f}%")
            lines.append("=" * 60)
        
        return "\n".join(lines)


@dataclass
class ProcessingResponse:
    """Main response for content processing"""
    session_id: str
    status: ProcessingStatus
    
    # Success data
    summary: Optional[ProcessingSummary] = None
    output_file: Optional[str] = None
    
    # Error data
    error: Optional[ProcessingError] = None
    
    # Metadata
    metrics: Optional[ProcessingMetrics] = None
    request_timestamp: datetime = field(default_factory=datetime.now)
    response_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Set response timestamp"""
        if self.response_timestamp is None:
            self.response_timestamp = datetime.now()
    
    @property
    def is_successful(self) -> bool:
        """Check if processing was successful"""
        return self.status == ProcessingStatus.COMPLETED and self.summary is not None
    
    @property
    def has_error(self) -> bool:
        """Check if there was an error"""
        return self.error is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            'session_id': self.session_id,
            'status': self.status.value,
            'request_timestamp': self.request_timestamp.isoformat(),
            'response_timestamp': self.response_timestamp.isoformat() if self.response_timestamp else None
        }
        
        if self.summary:
            result['summary'] = self.summary.to_dict()
        
        if self.output_file:
            result['output_file'] = self.output_file
        
        if self.error:
            result['error'] = self.error.to_dict()
        
        if self.metrics:
            result['metrics'] = self.metrics.to_dict()
        
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)


@dataclass
class BatchProcessingResponse:
    """Response for batch processing operations"""
    batch_id: str
    session_id: str
    total_files: int
    completed_files: int = 0
    failed_files: int = 0
    
    individual_responses: List[ProcessingResponse] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def is_complete(self) -> bool:
        """Check if batch processing is complete"""
        return (self.completed_files + self.failed_files) >= self.total_files
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total_processed = self.completed_files + self.failed_files
        if total_processed == 0:
            return 0.0
        return self.completed_files / total_processed
    
    def add_response(self, response: ProcessingResponse):
        """Add an individual response to the batch"""
        self.individual_responses.append(response)
        
        if response.is_successful:
            self.completed_files += 1
        else:
            self.failed_files += 1
        
        # Check if batch is complete
        if self.is_complete and self.end_time is None:
            self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'batch_id': self.batch_id,
            'session_id': self.session_id,
            'total_files': self.total_files,
            'completed_files': self.completed_files,
            'failed_files': self.failed_files,
            'success_rate': self.success_rate,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'individual_responses': [resp.to_dict() for resp in self.individual_responses]
        }
