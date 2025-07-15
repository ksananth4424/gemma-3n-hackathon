# Development Environment Setup

## Prerequisites
- Python 3.8+
- Git
- Ollama installed
- Gemma 3n models downloaded

## Local Development

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configuration
Copy configuration templates and customize:
```bash
cp config/ai_config.json.example config/ai_config.json
# Edit configuration files as needed
```

### 3. Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test module
pytest tests/test_processors.py -v
```

### 4. Linting and Formatting
```bash
# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/

# Type checking
mypy src/
```

## Build Process

### Development Build
```bash
python build/build.py --dev
```

### Production Build
```bash
python build/build.py --prod --installer
```

## Debugging

### Enable Debug Logging
```bash
python main.py --verbose file.pdf
```

### Service Debugging
```bash
# Run service in console mode
python src/service/accessibility_service.py debug
```
