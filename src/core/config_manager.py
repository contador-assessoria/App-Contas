"""
Configuration management for expense tracking system.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import logging
import threading
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """Application configuration data class."""
    
    # General settings
    theme: str = "dark"
    language: str = "pt_BR"
    auto_save: bool = True
    auto_save_interval: int = 60  # seconds
    calculate_on_type: bool = True
    
    # Display settings
    currency_symbol: str = "R$"
    decimal_places: int = 2
    date_format: str = "dd/MM/yyyy"
    number_format: str = "1.234,56"
    
    # Default values
    default_casa2_percentage: float = 67.0
    default_backup_count: int = 10
    
    # UI settings
    window_width: int = 1400
    window_height: int = 900
    window_maximized: bool = False
    sidebar_width: int = 250
    
    # Notifications
    show_notifications: bool = True
    sound_notifications: bool = False
    notification_duration: int = 5000  # milliseconds
    
    # Backup settings
    auto_backup: bool = True
    backup_location: str = "data/backups"
    backup_frequency: str = "daily"  # daily, weekly, monthly
    max_backups: int = 10
    compress_backups: bool = True
    
    # Export settings
    default_export_format: str = "xlsx"
    export_location: str = "exports"
    include_charts: bool = True
    
    # Advanced settings
    debug_mode: bool = False
    log_level: str = "INFO"
    max_undo_steps: int = 20
    
    # Performance settings
    cache_enabled: bool = True
    cache_size_mb: int = 50
    lazy_loading: bool = True


class ConfigManager:
    """
    Thread-safe configuration manager for the expense tracking system.
    Handles loading, saving, and validation of application settings.
    """
    
    def __init__(self, config_file: str = "data/settings.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self.config_dir = self.config_file.parent
        self._config = AppConfig()
        self._lock = threading.RLock()
        self._dirty = False
        self._observers = []
        
        self._ensure_config_directory()
        self._load_config()
        
        # Setup auto-save if enabled
        self._auto_save_timer = None
        if self._config.auto_save:
            self._start_auto_save()
    
    def _ensure_config_directory(self):
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self):
        """Load configuration from file."""
        with self._lock:
            if self.config_file.exists():
                try:
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    
                    # Validate and merge with defaults
                    self._config = self._merge_config(config_data)
                    logger.info(f"Configuration loaded from {self.config_file}")
                    
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.error(f"Failed to load configuration: {e}")
                    self._config = AppConfig()
                    self._save_config()  # Save defaults
                except Exception as e:
                    logger.error(f"Unexpected error loading configuration: {e}")
                    self._config = AppConfig()
            else:
                logger.info("No configuration file found, using defaults")
                self._config = AppConfig()
                self._save_config()  # Create initial config file
    
    def _merge_config(self, config_data: Dict) -> AppConfig:
        """Merge loaded configuration with defaults."""
        defaults = asdict(AppConfig())
        
        # Update defaults with loaded values
        for key, value in config_data.items():
            if key in defaults:
                # Validate type
                expected_type = type(defaults[key])
                if isinstance(value, expected_type):
                    defaults[key] = value
                else:
                    logger.warning(f"Invalid type for config key {key}: expected {expected_type}, got {type(value)}")
            else:
                logger.warning(f"Unknown configuration key: {key}")
        
        return AppConfig(**defaults)
    
    def _save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            config_data = asdict(self._config)
            config_data['_metadata'] = {
                'saved_at': datetime.now().isoformat(),
                'version': '2.0'
            }
            
            # Write to temporary file first
            temp_file = self.config_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Atomic replace
            temp_file.replace(self.config_file)
            
            self._dirty = False
            logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            # Clean up temp file if it exists
            temp_file = self.config_file.with_suffix('.tmp')
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        with self._lock:
            return getattr(self._config, key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            True if set successfully
        """
        with self._lock:
            if not hasattr(self._config, key):
                logger.warning(f"Unknown configuration key: {key}")
                return False
            
            # Validate type
            current_value = getattr(self._config, key)
            expected_type = type(current_value)
            
            if not isinstance(value, expected_type):
                logger.warning(f"Invalid type for {key}: expected {expected_type}, got {type(value)}")
                return False
            
            # Set value
            setattr(self._config, key, value)
            self._dirty = True
            
            # Notify observers
            self._notify_observers(key, value)
            
            logger.debug(f"Configuration updated: {key} = {value}")
            return True
    
    def update(self, config_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Update multiple configuration values.
        
        Args:
            config_dict: Dictionary of configuration updates
            
        Returns:
            Tuple of (success, list of errors)
        """
        errors = []
        
        with self._lock:
            for key, value in config_dict.items():
                if not self.set(key, value):
                    errors.append(f"Failed to set {key}")
        
        return len(errors) == 0, errors
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values as dictionary."""
        with self._lock:
            return asdict(self._config)
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to default values."""
        with self._lock:
            try:
                self._config = AppConfig()
                self._dirty = True
                self._save_config()
                
                # Notify all observers
                for key in asdict(self._config).keys():
                    self._notify_observers(key, getattr(self._config, key))
                
                logger.info("Configuration reset to defaults")
                return True
                
            except Exception as e:
                logger.error(f"Failed to reset configuration: {e}")
                return False
    
    def save(self) -> bool:
        """Manually save configuration."""
        with self._lock:
            return self._save_config()
    
    def is_dirty(self) -> bool:
        """Check if configuration has unsaved changes."""
        with self._lock:
            return self._dirty
    
    def add_observer(self, callback):
        """
        Add configuration change observer.
        
        Args:
            callback: Function to call when configuration changes (key, value)
        """
        with self._lock:
            self._observers.append(callback)
    
    def remove_observer(self, callback):
        """Remove configuration change observer."""
        with self._lock:
            if callback in self._observers:
                self._observers.remove(callback)
    
    def _notify_observers(self, key: str, value: Any):
        """Notify observers of configuration change."""
        for observer in self._observers:
            try:
                observer(key, value)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
    
    def _start_auto_save(self):
        """Start auto-save timer."""
        import threading
        
        def auto_save_worker():
            if self._dirty:
                self._save_config()
        
        if self._auto_save_timer:
            self._auto_save_timer.cancel()
        
        self._auto_save_timer = threading.Timer(
            self._config.auto_save_interval,
            auto_save_worker
        )
        self._auto_save_timer.daemon = True
        self._auto_save_timer.start()
    
    def export_config(self, output_file: Path) -> bool:
        """
        Export configuration to file.
        
        Args:
            output_file: File to export to
            
        Returns:
            True if successful
        """
        try:
            config_data = self.get_all()
            config_data['_export_metadata'] = {
                'exported_at': datetime.now().isoformat(),
                'version': '2.0',
                'exported_by': 'ExpenseTracker'
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, input_file: Path, merge: bool = True) -> Tuple[bool, List[str]]:
        """
        Import configuration from file.
        
        Args:
            input_file: File to import from
            merge: Whether to merge with existing config or replace
            
        Returns:
            Tuple of (success, list of errors/warnings)
        """
        messages = []
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Remove metadata
            import_data.pop('_metadata', None)
            import_data.pop('_export_metadata', None)
            
            if merge:
                # Merge with existing configuration
                success, errors = self.update(import_data)
                messages.extend(errors)
            else:
                # Replace configuration
                self.reset_to_defaults()
                success, errors = self.update(import_data)
                messages.extend(errors)
            
            if success and not errors:
                messages.append("Configuration imported successfully")
                logger.info(f"Configuration imported from {input_file}")
            
            return success, messages
            
        except Exception as e:
            error_msg = f"Failed to import configuration: {e}"
            logger.error(error_msg)
            return False, [error_msg]
    
    def validate_config(self) -> Tuple[bool, List[str]]:
        """
        Validate current configuration.
        
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []
        
        with self._lock:
            # Validate theme
            if self._config.theme not in ["dark", "light", "auto"]:
                errors.append(f"Invalid theme: {self._config.theme}")
            
            # Validate language
            valid_languages = ["pt_BR", "en_US", "es_ES"]
            if self._config.language not in valid_languages:
                errors.append(f"Invalid language: {self._config.language}")
            
            # Validate auto_save_interval
            if self._config.auto_save_interval < 10:
                errors.append("Auto-save interval too short (minimum 10 seconds)")
            
            # Validate decimal_places
            if not 0 <= self._config.decimal_places <= 4:
                errors.append("Decimal places must be between 0 and 4")
            
            # Validate casa2_percentage
            if not 0 <= self._config.default_casa2_percentage <= 100:
                errors.append("Casa 2 percentage must be between 0 and 100")
            
            # Validate window dimensions
            if self._config.window_width < 800:
                errors.append("Window width too small (minimum 800)")
            if self._config.window_height < 600:
                errors.append("Window height too small (minimum 600)")
            
            # Validate backup settings
            if self._config.max_backups < 1:
                errors.append("Maximum backups must be at least 1")
            
            # Validate paths
            try:
                Path(self._config.backup_location)
                Path(self._config.export_location)
            except Exception:
                errors.append("Invalid path in configuration")
        
        return len(errors) == 0, errors
    
    def get_config_schema(self) -> Dict:
        """Get configuration schema with descriptions and constraints."""
        return {
            "theme": {
                "type": "string",
                "description": "Application theme",
                "values": ["dark", "light", "auto"],
                "default": "dark"
            },
            "language": {
                "type": "string", 
                "description": "Application language",
                "values": ["pt_BR", "en_US", "es_ES"],
                "default": "pt_BR"
            },
            "auto_save": {
                "type": "boolean",
                "description": "Enable automatic saving",
                "default": True
            },
            "auto_save_interval": {
                "type": "integer",
                "description": "Auto-save interval in seconds",
                "min": 10,
                "max": 3600,
                "default": 60
            },
            "currency_symbol": {
                "type": "string",
                "description": "Currency symbol",
                "default": "R$"
            },
            "decimal_places": {
                "type": "integer",
                "description": "Number of decimal places",
                "min": 0,
                "max": 4,
                "default": 2
            },
            "default_casa2_percentage": {
                "type": "float",
                "description": "Default percentage for Casa 2",
                "min": 0.0,
                "max": 100.0,
                "default": 67.0
            },
            "window_width": {
                "type": "integer",
                "description": "Application window width",
                "min": 800,
                "max": 4000,
                "default": 1400
            },
            "window_height": {
                "type": "integer",
                "description": "Application window height", 
                "min": 600,
                "max": 3000,
                "default": 900
            },
            "max_backups": {
                "type": "integer",
                "description": "Maximum number of backups to keep",
                "min": 1,
                "max": 100,
                "default": 10
            }
        }
    
    def close(self):
        """Close configuration manager and save any pending changes."""
        with self._lock:
            if self._auto_save_timer:
                self._auto_save_timer.cancel()
            
            if self._dirty:
                self._save_config()
            
            logger.info("Configuration manager closed")


# Global configuration instance
_config_manager = None


def get_config_manager(config_file: str = "data/settings.json") -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """Convenience function to get configuration value."""
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any) -> bool:
    """Convenience function to set configuration value."""
    return get_config_manager().set(key, value)


def save_config() -> bool:
    """Convenience function to save configuration."""
    return get_config_manager().save()