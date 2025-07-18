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
├── shell/              # Windows Explorer context menu integration  
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

### 4. Test Installation
```bash
python test_setup.py
```

### 5. Setup Models (First Time)
```bash
python main.py --setup-models
```

## Current Status

 **Backend Complete & Tested**
- Dependency injection system working
- Ollama service integration functional
- Smart model selection operational
- Text file processing confirmed working
- ADHD-optimized summarization generating quality output
- End-to-end pipeline tested successfully

 **Partially Complete**
- PDF processing (requires PyMuPDF installation)
- Video processing (requires whisper and ffmpeg)

 **In Development**
- Windows Explorer context menu integration
- GUI interface for non-technical users

## Usage

### Command Line Interface
```bash
# Process a PDF
python main.py document.pdf

# Process a video with verbose output
python main.py video.mp4 --verbose

# Save summary to file
python main.py document.txt --output summary.txt

# Output as JSON
python main.py file.pdf --format json
```

### File Processing Examples
```bash
# Text documents
python main.py "C:\Documents\report.txt"
python main.py "C:\Documents\article.docx"

# PDF documents  
python main.py "C:\Documents\research.pdf"

# Video files
python main.py "C:\Videos\lecture.mp4"
python main.py "C:\Videos\tutorial.avi"
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

## Quick Start

### Command Line Usage
```bash
# Process a PDF file
python main.py document.pdf

# Process with custom output
python main.py video.mp4 --output summary.txt --format text

# Verbose logging
python main.py document.docx --verbose
```

### Windows Explorer Integration (Coming Soon)
1. Right-click any supported file in Windows Explorer
2. Select "Generate Accessibility Summary"
3. View ADHD-friendly summary in popup window

## Configuration

### AI Configuration (`config/ai_config.json`)
- **Model Selection**: Choose between `gemma3n:e2b` or `gemma3n:e4b`
- **Summarization Settings**: Adjust key points count, length, formatting
- **Performance**: Memory limits, GPU settings

### Service Configuration (`config/service_config.json`)
- **File Support**: Enable/disable file types
- **Size Limits**: Maximum file size processing
- **Concurrency**: Parallel processing settings

## Supported File Types

| Type | Extensions | Processing Method |
|------|------------|------------------|
| **PDFs** | `.pdf` | PyMuPDF + OCR for scanned docs |
| **Videos** | `.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv` | FFmpeg + Whisper transcription |
| **Documents** | `.txt`, `.docx`, `.rtf`, `.md` | Direct text extraction |

## ADHD-Optimized Features

- **Limited Key Points**: Summaries focus on 3-5 main points maximum
- **Clear Structure**: Consistent formatting with headers and bullet points
- **Simple Language**: Avoids jargon and complex terminology
- **High Contrast UI**: Accessibility-compliant visual design
- **Progress Indicators**: Clear feedback during processing
- **Distraction-Free**: Minimal, focused interfaces

## Development

### Project Structure
```
├── src/                    # Source code
│   ├── processors/         # Content extraction engines
│   ├── service/           # Windows service implementation
│   ├── shell/             # Explorer context menu
│   ├── ui/                # User interface components
│   ├── utils/             # Shared utilities
│   └── models/            # Data models
├── config/                # Configuration files
├── resources/             # Icons, templates
├── tests/                 # Test suite
├── docs/                  # Documentation
├── installer/             # Installation scripts
└── build/                 # Build and packaging
```

---

**Note**: This project is currently in active development. 
