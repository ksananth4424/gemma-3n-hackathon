# Build script for Windows Accessibility Assistant
import os
import subprocess
import shutil
import sys
from pathlib import Path
import argparse
import json

class ProjectBuilder:
    def __init__(self, project_root=None):
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.build_dir = self.project_root / "build" / "dist"
        self.src_dir = self.project_root / "src"
        self.config_dir = self.project_root / "config"
        self.resources_dir = self.project_root / "resources"
        
    def clean_build(self):
        """Clean previous build artifacts"""
        print("🧹 Cleaning build directory...")
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.build_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean other build artifacts
        for pattern in ["*.spec", "dist/", "__pycache__/"]:
            for path in self.project_root.rglob(pattern):
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                elif path.is_file() and pattern.endswith('.spec'):
                    path.unlink()
        
        print("   ✅ Build directory cleaned")
    
    def install_build_dependencies(self):
        """Install build dependencies"""
        print("📦 Installing build dependencies...")
        
        dependencies = [
            "pyinstaller>=6.0.0",
            "setuptools>=68.0.0", 
            "wheel>=0.41.0"
        ]
        
        for dep in dependencies:
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], check=True, capture_output=True)
                print(f"   ✅ Installed {dep}")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to install {dep}: {e}")
                return False
        
        return True
    
    def build_executable(self):
        """Build executable with PyInstaller"""
        print("🔨 Building executable...")
        
        try:
            # Create simple one-file executable
            cmd = [
                "pyinstaller",
                "--onefile",
                "--console",
                "--name", "accessibility-assistant",
                "--add-data", f"{self.config_dir};config",
                "--add-data", f"{self.src_dir};src",
                "--hidden-import", "src.bootstrap",
                "--hidden-import", "src.service.ollama_service",
                "--hidden-import", "src.processors.content_processor",
                "--hidden-import", "src.utils.config_manager",
                "--hidden-import", "ollama",
                "--clean",
                "--noconfirm",
                str(self.project_root / "main.py")
            ]
            
            print(f"   Running: pyinstaller...")
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("   ✅ Executable built successfully")
                return True
            else:
                print(f"   ❌ Build failed:")
                print(f"   STDERR: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Build failed: {e}")
            return False
    
    def create_portable_package(self):
        """Create portable package"""
        print("📦 Creating portable package...")
        
        portable_dir = self.build_dir / "portable"
        portable_dir.mkdir(exist_ok=True)
        
        # Copy executable
        exe_path = self.project_root / "dist" / "accessibility-assistant.exe"
        if exe_path.exists():
            shutil.copy2(exe_path, portable_dir)
        
        # Create run script
        run_script = portable_dir / "run.bat"
        run_script.write_text('''@echo off
echo Windows Accessibility Assistant
echo ================================
echo.
accessibility-assistant.exe %*
if errorlevel 1 (
    echo.
    echo An error occurred. Press any key to exit.
    pause > nul
)
''')
        
        # Create readme
        readme = portable_dir / "README.txt"
        readme.write_text('''Windows Accessibility Assistant - Portable Version

This is a portable version of the Windows Accessibility Assistant.
No installation is required.

Prerequisites:
- Ollama installed and running on your system
- Gemma 3n models (gemma3n:e2b, gemma3n:e4b) available in Ollama

Usage:
1. Run "accessibility-assistant.exe" directly
2. Or use "run.bat" for a nicer experience

Examples:
  accessibility-assistant.exe document.pdf
  accessibility-assistant.exe video.mp4 --output summary.txt
  accessibility-assistant.exe text.md --format json

For more information, visit: https://github.com/yourusername/accessibility-assistant
''')
        
        print(f"   ✅ Portable package created: {portable_dir}")
        return portable_dir
    
    def create_archive(self, target_dir, archive_name):
        """Create compressed archive"""
        print(f"🗜️ Creating archive: {archive_name}")
        
        try:
            archive_path = self.build_dir / archive_name
            shutil.make_archive(
                str(archive_path.with_suffix('')), 
                'zip', 
                target_dir
            )
            print(f"   ✅ Archive created: {archive_path}.zip")
            return archive_path.with_suffix('.zip')
        except Exception as e:
            print(f"   ❌ Failed to create archive: {e}")
            return None
    
    def validate_build(self):
        """Validate the built executable"""
        print("🔍 Validating build...")
        
        executable = self.project_root / "dist" / "accessibility-assistant.exe"
        if not executable.exists():
            print("   ❌ Main executable not found")
            return False
        
        print("   ✅ Executable exists")
        
        # Check file size (should be reasonable)
        file_size_mb = executable.stat().st_size / (1024 * 1024)
        print(f"   📊 Executable size: {file_size_mb:.1f} MB")
        
        if file_size_mb < 10:
            print("   ⚠️ Executable seems small - might be missing dependencies")
        elif file_size_mb > 500:
            print("   ⚠️ Executable seems large - might include unnecessary files")
        
        return True
    
    def full_build(self, create_installer=True, create_portable=True):
        """Perform complete build process"""
        print("🚀 Starting full build process...")
        print("=" * 60)
        
        # Step 1: Clean
        self.clean_build()
        
        # Step 2: Install dependencies
        if not self.install_build_dependencies():
            print("❌ Build failed: Could not install dependencies")
            return False
        
        # Step 3: Build main executable
        if not self.build_executable():
            print("❌ Build failed: Could not build main executable")
            return False
        
        # Step 4: Validate
        if not self.validate_build():
            print("❌ Build failed: Validation failed")
            return False
        
        # Step 5: Create packages
        success = True
        
        if create_portable:
            portable_dir = self.create_portable_package()
            if portable_dir:
                archive = self.create_archive(portable_dir, "accessibility-assistant-portable")
                if archive:
                    print(f"   📦 Portable package: {archive}")
        
        print("=" * 60)
        if success:
            print("🎉 Build completed successfully!")
            print(f"📁 Build output: {self.build_dir}")
            
            # Print what was created
            exe_path = self.project_root / "dist" / "accessibility-assistant.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"   🎯 Main executable: {exe_path} ({size_mb:.1f} MB)")
            
            if (self.build_dir / "portable").exists():
                print(f"   📦 Portable package: {self.build_dir / 'portable'}")
                
            print("\n📋 Next steps:")
            print("   1. Test the executable")
            print("   2. Distribute the portable package")
        else:
            print("❌ Build failed")
        
        return success


def main():
    parser = argparse.ArgumentParser(description="Build Windows Accessibility Assistant")
    parser.add_argument("--clean-only", action="store_true", help="Only clean build directory")
    parser.add_argument("--no-installer", action="store_true", help="Skip installer creation")
    parser.add_argument("--no-portable", action="store_true", help="Skip portable package")
    parser.add_argument("--validate-only", action="store_true", help="Only validate existing build")
    
    args = parser.parse_args()
    
    builder = ProjectBuilder()
    
    if args.clean_only:
        builder.clean_build()
        return
    
    if args.validate_only:
        success = builder.validate_build()
        sys.exit(0 if success else 1)
    
    # Full build
    success = builder.full_build(
        create_installer=not args.no_installer,
        create_portable=not args.no_portable
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
