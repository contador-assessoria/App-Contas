#!/usr/bin/env python3
"""
Packaging script for creating distributable packages.
Handles different package formats and deployment preparations.
"""

import os
import sys
import shutil
import subprocess
import argparse
import zipfile
import tarfile
from pathlib import Path
from datetime import datetime
import json
import hashlib
import tempfile

# Package configuration
PACKAGE_CONFIG = {
    "app_name": "ExpenseTracker",
    "version": "2.0.0",
    "author": "Expense Tracker Team",
    "license": "MIT",
    "homepage": "https://github.com/expense-tracker/expense-tracker",
    "description": "Advanced expense splitting application for households",
    "keywords": ["expense", "tracker", "household", "budget", "finance"],
    "platforms": ["Windows", "Linux", "macOS"],
    "python_requires": ">=3.9",
    "dependencies": [
        "PySide6>=6.5.0",
        "openpyxl>=3.1.0",
        "reportlab>=4.0.0"
    ]
}


def log_message(message: str, level: str = "INFO"):
    """Log packaging message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate file hash."""
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def create_source_package():
    """Create source code package."""
    log_message("Creating source package...")
    
    # Create package directory
    package_dir = Path("packages")
    package_dir.mkdir(exist_ok=True)
    
    # Source files to include
    source_files = [
        "src/",
        "resources/",
        "scripts/",
        "requirements.txt",
        "README.md",
        "LICENSE",
        "main.py"
    ]
    
    # Create source archive
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{PACKAGE_CONFIG['app_name']}_source_v{PACKAGE_CONFIG['version']}_{timestamp}"
    
    # Create both zip and tar.gz versions
    formats = [
        ("zip", zipfile.ZipFile, zipfile.ZIP_DEFLATED),
        ("tar.gz", tarfile.open, "w:gz")
    ]
    
    created_packages = []
    
    for ext, archive_class, mode in formats:
        archive_path = package_dir / f"{archive_name}.{ext}"
        
        if ext == "zip":
            with archive_class(archive_path, 'w', mode) as archive:
                for item in source_files:
                    if os.path.exists(item):
                        if os.path.isdir(item):
                            for root, dirs, files in os.walk(item):
                                # Skip __pycache__ and .git directories
                                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.pytest_cache']]
                                
                                for file in files:
                                    if not file.endswith('.pyc'):
                                        file_path = Path(root) / file
                                        arcname = str(file_path)
                                        archive.write(file_path, arcname)
                        else:
                            archive.write(item, item)
        else:  # tar.gz
            with archive_class(archive_path, mode) as archive:
                for item in source_files:
                    if os.path.exists(item):
                        archive.add(item, arcname=item, 
                                  filter=lambda tarinfo: None if tarinfo.name.endswith('.pyc') or 
                                         '__pycache__' in tarinfo.name else tarinfo)
        
        # Calculate hash
        file_hash = calculate_file_hash(archive_path)
        
        # Create hash file
        hash_file = archive_path.with_suffix(f"{archive_path.suffix}.sha256")
        with open(hash_file, "w") as f:
            f.write(f"{file_hash}  {archive_path.name}\n")
        
        created_packages.append((archive_path, file_hash))
        log_message(f"Created source package: {archive_path}")
    
    return created_packages


def create_binary_package():
    """Create binary distribution package."""
    log_message("Creating binary package...")
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        log_message("Distribution directory not found. Run build script first.", "ERROR")
        return []
    
    package_dir = Path("packages")
    package_dir.mkdir(exist_ok=True)
    
    # Platform-specific packaging
    platform = sys.platform
    if platform.startswith("win"):
        platform_name = "windows"
        archive_ext = "zip"
    elif platform.startswith("linux"):
        platform_name = "linux"
        archive_ext = "tar.gz"
    elif platform.startswith("darwin"):
        platform_name = "macos"
        archive_ext = "zip"
    else:
        platform_name = "unknown"
        archive_ext = "zip"
    
    # Create binary archive
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{PACKAGE_CONFIG['app_name']}_binary_{platform_name}_v{PACKAGE_CONFIG['version']}_{timestamp}"
    archive_path = package_dir / f"{archive_name}.{archive_ext}"
    
    if archive_ext == "zip":
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in dist_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(dist_dir)
                    zipf.write(file_path, arcname)
    else:  # tar.gz
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(dist_dir, arcname=PACKAGE_CONFIG['app_name'])
    
    # Calculate hash
    file_hash = calculate_file_hash(archive_path)
    
    # Create hash file
    hash_file = archive_path.with_suffix(f"{archive_path.suffix}.sha256")
    with open(hash_file, "w") as f:
        f.write(f"{file_hash}  {archive_path.name}\n")
    
    log_message(f"Created binary package: {archive_path}")
    return [(archive_path, file_hash)]


