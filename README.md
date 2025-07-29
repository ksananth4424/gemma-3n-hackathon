# Windows Accessibility Assistant

A sophisticated Windows plugin that provides AI-powered content summarization for neurodivergent users, particularly those with ADHD. The assistant integrates directly into Windows Explorer's context menu, allowing users to quickly generate accessible summaries of PDFs, videos, and text documents using the local Gemma 3n language model.

## Key Features

- ADHD-Friendly Summarization: Generates clear, concise summaries optimized for neurodivergent users
- Windows Explorer Integration: Right-click context menu for seamless file processing
- Privacy-First: Runs entirely locally using Ollama and Gemma 3n - no data sent to cloud services
- Multi-Format Support: Processes PDFs, videos (MP4, AVI, MOV), and text documents
- Offline Capable: Works without internet connection
- Accessibility Focused: Designed with ADHD-specific UI/UX principles
- Smart Model Selection: Uses optimal model based on content type and complexity
- Dependency Injection: Efficient resource management and modular architecture

## Architecture

This application follows a sophisticated multi-layer architecture with dependency injection:

```
src/
├── bootstrap.py         # Dependency injection setup
├── service/            # Windows service and Ollama integration
│   └── ollama_service.py   # Smart model selection and AI processing
├── shell/            # Windows Explorer context menu integration  
├── processors/         # Content extraction with specialized processors
│   ├── content_processor.py  # Main orchestrator
│   ├── pdf_processor.py     # PDF extraction with OCR
│   ├── video_processor.py   # Video transcription with Whisper
│   └── text_processor.py    # Text format handling
├── ui/                # ADHD-friendly user interfaces
├── utils/             # Configuration, logging, DI container
└── models/            # Ollama Modelfiles for optimized prompts
```

## Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.8+**
- **Ollama** (for running Gemma 3n locally)
- **Gemma 3n models** (gemma3n:e2b and gemma3n:e4b)

## Quick Start

### 1. Install Ollama
```bash
# Download from https://ollama.com
# Or via winget:
winget install Ollama.Ollama
```

### 2. Install Gemma 3n Models
```bash
ollama pull gemma3n:e2b  # 5.6GB - for text processing
ollama pull gemma3n:e4b  # 7.5GB - for video/audio processing
```

### 3. Clone and Setup
```bash
git clone https://github.com/your-username/gemma-3n-hackathon.git
cd gemma-3n-hackathon
pip install -r requirements.txt
```

### 4. Ollama 
```bash
ollama pull gemma3n:e2b

ollama pull gemma3n:e2b
```

### 5. Test Installation
```bash
python src\ui\main.py README.md
```

### 6. Setup Windows Context Menu Integration

1. Right-click on `src\shell\add_adhd_reader_silent.reg`
2. Select "Run as administrator"
3. Click "Yes" to confirm registry changes

### 7. Usage via Context Menu
1. Right-click any supported file (.pdf, .txt, .md, .docx, .rtf)
2. Select **"Open with Prism"**
3. The ADHD-friendly summary will open automatically (no console windows!)

### 8. Manual Usage (Alternative)
```bash
# Direct Python execution
python src\ui\main.py "path\to\your\file.pdf"
```

## Usage

### Windows Context Menu (Recommended)
1. **Install context menu**: Right-click `src\shell\add_adhd_reader_silent.reg` → Run as administrator
2. **Process any file**: Right-click supported file → "Open with Prism"
3. **View summary**: ADHD-friendly interface opens automatically with:
   - 📌 **TL;DR**: Quick 1-2 sentence summary
   - 🔹 **Key Points**: 3-5 bullet points highlighting main ideas
   - 🧾 **Full Summary**: Complete paragraph overview (click to expand)
   - 📘 **File Content**: Raw extracted text for reference

### Supported File Types & Processing
| File Type | Extensions | Processing Method |
|-----------|------------|------------------|
| **Text Documents** | `.txt`, `.md` | Direct text extraction |
| **Rich Documents** | `.docx`, `.rtf` | Document structure parsing |  
| **PDFs** | `.pdf` | Text extraction + basic OCR |
| **Videos** | `.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv` | Audio transcription (requires setup) |

