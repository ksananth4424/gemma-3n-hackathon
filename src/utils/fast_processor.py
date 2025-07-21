"""
Fast Content Processor - Simplified without heavy dependency injection
For basic file operations that don't need full DI overhead
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

def fast_extract_text_content(file_path: str) -> str:
    """Fast text extraction without DI overhead"""
    try:
        file_path = Path(file_path)
        
        if file_path.suffix.lower() in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        elif file_path.suffix.lower() == '.py':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Add simple Python context
                return f"Python source code file:\n\n{content}"
        
        else:
            # For other text-like files, try reading as text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(5000)  # Limit for performance
                return content
                
    except Exception as e:
        return f"Could not extract text content: {e}"

def fast_file_validation(file_path: str) -> Dict[str, Any]:
    """Fast file validation without DI"""
    try:
        if not os.path.exists(file_path):
            return {"valid": False, "error": "File not found"}
        
        if not os.path.isfile(file_path):
            return {"valid": False, "error": "Path is not a file"}
        
        file_size = os.path.getsize(file_path)
        if file_size > 100 * 1024 * 1024:  # 100MB limit
            return {"valid": False, "error": "File too large (>100MB)"}
        
        return {
            "valid": True,
            "size": file_size,
            "extension": Path(file_path).suffix.lower()
        }
        
    except Exception as e:
        return {"valid": False, "error": str(e)}

def is_text_file(file_path: str) -> bool:
    """Quick check if file is likely text-based"""
    text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.csv'}
    return Path(file_path).suffix.lower() in text_extensions

def create_quick_summary(content: str, file_path: str) -> Dict[str, Any]:
    """Create a quick summary without AI when AI is not available"""
    file_name = Path(file_path).name
    content_preview = content[:500] + "..." if len(content) > 500 else content
    
    # Simple text analysis
    lines = content.split('\n')
    word_count = len(content.split())
    char_count = len(content)
    
    return {
        "tldr": f"Text file '{file_name}' with {word_count} words and {len(lines)} lines.",
        "bullets": [
            f"📄 File: {file_name}",
            f"📊 {word_count:,} words, {len(lines):,} lines",
            f"📏 {char_count:,} characters",
            f"📝 Content type: Text document"
        ],
        "paragraph": f"This is a text document named '{file_name}' containing {word_count:,} words across {len(lines):,} lines. The file contains {char_count:,} characters of text content. Preview: {content_preview[:200]}..."
    }