def create_portable_package():
    """Create portable application package."""
    log_message("Creating portable package...")
    
    dist_dir = Path("dist")
    if not dist_dir.exists():
        log_message("Distribution directory not found", "ERROR")
        return []
    
    package_dir = Path("packages")
    package_dir.mkdir(exist_ok=True)
    
    # Create portable directory structure
    portable_name = f"{PACKAGE_CONFIG['app_name']}_portable_v{PACKAGE_CONFIG['version']}"
    portable_dir = package_dir / portable_name
    
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir()
    
    # Copy application files
    app_dir = portable_dir / "app"
    shutil.copytree(dist_dir, app_dir)
    
    # Create data directory
    data_dir = portable_dir / "data"
    data_dir.mkdir()
    
    # Create settings directory
    settings_dir = portable_dir / "settings"
    settings_dir.mkdir()
    
    # Create launcher script
    if sys.platform.startswith("win"):
        launcher_content = f"""@echo off
cd /d "%~dp0"
app\\{PACKAGE_CONFIG['app_name']}.exe
pause
"""
        launcher_path = portable_dir / f"Run_{PACKAGE_CONFIG['app_name']}.bat"
    else:
        launcher_content = f"""#!/bin/bash
cd "$(dirname "$0")"
./app/{PACKAGE_CONFIG['app_name']}
"""
        launcher_path = portable_dir / f"run_{PACKAGE_CONFIG['app_name'].lower()}.sh"
        # Make executable
        os.chmod(launcher_path, 0o755)
    
    with open(launcher_path, "w") as f:
        f.write(launcher_content)
    
    # Create README for portable version
    readme_content = f"""# {PACKAGE_CONFIG['app_name']} Portable

This is a portable version of {PACKAGE_CONFIG['app_name']} v{PACKAGE_CONFIG['version']}.

## How to Run

### Windows:
Double-click on "Run_{PACKAGE_CONFIG['app_name']}.bat"

### Linux/macOS:
Run "./run_{PACKAGE_CONFIG['app_name'].lower()}.sh" in terminal

## Portable Features

- No installation required
- All data stored in the "data" folder
- Settings stored in the "settings" folder
- Can be run from USB drive or any location

## Folders

- app/: Application files
- data/: Application data (expenses, backups)
- settings/: Configuration files

## System Requirements

- {PACKAGE_CONFIG['python_requires']} (bundled)
- Minimum 100MB free space
- Supported OS: {', '.join(PACKAGE_CONFIG['platforms'])}

For more information, visit: {PACKAGE_CONFIG['homepage']}
"""
    
    readme_path = portable_dir / "README.txt"
    with open(readme_path, "w") as f:
        f.write(readme_content)
    
    # Create zip archive of portable version
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{portable_name}_{timestamp}.zip"
    archive_path = package_dir / archive_name
    
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in portable_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)
    
    # Clean up temporary directory
    shutil.rmtree(portable_dir)
    
    # Calculate hash
    file_hash = calculate_file_hash(archive_path)
    
    # Create hash file
    hash_file = archive_path.with_suffix(f"{archive_path.suffix}.sha256")
    with open(hash_file, "w") as f:
        f.write(f"{file_hash}  {archive_path.name}\n")
    
    log_message(f"Created portable package: {archive_path}")
    return [(archive_path, file_hash)]


def create_installer_package():
    """Create installer package using platform-specific tools."""
    log_message("Creating installer package...")
    
    if sys.platform.startswith("win"):
        return create_windows_installer()
    elif sys.platform.startswith("linux"):
        return create_linux_package()
    elif sys.platform.startswith("darwin"):
        return create_macos_package()
    else:
        log_message("Installer creation not supported on this platform", "WARNING")
        return []


