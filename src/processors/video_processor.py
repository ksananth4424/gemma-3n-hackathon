"""
Video Content Processor using Whisper for transcription
"""

import whisper
import ffmpeg
import tempfile
import os
import logging
from pathlib import Path
from typing import Optional

from ..utils.config_manager import ConfigManager

logger = logging.getLogger('accessibility_assistant.video_processor')


class VideoProcessor:
    """
    Video content processor with audio extraction and transcription
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self._whisper_model = None
        self._setup_whisper()
        
    def _setup_whisper(self):
        """Setup Whisper model for transcription"""
        try:
            # Get model size from config
            model_size = self.config.get('ai', 'whisper_model', 'base')
            
            # Load model lazily
            logger.info(f"Will use Whisper model: {model_size}")
            
        except Exception as e:
            logger.error(f"Error setting up Whisper: {e}")
    
    @property
    def whisper_model(self):
        """Lazy load Whisper model"""
        if self._whisper_model is None:
            model_size = self.config.get('ai', 'whisper_model', 'base')
            logger.info(f"Loading Whisper model: {model_size}")
            self._whisper_model = whisper.load_model(model_size)
        return self._whisper_model
    
    def extract_content(self, file_path: str) -> str:
        """
        Extract content from video file via audio transcription
        
        Args:
            file_path: Path to video file
            
        Returns:
            Transcribed text content
        """
        temp_audio_path = None
        
        try:
            logger.info(f"Starting video processing for: {file_path}")
            
            # Extract audio from video
            temp_audio_path = self._extract_audio(file_path)
            
            # Transcribe audio to text
            transcript = self._transcribe_audio(temp_audio_path)
            
            logger.info(f"Video transcription completed: {len(transcript)} characters")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error processing video {file_path}: {e}")
            raise
        finally:
            # Clean up temporary audio file
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                    logger.debug("Cleaned up temporary audio file")
                except Exception as e:
                    logger.warning(f"Could not remove temp file {temp_audio_path}: {e}")
    
    def _extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file using FFmpeg
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file
        """
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            logger.debug(f"Extracting audio to: {temp_audio_path}")
            
            # Extract audio using FFmpeg
            (
                ffmpeg
                .input(video_path)
                .output(
                    temp_audio_path,
                    acodec='pcm_s16le',  # 16-bit PCM
                    ac=1,                # Mono
                    ar='16k'             # 16kHz sample rate (good for speech)
                )
                .overwrite_output()
                .run(
                    quiet=True,
                    capture_stdout=True,
                    capture_stderr=True
                )
            )
            
            logger.debug("Audio extraction completed")
            return temp_audio_path
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error during audio extraction: {e}")
            # Try to get more details from stderr
            if hasattr(e, 'stderr') and e.stderr:
                stderr_msg = e.stderr.decode('utf-8')
                logger.error(f"FFmpeg stderr: {stderr_msg}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during audio extraction: {e}")
            raise
    
    def _transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio to text using Whisper
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            logger.debug("Starting audio transcription")
            
            # Transcribe using Whisper
            result = self.whisper_model.transcribe(
                audio_path,
                language=None,  # Auto-detect language
                task='transcribe',
                temperature=0.0,  # Deterministic output
                best_of=1,
                beam_size=1,
                word_timestamps=False,
                verbose=False
            )
            
            transcript = result["text"].strip()
            
            # Add timing information if available
            if 'segments' in result and result['segments']:
                formatted_transcript = self._format_transcript_with_timestamps(result['segments'])
                return formatted_transcript
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise
    
    def _format_transcript_with_timestamps(self, segments) -> str:
        """
        Format transcript with timestamp information
        
        Args:
            segments: Whisper segments with timing
            
        Returns:
            Formatted transcript with timestamps
        """
        formatted_lines = []
        
        for segment in segments:
            start_time = segment.get('start', 0)
            end_time = segment.get('end', 0)
            text = segment.get('text', '').strip()
            
            if text:
                # Format timestamp as [MM:SS]
                start_min = int(start_time // 60)
                start_sec = int(start_time % 60)
                timestamp = f"[{start_min:02d}:{start_sec:02d}]"
                
                formatted_lines.append(f"{timestamp} {text}")
        
        return '\n'.join(formatted_lines)
    
    def get_video_info(self, file_path: str) -> dict:
        """
        Get metadata about the video file
        
        Args:
            file_path: Path to video file
            
        Returns:
            Dictionary with video metadata
        """
        try:
            probe = ffmpeg.probe(file_path)
            
            # Extract video stream info
            video_streams = [stream for stream in probe['streams'] 
                           if stream['codec_type'] == 'video']
            audio_streams = [stream for stream in probe['streams'] 
                           if stream['codec_type'] == 'audio']
            
            metadata = {
                'duration': float(probe['format'].get('duration', 0)),
                'size': int(probe['format'].get('size', 0)),
                'bitrate': int(probe['format'].get('bit_rate', 0)),
                'video_streams': len(video_streams),
                'audio_streams': len(audio_streams),
                'format_name': probe['format'].get('format_name', ''),
            }
            
            # Add video stream details if available
            if video_streams:
                video = video_streams[0]
                metadata.update({
                    'width': int(video.get('width', 0)),
                    'height': int(video.get('height', 0)),
                    'fps': eval(video.get('r_frame_rate', '0/1')),
                    'video_codec': video.get('codec_name', '')
                })
            
            # Add audio stream details if available
            if audio_streams:
                audio = audio_streams[0]
                metadata.update({
                    'audio_codec': audio.get('codec_name', ''),
                    'sample_rate': int(audio.get('sample_rate', 0)),
                    'channels': int(audio.get('channels', 0))
                })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return {}
    
    def estimate_processing_time(self, file_path: str) -> float:
        """
        Estimate processing time based on video duration
        
        Args:
            file_path: Path to video file
            
        Returns:
            Estimated processing time in seconds
        """
        try:
            video_info = self.get_video_info(file_path)
            duration = video_info.get('duration', 0)
            
            # Rough estimate: transcription takes about 10-20% of video duration
            # Add overhead for audio extraction
            estimated_time = duration * 0.15 + 10  # Base 10 seconds overhead
            
            return estimated_time
            
        except Exception:
            return 60  # Default estimate
