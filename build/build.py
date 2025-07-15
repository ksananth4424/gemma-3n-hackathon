# Build script for Windows Accessibility Assistant
import os
import subprocess
import shutil
import sys
from pathlib import Path
import argparse

class ProjectBuilder:
    def __init__(self, project_root=None):
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.build_dir = self.project_root / "build" / "dist"
        self.src_dir = self.project_root / "src"
        
    def clean_build(self):
        """Clean previous build artifacts"""
        print("Cleaning build directory...")
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.build_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean other build artifacts
        for pattern in ["*.spec", "build/", "dist/"]:
            for path in self.project_root.glob(pattern):
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
    
    def install_build_dependencies(self):
        """Install build dependencies"""
        print("Installing build dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pyinstaller", "setuptools", "wheel"
        ], check=True)
    
    def build_main_executable(self):
        """Build main processor executable"""
        print("Building main executable...")
        cmd = [
            "pyinstaller",
            "--onefile",
            "--console",
            "--name", "accessibility-processor",
            "--add-data", f"{self.src_dir};src",
            "--add-data", f"{self.project_root}/config;config",
            str(self.project_root / "main.py")
        ]
        
        subprocess.run(cmd, cwd=self.project_root, check=True)
    
    def create_development_installer(self):
        """Create simple development installer"""
        print("Creating development installer...")
        
        installer_script = self.project_root / "install_dev.bat"
        installer_content = f"""@echo off
echo Installing Windows Accessibility Assistant (Development)
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check Ollama installation
ollama list >nul 2>&1
if errorlevel 1 (
    echo Ollama is not installed or not in PATH
    echo Please install Ollama and try again
    pause
    exit /b 1
)

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Test installation
echo Testing installation...
python main.py --help

echo.
echo Installation completed!
echo You can now use: python main.py "file_path"
pause
"""
        
        with open(installer_script, 'w') as f:
            f.write(installer_content)
        
        print(f"Development installer created: {installer_script}")
    
    def build_development(self):
        """Build for development"""
        print("Building development version...")
        self.clean_build()
        self.install_build_dependencies()
        self.create_development_installer()
        print("Development build completed!")
    
    def build_production(self):
        """Build for production"""
        print("Building production version...")
        self.clean_build()
        self.install_build_dependencies()
        self.build_main_executable()
        self.create_development_installer()  # For now, same as dev
        print("Production build completed!")

def main():
    parser = argparse.ArgumentParser(description="Build Windows Accessibility Assistant")
    parser.add_argument("--dev", action="store_true", help="Development build")
    parser.add_argument("--prod", action="store_true", help="Production build")
    parser.add_argument("--clean", action="store_true", help="Clean only")
    
    args = parser.parse_args()
    
    builder = ProjectBuilder()
    
    if args.clean:
        builder.clean_build()
    elif args.dev:
        builder.build_development()
    elif args.prod:
        builder.build_production()
    else:
        print("Please specify --dev, --prod, or --clean")
        parser.print_help()

if __name__ == "__main__":
    main()