def create_windows_installer():
    """Create Windows installer using NSIS or Inno Setup."""
    log_message("Creating Windows installer...")
    
    # Check if NSIS is available
    nsis_available = shutil.which("makensis") is not None
    
    if not nsis_available:
        log_message("NSIS not found, skipping Windows installer creation", "WARNING")
        return []
    
    # Create NSIS script
    nsis_script = f"""
!define APP_NAME "{PACKAGE_CONFIG['app_name']}"
!define APP_VERSION "{PACKAGE_CONFIG['version']}"
!define APP_PUBLISHER "{PACKAGE_CONFIG['author']}"
!define APP_URL "{PACKAGE_CONFIG['homepage']}"
!define APP_EXE "${{APP_NAME}}.exe"

Name "${{APP_NAME}}"
OutFile "packages\\${{APP_NAME}}_installer_v${{APP_VERSION}}.exe"
InstallDir "$PROGRAMFILES\\${{APP_NAME}}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath $INSTDIR
    File /r "dist\\*"
    
    CreateDirectory "$SMPROGRAMS\\${{APP_NAME}}"
    CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
    CreateShortCut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
    
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayName" "${{APP_NAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\*"
    RMDir /r "$INSTDIR"
    Delete "$SMPROGRAMS\\${{APP_NAME}}\\*"
    RMDir "$SMPROGRAMS\\${{APP_NAME}}"
    Delete "$DESKTOP\\${{APP_NAME}}.lnk"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}"
SectionEnd
"""
    
    nsis_file = "installer.nsi"
    with open(nsis_file, "w") as f:
        f.write(nsis_script)
    
    try:
        subprocess.run(["makensis", nsis_file], check=True)
        os.remove(nsis_file)
        
        installer_path = Path("packages") / f"{PACKAGE_CONFIG['app_name']}_installer_v{PACKAGE_CONFIG['version']}.exe"
        if installer_path.exists():
            file_hash = calculate_file_hash(installer_path)
            log_message(f"Created Windows installer: {installer_path}")
            return [(installer_path, file_hash)]
    except subprocess.CalledProcessError:
        log_message("Failed to create Windows installer", "ERROR")
    
    return []


def create_linux_package():
    """Create Linux package (AppImage or DEB)."""
    log_message("Creating Linux package...")
    
    # For now, create a simple AppImage-style package
    package_dir = Path("packages")
    
    # Create AppDir structure
    app_name = PACKAGE_CONFIG['app_name']
    appdir_name = f"{app_name}.AppDir"
    appdir_path = package_dir / appdir_name
    
    if appdir_path.exists():
        shutil.rmtree(appdir_path)
    
    appdir_path.mkdir(parents=True)
    
    # Copy application
    shutil.copytree("dist", appdir_path / "usr" / "bin")
    
    # Create desktop file
    desktop_content = f"""[Desktop Entry]
Name={PACKAGE_CONFIG['app_name']}
Exec={PACKAGE_CONFIG['app_name']}
Icon={PACKAGE_CONFIG['app_name'].lower()}
Type=Application
Categories=Office;Finance;
Comment={PACKAGE_CONFIG['description']}
"""
    
    with open(appdir_path / f"{app_name}.desktop", "w") as f:
        f.write(desktop_content)
    
    # Create AppRun script
    apprun_content = f"""#!/bin/bash
HERE="$(dirname "$(readlink -f "${{0}}")")"
exec "$HERE/usr/bin/{PACKAGE_CONFIG['app_name']}" "$@"
"""
    
    apprun_path = appdir_path / "AppRun"
    with open(apprun_path, "w") as f:
        f.write(apprun_content)
    os.chmod(apprun_path, 0o755)
    
    # Create tar.gz package
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{app_name}_linux_v{PACKAGE_CONFIG['version']}_{timestamp}.tar.gz"
    archive_path = package_dir / archive_name
    
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(appdir_path, arcname=appdir_name)
    
    # Clean up
    shutil.rmtree(appdir_path)
    
    file_hash = calculate_file_hash(archive_path)
    log_message(f"Created Linux package: {archive_path}")
    return [(archive_path, file_hash)]