### File Processing Examples
```bash
# Prism automatically handles different file types:
python src\ui\main.py "meeting-notes.txt"      # → Instant text analysis
python src\ui\main.py "research-paper.pdf"     # → PDF text extraction + AI summary
python src\ui\main.py "project-spec.md"        # → Markdown parsing + summary
python src\ui\main.py "report.docx"            # → Document structure analysis
```

## Smart Model Selection

The system automatically selects the optimal model based on content type:

- **gemma3n:e4b (7.5GB)**: For complex content (videos, audio, long PDFs)
- **gemma3n:e2b (5.6GB)**: For text documents and quick processing

## Configuration

Configuration files are located in `config/`:

- `service_config.json`: General service settings
- `ai_config.json`: AI model and prompt configuration  
- `logging_config.json`: Logging configuration

### AI Configuration Example
```json
{
  "model": {
    "name": "gemma3n:e4b",
    "fallback_model": "gemma3n:e2b",
    "temperature": 0.3
  },
  "summarization": {
    "max_key_points": 5,
    "adhd_optimized": true,
    "use_bullet_points": true
  }
}
```
```bash
pip install -r requirements.txt
```

### 5. Test Installation
```bash
python main.py "path/to/test/file.pdf"
```

## Configuration

### AI Configuration (`config/ai_config.json`)
- **Model Selection**: Choose between `gemma3n:e2b` or `gemma3n:e4b`
- **Summarization Settings**: Adjust key points count, length, formatting
- **Performance**: Memory limits, GPU settings

### Service Configuration (`config/service_config.json`)
- **File Support**: Enable/disable file types
- **Size Limits**: Maximum file size processing
- **Concurrency**: Parallel processing settings

## ADHD-Optimized Features

**Cognitive Load Management**
- **Limited Key Points**: Summaries focus on 3-5 main points maximum
- **Clear Structure**: Consistent formatting with headers and bullet points
- **Simple Language**: Grade 8 reading level, avoids jargon and complex terminology
- **Collapsible Sections**: Show/hide full summary to reduce overwhelm

**Visual Design**  
- **Clean Interface**: Removed colored boxes and distracting elements
- **High Contrast**: Accessibility-compliant visual design
- **Font Controls**: Adjustable text size (12-24px)
- **Dark Mode**: Reduces eye strain during extended use

**Performance & Feedback**
- **Fast Processing**: Optimized prompts for quicker AI responses
- **Loading Animations**: Clear progress feedback during processing
- **Silent Operation**: No console windows or technical distractions
- **Instant Previews**: Immediate file info while AI processes

**ADHD-Specific Adaptations**
- **Structured Output**: TL;DR → Key Points → Full Summary progression
- **Scannable Format**: Easy to skim and find relevant information
- **Context Preservation**: File content always available for reference
- **Distraction-Free**: Minimal, focused interfaces without clutter

### Ollama Service Issues
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Verify models are installed
ollama list | findstr gemma3n
```

### Python Dependencies
```bash
# Reinstall requirements
pip install -r requirements.txt

# Test Python execution
python src\ui\main.py README.md
```

## Development

### Project Structure
```
├── src/                          # Source code
│   ├── ui/main.py               # Main ADHD-friendly interface  
│   ├── processors/              # Content extraction engines
│   ├── service/ollama_service.py # AI model integration
│   ├── shell/                   # Windows Explorer integration
│   ├── utils/                   # Configuration and utilities
│   └── models/                  # Data models
├── config/                      # Configuration files
│   ├── ai_config.json          # AI prompts and settings
│   └── service_config.json     # Service configuration  
├── run_adhd_reader_silent.vbs  # Silent VBScript launcher
├── adhd_reader.bat             # Batch file launcher
└── requirements.txt            # Python dependencies
```

---

**Note**: This project provides a complete, production-ready ADHD accessibility tool with seamless Windows integration. The silent launcher system ensures a professional, distraction-free user experience. 
