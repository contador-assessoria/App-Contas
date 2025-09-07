#!/usr/bin/env python3
"""
Installation script for expense tracking application.
Handles setup, dependency installation, and configuration.
"""

import os
import sys
import subprocess
import argparse
import shutil
import urllib.request
import json
from pathlib import Path
from datetime import datetime
import tempfile
import platform

# Installation configuration
INSTALL_CONFIG = {
    "app_name": "ExpenseTracker",
    "version": "2.0.0",
    "min_python_version": (3, 9),
    "required_packages": [
        "PySide6>=6.5.0",
        "openpyxl>=3.1.0", 
        "reportlab>=4.0.0"
    ],
    "optional_packages": [
        "matplotlib>=3.5.0",
        "pandas>=1.5.0"
    ],
    "app_directories": [
        "data",
        "data/backups",
        "exports",
        "logs"
    ],
    "default_config": {
        "theme": "dark",
        "language": "pt_BR",
        "auto_save": True,
        "auto_backup": True
    }
}


def log_message(message: str, level: str = "INFO"):
    """Log installation message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def check_python_version():
    """Check if Python version meets requirements."""
    log_message("Checking Python version...")
    
    current_version = sys.version_info[:2]
    required_version = INSTALL_CONFIG["min_python_version"]
    
    if current_version < required_version:
        log_message(
            f"Python {required_version[0]}.{required_version[1]}+ required, "
            f"but {current_version[0]}.{current_version[1]} found",
            "ERROR"
        )
        return False
    
    log_message(f"Python {current_version[0]}.{current_version[1]} found - OK")
    return True


def check_pip_available():
    """Check if pip is available."""
    log_message("Checking pip availability...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True, text=True)
        log_message("pip is available")
        return True
    except subprocess.CalledProcessError:
        log_message("pip not found", "ERROR")
        return False


def create_virtual_environment(venv_path: Path):
    """Create virtual environment."""
    log_message(f"Creating virtual environment at {venv_path}...")
    
    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        log_message("Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"Failed to create virtual environment: {e}", "ERROR")
        return False


def get_venv_python(venv_path: Path):
    """Get path to Python executable in virtual environment."""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_venv_pip(venv_path: Path):
    """Get path to pip executable in virtual environment."""
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def install_packages(packages: list, venv_path: Path = None, optional: bool = False):
    """Install Python packages."""
    package_type = "optional" if optional else "required"
    log_message(f"Installing {package_type} packages...")
    
    if venv_path:
        pip_cmd = [str(get_venv_pip(venv_path))]
    else:
        pip_cmd = [sys.executable, "-m", "pip"]
    
    for package in packages:
        try:
            log_message(f"Installing {package}...")
            cmd = pip_cmd + ["install", package]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            log_message(f"✓ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            if optional:
                log_message(f"⚠ Failed to install optional package {package}: {e}", "WARNING")
            else:
                log_message(f"✗ Failed to install required package {package}: {e}", "ERROR")
                return False
    
    return True


def create_app_directories(install_path: Path):
    """Create application directories."""
    log_message("Creating application directories...")
    
    for dir_name in INSTALL_CONFIG["app_directories"]:
        dir_path = install_path / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            log_message(f"Created directory: {dir_path}")
        except OSError as e:
            log_message(f"Failed to create directory {dir_path}: {e}", "ERROR")
            return False
    
    return True


def copy_application_files(source_path: Path, install_path: Path):
    """Copy application files to installation directory."""
    log_message("Copying application files...")
    
    files_to_copy = [
        "src/",
        "main.py",
        "requirements.txt",
        "README.md",
        "LICENSE"
    ]
    
    optional_files = [
        "resources/",
        "docs/"
    ]
    
    # Copy required files
    for item in files_to_copy:
        source_item = source_path / item
        if source_item.exists():
            if source_item.is_dir():
                dest_item = install_path / item
                shutil.copytree(source_item, dest_item, dirs_exist_ok=True)
                log_message(f"Copied directory: {item}")
            else:
                shutil.copy2(source_item, install_path)
                log_message(f"Copied file: {item}")
        else:
            log_message(f"Required file not found: {item}", "ERROR")
            return False
    
    # Copy optional files
    for item in optional_files:
        source_item = source_path / item
        if source_item.exists():
            if source_item.is_dir():
                dest_item = install_path / item
                shutil.copytree(source_item, dest_item, dirs_exist_ok=True)
                log_message(f"Copied optional directory: {item}")
            else:
                shutil.copy2(source_item, install_path)
                log_message(f"Copied optional file: {item}")
    
    return True


def create_default_config(install_path: Path):
    """Create default configuration file."""
    log_message("Creating default configuration...")
    
    config_path = install_path / "data" / "settings.json"
    
    try:
        with open(config_path, "w") as f:
            json.dump(INSTALL_CONFIG["default_config"], f, indent=2)
        
        log_message(f"Default configuration created: {config_path}")
        return True
    except OSError as e:
        log_message(f"Failed to create configuration: {e}", "ERROR")
        return False


def create_launcher_scripts(install_path: Path, venv_path: Path = None):
    """Create launcher scripts for the application."""
    log_message("Creating launcher scripts...")
    
    if platform.system() == "Windows":
        return create_windows_launcher(install_path, venv_path)
    else:
        return create_unix_launcher(install_path, venv_path)


def create_windows_launcher(install_path: Path, venv_path: Path = None):
    """Create Windows batch launcher."""
    launcher_content = f"""@echo off
