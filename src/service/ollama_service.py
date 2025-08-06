"""
Ollama Service for AI model interaction
Handles model selection, initialization, and inference
"""

import ollama
import logging
import time
import re
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
    def generate_summary(self, content: str, content_type: ContentType, **kwargs) -> Dict[str, str]:
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
            # Define model selection rules - prioritize custom models with source references
            if content_type in [ContentType.VIDEO, ContentType.AUDIO]:
                # Use larger model for complex audio/video content
                preferred_models = ['accessibility-e4b', 'gemma3n:e4b']
            elif content_type == ContentType.PDF and content_length > 10000:
                # Use larger model for long PDFs
                preferred_models = ['accessibility-e4b', 'gemma3n:e4b']
            else:
                # Use smaller, faster model for text and short content
                preferred_models = ['accessibility-e2b', 'gemma3n:e2b']
            
            # Find first available model from preferred list
            for model_name in preferred_models:
                # Check both with and without :latest suffix
                available_names = [model_name, f"{model_name}:latest"]
                for name in available_names:
                    if name in self._models_cache:
                        logger.debug(f"Selected model {name} for {content_type.value}")
                        return name
            
            # Fallback to any available model
            available_models = list(self._models_cache.keys())
            if available_models:
                fallback = available_models[0]
                logger.warning(f"Using fallback model {fallback} for {content_type.value}")
                return fallback
            
            raise RuntimeError("No models available")
    
    def generate_summary(self, content: str, content_type: ContentType, **kwargs) -> Dict[str, str]:
        """
        Generate structured ADHD-friendly summary using appropriate model
        
        Args:
            content: Content to summarize
            content_type: Type of content
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with structured summary sections
        """
        try:
            # Select appropriate model
            model_name = self._select_model(content_type, len(content))
            
            # Get AI configuration
            ai_config = self.config.get_ai_config()
            
            # Build structured prompt
            prompt = self._build_structured_prompt(content, content_type)
            
            # Generate response with better settings for complete summaries
            response = self.client.chat(
                model=model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': "You are an expert at creating ADHD-friendly summaries. Always provide complete, well-structured responses that finish properly."
                    },
                    {
                        'role': 'user', 
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,  # Lower for more consistent structure
                    'top_p': 0.9,
                    'top_k': 40,
                    'num_predict': 800,  # Increased to allow complete summaries
                    'num_ctx': 4096     # Larger context for better understanding
                }
            )
            
            raw_summary = response['message']['content']
            logger.info(f"Generated summary using {model_name} ({len(raw_summary)} chars)")
            print(f"DEBUG: Full raw response: {repr(raw_summary)}")
            
            # Parse structured response
            result = self._parse_structured_summary(raw_summary)
            print(f"DEBUG: Parse result: {result}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._create_fallback_summary(content)
    
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

    def _build_structured_prompt(self, content: str, content_type: ContentType) -> str:
        """Build structured prompt for consistent UI section output"""
        ai_config = self.config.get_ai_config()
        prompts = ai_config.get('model_prompts', {})
        
        # Get the structured prompt template
        base_prompt = prompts.get('structured_summary_prompt', '')
        
        # Get content-specific prompt
        if content_type == ContentType.PDF:
            content_prompt = prompts.get('pdf_processing_prompt', '')
        elif content_type in [ContentType.VIDEO, ContentType.AUDIO]:
            content_prompt = prompts.get('video_processing_prompt', '')
        else:
            content_prompt = prompts.get('text_processing_prompt', '')
        
        # Optimize content length for faster processing
        performance_config = ai_config.get('performance', {})
        max_length = performance_config.get('max_content_length', 3000)
        
        if len(content) > max_length:
            content = content[:max_length] + "...\n[Content truncated for faster processing]"
        
        return f"{content_prompt}\n\n{base_prompt}\n\nContent to analyze:\n{content}"
    
    def _parse_structured_summary(self, raw_summary: str) -> Dict[str, Any]:
        """Parse structured summary with robust error handling and source extraction"""
        logger.debug(f"Raw summary to parse: {raw_summary}")
        
        result = {
            'tldr': '',
            'bullets': [],
            'paragraph': '',
            'sources': {
                'tldr': '',
                'bullets': [],
                'paragraph': []
            }
        }
        
        try:
            # Clean up the input text - remove artifacts and normalize whitespace
            cleaned_summary = self._clean_raw_text(raw_summary)
            logger.debug(f"Cleaned summary: {cleaned_summary}")
            
            # Parse each section using robust extraction methods
            self._extract_tldr_section(cleaned_summary, result)
            self._extract_bullets_section(cleaned_summary, result)
            self._extract_paragraph_section(cleaned_summary, result)
            
            # If parsing completely fails, use intelligent fallback
            if not any([result['tldr'], result['bullets'], result['paragraph']]):
                logger.warning("Primary parsing failed, using intelligent fallback")
                self._apply_intelligent_fallback(raw_summary, result)
            
            logger.debug(f"Final parsed result: {result}")
            
        except Exception as e:
            logger.warning(f"Failed to parse structured summary: {e}")
            self._apply_emergency_fallback(raw_summary, result)
        
        return result

    def _clean_raw_text(self, text: str) -> str:
        """Clean and normalize raw text"""
        # Remove termination tokens
        text = re.sub(r'<\|[^|]*\|>', '', text)
        # Remove duplicate newlines
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        # Remove markdown headers at start of lines
        text = re.sub(r'^#+\s+.*?\n', '', text, flags=re.MULTILINE)
        return text.strip()

    def _extract_source_from_text(self, text: str) -> tuple[str, str]:
        """Extract source reference from text using simple string operations"""
        if not text:
            return "", ""
            
        original_text = text
        text = text.strip()
        
        # Debug logging to see what's being processed
        if '-' in text and len(text) < 200:
            print(f"DEBUG: Processing text with hyphen: {repr(text)}")
        
        # Look for sources in parentheses at the end
        if text.endswith(')') and '(' in text:
            # Find the last opening parenthesis
            last_paren = text.rfind('(')
            if last_paren > 0:
                source = text[last_paren+1:-1].strip()
                cleaned_text = text[:last_paren].strip()
                print(f"DEBUG: Found parentheses source: {repr(cleaned_text)} -> {repr(source)}")
                return cleaned_text, source
        
        # Look for sources in brackets at the end
        if text.endswith(']') and '[' in text:
            # Find the last opening bracket
            last_bracket = text.rfind('[')
            if last_bracket > 0:
                source = text[last_bracket+1:-1].strip()
                cleaned_text = text[:last_bracket].strip()
                print(f"DEBUG: Found bracket source: {repr(cleaned_text)} -> {repr(source)}")
                return cleaned_text, source
        
        # No source found, return original text
        return text, ""

    def _extract_tldr_section(self, text: str, result: dict):
        """Extract TL;DR section with simple string operations"""
        # Simple approach: find **TL;DR:** and get everything until next **section
        if '**TL;DR:**' in text:
            start_marker = '**TL;DR:**'
            start_pos = text.find(start_marker)
            if start_pos != -1:
                # Get text after the marker
                after_marker = text[start_pos + len(start_marker):].strip()
                
                # Find where it ends (at next ** section)
                end_pos = after_marker.find('**KEY POINTS')
                if end_pos == -1:
                    end_pos = after_marker.find('**FULL SUMMARY')
                if end_pos == -1:
                    end_pos = after_marker.find('**SOURCES')
                if end_pos == -1:
                    # Use until newline or end
                    end_pos = after_marker.find('\n')
                    if end_pos == -1:
                        tldr_text = after_marker.strip()
                    else:
                        tldr_text = after_marker[:end_pos].strip()
                else:
                    tldr_text = after_marker[:end_pos].strip()
                
                if tldr_text:
                    # Clean and extract source
                    cleaned_tldr, source = self._extract_source_from_text(tldr_text)
                    
                    if cleaned_tldr:
                        result['tldr'] = cleaned_tldr
                        result['sources']['tldr'] = source if source else "Content"
                        return
        
        print("DEBUG: No **TL;DR:** section found")

    def _extract_bullets_section(self, text: str, result: dict):
        """Extract bullets section with simple string operations"""
        # Simple approach: find **KEY POINTS:** and get bullet lines until next **section
        if '**KEY POINTS:**' in text:
            start_marker = '**KEY POINTS:**'
            start_pos = text.find(start_marker)
            if start_pos != -1:
                # Get text after the marker
                after_marker = text[start_pos + len(start_marker):].strip()
                
                # Find where it ends (at next ** section)
                end_pos = after_marker.find('**FULL SUMMARY')
                if end_pos == -1:
                    end_pos = after_marker.find('**SOURCES')
                if end_pos == -1:
                    # Use the whole remaining text
                    bullets_text = after_marker.strip()
                else:
                    bullets_text = after_marker[:end_pos].strip()
                
                # Parse bullet lines
                bullets, sources = self._parse_bullet_list(bullets_text)
                if bullets:
                    result['bullets'] = bullets
                    result['sources']['bullets'] = sources
                    return
        
        print("DEBUG: No **KEY POINTS:** section found")

    def _parse_bullet_list(self, bullets_text: str) -> tuple[list, list]:
        """Parse bullet list text into bullets and sources"""
        cleaned_bullets = []
        bullet_sources = []
        
        # Split into lines and process each potential bullet
        lines = bullets_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for bullet markers (•, -, *, or numbers) - be more specific about dash
            if line.startswith('- ') or line.startswith('• ') or line.startswith('* ') or re.match(r'^\d+\.\s', line):
                # Extract the content after the bullet marker
                if line.startswith('- '):
                    bullet_content = line[2:].strip()
                elif line.startswith('• '):
                    bullet_content = line[2:].strip()
                elif line.startswith('* '):
                    bullet_content = line[2:].strip()
                else:  # numbered list
                    bullet_content = re.sub(r'^\d+\.\s*', '', line).strip()
                
                # Debug hyphen cutting
                if '-' in bullet_content and len(bullet_content) < 100:
                    print(f"DEBUG: Bullet content with hyphen: {repr(bullet_content)}")
                
                # Extract source and clean text
                cleaned_text, source = self._extract_source_from_text(bullet_content)
                
                # Clean up markdown formatting
                cleaned_text = re.sub(r'\*\*([^*]+)\*\*:\s*', r'\1: ', cleaned_text)
                cleaned_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned_text)
                
                # Handle source defaults - avoid Para X fallback
                if not source:
                    source = "Content"  # Simple default instead of Para X
                elif source.lower() in ['source', 'sources']:
                    # Look for section markers or use paragraph number
                    section_markers = re.findall(r'\[SOURCE_MARKER:\s*([^]]+)\]', bullet_content)
                    if section_markers:
                        source = section_markers[-1].strip()
                    else:
                        para_num = len(cleaned_bullets) + 1
                        source = f"Para {para_num}"
                
                # Only add if bullet has meaningful content
                if cleaned_text and len(cleaned_text) > 5:
                    cleaned_bullets.append(cleaned_text)
                    bullet_sources.append(source)
        
        return cleaned_bullets, bullet_sources

    def _extract_paragraph_section(self, text: str, result: dict):
        """Extract paragraph section with simple string operations"""
        print(f"DEBUG: Extracting paragraph from text: {repr(text[:200])}...")
        
        # Simple approach: find **FULL SUMMARY:** and get everything until **SOURCES:**
        if '**FULL SUMMARY:**' in text:
            start_marker = '**FULL SUMMARY:**'
            start_pos = text.find(start_marker)
            if start_pos != -1:
                # Get text after the marker
                after_marker = text[start_pos + len(start_marker):].strip()
                
                # Find where it ends (at **SOURCES:** or end of text)
                end_pos = after_marker.find('**SOURCES:')
                if end_pos == -1:
                    end_pos = after_marker.find('**SOURCES:**')
                if end_pos == -1:
                    # Use the whole remaining text
                    paragraph_text = after_marker.strip()
                else:
                    paragraph_text = after_marker[:end_pos].strip()
                
                print(f"DEBUG: Extracted paragraph: {repr(paragraph_text[:100])}...")
                
                if paragraph_text:
                    # Just clean up basic artifacts
                    paragraph_text = paragraph_text.replace('<|file_separator|>', '').strip()
                    if paragraph_text and paragraph_text[-1] not in '.!?':
                        paragraph_text = paragraph_text + '.'
                    
                    result['paragraph'] = paragraph_text
                    result['sources']['paragraph'] = ['Full Content']
                    return
        
        print("DEBUG: No **FULL SUMMARY:** section found")

    def _clean_paragraph_text(self, text: str) -> str:
        """Clean and format paragraph text without cutting content"""
        # Remove artifacts and clean formatting
        text = re.sub(r'<\|[^|]*\|>', '', text)
        text = text.strip()
        
        # Simply ensure text ends with proper punctuation if it doesn't already
        if text and text[-1] not in '.!?':
            text = text + '.'
        
        return text

    def _extract_paragraph_sources(self, text: str) -> list:
        """Extract sources from paragraph sources section"""
        sources_match = re.search(r'\*\*SOURCES?:\*\*\s*(.*?)(?=\*\*|$)', text, re.DOTALL | re.IGNORECASE)
        if not sources_match:
            return []
        
        sources_text = sources_match.group(1).strip()
        sources_text = re.sub(r'<\|[^|]*\|>', '', sources_text).strip()
        
        if not sources_text:
            return []
        
        # Try different source extraction methods
        sources_list = []
        
        # Method 1: Bracketed sources [XX:XX:XX] or (Para X)
        bracketed_sources = re.findall(r'\[([^\]]+)\]|\(([^)]+)\)', sources_text)
        if bracketed_sources:
            sources_list = [s[0] or s[1] for s in bracketed_sources if s[0] or s[1]]
        
        # Method 2: Bullet list format
        elif re.search(r'(?:^|\n)\s*(?:[•\-\*]|\d+\.)', sources_text, re.MULTILINE):
            bullet_sources = re.findall(r'(?:^|\n)\s*(?:[•\-\*]|\d+\.)\s*([^\n]+)', sources_text, re.MULTILINE)
            sources_list = [s.strip() for s in bullet_sources if s.strip()]
        
        # Method 3: Comma/semicolon separated
        else:
            sources_list = [s.strip() for s in re.split(r'[,;]|\sand\s', sources_text) if s.strip()]
        
        # Clean up sources
        cleaned_sources = []
        for source in sources_list:
            source = re.sub(r'<\|[^|]*\|>', '', source).strip()
            if source and len(source) > 1:
                cleaned_sources.append(source)
        
        return cleaned_sources

    def _apply_intelligent_fallback(self, raw_summary: str, result: dict):
        """Apply intelligent fallback parsing when structured parsing fails"""
        # Clean the raw text
        clean_text = self._clean_raw_text(raw_summary)
        
        # Split by lines instead of sentences to avoid cutting content
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
        
        if lines:
            # Use first line as TL;DR
            result['tldr'] = lines[0]
            result['sources']['tldr'] = "Content"
            
            # Use remaining lines as bullets
            if len(lines) > 1:
                result['bullets'] = lines[1:4] if len(lines) > 4 else lines[1:]
                result['sources']['bullets'] = [f"Line {i+2}" for i in range(len(result['bullets']))]
            else:
                result['bullets'] = ["Content processed successfully"]
                result['sources']['bullets'] = ["Para 1"]
            
            # Use the entire clean text as paragraph without cutting
            result['paragraph'] = clean_text
            result['sources']['paragraph'] = ["Para 1"]
        else:
            # Last resort fallback
            self._apply_emergency_fallback(raw_summary, result)

    def _apply_emergency_fallback(self, raw_summary: str, result: dict):
        """Emergency fallback when all else fails - preserve all content"""
        # Just use the raw content as paragraph and create simple structure
        result['paragraph'] = raw_summary.strip()
        result['tldr'] = raw_summary[:150] + "..." if len(raw_summary) > 150 else raw_summary
        
        # Split into simple lines for bullets without cutting
        lines = [line.strip() for line in raw_summary.split('\n') if line.strip() and len(line.strip()) > 10]
        result['bullets'] = lines[:5] if lines else ["Content processed"]
        
        # Set simple sources without Para numbers
        result['sources']['tldr'] = "Content"
        result['sources']['bullets'] = ["Content" for _ in result['bullets']]
        result['sources']['paragraph'] = ["Full Content"]
    
    def _create_fallback_summary(self, content: str) -> Dict[str, str]:
        """Create fallback summary when AI processing fails"""
        preview = content[:200] + "..." if len(content) > 200 else content
        
        return {
            'tldr': "Content loaded successfully but AI summary unavailable.",
            'bullets': [
                "File content extracted",
                "AI processing temporarily unavailable", 
                "Raw content displayed below"
            ],
            'paragraph': f"The file has been loaded and content extracted successfully. AI summarization is currently unavailable, but you can review the raw content below. Preview: {preview}"
        }
    
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
