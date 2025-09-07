#!/usr/bin/env python3
"""
Build script for expense tracking application.
Handles compilation, resource bundling, and executable creation.
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
import json
import zipfile
import tempfile

# Build configuration
BUILD_CONFIG = {
    "app_name": "ExpenseTracker",
    "version": "2.0.0",
    "author": "Expense Tracker Team",
    "description": "Advanced expense splitting application",
    "main_script": "main.py",
    "icon_file": "resources/icons/app.ico",
    "exclude_modules": [
        "test",
        "tests",
        "pytest",
        "unittest",
        "doctest"
    ],
    "include_files": [
        "resources/",
        "data/",
        "README.md",
        "LICENSE"
    ]
}


def log_message(message: str, level: str = "INFO"):
    """Log build message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def check_dependencies():
    """Check if required build dependencies are installed."""
    log_message("Checking build dependencies...")
    
    required_packages = [
        "PyInstaller",
        "PySide6"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace("-", "_"))
            log_message(f"✓ {package} found")
        except ImportError:
            missing_packages.append(package)
            log_message(f"✗ {package} missing", "ERROR")
    
    if missing_packages:
        log_message("Installing missing packages...", "INFO")
        for package in missing_packages:
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
    
    return True


def clean_build_dirs():
    """Clean previous build artifacts."""
    log_message("Cleaning build directories...")
    
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            log_message(f"Removed {dir_name}")
    
    # Clean .pyc files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pyc"):
                os.remove(os.path.join(root, file))


def generate_version_info():
    """Generate version info file for Windows builds."""
    log_message("Generating version info...")
    
    version_info = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({BUILD_CONFIG['version'].replace('.', ',')},0),
    prodvers=({BUILD_CONFIG['version'].replace('.', ',')},0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'{BUILD_CONFIG["author"]}'),
           StringStruct(u'FileDescription', u'{BUILD_CONFIG["description"]}'),
           StringStruct(u'FileVersion', u'{BUILD_CONFIG["version"]}'),
           StringStruct(u'InternalName', u'{BUILD_CONFIG["app_name"]}'),
           StringStruct(u'LegalCopyright', u'Copyright © 2025'),
           StringStruct(u'OriginalFilename', u'{BUILD_CONFIG["app_name"]}.exe'),
           StringStruct(u'ProductName', u'{BUILD_CONFIG["app_name"]}'),
           StringStruct(u'ProductVersion', u'{BUILD_CONFIG["version"]}')]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    with open("version_info.txt", "w") as f:
        f.write(version_info)
    
    return "version_info.txt"