setlocal

REM Change to application directory
cd /d "{install_path}"

REM Set up environment
set PYTHONPATH={install_path};%PYTHONPATH%

REM Run application
"""
    
    if venv_path:
        python_exe = get_venv_python(venv_path)
        launcher_content += f'"{python_exe}" main.py %*\n'
    else:
        launcher_content += f'python main.py %*\n'
    
    launcher_content += """
if errorlevel 1 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)
endlocal
"""
    
    launcher_path = install_path / f"{INSTALL_CONFIG['app_name']}.bat"
    
    try:
        with open(launcher_path, "w") as f:
            f.write(launcher_content)
        log_message(f"Windows launcher created: {launcher_path}")
        return True
    except OSError as e:
        log_message(f"Failed to create Windows launcher: {e}", "ERROR")
        return False


def create_unix_launcher(install_path: Path, venv_path: Path = None):
    """Create Unix shell launcher."""
    launcher_content = f"""#!/bin/bash

# Change to application directory
cd "{install_path}"

# Set up environment
export PYTHONPATH="{install_path}:$PYTHONPATH"

# Run application
"""
    
    if venv_path:
        python_exe = get_venv_python(venv_path)
        launcher_content += f'"{python_exe}" main.py "$@"\n'
    else:
        launcher_content += 'python3 main.py "$@"\n'
    
    launcher_content += """
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo
    echo "Application exited with error code $exit_code"
    read -p "Press Enter to continue..."
fi
"""
    
    launcher_path = install_path / f"{INSTALL_CONFIG['app_name'].lower()}.sh"
    
    try:
        with open(launcher_path, "w") as f:
            f.write(launcher_content)
        
        # Make executable
        os.chmod(launcher_path, 0o755)
        
        log_message(f"Unix launcher created: {launcher_path}")
        return True
    except OSError as e:
        log_message(f"Failed to create Unix launcher: {e}", "ERROR")
        return False


def create_desktop_entry(install_path: Path):
    """Create desktop entry for Linux."""
    if platform.system() != "Linux":
        return True
    
    log_message("Creating desktop entry...")
    
    desktop_content = f"""[Desktop Entry]
Name={INSTALL_CONFIG['app_name']}
Comment=Advanced expense splitting application
Exec={install_path}/{INSTALL_CONFIG['app_name'].lower()}.sh
Icon={install_path}/resources/icons/app.png
Terminal=false
Type=Application
Categories=Office;Finance;
StartupNotify=true
"""
    
    # Try to create in user applications directory
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_path = desktop_dir / f"{INSTALL_CONFIG['app_name'].lower()}.desktop"
    
    try:
        with open(desktop_path, "w") as f:
            f.write(desktop_content)
        
        # Make executable
        os.chmod(desktop_path, 0o755)
        
        log_message(f"Desktop entry created: {desktop_path}")
        return True
    except OSError as e:
        log_message(f"Failed to create desktop entry: {e}", "WARNING")
        return True  # Not critical


def verify_installation(install_path: Path, venv_path: Path = None):
    """Verify that installation was successful."""
    log_message("Verifying installation...")
    
    # Check if main script exists
    main_script = install_path / "main.py"
    if not main_script.exists():
        log_message("Main script not found", "ERROR")
        return False
    
    # Check if src directory exists
    src_dir = install_path / "src"
    if not src_dir.exists():
        log_message("Source directory not found", "ERROR")
        return False
    
    # Try to import main modules
    try:
        if venv_path:
            python_exe = get_venv_python(venv_path)
        else:
            python_exe = sys.executable
        
        test_cmd = [
            str(python_exe), "-c",
            f"import sys; sys.path.insert(0, '{install_path}'); "
            "from src.core import DataManager; print('Import test passed')"
        ]
        
        result = subprocess.run(test_cmd, check=True, capture_output=True, text=True)
        log_message("Module import test passed")
        return True
        
    except subprocess.CalledProcessError as e:
        log_message(f"Module import test failed: {e}", "ERROR")
        return False


def create_uninstaller(install_path: Path, venv_path: Path = None):
    """Create uninstaller script."""
    log_message("Creating uninstaller...")
    
    if platform.system() == "Windows":
        uninstaller_content = f"""@echo off
