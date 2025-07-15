# Windows Accessibility Assistant

A Windows plugin that provides AI-powered content summarization for neurodivergent users, particularly those with ADHD. The assistant integrates directly into Windows Explorer's context menu, allowing users to quickly generate accessible summaries of PDFs, videos, and text documents using the local Gemma 3n language model.

## Key Features

- **ADHD-Friendly Summarization**: Generates clear, concise summaries optimized for neurodivergent users
- **Windows Explorer Integration**: Right-click context menu for seamless file processing
- **Privacy-First**: Runs entirely locally using Ollama and Gemma 3n - no data sent to cloud services
- **Multi-Format Support**: Processes PDFs, videos (MP4, AVI, MOV), and text documents
- **Offline Capable**: Works without internet connection
- **Accessibility Focused**: Designed with ADHD-specific UI/UX principles

## Architecture

```
src/
├── service/          # Windows service for background processing
├── shell/            # Windows Explorer context menu integration  
├── processors/       # Content extraction (PDF, video, text)
├── ui/              # ADHD-friendly user interfaces
├── utils/           # Configuration, logging, helpers
└── models/          # Data models for requests/responses
```

## Prerequisites

- **Windows 10/11** (64-bit)
- **Python 3.8+**
- **Ollama** (for running Gemma 3n locally)
- **Gemma 3n model** (via Ollama)

## Installation

### 1. Install Ollama
Download and install Ollama from [ollama.com](https://ollama.com)

### 2. Install Gemma 3n Models
```bash
ollama pull gemma3n:e2b  # 5.6GB model
ollama pull gemma3n:e4b  # 7.5GB model (recommended)
```

### 3. Clone Repository
```bash
git clone https://github.com/your-username/gemma-3n-hackathon.git
cd gemma-3n-hackathon
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Test Installation
```bash
python main.py "path/to/test/file.pdf"
```

## 🚀 Quick Start

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