def create_macos_package():
    """Create macOS package (DMG or PKG)."""
    log_message("Creating macOS package...")
    
    # Create macOS app bundle structure
    package_dir = Path("packages")
    app_name = f"{PACKAGE_CONFIG['app_name']}.app"
    app_path = package_dir / app_name
    
    if app_path.exists():
        shutil.rmtree(app_path)
    
    # Create bundle directories
    contents_dir = app_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    for dir_path in [contents_dir, macos_dir, resources_dir]:
        dir_path.mkdir(parents=True)
    
    # Copy executable
    dist_dir = Path("dist")
    if dist_dir.exists():
        for item in dist_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, macos_dir)
            else:
                shutil.copytree(item, macos_dir / item.name)
    
    # Create Info.plist
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>{PACKAGE_CONFIG['app_name']}</string>
    <key>CFBundleDisplayName</key>
    <string>{PACKAGE_CONFIG['app_name']}</string>
    <key>CFBundleIdentifier</key>
    <string>com.expensetracker.{PACKAGE_CONFIG['app_name'].lower()}</string>
    <key>CFBundleVersion</key>
    <string>{PACKAGE_CONFIG['version']}</string>
    <key>CFBundleShortVersionString</key>
    <string>{PACKAGE_CONFIG['version']}</string>
    <key>CFBundleExecutable</key>
    <string>{PACKAGE_CONFIG['app_name']}</string>
    <key>CFBundleIconFile</key>
    <string>app.icns</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>"""
    
    with open(contents_dir / "Info.plist", "w") as f:
        f.write(plist_content)
    
    # Create DMG if hdiutil is available
    if shutil.which("hdiutil"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dmg_name = f"{PACKAGE_CONFIG['app_name']}_macos_v{PACKAGE_CONFIG['version']}_{timestamp}.dmg"
        dmg_path = package_dir / dmg_name
        
        try:
            subprocess.run([
                "hdiutil", "create", "-srcfolder", str(app_path),
                "-volname", PACKAGE_CONFIG['app_name'],
                str(dmg_path)
            ], check=True)
            
            file_hash = calculate_file_hash(dmg_path)
            log_message(f"Created macOS DMG: {dmg_path}")
            return [(dmg_path, file_hash)]
        except subprocess.CalledProcessError:
            log_message("Failed to create DMG", "ERROR")
    
    # Fallback: create zip
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"{PACKAGE_CONFIG['app_name']}_macos_v{PACKAGE_CONFIG['version']}_{timestamp}.zip"
    zip_path = package_dir / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in app_path.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)
    
    file_hash = calculate_file_hash(zip_path)
    log_message(f"Created macOS package: {zip_path}")
    return [(zip_path, file_hash)]


def create_package_manifest(packages: list):
    """Create manifest file with package information."""
    log_message("Creating package manifest...")
    
    manifest = {
        "app_info": PACKAGE_CONFIG,
        "build_info": {
            "build_date": datetime.now().isoformat(),
            "build_platform": sys.platform,
            "python_version": sys.version
        },
        "packages": []
    }
    
    for package_path, file_hash in packages:
        package_info = {
            "filename": package_path.name,
            "size_bytes": package_path.stat().st_size,
            "size_mb": round(package_path.stat().st_size / (1024 * 1024), 2),
            "sha256": file_hash,
            "created": datetime.fromtimestamp(package_path.stat().st_ctime).isoformat()
        }
        manifest["packages"].append(package_info)
    
    # Save manifest
    manifest_path = Path("packages") / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    log_message(f"Package manifest created: {manifest_path}")
    return manifest_path


def create_release_notes():
    """Create release notes file."""
    log_message("Creating release notes...")
    
    release_notes = f"""# {PACKAGE_CONFIG['app_name']} v{PACKAGE_CONFIG['version']} Release Notes

## Overview

This release includes various improvements and bug fixes for the expense tracking application.

## New Features

- Enhanced expense splitting algorithms
- Improved backup and restore functionality
- Better export options (Excel, PDF, CSV)
- Advanced configuration management
- Comprehensive validation framework

## System Requirements

- **Python**: {PACKAGE_CONFIG['python_requires']}
- **Operating Systems**: {', '.join(PACKAGE_CONFIG['platforms'])}
- **Memory**: Minimum 512MB RAM
- **Storage**: Minimum 100MB free space

## Dependencies

{chr(10).join('- ' + dep for dep in PACKAGE_CONFIG['dependencies'])}

## Installation

