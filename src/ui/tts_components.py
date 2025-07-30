"""
Text-to-Speech UI Components for Prism
Provides TTS controls and interface elements
"""

import flet as ft
from typing import Dict, Any, Callable

# Import TTS manager with fallback for direct execution
try:
    from .tts_manager import tts_manager
except ImportError:
    # Fallback for direct script execution
    from tts_manager import tts_manager


def create_tts_controls_panel(
    data: Dict[str, Any], 
    paragraph_visible: ft.Ref[ft.Text], 
    page: ft.Page,
    theme_mode: ft.ThemeMode
) -> ft.Container:
    """Create the TTS controls panel"""
    
    # TTS State variables
    tts_state = {
        "is_speaking": False,
        "is_paused": False,
        "current_voice": 0,
        "rate": 0,
        "volume": 80
    }
    
    # TTS Controls References
    play_pause_button = ft.Ref[ft.IconButton]()
    restart_button = ft.Ref[ft.IconButton]()
    tts_status = ft.Ref[ft.Text]()
    voice_dropdown = ft.Ref[ft.Dropdown]()
    rate_slider = ft.Ref[ft.Slider]()
    volume_slider = ft.Ref[ft.Slider]()
    
    def update_tts_status(status_text: str, color: str = "#666666"):
        """Update TTS status text and color"""
        if tts_status.current:
            tts_status.current.value = status_text
            tts_status.current.color = color
            page.update()
    
    def on_speech_complete(success: bool):
        """Callback when speech completes"""
        tts_state["is_speaking"] = False
        tts_state["is_paused"] = False
        
        try:
            if play_pause_button.current:
                play_pause_button.current.icon = ft.Icons.PLAY_ARROW
                play_pause_button.current.tooltip = "Play speech"
            if restart_button.current:
                restart_button.current.disabled = False
            
            if success:
                update_tts_status("✅ Speech completed", "#4CAF50")
            else:
                update_tts_status("❌ Speech failed", "#F44336")
            
            page.update()
        except Exception as e:
            print(f"Error in speech complete callback: {e}")
    
    def play_pause_speech(e):
        """Handle play/pause button click with proper state synchronization"""
        try:
            if not tts_manager.is_available:
                update_tts_status("❌ TTS not available", "#F44336")
                return
            
            if not paragraph_visible.current or not paragraph_visible.current.visible:
                update_tts_status("ℹ️ Show summary first", "#FF9800")
                return
            
            # Sync local state with TTS manager state
            tts_state["is_speaking"] = tts_manager.is_speaking
            tts_state["is_paused"] = tts_manager.is_paused
            
            if tts_manager.is_paused and tts_manager.is_speaking:
                # Resume paused speech
                print("Resume button clicked - attempting to resume speech")
                try:
                    tts_manager.resume()
                    tts_state["is_paused"] = False
                    if play_pause_button.current:
                        play_pause_button.current.icon = ft.Icons.PAUSE
                        play_pause_button.current.tooltip = "Pause speech"
                    if restart_button.current:
                        restart_button.current.disabled = False
                    update_tts_status("▶️ Speech resumed", "#4CAF50")
                except Exception as resume_error:
                    print(f"Resume error: {resume_error}")
                    update_tts_status(f"❌ Resume failed: {str(resume_error)[:30]}...", "#F44336")
                    
            elif tts_manager.is_speaking and not tts_manager.is_paused:
                # Pause current speech
                print("Pause button clicked - attempting to pause speech")
                try:
                    tts_manager.pause()
                    tts_state["is_paused"] = True
                    if play_pause_button.current:
                        play_pause_button.current.icon = ft.Icons.PLAY_ARROW
                        play_pause_button.current.tooltip = "Resume speech"
                    update_tts_status("⏸️ Speech paused", "#FF9800")
                except Exception as pause_error:
                    print(f"Pause error: {pause_error}")
                    update_tts_status(f"❌ Pause failed: {str(pause_error)[:30]}...", "#F44336")
            else:
                # Start new speech
                text_to_speak = data["summaries"]["paragraph"]
                if not text_to_speak.strip():
                    update_tts_status("❌ No text to speak", "#F44336")
                    return
                
                # Test TTS first
                print("Testing TTS functionality before speaking...")
                if not tts_manager.test_speech():
                    update_tts_status("🔄 Retrying TTS...", "#FF9800")
                    page.update()
                    
                    # Try reinitializing TTS
                    if tts_manager.reinitialize_engine() and tts_manager.test_speech():
                        update_tts_status("✅ TTS recovered", "#4CAF50")
                    else:
                        update_tts_status("❌ TTS failed", "#F44336")
                        return
                
                # Start speaking
                tts_state["is_speaking"] = True
                tts_state["is_paused"] = False
                
                if play_pause_button.current:
                    play_pause_button.current.icon = ft.Icons.PAUSE
                    play_pause_button.current.tooltip = "Pause speech"
                if restart_button.current:
                    restart_button.current.disabled = False
                
                update_tts_status("🔊 Starting speech...", "#4CAF50")
                print(f"Speaking text: {text_to_speak[:100]}...")
                tts_manager.speak(text_to_speak, on_speech_complete)
            
            page.update()
        except Exception as e:
            print(f"Error in play_pause_speech: {e}")
            update_tts_status(f"❌ Error: {str(e)[:30]}...", "#F44336")
    
    def restart_speech(e):
        """Handle restart button click - stops current speech and starts from beginning"""
        try:
            if tts_manager.is_available:
                print("Restart button clicked - stopping and restarting speech")
                
                # Stop any current speech
                tts_manager.stop()
                tts_state["is_speaking"] = False
                tts_state["is_paused"] = False
                
                # Get text to speak
                text_to_speak = data["summaries"]["paragraph"]
                if not text_to_speak.strip():
                    update_tts_status("❌ No text to speak", "#F44336")
                    return
                
                # Start speaking from beginning
                tts_state["is_speaking"] = True
                tts_state["is_paused"] = False
                
                if play_pause_button.current:
                    play_pause_button.current.icon = ft.Icons.PAUSE
                    play_pause_button.current.tooltip = "Pause speech"
                if restart_button.current:
                    restart_button.current.disabled = False
                
                update_tts_status("🔄 Restarting speech...", "#4CAF50")
                print(f"Restarting speech from beginning: {text_to_speak[:100]}...")
                tts_manager.speak(text_to_speak, on_speech_complete)
                
                page.update()
        except Exception as e:
            print(f"Error in restart_speech: {e}")
            update_tts_status("❌ Restart error", "#F44336")
    
    def change_voice(e):
        """Handle voice selection change"""
        if tts_manager.is_available and voice_dropdown.current:
            voice_id = int(voice_dropdown.current.value) if voice_dropdown.current.value else 0
            tts_manager.set_voice(voice_id)
            tts_state["current_voice"] = voice_id
            update_tts_status(f"🎭 Voice changed", "#2196F3")
    
    def change_rate(e):
        """Handle speech rate change"""
        if tts_manager.is_available and rate_slider.current:
            rate = int(rate_slider.current.value)
            tts_manager.set_rate(rate)
            tts_state["rate"] = rate
    
    def change_volume(e):
        """Handle volume change"""
        if tts_manager.is_available and volume_slider.current:
            volume = int(volume_slider.current.value)
            tts_manager.set_volume(volume)
            tts_state["volume"] = volume
    
    # Get available voices for dropdown with enhanced gender/quality information
    voices = tts_manager.get_available_voices() if tts_manager.is_available else []
    voice_options = [ft.dropdown.Option(str(voice['id']), voice['display_name']) for voice in voices]
    if not voice_options:
        voice_options = [ft.dropdown.Option("0", "🌟 👩 Default Voice (Female recommended)")]
    
    # Find best default voice: Zira first, then any female recommended voice, then any recommended voice
    default_voice = "0"
    for voice in voices:
        if 'zira' in voice.get('name', '').lower():
            default_voice = str(voice['id'])
            break
        elif voice.get('is_female', False) and voice.get('recommended', False) and default_voice == "0":
            default_voice = str(voice['id'])
        elif voice.get('recommended', False) and default_voice == "0":
            default_voice = str(voice['id'])
    
    # TTS Controls Panel - Optimized for neurodivergent users
    tts_controls = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.RECORD_VOICE_OVER, color="#1976D2", size=20),
                ft.Text("🎤 Read Aloud", size=16, weight="bold", color="#1976D2"),
            ]),
            ft.Container(height=8),
            
            # Main controls row - simplified to just play/pause and restart
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.PLAY_ARROW,
                    tooltip="Play/Pause speech",
                    on_click=play_pause_speech,
                    ref=play_pause_button,
                    style=ft.ButtonStyle(
                        color="#FFFFFF",
                        bgcolor="#4CAF50",
                        shape=ft.CircleBorder(),
                        padding=12
                    )
                ),
                ft.IconButton(
                    icon=ft.Icons.RESTART_ALT,
                    tooltip="Restart from beginning",
                    on_click=restart_speech,
                    ref=restart_button,
                    style=ft.ButtonStyle(
                        color="#FFFFFF",
                        bgcolor="#2196F3",
                        shape=ft.CircleBorder(),
                        padding=12
                    )
                ),
            ], alignment=ft.MainAxisAlignment.START),
            
            # Status with better spacing
            ft.Container(height=8),
            ft.Text(
                "🔇 Ready to read aloud" if tts_manager.is_available else "❌ TTS not available",
                size=12,
                ref=tts_status,
                color="#666666",
                text_align=ft.TextAlign.CENTER
            ),
            
            ft.Container(height=12),
            
            # Voice selection with better labeling
            ft.Column([
                ft.Text("🎭 Voice Selection:", size=13, weight="w600", color="#1976D2"),
                ft.Container(height=4),
                ft.Dropdown(
                    options=voice_options,
                    value=default_voice,
                    on_change=change_voice,
                    ref=voice_dropdown,
                    disabled=not tts_manager.is_available,
                    text_size=12,
                    content_padding=10,
                    border_radius=8,
                    hint_text="Choose voice..."
                )
            ], spacing=0),
            
            ft.Container(height=12),
            
            # Speed control with neurodivergent-friendly range
            ft.Column([
                ft.Text("🐌 Reading Speed:", size=13, weight="w600", color="#1976D2"),
                ft.Container(height=4),
                ft.Slider(
                    min=-4,
                    max=2,
                    value=-2,  # Default slower speed for neurodivergent users
                    divisions=6,
                    label="Speed: {value}",
                    on_change=change_rate,
                    ref=rate_slider,
                    disabled=not tts_manager.is_available,
                    active_color="#2196F3",
                    thumb_color="#1976D2"
                )
            ], spacing=0),
            
            ft.Container(height=8),
            
            # Volume control
            ft.Column([
                ft.Text("🔊 Volume:", size=13, weight="w600", color="#1976D2"),
                ft.Container(height=4),
                ft.Slider(
                    min=0,
                    max=100,
                    value=85,  # Comfortable default volume
                    divisions=10,
                    label="Volume: {value}%",
                    on_change=change_volume,
                    ref=volume_slider,
                    disabled=not tts_manager.is_available,
                    active_color="#2196F3",
                    thumb_color="#1976D2"
                )
            ], spacing=0),
            
            ft.Container(height=12),
            
            # Voice information display
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "ℹ️ Voice Guide:",
                        size=12,
                        weight="w600",
                        color="#1976D2"
                    ),
                    ft.Text(
                        "🌟 = Recommended for neurodivergent users\n👩 = Female voice | 👨 = Male voice\n🎙️ = Standard quality voice",
                        size=10,
                        color="#666666",
                        text_align=ft.TextAlign.LEFT
                    )
                ], spacing=4),
                padding=8,
                bgcolor=ft.Colors.with_opacity(0.05, "#2196F3"),
                border_radius=8
            ),
            
            ft.Container(height=8),
            
            # Helpful tip for neurodivergent users
            ft.Container(
                content=ft.Text(
                    "💡 Tip: Try different voices and speeds to find what works best for you!",
                    size=10,
                    color="#666666",
                    text_align=ft.TextAlign.CENTER,
                    italic=True
                ),
                padding=8,
                bgcolor=ft.Colors.with_opacity(0.05, "#1976D2"),
                border_radius=8
            )
        ], spacing=0),
        padding=20,
        bgcolor="#F8F9FA" if theme_mode == ft.ThemeMode.LIGHT else "#383838",
        border_radius=12,
        border=ft.border.all(2, "#E3F2FD" if theme_mode == ft.ThemeMode.LIGHT else "#444851"),
        width=280,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=4,
            color=ft.Colors.with_opacity(0.1, "#1976D2"),
            offset=ft.Offset(0, 2),
        )
    )
    
    return tts_controls


def create_tts_unavailable_panel(theme_mode: ft.ThemeMode) -> ft.Container:
    """Create panel shown when TTS is not available"""
    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.VOICE_OVER_OFF, color="#999999", size=20),
                ft.Text("🎤 Read Aloud", size=16, weight="bold", color="#999999"),
            ]),
            ft.Container(height=10),
            ft.Text("❌ TTS not available", size=13, color="#999999", text_align=ft.TextAlign.CENTER),
            ft.Container(height=5),
            ft.Container(
                content=ft.Text(
                    "Install pywin32 for text-to-speech support",
                    size=10,
                    color="#999999",
                    italic=True,
                    text_align=ft.TextAlign.CENTER
                ),
                padding=8,
                bgcolor=ft.Colors.with_opacity(0.05, "#999999"),
                border_radius=8
            )
        ], spacing=5),
        padding=20,
        bgcolor="#F0F0F0" if theme_mode == ft.ThemeMode.LIGHT else "#2A2A2A",
        border_radius=12,
        border=ft.border.all(1, "#CCCCCC" if theme_mode == ft.ThemeMode.LIGHT else "#444444"),
        width=280
    )
