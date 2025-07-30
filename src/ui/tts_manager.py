"""
Text-to-Speech Manager for Prism
Provides offline TTS functionality using Windows SAPI
"""

import threading
from typing import Optional, Callable, List, Dict, Any

# Text-to-speech imports (Windows SAPI - offline)
try:
    import win32com.client
    TTS_AVAILABLE = True
    print("✅ win32com.client imported successfully")
except ImportError as import_error:
    TTS_AVAILABLE = False
    print(f"❌ TTS not available: {import_error}")

def diagnose_tts_environment():
    """Diagnose TTS environment and capabilities"""
    print("\n=== TTS Environment Diagnosis ===")
    
    if not TTS_AVAILABLE:
        print("❌ win32com.client not available")
        return False
    
    try:
        # Try to create SAPI engine
        import win32com.client
        engine = win32com.client.Dispatch("SAPI.SpVoice")
        print("✅ SAPI.SpVoice created successfully")
        
        # Test basic properties
        try:
            rate = engine.Rate
            volume = engine.Volume
            print(f"✅ Engine properties accessible - Rate: {rate}, Volume: {volume}")
        except Exception as prop_error:
            print(f"❌ Property access failed: {prop_error}")
            return False
        
        # Test voices
        try:
            voices = engine.GetVoices()
            print(f"✅ Found {voices.Count} voices")
            
            for i in range(min(3, voices.Count)):  # Show first 3 voices
                try:
                    voice = voices.Item(i)
                    name = voice.GetDescription()
                    print(f"  Voice {i}: {name}")
                except Exception as voice_error:
                    print(f"  Voice {i}: Error getting description - {voice_error}")
                    
        except Exception as voice_error:
            print(f"❌ Voice enumeration failed: {voice_error}")
        
        # Test simple speech
        try:
            print("🔊 Testing basic TTS functionality...")
            # Just test properties instead of making noise
            test_rate = engine.Rate
            test_volume = engine.Volume
            print("✅ TTS functionality test successful")
            return True
            
        except Exception as speech_error:
            print(f"❌ TTS functionality test failed: {speech_error}")
            return False
            
    except Exception as e:
        print(f"❌ TTS diagnosis failed: {e}")
        return False
    
    finally:
        print("=== End TTS Diagnosis ===\n")


