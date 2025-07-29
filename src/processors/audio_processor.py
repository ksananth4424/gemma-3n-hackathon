"""
Audio Content Processor using Whisper for transcription
Optimized for direct audio file processing without video extraction overhead
"""

import whisper
import os
import logging
import librosa
import soundfile as sf
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

from ..utils.config_manager import ConfigManager

logger = logging.getLogger('accessibility_assistant.audio_processor')


class AudioProcessor:
    """
    Audio content processor with direct transcription
    Optimized for audio files without video processing overhead
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
            logger.info(f"Will use Whisper model: {model_size}")
            
        except Exception as e:
            logger.error(f"Error setting up Whisper for audio: {e}")
    
    @property
    def whisper_model(self):
        """Lazy load Whisper model"""
        if self._whisper_model is None:
            model_size = self.config.get('ai', 'whisper_model', 'base')
            logger.info(f"Loading Whisper model for audio: {model_size}")
            self._whisper_model = whisper.load_model(model_size)
        return self._whisper_model
    
    def extract_content(self, file_path: str) -> str:
        """
        Extract content from audio file via transcription
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Transcribed text content
        """
        processed_audio_path = None
        
        try:
            logger.info(f"Starting audio processing for: {file_path}")
            
            # Pre-process audio for optimal Whisper performance
            processed_audio_path = self._preprocess_audio(file_path)
            
            # Transcribe audio to text
            transcript = self._transcribe_audio(processed_audio_path)
            
            logger.info(f"Audio transcription completed: {len(transcript)} characters")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error processing audio {file_path}: {e}")
            raise
        finally:
            # Clean up temporary processed audio file if created
            if processed_audio_path and processed_audio_path != file_path and os.path.exists(processed_audio_path):
                try:
                    os.remove(processed_audio_path)
                    logger.debug("Cleaned up temporary processed audio file")
                except Exception as e:
                    logger.warning(f"Could not remove temp file {processed_audio_path}: {e}")
    
    def _preprocess_audio(self, audio_path: str) -> str:
        """
        Preprocess audio for optimal Whisper performance
        
        Args:
            audio_path: Path to original audio file
            
        Returns:
            Path to preprocessed audio file (may be same as input if no processing needed)
        """
        try:
            # Get audio info first
            audio_info = self.get_audio_info(audio_path)
            
            # Check if preprocessing is needed
            sample_rate = audio_info.get('sample_rate', 0)
            channels = audio_info.get('channels', 0)
            duration = audio_info.get('duration', 0)
            
            # Whisper works best with 16kHz mono
            needs_resampling = sample_rate != 16000
            needs_mono_conversion = channels > 1
            
            # Skip preprocessing for very long files to save time/space
            if duration > 3600:  # 1 hour
                logger.info("Skipping preprocessing for long audio file (>1 hour)")
                return audio_path
            
            if not (needs_resampling or needs_mono_conversion):
                logger.debug("Audio already in optimal format")
                return audio_path
            
            logger.debug(f"Preprocessing audio: resample={needs_resampling}, mono={needs_mono_conversion}")
            
            # Load and process audio
            audio_data, original_sr = librosa.load(audio_path, sr=None, mono=False)
            
            # Convert to mono if needed
            if needs_mono_conversion and audio_data.ndim > 1:
                audio_data = librosa.to_mono(audio_data)
            
            # Resample if needed
            if needs_resampling:
                audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=16000)
                target_sr = 16000
            else:
                target_sr = original_sr
            
            # Create temporary file for processed audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            # Save processed audio
            sf.write(temp_audio_path, audio_data, target_sr)
            
            logger.debug(f"Audio preprocessed and saved to: {temp_audio_path}")
            return temp_audio_path
            
        except Exception as e:
            logger.warning(f"Audio preprocessing failed, using original: {e}")
            return audio_path
    
    def _transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio to text using Whisper
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text with timestamps
        """
        try:
            logger.debug("Starting audio transcription")
            
            # Get optimal Whisper settings for audio files
            transcribe_options = {
                'language': None,  # Auto-detect language
                'task': 'transcribe',
                'temperature': 0.0,  # Deterministic output
                'best_of': 1,
                'beam_size': 1,
                'word_timestamps': True,  # Enable for better timestamp accuracy
                'verbose': False
            }
            
            # Adjust settings based on file size for performance
            audio_info = self.get_audio_info(audio_path)
            duration = audio_info.get('duration', 0)
            
            if duration > 1800:  # 30 minutes
                # Use faster settings for long files
                transcribe_options.update({
                    'beam_size': 1,
                    'best_of': 1,
                    'word_timestamps': False
                })
                logger.debug("Using fast transcription settings for long audio")
            
            # Transcribe using Whisper
            result = self.whisper_model.transcribe(audio_path, **transcribe_options)
            
            transcript = result["text"].strip()
            
            # Add timing information if available and useful
            if 'segments' in result and result['segments'] and duration < 1800:
                formatted_transcript = self._format_transcript_with_timestamps(result['segments'])
                return formatted_transcript
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error during audio transcription: {e}")
            raise
    
    def _format_transcript_with_timestamps(self, segments) -> str:
        """
        Format transcript with timestamp information optimized for audio
        
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
                # Format timestamp as [MM:SS] for readability
                start_min = int(start_time // 60)
                start_sec = int(start_time % 60)
                timestamp = f"[{start_min:02d}:{start_sec:02d}]"
                
                formatted_lines.append(f"{timestamp} {text}")
        
        return '\n'.join(formatted_lines)
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata about the audio file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio metadata
        """
        try:
            # Use librosa for audio info - more reliable than ffmpeg for audio-only files
            duration = librosa.get_duration(path=file_path)
            
            # Load a small sample to get format info
            sample_data, sample_rate = librosa.load(file_path, sr=None, duration=1.0)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Determine channels
            if sample_data.ndim == 1:
                channels = 1
            else:
                channels = sample_data.shape[0]
            
            metadata = {
                'duration': duration,
                'size': file_size,
                'sample_rate': sample_rate,
                'channels': channels,
                'format_name': Path(file_path).suffix.lower().replace('.', ''),
                'bitrate': int((file_size * 8) / duration) if duration > 0 else 0
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting audio metadata: {e}")
            return {}
    
    def estimate_processing_time(self, file_path: str) -> float:
        """
        Estimate processing time based on audio duration
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Estimated processing time in seconds
        """
        try:
            audio_info = self.get_audio_info(file_path)
            duration = audio_info.get('duration', 0)
            
            # Audio files are typically faster to process than video
            # Estimate: transcription takes about 5-15% of audio duration
            # Less overhead since no video extraction needed
            base_time = duration * 0.10 + 5  # Base 5 seconds overhead
            
            # Add extra time for preprocessing if needed
            sample_rate = audio_info.get('sample_rate', 16000)
            if sample_rate != 16000:
                base_time += duration * 0.02  # 2% extra for resampling
            
            return base_time
            
        except Exception:
            return 30  # Default estimate for audio
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return ['.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg', '.wma']
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file format is supported"""
        return Path(file_path).suffix.lower() in self.get_supported_formats()