def create_spec_file():
    """Create PyInstaller spec file."""
    log_message("Creating PyInstaller spec file...")
    
    # Determine data files
    data_files = []
    for include_path in BUILD_CONFIG["include_files"]:
        if os.path.exists(include_path):
            if os.path.isdir(include_path):
                data_files.append((include_path, include_path))
            else:
                data_files.append((include_path, "."))
    
    # Create spec content
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{BUILD_CONFIG["main_script"]}'],
    pathex=[],
    binaries=[],
    datas={data_files},
    hiddenimports=['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={BUILD_CONFIG["exclude_modules"]},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{BUILD_CONFIG["app_name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{BUILD_CONFIG.get("icon_file", "")}',
    version='version_info.txt' if os.name == 'nt' else None,
)
"""
    
    spec_file = f"{BUILD_CONFIG['app_name']}.spec"
    with open(spec_file, "w") as f:
        f.write(spec_content)
    
    return spec_file


def build_executable(debug=False):
    """Build executable using PyInstaller."""
    log_message("Building executable...")
    
    # Generate version info for Windows
    version_file = None
    if os.name == 'nt':
        version_file = generate_version_info()
    
    # Create spec file
    spec_file = create_spec_file()
    
    # Build command
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        spec_file
    ]
    
    if debug:
        build_cmd.append("--debug=all")
    
    # Run build
    try:
        result = subprocess.run(build_cmd, check=True, capture_output=True, text=True)
        log_message("Build completed successfully")
        
        # Check if executable was created
        exe_name = f"{BUILD_CONFIG['app_name']}.exe" if os.name == 'nt' else BUILD_CONFIG['app_name']
        exe_path = Path("dist") / exe_name
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            log_message(f"Executable created: {exe_path} ({size_mb:.1f} MB)")
        else:
            log_message("Executable not found in expected location", "ERROR")
            return False
        
    except subprocess.CalledProcessError as e:
        log_message(f"Build failed: {e}", "ERROR")
        log_message(f"stdout: {e.stdout}", "ERROR")
        log_message(f"stderr: {e.stderr}", "ERROR")
        return False
    
    finally:
        # Cleanup
        if version_file and os.path.exists(version_file):
            os.remove(version_file)
        if os.path.exists(spec_file):
            os.remove(spec_file)
    
    return True


def create_installer():
    """Create installer package."""
    log_message("Creating installer package...")
    
    # Create installer directory
    installer_dir = Path("installer")
    installer_dir.mkdir(exist_ok=True)
    
    # Copy executable and resources
    dist_dir = Path("dist")
    if not dist_dir.exists():
        log_message("Distribution directory not found", "ERROR")
        return False
    
    # Create zip package
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"{BUILD_CONFIG['app_name']}_v{BUILD_CONFIG['version']}_{timestamp}.zip"
    zip_path = installer_dir / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add executable
        for file_path in dist_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(dist_dir)
                zipf.write(file_path, arcname)
        
        # Add additional files
        additional_files = ["README.md", "LICENSE"]
        for file_name in additional_files:
            if os.path.exists(file_name):
                zipf.write(file_name, file_name)
    
    log_message(f"Installer package created: {zip_path}")
    return True


def run_tests():
    """Run test suite before building."""
    log_message("Running tests...")
    
    test_dirs = ["tests", "test"]
    test_found = False
    
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            test_found = True
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", test_dir, "-v"
                ], check=True, capture_output=True, text=True)
                log_message("All tests passed")
            except subprocess.CalledProcessError as e:
                log_message(f"Tests failed: {e}", "ERROR")
                return False
            except ImportError:
                log_message("pytest not available, skipping tests", "WARNING")
            break
    
    if not test_found:
        log_message("No test directory found, skipping tests", "WARNING")
    
    return True


def optimize_build():
    """Optimize the built executable."""
    log_message("Optimizing build...")
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        return False
    
    # Remove unnecessary files
    unnecessary_patterns = [
        "*.pdb",
        "*.lib",
        "*test*",
        "*debug*"
    ]
    
    for pattern in unnecessary_patterns:
        for file_path in dist_dir.rglob(pattern):
            if file_path.is_file():
                file_path.unlink()
                log_message(f"Removed unnecessary file: {file_path}")
    
    return True


def generate_build_info():
    """Generate build information file."""
    log_message("Generating build info...")
    
    build_info = {
        "app_name": BUILD_CONFIG["app_name"],
        "version": BUILD_CONFIG["version"],
        "build_date": datetime.now().isoformat(),
        "build_platform": sys.platform,
        "python_version": sys.version,
        "build_type": "release"
    }
    
    # Save build info
    with open("dist/build_info.json", "w") as f:
        json.dump(build_info, f, indent=2)
    
    log_message("Build info generated")


def main():
    """Main build function."""
    parser = argparse.ArgumentParser(description="Build expense tracking application")
    parser.add_argument("--debug", action="store_true", help="Build in debug mode")
    parser.add_argument("--no-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--no-installer", action="store_true", help="Skip creating installer")
    parser.add_argument("--clean-only", action="store_true", help="Only clean build directories")
    
    args = parser.parse_args()
    
    try:
        # Clean previous builds
        clean_build_dirs()
        
        if args.clean_only:
            log_message("Clean completed")
            return 0
        
        # Check dependencies
        if not check_dependencies():
            return 1
        
        # Run tests unless skipped
        if not args.no_tests:
            if not run_tests():
                log_message("Build aborted due to test failures", "ERROR")
                return 1
        
        # Build executable
        if not build_executable(args.debug):
            return 1
        
        # Optimize build
        optimize_build()
        
        # Generate build info
        generate_build_info()
        
        # Create installer package
        if not args.no_installer:
            create_installer()
        
        log_message("Build process completed successfully!", "SUCCESS")
        return 0
        
    except KeyboardInterrupt:
        log_message("Build cancelled by user", "WARNING")
        return 1
    except Exception as e:
        log_message(f"Unexpected error: {e}", "ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())