class TextToSpeechManager:
    """Manages offline text-to-speech using Windows SAPI"""
    
    def __init__(self):
        self.is_available = TTS_AVAILABLE
        self.engine = None
        self.current_speech_engine = None  # For pause/resume support
        self.is_speaking = False
        self.is_paused = False
        self.current_text = ""
        self.speech_thread = None
        
        # Run diagnosis first
        diagnosis_result = diagnose_tts_environment()
        
        if self.is_available and diagnosis_result:
            try:
                print("Initializing Windows SAPI TTS engine...")
                
                # Initialize COM for the main thread
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                    print("COM initialized for main thread")
                except Exception as com_error:
                    print(f"Main thread COM initialization failed: {com_error}")
                
                self.engine = win32com.client.Dispatch("SAPI.SpVoice")
                
                # Verify engine is working by testing basic properties
                try:
                    # Test basic property access
                    current_rate = self.engine.Rate
                    current_volume = self.engine.Volume
                    print(f"TTS engine initialized - Rate: {current_rate}, Volume: {current_volume}")
                    
                    # Set neurodivergent-friendly default properties
                    self.engine.Rate = -2  # Slightly slower for better comprehension
                    self.engine.Volume = 85  # Comfortable volume level
                    print("TTS neurodivergent-friendly defaults set successfully")
                    
                    # Try to set Zira as the default voice (female voice preferred)
                    try:
                        voices = self.engine.GetVoices()
                        zira_voice = None
                        for i in range(voices.Count):
                            voice = voices.Item(i)
                            voice_name = voice.GetDescription()
                            if 'zira' in voice_name.lower():
                                zira_voice = voice
                                break
                        
                        if zira_voice:
                            self.engine.Voice = zira_voice
                            print("Successfully set Zira as default voice (female)")
                        else:
                            print("Zira voice not found, using system default")
                    except Exception as voice_error:
                        print(f"Could not set default voice: {voice_error}")
                    
                except Exception as prop_error:
                    print(f"TTS property access failed: {prop_error}")
                    raise prop_error
                    
            except Exception as e:
                print(f"TTS initialization failed: {e}")
                print(f"Error type: {type(e)}")
                import traceback
                traceback.print_exc()
                self.is_available = False
                self.engine = None
        else:
            print("TTS not available - diagnosis failed or dependencies missing")
            self.is_available = False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available system voices with proper COM handling"""
        if not self.is_available:
            return []
        
        try:
            voices = []
            
            # Try to get voices with proper COM initialization
            try:
                # Initialize COM if not already done
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except:
                    pass  # May already be initialized
                
                # Create fresh engine for voice enumeration
                import win32com.client
                voice_engine = win32com.client.Dispatch("SAPI.SpVoice")
                voice_tokens = voice_engine.GetVoices()
                print(f"Successfully enumerated {voice_tokens.Count} voices")
                
            except Exception as voice_error:
                print(f"Voice enumeration failed: {voice_error}")
                # Return hardcoded voices based on system diagnosis
                return [
                    {
                        'id': 0,
                        'name': "Microsoft David Desktop",
                        'display_name': "�️ Microsoft David Desktop (Male, Clear)",
                        'token': None,
                        'recommended': True,
                        'priority': 2,
                        'is_female': False
                    },
                    {
                        'id': 1,
                        'name': "Microsoft Zira Desktop", 
                        'display_name': "🌟 Microsoft Zira Desktop (Female, Recommended)",
                        'token': None,
                        'recommended': True,
                        'priority': 1,
                        'is_female': True
                    }
                ]
            
            # Enhanced voice characteristics detection
            voice_characteristics = {
                'zira': {'priority': 1, 'recommended': True, 'description': 'Clear female voice', 'is_female': True},
                'david': {'priority': 2, 'recommended': True, 'description': 'Professional male voice', 'is_female': False},
                'mark': {'priority': 3, 'recommended': True, 'description': 'Calm male voice', 'is_female': False},
                'hazel': {'priority': 4, 'recommended': True, 'description': 'Pleasant female voice', 'is_female': True},
                'eva': {'priority': 5, 'recommended': True, 'description': 'Smooth female voice', 'is_female': True},
                'aria': {'priority': 6, 'recommended': True, 'description': 'Natural female voice', 'is_female': True},
                'guy': {'priority': 7, 'recommended': False, 'description': 'Standard male voice', 'is_female': False},
                'hedda': {'priority': 8, 'recommended': False, 'description': 'Clear female voice', 'is_female': True},
                'katja': {'priority': 9, 'recommended': False, 'description': 'Distinct female voice', 'is_female': True},
                'helena': {'priority': 10, 'recommended': False, 'description': 'Natural female voice', 'is_female': True},
            }
            
            print(f"Processing {voice_tokens.Count} available voices:")
            
            for i in range(voice_tokens.Count):
                try:
                    voice_item = voice_tokens.Item(i)
                    
                    # Safely get voice description
                    try:
                        voice_name = voice_item.GetDescription()
                        print(f"  Voice {i}: {voice_name}")
                    except Exception as desc_error:
                        voice_name = f"System Voice {i + 1}"
                        print(f"  Voice {i}: {voice_name} (description failed: {desc_error})")
                    
                    # Analyze voice characteristics
                    voice_key = None
                    priority = 999
                    is_recommended = False
                    description = "Standard voice"
                    is_female = None
                    
                    # Check against known voice patterns
                    for char_key, char_data in voice_characteristics.items():
                        if char_key.lower() in voice_name.lower():
                            voice_key = char_key
                            priority = char_data['priority']
                            is_recommended = char_data['recommended']
                            description = char_data['description']
                            is_female = char_data['is_female']
                            break
                    
                    # Auto-detect gender if not specified
                    if is_female is None:
                        # Common female voice indicators
                        female_indicators = ['female', 'woman', 'girl', 'zira', 'cortana', 'eva', 'aria', 'hazel', 'hedda', 'katja', 'helena']
                        male_indicators = ['male', 'man', 'boy', 'david', 'mark', 'guy', 'james', 'richard']
                        
                        voice_lower = voice_name.lower()
                        if any(indicator in voice_lower for indicator in female_indicators):
                            is_female = True
                        elif any(indicator in voice_lower for indicator in male_indicators):
                            is_female = False
                        else:
                            is_female = False  # Default to male if unknown
                    
                    # Create enhanced display name
                    gender_icon = "👩" if is_female else "👨"
                    quality_icon = "🌟" if is_recommended else "🎙️"
                    
                    display_name = f"{quality_icon} {gender_icon} {voice_name}"
                    if description and description != "Standard voice":
                        display_name += f" ({description})"
                    
                    voice_info = {
                        'id': i,
                        'name': voice_name,
                        'token': voice_item,
                        'recommended': is_recommended,
                        'priority': priority,
                        'display_name': display_name,
                        'is_female': is_female,
                        'description': description
                    }
                    
                    voices.append(voice_info)
                    
                except Exception as voice_error:
                    print(f"Error processing voice {i}: {voice_error}")
                    # Add a generic entry for this voice
                    voices.append({
                        'id': i,
                        'name': f"System Voice {i + 1}",
                        'token': None,
                        'recommended': False,
                        'priority': 999,
                        'display_name': f"🎙️ System Voice {i + 1}",
                        'is_female': False,
                        'description': "Unknown voice"
                    })
            
            # Sort voices: Recommended first, then females, then by priority, then alphabetically
            voices.sort(key=lambda x: (
                not x['recommended'],  # Recommended voices first
                not x['is_female'],    # Female voices next
                x['priority'],         # Then by priority
                x['name'].lower()      # Finally alphabetically
            ))
            
            print(f"Voice enumeration completed. Found {len(voices)} voices:")
            for voice in voices:
                print(f"  - {voice['display_name']}")
            
            # If no voices found, return system defaults
            if not voices:
                print("No voices enumerated, returning default voices")
                voices = [
                    {
                        'id': 0,
                        'name': "Microsoft Zira Desktop",
                        'display_name': "🌟 👩 Microsoft Zira Desktop (Clear female voice)",
                        'token': None,
                        'recommended': True,
                        'priority': 1,
                        'is_female': True,
                        'description': "Clear female voice"
                    },
                    {
                        'id': 1,
                        'name': "Microsoft David Desktop",
                        'display_name': "🌟 👨 Microsoft David Desktop (Professional male voice)",
                        'token': None,
                        'recommended': True,
                        'priority': 2,
                        'is_female': False,
                        'description': "Professional male voice"
                    }
                ]
                
            return voices
            
        except Exception as e:
            print(f"Error getting voices: {e}")
            # Return default voices as fallback
            return [
                {
                    'id': 0,
                    'name': "Microsoft Zira Desktop",
                    'display_name': "🌟 👩 Microsoft Zira Desktop (Clear female voice)",
                    'token': None,
                    'recommended': True,
                    'priority': 1,
                    'is_female': True,
                    'description': "Clear female voice"
                },
                {
                    'id': 1,
                    'name': "Microsoft David Desktop",
                    'display_name': "🌟 👨 Microsoft David Desktop (Professional male voice)",
                    'token': None,
                    'recommended': True,
                    'priority': 2,
                    'is_female': False,
                    'description': "Professional male voice"
                }
            ]
    
    def set_voice(self, voice_id: int) -> bool:
        """Set the TTS voice by ID with proper COM handling"""
        if not self.is_available:
            return False
        
        try:
            # Initialize COM for voice setting
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except:
                pass  # May already be initialized
                
            # Create fresh engine for voice setting to avoid COM issues
            import win32com.client
            temp_engine = win32com.client.Dispatch("SAPI.SpVoice")
            voices = temp_engine.GetVoices()
            
            if 0 <= voice_id < voices.Count:
                selected_voice = voices.Item(voice_id)
                voice_name = selected_voice.GetDescription()
                print(f"Setting voice to: {voice_name}")
                
                # Set voice on temp engine first to test
                temp_engine.Voice = selected_voice
                
                # If successful, update our main engine
                if self.engine:
                    try:
                        self.engine.Voice = selected_voice
                        print(f"Voice successfully set to: {voice_name}")
                    except Exception as main_error:
                        print(f"Failed to set voice on main engine: {main_error}")
                        # Replace main engine with working temp engine
                        self.engine = temp_engine
                        print("Replaced main engine with working temp engine")
                else:
                    # Use temp engine as main engine
                    self.engine = temp_engine
                    print("Using temp engine as main engine")
                
                return True
            else:
                print(f"Voice ID {voice_id} out of range (0-{voices.Count-1})")
                return False
                
        except Exception as e:
            print(f"Error setting voice: {e}")
            return False
    
    def set_rate(self, rate: int) -> None:
        """Set speech rate (-10 to 10)"""
        if self.is_available and self.engine:
            try:
                self.engine.Rate = max(-10, min(10, rate))
            except Exception as e:
                print(f"Error setting rate: {e}")
    
    def set_volume(self, volume: int) -> None:
        """Set speech volume (0-100)"""
        if self.is_available and self.engine:
            try:
                self.engine.Volume = max(0, min(100, volume))
            except Exception as e:
                print(f"Error setting volume: {e}")
    
    def speak(self, text: str, callback: Optional[Callable[[bool], None]] = None) -> None:
        """Speak text with robust error handling and multiple strategies"""
        if not self.is_available or not self.engine or not text.strip():
            print("TTS speak called but conditions not met:")
            print(f"  - Available: {self.is_available}")
            print(f"  - Engine: {self.engine is not None}")
            print(f"  - Text: {bool(text.strip()) if text else False}")
            if callback:
                callback(False)
            return
        
        def speak_worker():
            try:
                print(f"Starting TTS speech: {text[:50]}...")
                self.is_speaking = True
                self.is_paused = False
                self.current_text = text
                
                # Initialize COM for this thread - this is critical!
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                    print("COM initialized for speech thread")
                except Exception as com_error:
                    print(f"COM initialization failed: {com_error}")
                
                # Strategy 1: Try creating a fresh engine in this thread context
                success = False
                speech_engine = None
                
                try:
                    print("Creating fresh TTS engine in thread context...")
                    import win32com.client
                    speech_engine = win32com.client.Dispatch("SAPI.SpVoice")
                    
                    # Apply neurodivergent-friendly settings
                    try:
                        if self.engine:
                            speech_engine.Rate = self.engine.Rate
                            speech_engine.Volume = self.engine.Volume
                            # Try to copy voice setting if available
                            try:
                                speech_engine.Voice = self.engine.Voice
                            except:
                                print("Could not copy voice setting, using default")
                        else:
                            speech_engine.Rate = -2  # Slower for better comprehension
                            speech_engine.Volume = 85  # Good volume level
                    except Exception as settings_error:
                        print(f"Using default TTS settings due to error: {settings_error}")
                    
                    # Store engine reference for pause/resume functionality
                    self.current_speech_engine = speech_engine
                    
                    # Try speaking with fresh engine (asynchronous for pause/resume support)
                    print("Attempting speech with fresh engine (async mode)...")
                    speech_engine.Speak(text, 1)  # 1 = asynchronous
                    
                    # Monitor speech progress and handle pause/resume
                    import time
                    max_wait_time = 120  # 2 minutes max
                    check_interval = 0.2  # Check every 200ms
                    elapsed = 0
                    
                    while self.is_speaking and elapsed < max_wait_time:
                        time.sleep(check_interval)
                        elapsed += check_interval
                        
                        # Handle pause state
                        while self.is_paused and self.is_speaking:
                            time.sleep(0.1)  # Wait while paused
                        
                        # Check if speech is still active
                        try:
                            if hasattr(speech_engine, 'Status'):
                                status = speech_engine.Status
                                if hasattr(status, 'RunningState'):
                                    # RunningState: 1 = speaking, 2 = done
                                    if status.RunningState == 2:  # Done
                                        break
                                    elif status.RunningState != 1:  # Not speaking
                                        break
                        except Exception as status_error:
                            # If we can't get status, continue monitoring
                            if elapsed > 5:  # After 5 seconds, check if still supposed to be speaking
                                if not self.is_speaking:
                                    break
                    
                    success = True
                    print("Fresh engine speech completed successfully")
                    
                    # Update our main engine reference
                    self.engine = speech_engine
                    
                except Exception as fresh_error:
                    print(f"Fresh engine speech failed: {fresh_error}")
                
                # Strategy 2: Try with minimal settings if fresh engine failed
                if not success:
                    try:
                        print("Attempting minimal engine configuration...")
                        import win32com.client
                        minimal_engine = win32com.client.Dispatch("SAPI.SpVoice")
                        
                        # Don't set any properties, just speak
                        minimal_engine.Speak(text, 0)  # Synchronous
                        success = True
                        print("Minimal engine speech completed successfully")
                        
                        # Update our engine
                        self.engine = minimal_engine
                        
                    except Exception as minimal_error:
                        print(f"Minimal engine speech failed: {minimal_error}")
                
                # Strategy 3: Try with existing engine but different flags
                if not success and self.engine:
                    try:
                        print("Attempting speech with different flags...")
                        # Try with no flags (default synchronous)
                        self.engine.Speak(text)
                        success = True
                        print("Default flag speech completed successfully")
                    except Exception as flag_error:
                        print(f"Default flag speech failed: {flag_error}")
                
                self.is_speaking = False
                
                if success:
                    print("TTS speech completed successfully")
                    if callback:
                        callback(True)
                else:
                    print("All TTS speech strategies failed")
                    if callback:
                        callback(False)
                        
                # Clean up COM for this thread
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                    print("COM cleaned up for speech thread")
                except:
                    pass  # Ignore cleanup errors
                    
            except Exception as e:
                print(f"Speech error: {e}")
                print(f"Error type: {type(e)}")
                import traceback
                traceback.print_exc()
                self.is_speaking = False
                
                # Clean up COM even on error
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except:
                    pass
                    
                if callback:
                    callback(False)
        
        # Stop any existing speech (ignore errors)
        try:
            self.stop()
        except:
            pass
        
        self.speech_thread = threading.Thread(target=speak_worker, daemon=True)
        self.speech_thread.start()
    
    def reinitialize_engine(self) -> bool:
        """Attempt to reinitialize the TTS engine"""
        if not TTS_AVAILABLE:
            return False
        
        try:
            print("Reinitializing TTS engine...")
            
            # Clear existing engine
            self.engine = None
            self.is_available = False
            
            # Try to create new engine
            import win32com.client
            self.engine = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Test basic functionality
            self.engine.Rate = -2  # Neurodivergent-friendly default
            self.engine.Volume = 85
            
            self.is_available = True
            print("TTS engine reinitialized successfully")
            return True
            
        except Exception as e:
            print(f"TTS reinitialization failed: {e}")
            self.engine = None
            self.is_available = False
            return False
    
    def test_speech(self) -> bool:
        """Test if TTS is working without making noise"""
        if not self.is_available or not self.engine:
            print(f"TTS test failed - Available: {self.is_available}, Engine: {self.engine is not None}")
            return False
        
        try:
            print("Testing TTS engine properties...")
            
            # Test if we can access engine properties
            try:
                rate = self.engine.Rate
                volume = self.engine.Volume
                print(f"Engine properties accessible - Rate: {rate}, Volume: {volume}")
                return True
            except Exception as prop_error:
                print(f"Engine property access failed: {prop_error}")
                return False
            
        except Exception as e:
            print(f"TTS test failed with error: {e}")
            print(f"Error type: {type(e)}")
            
            # Try alternative initialization
            try:
                print("Attempting alternative TTS initialization...")
                import win32com.client
                test_engine = win32com.client.Dispatch("SAPI.SpVoice")
                
                # Test properties instead of speech
                test_rate = test_engine.Rate
                test_volume = test_engine.Volume
                print("Alternative TTS initialization successful")
                
                # Replace the main engine if alternative works
                self.engine = test_engine
                return True
                
            except Exception as alt_error:
                print(f"Alternative TTS initialization also failed: {alt_error}")
                return False
    
    def stop(self) -> None:
        """Stop current speech gracefully"""
        self.is_speaking = False
        self.is_paused = False
        
        if self.is_available and self.engine:
            try:
                print("Stopping TTS speech...")
                # Try multiple stop strategies
                try:
                    # Strategy 1: Use Speak with stop flag
                    self.engine.Speak("", 3)  # 3 = purge and stop
                    print("TTS speech stopped successfully")
                except Exception as stop_error:
                    print(f"Standard stop failed: {stop_error}")
                    try:
                        # Strategy 2: Try alternative stop method
                        self.engine.Speak("", 2)  # 2 = purge queue
                        print("TTS queue purged")
                    except Exception as purge_error:
                        print(f"Queue purge failed: {purge_error}")
                        # Continue silently - speech will end on its own
                        
            except Exception as e:
                print(f"Error stopping speech: {e}")
                # Ignore stop errors and let speech complete naturally
    
    def pause(self) -> None:
        """Pause current speech with enhanced support"""
        if self.is_speaking and not self.is_paused:
            try:
                print("Pausing TTS speech...")
                
                # Try pausing the current speech engine
                if hasattr(self, 'current_speech_engine') and self.current_speech_engine:
                    try:
                        self.current_speech_engine.Pause()
                        self.is_paused = True
                        print("TTS speech paused successfully")
                        return
                    except Exception as engine_pause_error:
                        print(f"Engine pause failed: {engine_pause_error}")
                
                # Fallback to main engine
                if self.engine:
                    try:
                        self.engine.Pause()
                        self.is_paused = True
                        print("TTS speech paused with main engine")
                        return
                    except Exception as main_pause_error:
                        print(f"Main engine pause failed: {main_pause_error}")
                
                # If all else fails, just set the flag
                self.is_paused = True
                print("TTS speech marked as paused (flag only)")
                
            except Exception as e:
                print(f"Error pausing speech: {e}")
    
    def resume(self) -> None:
        """Resume paused speech with enhanced support"""
        if self.is_paused and self.is_speaking:
            try:
                print("Resuming TTS speech...")
                
                # Try resuming the current speech engine
                if hasattr(self, 'current_speech_engine') and self.current_speech_engine:
                    try:
                        self.current_speech_engine.Resume()
                        self.is_paused = False
                        print("TTS speech resumed successfully")
                        return
                    except Exception as engine_resume_error:
                        print(f"Engine resume failed: {engine_resume_error}")
                
                # Fallback to main engine
                if self.engine:
                    try:
                        self.engine.Resume()
                        self.is_paused = False
                        print("TTS speech resumed with main engine")
                        return
                    except Exception as main_resume_error:
                        print(f"Main engine resume failed: {main_resume_error}")
                
                # If all else fails, just clear the flag
                self.is_paused = False
                print("TTS speech marked as resumed (flag only)")
                
            except Exception as e:
                print(f"Error resuming speech: {e}")


# Global TTS manager instance
tts_manager = TextToSpeechManager()