### Source Package
1. Extract the source archive
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`

### Binary Package
1. Extract the binary archive
2. Run the executable directly

### Portable Package
1. Extract the portable archive
2. Run the launcher script

## Known Issues

- None at this time

## Support

For support and bug reports, please visit: {PACKAGE_CONFIG['homepage']}

## License

This software is released under the {PACKAGE_CONFIG['license']} license.

---
Build Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    release_notes_path = Path("packages") / "RELEASE_NOTES.md"
    with open(release_notes_path, "w") as f:
        f.write(release_notes)
    
    log_message(f"Release notes created: {release_notes_path}")
    return release_notes_path


def validate_packages(packages: list):
    """Validate created packages."""
    log_message("Validating packages...")
    
    validation_results = []
    
    for package_path, expected_hash in packages:
        if not package_path.exists():
            validation_results.append((package_path.name, False, "File not found"))
            continue
        
        # Verify hash
        actual_hash = calculate_file_hash(package_path)
        if actual_hash != expected_hash:
            validation_results.append((package_path.name, False, "Hash mismatch"))
            continue
        
        # Check file size
        size_mb = package_path.stat().st_size / (1024 * 1024)
        if size_mb < 0.1:
            validation_results.append((package_path.name, False, "File too small"))
            continue
        
        validation_results.append((package_path.name, True, "Valid"))
    
    # Report results
    for filename, is_valid, message in validation_results:
        status = "✓" if is_valid else "✗"
        level = "INFO" if is_valid else "ERROR"
        log_message(f"{status} {filename}: {message}", level)
    
    return all(result[1] for result in validation_results)


def clean_temp_files():
    """Clean temporary files created during packaging."""
    log_message("Cleaning temporary files...")
    
    temp_patterns = [
        "*.nsi",
        "build/",
        "*.spec",
        "__pycache__/",
        "*.pyc"
    ]
    
    for pattern in temp_patterns:
        if '*' in pattern:
            import glob
            for file_path in glob.glob(pattern, recursive=True):
                try:
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                except OSError:
                    pass
        else:
            if os.path.exists(pattern):
                if os.path.isdir(pattern):
                    shutil.rmtree(pattern)
                else:
                    os.remove(pattern)


def main():
    """Main packaging function."""
    parser = argparse.ArgumentParser(description="Package expense tracking application")
    parser.add_argument("--source-only", action="store_true", help="Create only source packages")
    parser.add_argument("--binary-only", action="store_true", help="Create only binary packages")
    parser.add_argument("--portable-only", action="store_true", help="Create only portable packages")
    parser.add_argument("--installer-only", action="store_true", help="Create only installer packages")
    parser.add_argument("--no-validation", action="store_true", help="Skip package validation")
    parser.add_argument("--clean", action="store_true", help="Clean packages directory before creating")
    
    args = parser.parse_args()
    
    try:
        # Clean packages directory if requested
        if args.clean:
            packages_dir = Path("packages")
            if packages_dir.exists():
                shutil.rmtree(packages_dir)
                log_message("Cleaned packages directory")
        
        # Create packages directory
        Path("packages").mkdir(exist_ok=True)
        
        all_packages = []
        
        # Create packages based on arguments
        if args.source_only:
            all_packages.extend(create_source_package())
        elif args.binary_only:
            all_packages.extend(create_binary_package())
        elif args.portable_only:
            all_packages.extend(create_portable_package())
        elif args.installer_only:
            all_packages.extend(create_installer_package())
        else:
            # Create all package types
            all_packages.extend(create_source_package())
            all_packages.extend(create_binary_package())
            all_packages.extend(create_portable_package())
            all_packages.extend(create_installer_package())
        
        if not all_packages:
            log_message("No packages were created", "ERROR")
            return 1
        
        # Validate packages
        if not args.no_validation:
            if not validate_packages(all_packages):
                log_message("Package validation failed", "ERROR")
                return 1
        
        # Create manifest and documentation
        create_package_manifest(all_packages)
        create_release_notes()
        
        # Clean temporary files
        clean_temp_files()
        
        # Summary
        log_message(f"Successfully created {len(all_packages)} packages:", "SUCCESS")
        for package_path, _ in all_packages:
            size_mb = package_path.stat().st_size / (1024 * 1024)
            log_message(f"  {package_path.name} ({size_mb:.1f} MB)")
        
        return 0
        
    except KeyboardInterrupt:
        log_message("Packaging cancelled by user", "WARNING")
        return 1
    except Exception as e:
        log_message(f"Unexpected error: {e}", "ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())
