"""
Document Structure Analyzer
Analyzes document content to identify sections, headers, and structure for intelligent source referencing
"""

import re
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger('accessibility_assistant.document_analyzer')


@dataclass
class DocumentSection:
    """Represents a section of a document"""
    title: str
    content: str
    section_type: str  # abstract, introduction, methods, results, discussion, conclusion, section, paragraph
    level: int  # header level (1=main, 2=sub, etc.)
    start_position: int
    end_position: int


class DocumentAnalyzer:
    """Analyzes document structure for intelligent source referencing"""
    
    def __init__(self):
        # Common academic paper section patterns
        self.section_patterns = {
            'abstract': [
                r'\b(?:abstract|summary)\b',
                r'^\s*abstract\s*$',
                r'^\s*summary\s*$'
            ],
            'introduction': [
                r'\b(?:introduction|intro|background)\b',
                r'^\s*(?:1\.?\s*)?introduction\s*$',
                r'^\s*(?:1\.?\s*)?background\s*$'
            ],
            'methods': [
                r'\b(?:methods?|methodology|approach|experimental)\b',
                r'^\s*(?:\d+\.?\s*)?methods?\s*$',
                r'^\s*(?:\d+\.?\s*)?methodology\s*$',
                r'^\s*(?:\d+\.?\s*)?experimental\s+(?:design|setup|procedure)\s*$'
            ],
            'results': [
                r'\b(?:results?|findings?|outcomes?)\b',
                r'^\s*(?:\d+\.?\s*)?results?\s*$',
                r'^\s*(?:\d+\.?\s*)?findings?\s*$'
            ],
            'discussion': [
                r'\b(?:discussion|analysis|interpretation)\b',
                r'^\s*(?:\d+\.?\s*)?discussion\s*$',
                r'^\s*(?:\d+\.?\s*)?analysis\s*$'
            ],
            'conclusion': [
                r'\b(?:conclusion|conclusions?|summary|final)\b',
                r'^\s*(?:\d+\.?\s*)?conclusions?\s*$',
                r'^\s*(?:\d+\.?\s*)?summary\s*$',
                r'^\s*(?:\d+\.?\s*)?final\s+remarks?\s*$'
            ],
            'references': [
                r'\b(?:references?|bibliography|works?\s+cited)\b',
                r'^\s*references?\s*$',
                r'^\s*bibliography\s*$'
            ]
        }
        
        # Header patterns
        self.header_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s]{2,})\s*$',  # ALL CAPS headers
            r'^(\d+\.?\s+[A-Z].+)$',  # Numbered sections
            r'^([A-Z][a-z\s]+)\s*$',  # Title Case headers (at line start)
        ]
    
    def analyze_document(self, content: str) -> Dict[str, Any]:
        """
        Analyze document structure and return section information
        
        Args:
            content: Raw document content
            
        Returns:
            Dictionary with document structure information
        """
        try:
            sections = self._identify_sections(content)
            structure = self._create_structure_map(content, sections)
            
            return {
                'sections': sections,
                'structure_map': structure,
                'has_academic_structure': self._has_academic_structure(sections),
                'enhanced_content': self._add_source_markers(content, sections)
            }
            
        except Exception as e:
            logger.warning(f"Document analysis failed: {e}")
            return {
                'sections': [],
                'structure_map': {},
                'has_academic_structure': False,
                'enhanced_content': self._add_paragraph_markers(content)
            }
    
    def _identify_sections(self, content: str) -> List[DocumentSection]:
        """Identify document sections and their types"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if not stripped_line:
                if current_content:
                    current_content.append(line)
                continue
            
            # Check if this line is a header
            header_match = self._is_header(stripped_line)
            if header_match:
                # Save previous section if exists
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    current_section.end_position = i
                    sections.append(current_section)
                
                # Start new section
                section_type, level = self._classify_section(header_match)
                current_section = DocumentSection(
                    title=header_match,
                    content="",
                    section_type=section_type,
                    level=level,
                    start_position=i,
                    end_position=i
                )
                current_content = []
            else:
                if current_content or current_section:
                    current_content.append(line)
        
        # Add final section
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            current_section.end_position = len(lines)
            sections.append(current_section)
        
        # If no sections found, treat entire content as one section
        if not sections:
            sections.append(DocumentSection(
                title="Document",
                content=content,
                section_type="document",
                level=1,
                start_position=0,
                end_position=len(lines)
            ))
        
        return sections
    
    def _is_header(self, line: str) -> str:
        """Check if a line is a header and return the header text"""
        for pattern in self.header_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else line
        return None
    
    def _classify_section(self, header_text: str) -> Tuple[str, int]:
        """Classify section type and determine hierarchy level"""
        header_lower = header_text.lower().strip()
        
        # Check against known section patterns
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, header_lower, re.IGNORECASE):
                    level = self._determine_level(header_text)
                    return section_type, level
        
        # Check for numbered sections
        if re.match(r'^\d+\.?\s+', header_text):
            level = self._determine_level(header_text)
            return 'section', level
        
        # Default to generic section
        level = self._determine_level(header_text)
        return 'section', level
    
    def _determine_level(self, header_text: str) -> int:
        """Determine header hierarchy level"""
        # Markdown headers
        if header_text.startswith('#'):
            return header_text.count('#')
        
        # Numbered sections
        match = re.match(r'^(\d+(?:\.\d+)*)', header_text)
        if match:
            return len(match.group(1).split('.'))
        
        # Default level
        return 1
    
    def _has_academic_structure(self, sections: List[DocumentSection]) -> bool:
        """Check if document has academic paper structure"""
        section_types = {section.section_type for section in sections}
        academic_indicators = {'abstract', 'introduction', 'methods', 'results', 'conclusion'}
        return len(section_types.intersection(academic_indicators)) >= 2
    
    def _create_structure_map(self, content: str, sections: List[DocumentSection]) -> Dict[str, Any]:
        """Create a map of content positions to section references"""
        structure_map = {}
        lines = content.split('\n')
        
        for section in sections:
            section_ref = self._create_section_reference(section)
            for line_num in range(section.start_position, section.end_position):
                if line_num < len(lines):
                    structure_map[line_num] = section_ref
        
        return structure_map
    
    def _create_section_reference(self, section: DocumentSection) -> str:
        """Create a human-readable section reference"""
        if section.section_type == 'abstract':
            return '(Abstract)'
        elif section.section_type == 'introduction':
            return '(Introduction)'
        elif section.section_type == 'methods':
            return '(Methods)'
        elif section.section_type == 'results':
            return '(Results)'
        elif section.section_type == 'discussion':
            return '(Discussion)'
        elif section.section_type == 'conclusion':
            return '(Conclusion)'
        elif section.section_type == 'references':
            return '(References)'
        elif section.section_type == 'section':
            # Try to create a meaningful section reference
            title = section.title.strip()
            if len(title) > 50:
                title = title[:47] + '...'
            return f'(Section: {title})'
        else:
            return f'(Section: {section.title})'
    
    def _add_source_markers(self, content: str, sections: List[DocumentSection]) -> str:
        """Add source markers to content for better AI referencing"""
        if not sections or len(sections) == 1:
            # If no meaningful sections found, use paragraph markers
            return self._add_paragraph_markers(content)
        
        enhanced_lines = []
        lines = content.split('\n')
        current_section_ref = None
        
        for i, line in enumerate(lines):
            # Find which section this line belongs to
            for section in sections:
                if section.start_position <= i < section.end_position:
                    section_ref = self._create_section_reference(section)
                    if section_ref != current_section_ref:
                        enhanced_lines.append(f"\n[SOURCE_MARKER: {section_ref}]")
                        current_section_ref = section_ref
                    break
            
            enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    def _add_paragraph_markers(self, content: str) -> str:
        """Add paragraph markers as fallback when no structure is detected"""
        # Split by double newlines to get paragraphs
        paragraphs = re.split(r'\n\s*\n', content)
        enhanced_paragraphs = []
        
        for i, paragraph in enumerate(paragraphs, 1):
            paragraph = paragraph.strip()
            if paragraph:
                # Check if this paragraph looks like a title/header
                if i == 1 and len(paragraph.split('\n')) == 1 and len(paragraph) < 100:
                    enhanced_paragraphs.append(f"[SOURCE_MARKER: (Title)]\n{paragraph}")
                else:
                    enhanced_paragraphs.append(f"[SOURCE_MARKER: (Para {i})]\n{paragraph}")
        
        return '\n\n'.join(enhanced_paragraphs)
