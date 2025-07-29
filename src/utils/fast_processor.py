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

def is_audio_file(file_path: str) -> bool:
    """Quick check if file is an audio file"""
    audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg', '.wma'}
    return Path(file_path).suffix.lower() in audio_extensions

def is_video_file(file_path: str) -> bool:
    """Quick check if file is a video file"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
    return Path(file_path).suffix.lower() in video_extensions

def create_quick_summary(content: str, file_path: str) -> Dict[str, Any]:
    """Create a quick summary without AI when AI is not available"""
    file_name = Path(file_path).name
    file_ext = Path(file_path).suffix.lower()
    
    # Handle audio files
    if is_audio_file(file_path):
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            return {
                "tldr": f"Audio file '{file_name}' ({size_mb:.1f} MB) - requires AI backend for transcription.",
                "bullets": [
                    f"🎵 Audio File: {file_name}",
                    f"📊 Size: {size_mb:.1f} MB ({file_size:,} bytes)",
                    f"🎧 Format: {file_ext.upper()} audio",
                    "🤖 Enable AI backend for automatic transcription",
                    "📝 Content summary will be available after processing"
                ],
                "paragraph": f"This is an audio file named '{file_name}' in {file_ext.upper()} format with a size of {size_mb:.1f} MB. To view the transcribed content and get an AI-generated summary, ensure the backend services are running and the Whisper transcription model is available. The system will automatically extract speech content and provide ADHD-friendly summaries."
            }
        except Exception:
            return {
                "tldr": f"Audio file '{file_name}' - processing requires AI backend.",
                "bullets": [
                    f"🎵 Audio File: {file_name}",
                    f"🎧 Format: {file_ext.upper()} audio",
                    "🤖 Requires AI backend for transcription"
                ],
                "paragraph": f"Audio file '{file_name}' detected. Audio transcription requires the AI backend to be running."
            }
    
    # Handle video files  
    if is_video_file(file_path):
        try:
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            return {
                "tldr": f"Video file '{file_name}' ({size_mb:.1f} MB) - requires AI backend for audio transcription.",
                "bullets": [
                    f"🎬 Video File: {file_name}",
                    f"📊 Size: {size_mb:.1f} MB ({file_size:,} bytes)",
                    f"📺 Format: {file_ext.upper()} video",
                    "🤖 Enable AI backend for automatic transcription",
                    "📝 Audio content will be extracted and transcribed"
                ],
                "paragraph": f"This is a video file named '{file_name}' in {file_ext.upper()} format with a size of {size_mb:.1f} MB. To view the transcribed audio content and get an AI-generated summary, ensure the backend services are running. The system will extract audio from the video and provide speech transcription with ADHD-friendly summaries."
            }
        except Exception:
            return {
                "tldr": f"Video file '{file_name}' - processing requires AI backend.",
                "bullets": [
                    f"🎬 Video File: {file_name}",
                    f"📺 Format: {file_ext.upper()} video",
                    "🤖 Requires AI backend for transcription"
                ],
                "paragraph": f"Video file '{file_name}' detected. Video transcription requires the AI backend to be running."
            }
    
    # Handle text files (existing logic)
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
