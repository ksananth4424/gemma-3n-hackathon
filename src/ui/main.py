import flet as ft
import json
import time
import sys
import os
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any

# Add the project root to the path so we can import from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import TTS functionality with fallback for direct execution
try:
    from .tts_manager import tts_manager
    from .tts_components import create_tts_controls_panel, create_tts_unavailable_panel
except ImportError:
    # Fallback for direct script execution
    from tts_manager import tts_manager
    from tts_components import create_tts_controls_panel, create_tts_unavailable_panel

# Global backend container - initialize once for performance
backend_container = None
processing_lock = threading.Lock()

def initialize_backend():
    """Initialize the backend once for fast response times"""
    global backend_container
    if backend_container is None:
        try:
            print("Initializing backend...")
            # Check if we're running from executable
            import sys
            if getattr(sys, 'frozen', False):
                print("Running from executable - adjusting paths...")
                # We're running from PyInstaller bundle
                import os
                bundle_dir = sys._MEIPASS
                sys.path.insert(0, bundle_dir)
                print(f"Bundle directory: {bundle_dir}")
            
            # Check if Ollama is running
            import subprocess
            try:
                result = subprocess.run(["ollama", "list"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    raise Exception("Ollama service not running")
                print("Ollama service verified")
            except FileNotFoundError:
                raise Exception("Ollama not found in PATH")
            except Exception as e:
                raise Exception(f"Ollama check failed: {e}")
            
            # Initialize bootstrap with error handling
            try:
                from src.bootstrap import get_bootstrap
                bootstrap = get_bootstrap()
                print("Bootstrap loaded")
            except ImportError as e:
                print(f"Bootstrap import failed: {e}")
                # Try alternative import for executable
                try:
                    import bootstrap
                    bootstrap = bootstrap.get_bootstrap()
                    print("Bootstrap loaded (alternative path)")
                except Exception as e2:
                    raise Exception(f"Could not import bootstrap: {e}, {e2}")
            
            # Perform health check
            try:
                if not bootstrap.health_check():
                    raise Exception("Backend health check failed")
                print("Health check passed")
            except Exception as e:
                raise Exception(f"Health check error: {e}")
            
            backend_container = bootstrap
            print("Backend initialized and ready")
            
        except ImportError as e:
            error_msg = f"Backend import failed: {e}"
            print(f"{error_msg}")
            print("Running in standalone mode without AI processing")
            backend_container = None
        except Exception as e:
            error_msg = f"Backend initialization failed: {e}"
            print(f"{error_msg}")
            print("Make sure Ollama service is running: ollama serve")
            print("Try running the Python version: python src\\ui\\main.py <file>")
            backend_container = None
    return backend_container

def process_file_with_backend(file_path):
    """Process file using the initialized backend"""
    try:
        bootstrap = initialize_backend()
        if not bootstrap:
            raise Exception("Backend not available")
        
        print(f"Processing file with backend: {file_path}")
        
        # Get content processor from bootstrap
        content_processor = bootstrap.get_content_processor()
        
        # Process file and get structured results
        result = content_processor.process_file(file_path)
        
        if not result.get('success', False):
            raise Exception(result.get('error', 'Processing failed'))
        
        # Extract structured summary data
        structured_summary = result.get('structured_summary', {})
        content = result.get('content', '')
        
        # Handle both old and new format for compatibility
        if structured_summary:
            tldr = structured_summary.get('tldr', '')
            bullets = structured_summary.get('bullets', [])
            paragraph = structured_summary.get('paragraph', '')
        else:
            # Fallback to old format
            summary = result.get('summary', '')
            sentences = summary.split('. ')[:3]
            tldr = summary[:200] + "..." if len(summary) > 200 else summary
            bullets = [sentence.strip() + '.' for sentence in sentences if sentence.strip()]
            paragraph = summary
        
        return {
            "file_path": file_path,
            "extension": Path(file_path).suffix,
            "summaries": {
                "tldr": tldr,
                "bullets": bullets,
                "paragraph": paragraph
            },
            "file_content": content[:2000] + "..." if len(content) > 2000 else content,
            "backend_used": True,
            "processing_time": result.get('metadata', {}).get('processing_time', 0)
        }
        
    except Exception as e:
        print(f"Backend processing failed: {e}")
        # Fallback to file info display
        return get_file_info_fallback(file_path, str(e))

def get_file_info_fallback(file_path, error_message=""):
    """Enhanced fallback with fast processing for immediate feedback"""
    if not file_path or not os.path.exists(file_path):
        return DUMMY_DATA
    
    file_path = Path(file_path)
    
    try:
        # Use fast processor for immediate results
        from src.utils.fast_processor import fast_file_validation, fast_extract_text_content, is_text_file, is_audio_file, is_video_file, create_quick_summary
        
        # Quick validation
        validation = fast_file_validation(str(file_path))
        if not validation.get("valid", False):
            return create_error_fallback(str(file_path), validation.get("error", "Unknown error"))
        
        file_size = validation["size"]
        size_mb = file_size / (1024 * 1024)
        
        # Fast content extraction for text files
        if is_text_file(str(file_path)):
            content = fast_extract_text_content(str(file_path))
            quick_summary = create_quick_summary(content, str(file_path))
            
            return {
                "file_path": str(file_path.absolute()),
                "extension": file_path.suffix,
                "summaries": quick_summary,
                "file_content": content[:2000] + "..." if len(content) > 2000 else content,
                "backend_used": False,
                "processing_time": 0.1  # Very fast
            }
        elif is_audio_file(str(file_path)) or is_video_file(str(file_path)):
            # Audio and video files - show informational summary
            quick_summary = create_quick_summary("", str(file_path))
            media_type = "audio" if is_audio_file(str(file_path)) else "video"
            
            return {
                "file_path": str(file_path.absolute()),
                "extension": file_path.suffix,
                "summaries": quick_summary,
                "file_content": f"{media_type.title()} file: {file_path.name}\nSize: {size_mb:.2f} MB\nType: {file_path.suffix.upper()}\n\nTo view transcribed content, ensure the AI backend is running and try again. The system will automatically extract speech content and provide ADHD-friendly summaries.",
                "backend_used": False,
                "processing_time": 0.05
            }
        else:
            # Non-text file
            return {
                "file_path": str(file_path.absolute()),
                "extension": file_path.suffix,
                "summaries": {
                    "tldr": f"Binary file '{file_path.name}' ({size_mb:.2f} MB)",
                    "bullets": [
                        f"📁 File: {file_path.name}",
                        f"📊 Size: {size_mb:.2f} MB ({file_size:,} bytes)",
                        f"📄 Type: {file_path.suffix.upper()} file",
                        "ℹ️ Binary file - content preview not available"
                    ],
                    "paragraph": f"This is a binary file named '{file_path.name}' with a size of {size_mb:.2f} MB. The file type is {file_path.suffix.upper()}. For AI-powered analysis of this file type, ensure the backend services are running and the file type is supported."
                },
                "file_content": f"Binary file: {file_path.name}\nSize: {size_mb:.2f} MB\nType: {file_path.suffix.upper()}\n\nContent preview not available for binary files.",
                "backend_used": False,
                "processing_time": 0.05
            }
    except Exception as e:
        return create_error_fallback(str(file_path), str(e))

def create_error_fallback(file_path: str, error: str) -> Dict[str, Any]:
    """Create error fallback result"""
    return {
        "file_path": file_path,
        "extension": ".txt",
        "summaries": {
            "tldr": f"Could not process file: {error[:100]}",
            "bullets": [
                "❌ File processing failed",
                f"Error: {error[:50]}...",
                "Try using the Python version directly"
            ],
            "paragraph": f"An error occurred while trying to process the file: {error}"
        },
        "file_content": f"Error reading file: {error}",
        "backend_used": False,
        "processing_time": 0
    }

def create_loading_page(page: ft.Page, file_name: str = None) -> ft.Container:
    """Create an animated loading page"""
    
    file_text = f"Processing {file_name}..." if file_name else "Initializing Prism..."
    
    # Create progress ring
    progress_ring = ft.ProgressRing(width=50, height=50, stroke_width=4)
    
    # Create loading messages that cycle
    loading_messages = [
        "🔍 Analyzing content...",
        "🧠 Generating neurodivergent-friendly summary...",
        "📝 Creating key points...",
        "✨ Almost ready..."
    ]
    
    loading_text = ft.Text(
        loading_messages[0],
        size=16,
        text_align=ft.TextAlign.CENTER,
        italic=True
    )
    
    # Create loading container
    loading_container = ft.Container(
        content=ft.Column([
            ft.Text(
                file_text,
                size=24,
                weight="bold",
                text_align=ft.TextAlign.CENTER,
                color="#0D47A1"
            ),
            ft.Container(height=20),  # Spacer
            progress_ring,
            ft.Container(height=20),  # Spacer
            loading_text,
            ft.Container(height=20),  # Spacer
            ft.Text(
                "⚡ Using optimized AI processing for faster results",
                size=12,
                text_align=ft.TextAlign.CENTER,
                color="#666",
                italic=True
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10
        ),
        alignment=ft.alignment.center,
        expand=True,
        padding=50
    )
    
    # Animate loading text
    def update_loading_message():
        import random
        if loading_text:
            loading_text.value = random.choice(loading_messages)
            page.update()
    
    # Update loading message every 2 seconds
    def loading_animation():
        for i in range(10):  # Run for 20 seconds max
            if loading_text:
                time.sleep(2)
                update_loading_message()
            else:
                break
    
    # Start animation in background
    threading.Thread(target=loading_animation, daemon=True).start()
    
    return loading_container

def process_file_async(file_path: str, page: ft.Page, callback):
    """Process file asynchronously and call callback when done"""
    def worker():
        with processing_lock:
            try:
                print(f"🚀 Starting async processing for: {file_path}")
                start_time = time.time()
                
                # Process the file
                result = process_file_with_backend(file_path)
                
                processing_time = time.time() - start_time
                result['actual_processing_time'] = processing_time
                
                print(f"✅ Processing completed in {processing_time:.2f}s")
                
                # Call the callback with results
                callback(result, None)
                
            except Exception as e:
                print(f"❌ Async processing failed: {e}")
                callback(None, str(e))
    
    # Start processing in background thread
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread
DUMMY_DATA = {
    "file_path": "C:/Users/aryah/Documents/sample_document.pdf",
    "extension": ".pdf",
    "summaries": {
        "tldr": "Quickly explains the core ideas behind attention strategies.",
        "bullets": [
            "Defines ADHD in simple terms",
            "Lists common behavioral patterns",
            "Shares techniques for improved focus"
        ],
        "paragraph": "The document gives a concise yet informative overview of Attention Deficit Hyperactivity Disorder (ADHD). "
            "It highlights symptoms, diagnosis methods, and behavioral therapy options for individuals, especially children. "
            "The emphasis is on early detection and practical coping mechanisms to manage attention-related challenges effectively."
    },
    "file_content": (
        "ADHD stands for Attention Deficit Hyperactivity Disorder. It is a neurological disorder that affects a person’s "
        "ability to focus, control impulses, and maintain attention. Children and adults with ADHD often struggle with "
        "organization and time management. This guide walks through essential ADHD symptoms, diagnosis procedures, and coping "
        "strategies such as creating structured environments, using reminders, and building positive routines."
    )
}

def main(page: ft.Page):
    page.title = "Prism"
    page.scroll = "auto"
    page.window_width = 900
    page.window_height = 800
    page.fonts = {"lexend": "https://fonts.googleapis.com/css2?family=Lexend&display=swap"}
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.bgcolor = "#FAFAFA"

    # Get file path from command line arguments (from context menu)
    file_path = None
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"File received from context menu: {file_path}")
    else:
        print("No file provided - using demo data")

    # Initialize backend in the background (non-blocking)
    print("Starting backend initialization...")
    initialize_backend()

    # State variables for async processing
    content_data = {"value": None}
    is_loading = {"value": True}
    summaries_controls = []  # Store summary controls for font size updates
    
    # Create loading page initially
    file_name = Path(file_path).name if file_path else None
    loading_container = create_loading_page(page, file_name)
    
    # Font size and theme settings
    font_size_slider = ft.Slider(
        min=12, 
        max=24, 
        divisions=6, 
        label="{value}px", 
        value=16,
        active_color="#1976D2",
        thumb_color="#1976D2"
    )
    
    theme_switch = ft.Switch(
        label="Dark Mode",
        active_color="#1976D2"
    )

    paragraph_visible = ft.Ref[ft.Text]()
    toggle_btn = ft.Ref[ft.ElevatedButton]()
    tts_container_ref = ft.Ref[ft.Container]()

    def toggle_paragraph(e):
        if paragraph_visible.current:
            # Toggle visibility of the paragraph container
            is_visible = not paragraph_visible.current.visible
            paragraph_visible.current.visible = is_visible
            
            # Also toggle TTS controls visibility
            if tts_container_ref.current:
                tts_container_ref.current.visible = is_visible
            
            if toggle_btn.current:
                if is_visible:
                    toggle_btn.current.text = "Hide Full Summary"
                    toggle_btn.current.icon = ft.Icons.EXPAND_LESS
                else:
                    toggle_btn.current.text = "Show Full Summary"
                    toggle_btn.current.icon = ft.Icons.EXPAND_MORE
            page.update()

    def change_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if theme_switch.value else ft.ThemeMode.LIGHT
        page.bgcolor = "#1E1E1E" if theme_switch.value else "#FAFAFA"
        # Rebuild UI to update all colors
        if content_data["value"]:
            build_content_ui(content_data["value"])
        else:
            page.update()

    def update_font_size(e):
        for ctrl in summaries_controls:
            if ctrl:
                ctrl.size = font_size_slider.value
        page.update()

    def create_card(content, padding=20):
        """Create a Streamlit-like card container"""
        card_bg = "#FFFFFF" if page.theme_mode == ft.ThemeMode.LIGHT else "#23272F"
        card_border = "#E0E0E0" if page.theme_mode == ft.ThemeMode.LIGHT else "#444851"
        return ft.Container(
            content=content,
            padding=padding,
            margin=ft.margin.only(bottom=20),
            bgcolor=card_bg,
            border_radius=12,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.1, "#000000"),
                offset=ft.Offset(0, 2),
            ),
            border=ft.border.all(1, card_border)
        )

    def create_section_header(text, icon=""):
        """Create a consistent section header"""
        return ft.Row([
            ft.Text(
                f"{icon} {text}",
                size=22,
                weight="bold",
                font_family="lexend",
                color="#1976D2"
            )
        ], alignment=ft.MainAxisAlignment.START)

    def build_content_ui(data):
        """Build the main content UI with processed data"""
        page.controls.clear()  # Clear loading screen
        
        # Main container for all content
        main_container = ft.Column(
            controls=[],
            spacing=0,
            expand=True
        )
        
        # Header section
        welcome_text = "Prism"
        if file_path:
            file_name = Path(file_path).name
            welcome_text = f"Prism\n{file_name}"
        
        header_text_color = "#1976D2" if page.theme_mode == ft.ThemeMode.LIGHT else "#FFB74D"
        status_color = "#4CAF50" if data.get("backend_used", False) else ("#FF9800" if page.theme_mode == ft.ThemeMode.LIGHT else "#FFD54F")
        header_card = create_card(
            ft.Column([
                ft.Text(
                    welcome_text,
                    size=36,
                    weight="bold",
                    font_family="lexend",
                    color=header_text_color,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=10),
                # Enhanced status indicator
                ft.Row([
                    ft.Icon(
                        ft.Icons.SMART_TOY if data.get("backend_used", False) else ft.Icons.DASHBOARD,
                        color=status_color,
                        size=20
                    ),
                    ft.Text(
                        f"Processed with AI Backend ({data.get('actual_processing_time', 0):.1f}s)" 
                        if data.get("backend_used", False) 
                        else "Demo Mode / Backend Unavailable",
                        size=14,
                        color=status_color,
                        font_family="lexend"
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=30
        )
        main_container.controls.append(header_card)

        # Settings card
        settings_card = create_card(
            ft.Column([
                create_section_header("Settings", "⚙️"),
                ft.Container(height=15),
                ft.Row([
                    ft.Container(
                        ft.Row([
                            ft.Text("Font Size:", font_family="lexend", weight="w500"),
                            ft.Container(width=10),
                            ft.Container(
                                font_size_slider,
                                expand=True
                            )
                        ]),
                        expand=True
                    ),
                    ft.Container(width=30),
                    theme_switch
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ])
        )
        main_container.controls.append(settings_card)
        
        # File info card
        label_color = "#666666" if page.theme_mode == ft.ThemeMode.LIGHT else "#BDBDBD"
        value_color = "#2E2E2E" if page.theme_mode == ft.ThemeMode.LIGHT else "#F5F5F5"
        file_info_card = create_card(
            ft.Column([
                create_section_header("File Information", "📄"),
                ft.Container(height=15),
                ft.Container(
                    ft.Column([
                        ft.Row([
                            ft.Text("File:", weight="bold", font_family="lexend", color=label_color),
                            ft.Text(Path(data["file_path"]).name, font_family="lexend", color=value_color)
                        ]),
                        ft.Row([
                            ft.Text("Type:", weight="bold", font_family="lexend", color=label_color),
                            ft.Text(data["extension"].upper(), font_family="lexend", color=value_color)
                        ]),
                        ft.Row([
                            ft.Text("AI Processed:", weight="bold", font_family="lexend", color=label_color),
                            ft.Text("Yes" if data.get("backend_used", False) else "No", font_family="lexend", color=value_color)
                        ])
                    ], spacing=8),
                    padding=15,
                    bgcolor="#F8F9FA" if page.theme_mode == ft.ThemeMode.LIGHT else "#383838",
                    border_radius=8
                )
            ])
        )
        main_container.controls.append(file_info_card)

        # Clear summaries controls for new content
        summaries_controls.clear()

        # TL;DR card
        tldr_text = ft.Text(
            data["summaries"]["tldr"],
            font_family="lexend",
            size=font_size_slider.value,
            color="#2E2E2E" if page.theme_mode == ft.ThemeMode.LIGHT else "#FFECB3"
        )
        tldr_card = create_card(
            ft.Column([
                create_section_header("TL;DR", "📌"),
                ft.Container(height=15),
                tldr_text
            ])
        )
        main_container.controls.append(tldr_card)
        summaries_controls.append(tldr_text)

        # Key points card
        bullet_controls = []
        bullet_column = ft.Column([], spacing=12)
        
        for i, point in enumerate(data["summaries"]["bullets"], 1):
            bullet = ft.Row([
                ft.Container(
                    ft.CircleAvatar(
                        content=ft.Text(str(i), size=12, weight="bold", color="#FFFFFF"),
                        bgcolor="#1976D2" if page.theme_mode == ft.ThemeMode.LIGHT else "#FFB300",
                        radius=12
                    )
                ),
                ft.Container(width=10),
                ft.Text(
                    point,
                    font_family="lexend",
                    size=font_size_slider.value,
                    expand=True,
                    color="#2E2E2E" if page.theme_mode == ft.ThemeMode.LIGHT else "#FFECB3"
                )
            ])
            bullet_column.controls.append(bullet)
            bullet_controls.append(bullet.controls[2])  # The text component
            summaries_controls.append(bullet.controls[2])

        key_points_card = create_card(
            ft.Column([
                create_section_header("Key Points", "🔹"),
                ft.Container(height=15),
                bullet_column
            ])
        )
        main_container.controls.append(key_points_card)

        # Full summary card (collapsible) with TTS controls positioned to the right
        paragraph_text = ft.Text(
            data["summaries"]["paragraph"],
            font_family="lexend",
            size=font_size_slider.value,
            visible=False,
            ref=paragraph_visible,
            color="#2E2E2E" if page.theme_mode == ft.ThemeMode.LIGHT else "#FFECB3"
        )
        
        toggle_button = ft.ElevatedButton(
            "Show Full Summary",
            ref=toggle_btn,
            on_click=toggle_paragraph,
            style=ft.ButtonStyle(
                bgcolor="#1976D2",
                color="#FFFFFF",
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            icon=ft.Icons.EXPAND_MORE
        )
        
        # Create TTS controls using the separate component
        tts_controls = create_tts_controls_panel(
            data=data,
            paragraph_visible=paragraph_visible,
            page=page,
            theme_mode=page.theme_mode
        ) if tts_manager.is_available else create_tts_unavailable_panel(page.theme_mode)
        
        # Full summary content with TTS positioned to the right when expanded
        full_summary_content = ft.Column([
            create_section_header("Full Summary", "📋"),
            ft.Container(height=15),
            
            # Toggle button row
            ft.Row([
                toggle_button,
            ], alignment=ft.MainAxisAlignment.START),
            
            ft.Container(height=10),
            
            # Content and TTS side by side when expanded
            ft.Row([
                # Left side: paragraph text
                ft.Container(
                    content=paragraph_text,
                    expand=True,
                    padding=ft.padding.only(right=20)
                ),
                # Right side: TTS controls (only visible when paragraph is visible)
                ft.Container(
                    content=tts_controls,
                    visible=False,  # Will be controlled by toggle
                    ref=tts_container_ref
                )
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START)
        ])
        
        full_summary_card = create_card(full_summary_content)
        main_container.controls.append(full_summary_card)
        summaries_controls.append(paragraph_text)

        # File content card
        file_content_bg = "#F8F9FA" if page.theme_mode == ft.ThemeMode.LIGHT else "#181A20"
        file_content_text = "#2E2E2E" if page.theme_mode == ft.ThemeMode.LIGHT else "#F5F5F5"
        content_card = create_card(
            ft.Column([
                create_section_header("File Content", "📘"),
                ft.Container(height=15),
                ft.Container(
                    ft.Text(
                        data["file_content"],
                        font_family="Consolas",
                        size=14,
                        selectable=True,
                        color=file_content_text
                    ),
                    padding=20,
                    bgcolor=file_content_bg,
                    border_radius=8,
                    border=ft.border.all(1, "#E0E0E0" if page.theme_mode == ft.ThemeMode.LIGHT else "#444851")
                )
            ])
        )
        main_container.controls.append(content_card)
        
        # Set up event handlers
        theme_switch.on_change = change_theme
        font_size_slider.on_change = update_font_size
        
        page.add(main_container)
        page.update()

    def on_processing_complete(result, error):
        """Callback when async processing completes"""
        if error:
            # Handle error case
            error_data = get_file_info_fallback(file_path, error)
            build_content_ui(error_data)
        else:
            # Handle success case
            content_data["value"] = result
            is_loading["value"] = False
            build_content_ui(result)

    # Show loading screen initially
    page.add(loading_container)
    page.update()

    # Start processing
    if file_path and os.path.exists(file_path):
        # Process file asynchronously
        process_file_async(file_path, page, on_processing_complete)
    else:
        # Use demo data immediately
        demo_data = DUMMY_DATA.copy()
        demo_data["backend_used"] = False
        demo_data["actual_processing_time"] = 0
        
        # Simulate brief loading for demo
        def show_demo():
            time.sleep(1)
            on_processing_complete(demo_data, None)
        
        threading.Thread(target=show_demo, daemon=True).start()

if __name__ == "__main__":
    # Use ASCII-safe messages for Windows console compatibility
    try:
        print("Starting Prism...")
        if len(sys.argv) > 1:
            print(f"File from context menu: {sys.argv[1]}")
        else:
            print("Running in demo mode")
    except UnicodeEncodeError:
        # Fallback to ASCII-safe messages
        print("Starting Prism...")
        if len(sys.argv) > 1:
            print(f"File from context menu: {sys.argv[1]}")
        else:
            print("Running in demo mode")
    
    ft.app(target=main)