echo Uninstalling {INSTALL_CONFIG['app_name']}...
echo.

set /p confirm="Are you sure you want to uninstall? (y/N): "
if /i not "%confirm%"=="y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo Removing application files...
cd /d "{install_path.parent}"
rmdir /s /q "{install_path.name}"

echo.
echo {INSTALL_CONFIG['app_name']} has been uninstalled.
echo Note: User data in %APPDATA%\\{INSTALL_CONFIG['app_name']} was preserved.
pause
"""
        uninstaller_path = install_path / "uninstall.bat"
    else:
        uninstaller_content = f"""#!/bin/bash

echo "Uninstalling {INSTALL_CONFIG['app_name']}..."
echo

read -p "Are you sure you want to uninstall? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo "Removing application files..."
rm -rf "{install_path}"

# Remove desktop entry if it exists
desktop_entry="$HOME/.local/share/applications/{INSTALL_CONFIG['app_name'].lower()}.desktop"
if [ -f "$desktop_entry" ]; then
    rm "$desktop_entry"
    echo "Desktop entry removed."
fi

echo
echo "{INSTALL_CONFIG['app_name']} has been uninstalled."
echo "Note: User data in ~/.{INSTALL_CONFIG['app_name'].lower()} was preserved."
"""
        uninstaller_path = install_path / "uninstall.sh"
    
    try:
        with open(uninstaller_path, "w") as f:
            f.write(uninstaller_content)
        
        if platform.system() != "Windows":
            os.chmod(uninstaller_path, 0o755)
        
        log_message(f"Uninstaller created: {uninstaller_path}")
        return True
    except OSError as e:
        log_message(f"Failed to create uninstaller: {e}", "WARNING")
        return True  # Not critical


def print_installation_summary(install_path: Path, venv_path: Path = None):
    """Print installation summary."""
    print("\n" + "="*60)
    print(f"{INSTALL_CONFIG['app_name']} v{INSTALL_CONFIG['version']} Installation Complete!")
    print("="*60)
    print(f"Installation directory: {install_path}")
    if venv_path:
        print(f"Virtual environment: {venv_path}")
    print()
    print("To run the application:")
    
    if platform.system() == "Windows":
        print(f"  Double-click: {install_path / (INSTALL_CONFIG['app_name'] + '.bat')}")
        print(f"  Or run: {install_path / (INSTALL_CONFIG['app_name'] + '.bat')}")
    else:
        print(f"  Run: {install_path / (INSTALL_CONFIG['app_name'].lower() + '.sh')}")
        if platform.system() == "Linux":
            print(f"  Or find '{INSTALL_CONFIG['app_name']}' in your applications menu")
    
    print()
    print("To uninstall:")
    uninstaller = "uninstall.bat" if platform.system() == "Windows" else "uninstall.sh"
    print(f"  Run: {install_path / uninstaller}")
    print()
    print("Enjoy using the application!")
    print("="*60)


def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="Install expense tracking application")
    parser.add_argument("--install-dir", type=Path, 
                       help="Installation directory (default: ~/ExpenseTracker)")
    parser.add_argument("--use-venv", action="store_true",
                       help="Create and use virtual environment")
    parser.add_argument("--system-install", action="store_true",
                       help="Install system-wide (requires admin privileges)")
    parser.add_argument("--no-optional", action="store_true",
                       help="Skip optional packages")
    parser.add_argument("--source-dir", type=Path, default=".",
                       help="Source directory (default: current directory)")
    
    args = parser.parse_args()
    
    try:
        log_message(f"Starting installation of {INSTALL_CONFIG['app_name']} v{INSTALL_CONFIG['version']}")
        
        # Check prerequisites
        if not check_python_version():
            return 1
        
        if not check_pip_available():
            return 1
        
        # Determine installation directory
        if args.install_dir:
            install_path = args.install_dir
        elif args.system_install:
            if platform.system() == "Windows":
                install_path = Path("C:/Program Files") /
