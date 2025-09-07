"""
Settings and configuration data models.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pathlib import Path


class Theme(Enum):
    """Available application themes."""
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"


class Language(Enum):
    """Supported languages."""
    PT_BR = "pt_BR"
    EN_US = "en_US"
    ES_ES = "es_ES"


class BackupFrequency(Enum):
    """Backup frequency options."""
    ON_SAVE = "on_save"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ExportFormat(Enum):
    """Export format options."""
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"
    JSON = "json"


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class UISettings:
    """
    User interface settings.
    
    Attributes:
        theme: Application theme
        language: Interface language
        font_family: Font family name
        font_size: Font size in points
        window_width: Window width in pixels
        window_height: Window height in pixels
        window_maximized: Whether window is maximized
        sidebar_width: Sidebar width in pixels
        show_tooltips: Whether to show tooltips
        animation_enabled: Whether to enable animations
        compact_mode: Whether to use compact interface
        show_grid_lines: Whether to show grid lines in tables
        row_height: Table row height in pixels
    """
    theme: Theme = Theme.DARK
    language: Language = Language.PT_BR
    font_family: str = "Segoe UI"
    font_size: int = 11
    window_width: int = 1400
    window_height: int = 900
    window_maximized: bool = False
    sidebar_width: int = 250
    show_tooltips: bool = True
    animation_enabled: bool = True
    compact_mode: bool = False
    show_grid_lines: bool = True
    row_height: int = 24
    
    def __post_init__(self):
        """Convert string enums."""
        if isinstance(self.theme, str):
            self.theme = Theme(self.theme)
        if isinstance(self.language, str):
            self.language = Language(self.language)
    
    def validate(self) -> List[str]:
        """Validate UI settings."""
        errors = []
        
        if self.font_size < 8 or self.font_size > 24:
            errors.append("Font size must be between 8 and 24")
        
        if self.window_width < 800:
            errors.append("Window width must be at least 800")
        
        if self.window_height < 600:
            errors.append("Window height must be at least 600")
        
        if self.sidebar_width < 100 or self.sidebar_width > 500:
            errors.append("Sidebar width must be between 100 and 500")
        
        if self.row_height < 16 or self.row_height > 50:
            errors.append("Row height must be between 16 and 50")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'theme': self.theme.value,
            'language': self.language.value,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'window_width': self.window_width,
            'window_height': self.window_height,
            'window_maximized': self.window_maximized,
            'sidebar_width': self.sidebar_width,
            'show_tooltips': self.show_tooltips,
            'animation_enabled': self.animation_enabled,
            'compact_mode': self.compact_mode,
            'show_grid_lines': self.show_grid_lines,
            'row_height': self.row_height
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UISettings':
        """Create from dictionary."""
        obj = cls()
        obj.theme = Theme(data.get('theme', 'dark'))
        obj.language = Language(data.get('language', 'pt_BR'))
        obj.font_family = data.get('font_family', 'Segoe UI')
        obj.font_size = data.get('font_size', 11)
        obj.window_width = data.get('window_width', 1400)
        obj.window_height = data.get('window_height', 900)
        obj.window_maximized = data.get('window_maximized', False)
        obj.sidebar_width = data.get('sidebar_width', 250)
        obj.show_tooltips = data.get('show_tooltips', True)
        obj.animation_enabled = data.get('animation_enabled', True)
        obj.compact_mode = data.get('compact_mode', False)
        obj.show_grid_lines = data.get('show_grid_lines', True)
        obj.row_height = data.get('row_height', 24)
        return obj


@dataclass
class BackupSettings:
    """
    Backup and restore settings.
    
    Attributes:
        auto_backup_enabled: Whether auto backup is enabled
        backup_frequency: How often to backup
        max_backups: Maximum number of backups to keep
        backup_location: Directory to store backups
        compress_backups: Whether to compress backup files
        verify_backups: Whether to verify backup integrity
        backup_on_exit: Whether to backup when closing app
        cloud_backup_enabled: Whether cloud backup is enabled
        cloud_provider: Cloud storage provider
        cloud_credentials: Cloud storage credentials
    """
    auto_backup_enabled: bool = True
    backup_frequency: BackupFrequency = BackupFrequency.DAILY
    max_backups: int = 10
    backup_location: str = "data/backups"
    compress_backups: bool = True
    verify_backups: bool = True
    backup_on_exit: bool = True
    cloud_backup_enabled: bool = False
    cloud_provider: str = ""
    cloud_credentials: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Convert string enums."""
        if isinstance(self.backup_frequency, str):
            self.backup_frequency = BackupFrequency(self.backup_frequency)
    
    def validate(self) -> List[str]:
        """Validate backup settings."""
        errors = []
        
        if self.max_backups < 1:
            errors.append("Maximum backups must be at least 1")
        
        if self.max_backups > 100:
            errors.append("Maximum backups cannot exceed 100")
        
        try:
            Path(self.backup_location)
        except Exception:
            errors.append("Invalid backup location path")
        
        if self.cloud_backup_enabled and not self.cloud_provider:
            errors.append("Cloud provider must be specified when cloud backup is enabled")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'auto_backup_enabled': self.auto_backup_enabled,
            'backup_frequency': self.backup_frequency.value,
            'max_backups': self.max_backups,
            'backup_location': self.backup_location,
            'compress_backups': self.compress_backups,
            'verify_backups': self.verify_backups,
            'backup_on_exit': self.backup_on_exit,
            'cloud_backup_enabled': self.cloud_backup_enabled,
            'cloud_provider': self.cloud_provider,
            'cloud_credentials': self.cloud_credentials
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupSettings':
        """Create from dictionary."""
        obj = cls()
        obj.auto_backup_enabled = data.get('auto_backup_enabled', True)
        obj.backup_frequency = BackupFrequency(data.get('backup_frequency', 'daily'))
        obj.max_backups = data.get('max_backups', 10)
        obj.backup_location = data.get('backup_location', 'data/backups')
        obj.compress_backups = data.get('compress_backups', True)
        obj.verify_backups = data.get('verify_backups', True)
        obj.backup_on_exit = data.get('backup_on_exit', True)
        obj.cloud_backup_enabled = data.get('cloud_backup_enabled', False)
        obj.cloud_provider = data.get('cloud_provider', '')
        obj.cloud_credentials = data.get('cloud_credentials', {})
        return obj


@dataclass
class ExportSettings:
    """
    Export and reporting settings.
    
    Attributes:
        default_format: Default export format
        default_location: Default export directory
        include_charts: Whether to include charts in exports
        include_summary: Whether to include summary in exports
        date_format: Date format for exports
        currency_format: Currency format for exports
        decimal_places: Number of decimal places
        auto_open_exports: Whether to auto-open exported files
        watermark_enabled: Whether to add watermark
        watermark_text: Watermark text
        template_path: Path to custom export template
    """
    default_format: ExportFormat = ExportFormat.XLSX
    default_location: str = "exports"
    include_charts: bool = True
    include_summary: bool = True
    date_format: str = "dd/MM/yyyy"
    currency_format: str = "R$ #,##0.00"
    decimal_places: int = 2
    auto_open_exports: bool = True
    watermark_enabled: bool = False
    watermark_text: str = ""
    template_path: str = ""
    
    def __post_init__(self):
        """Convert string enums."""
        if isinstance(self.default_format, str):
            self.default_format = ExportFormat(self.default_format)
    
    def validate(self) -> List[str]:
        """Validate export settings."""
        errors = []
        
        if self.decimal_places < 0 or self.decimal_places > 4:
            errors.append("Decimal places must be between 0 and 4")
        
        try:
            Path(self.default_location)
        except Exception:
            errors.append("Invalid export location path")
        
        if self.template_path and not Path(self.template_path).exists():
            errors.append("Template file does not exist")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'default_format': self.default_format.value,
            'default_location': self.default_location,
            'include_charts': self.include_charts,
            'include_summary': self.include_summary,
            'date_format': self.date_format,
            'currency_format': self.currency_format,
            'decimal_places': self.decimal_places,
            'auto_open_exports': self.auto_open_exports,
            'watermark_enabled': self.watermark_enabled,
            'watermark_text': self.watermark_text,
            'template_path': self.template_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportSettings':
        """Create from dictionary."""
        obj = cls()
        obj.default_format = ExportFormat(data.get('default_format', 'xlsx'))
        obj.default_location = data.get('default_location', 'exports')
        obj.include_charts = data.get('include_charts', True)
        obj.include_summary = data.get('include_summary', True)
        obj.date_format = data.get('date_format', 'dd/MM/yyyy')
        obj.currency_format = data.get('currency_format', 'R$ #,##0.00')
        obj.decimal_places = data.get('decimal_places', 2)
        obj.auto_open_exports = data.get('auto_open_exports', True)
        obj.watermark_enabled = data.get('watermark_enabled', False)
        obj.watermark_text = data.get('watermark_text', '')
        obj.template_path = data.get('template_path', '')
        return obj


@dataclass
class NotificationSettings:
    """
    Notification settings.
    
    Attributes:
        enabled: Whether notifications are enabled
        show_system_notifications: Whether to show system notifications
        play_sound: Whether to play notification sounds
        sound_file: Path to custom sound file
        duration: Notification duration in milliseconds
        position: Notification position on screen
        remind_overdue: Whether to remind about overdue expenses
        remind_backup: Whether to remind about backups
        remind_reports: Whether to remind about monthly reports
    """
    enabled: bool = True
    show_system_notifications: bool = True
    play_sound: bool = False
    sound_file: str = ""
    duration: int = 5000
    position: str = "bottom_right"
    remind_overdue: bool = True
    remind_backup: bool = True
    remind_reports: bool = True
    
    def validate(self) -> List[str]:
        """Validate notification settings."""
        errors = []
        
        if self.duration < 1000 or self.duration > 30000:
            errors.append("Duration must be between 1000 and 30000 milliseconds")
        
        valid_positions = ["top_left", "top_right", "bottom_left", "bottom_right", "center"]
        if self.position not in valid_positions:
            errors.append(f"Position must be one of: {', '.join(valid_positions)}")
        
        if self.sound_file and not Path(self.sound_file).exists():
            errors.append("Sound file does not exist")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enabled': self.enabled,
            'show_system_notifications': self.show_system_notifications,
            'play_sound': self.play_sound,
            'sound_file': self.sound_file,
            'duration': self.duration,
            'position': self.position,
            'remind_overdue': self.remind_overdue,
            'remind_backup': self.remind_backup,
            'remind_reports': self.remind_reports
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationSettings':
        """Create from dictionary."""
        obj = cls()
        obj.enabled = data.get('enabled', True)
        obj.show_system_notifications = data.get('show_system_notifications', True)
        obj.play_sound = data.get('play_sound', False)
        obj.sound_file = data.get('sound_file', '')
        obj.duration = data.get('duration', 5000)
        obj.position = data.get('position', 'bottom_right')
        obj.remind_overdue = data.get('remind_overdue', True)
        obj.remind_backup = data.get('remind_backup', True)
        obj.remind_reports = data.get('remind_reports', True)
        return obj


@dataclass
class CalculationSettings:
    """
    Calculation and business logic settings.
    
    Attributes:
        auto_calculate: Whether to calculate automatically
        calculation_delay: Delay before auto-calculation in milliseconds
        default_casa2_percentage: Default percentage for Casa 2
        currency_symbol: Currency symbol
        rounding_mode: Decimal rounding mode
        validate_on_input: Whether to validate while typing
        strict_validation: Whether to use strict validation
        allow_negative_balances: Whether to allow negative balances
    """
    auto_calculate: bool = True
    calculation_delay: int = 500
    default_casa2_percentage: float = 67.0
    currency_symbol: str = "R$"
    rounding_mode: str = "ROUND_HALF_UP"
    validate_on_input: bool = True
    strict_validation: bool = False
    allow_negative_balances: bool = True
    
    def validate(self) -> List[str]:
        """Validate calculation settings."""
        errors = []
        
        if self.calculation_delay < 100 or self.calculation_delay > 5000:
            errors.append("Calculation delay must be between 100 and 5000 milliseconds")
        
        if not 0 <= self.default_casa2_percentage <= 100:
            errors.append("Default Casa 2 percentage must be between 0 and 100")
        
        valid_rounding = ["ROUND_HALF_UP", "ROUND_HALF_DOWN", "ROUND_UP", "ROUND_DOWN", "ROUND_CEILING", "ROUND_FLOOR"]
        if self.rounding_mode not in valid_rounding:
            errors.append(f"Rounding mode must be one of: {', '.join(valid_rounding)}")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'auto_calculate': self.auto_calculate,
            'calculation_delay': self.calculation_delay,
            'default_casa2_percentage': self.default_casa2_percentage,
            'currency_symbol': self.currency_symbol,
            'rounding_mode': self.rounding_mode,
            'validate_on_input': self.validate_on_input,
            'strict_validation': self.strict_validation,
            'allow_negative_balances': self.allow_negative_balances
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationSettings':
        """Create from dictionary."""
        obj = cls()
        obj.auto_calculate = data.get('auto_calculate', True)
        obj.calculation_delay = data.get('calculation_delay', 500)
        obj.default_casa2_percentage = data.get('default_casa2_percentage', 67.0)
        obj.currency_symbol = data.get('currency_symbol', 'R$')
        obj.rounding_mode = data.get('rounding_mode', 'ROUND_HALF_UP')
        obj.validate_on_input = data.get('validate_on_input', True)
        obj.strict_validation = data.get('strict_validation', False)
        obj.allow_negative_balances = data.get('allow_negative_balances', True)
        return obj


@dataclass
class AdvancedSettings:
    """
    Advanced system settings.
    
    Attributes:
        debug_mode: Whether debug mode is enabled
        log_level: Logging level
        log_file: Path to log file
        cache_enabled: Whether caching is enabled
        cache_size_mb: Cache size limit in MB
        auto_save: Whether auto-save is enabled
        auto_save_interval: Auto-save interval in seconds
        check_updates: Whether to check for updates
        send_analytics: Whether to send usage analytics
        developer_mode: Whether developer mode is enabled
    """
    debug_mode: bool = False
    log_level: LogLevel = LogLevel.INFO
    log_file: str = "data/app.log"
    cache_enabled: bool = True
    cache_size_mb: int = 50
    auto_save: bool = True
    auto_save_interval: int = 60
    check_updates: bool = True
    send_analytics: bool = False
    developer_mode: bool = False
    
    def __post_init__(self):
        """Convert string enums."""
        if isinstance(self.log_level, str):
            self.log_level = LogLevel(self.log_level)
    
    def validate(self) -> List[str]:
        """Validate advanced settings."""
        errors = []
        
        if self.cache_size_mb < 10 or self.cache_size_mb > 1000:
            errors.append("Cache size must be between 10 and 1000 MB")
        
        if self.auto_save_interval < 10 or self.auto_save_interval > 3600:
            errors.append("Auto-save interval must be between 10 and 3600 seconds")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'debug_mode': self.debug_mode,
            'log_level': self.log_level.value,
            'log_file': self.log_file,
            'cache_enabled': self.cache_enabled,
            'cache_size_mb': self.cache_size_mb,
            'auto_save': self.auto_save,
            'auto_save_interval': self.auto_save_interval,
            'check_updates': self.check_updates,
            'send_analytics': self.send_analytics,
            'developer_mode': self.developer_mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdvancedSettings':
        """Create from dictionary."""
        obj = cls()
        obj.debug_mode = data.get('debug_mode', False)
        obj.log_level = LogLevel(data.get('log_level', 'INFO'))
        obj.log_file = data.get('log_file', 'data/app.log')
        obj.cache_enabled = data.get('cache_enabled', True)
        obj.cache_size_mb = data.get('cache_size_mb', 50)
        obj.auto_save = data.get('auto_save', True)
        obj.auto_save_interval = data.get('auto_save_interval', 60)
        obj.check_updates = data.get('check_updates', True)
        obj.send_analytics = data.get('send_analytics', False)
        obj.developer_mode = data.get('developer_mode', False)
        return obj


@dataclass
class AppSettings:
    """
    Complete application settings.
    
    Attributes:
        version: Settings version
        ui: UI settings
        backup: Backup settings
        export: Export settings
        notifications: Notification settings
        calculation: Calculation settings
        advanced: Advanced settings
        created_at: When settings were created
        modified_at: When settings were last modified
    """
    version: str = "2.0"
    ui: UISettings = field(default_factory=UISettings)
    backup: BackupSettings = field(default_factory=BackupSettings)
    export: ExportSettings = field(default_factory=ExportSettings)
    notifications: NotificationSettings = field(default_factory=NotificationSettings)
    calculation: CalculationSettings = field(default_factory=CalculationSettings)
    advanced: AdvancedSettings = field(default_factory=AdvancedSettings)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Initialize nested objects if they are dicts."""
        if isinstance(self.ui, dict):
            self.ui = UISettings.from_dict(self.ui)
        
        if isinstance(self.backup, dict):
            self.backup = BackupSettings.from_dict(self.backup)
        
        if isinstance(self.export, dict):
            self.export = ExportSettings.from_dict(self.export)
        
        if isinstance(self.notifications, dict):
            self.notifications = NotificationSettings.from_dict(self.notifications)
        
        if isinstance(self.calculation, dict):
            self.calculation = CalculationSettings.from_dict(self.calculation)
        
        if isinstance(self.advanced, dict):
            self.advanced = AdvancedSettings.from_dict(self.advanced)
    
    def validate(self) -> List[str]:
        """Validate all settings."""
        errors = []
        
        errors.extend(self.ui.validate())
        errors.extend(self.backup.validate())
        errors.extend(self.export.validate())
        errors.extend(self.notifications.validate())
        errors.extend(self.calculation.validate())
        errors.extend(self.advanced.validate())
        
        return errors
    
    def update_modified_time(self):
        """Update modification timestamp."""
        self.modified_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'version': self.version,
            'ui': self.ui.to_dict(),
            'backup': self.backup.to_dict(),
            'export': self.export.to_dict(),
            'notifications': self.notifications.to_dict(),
            'calculation': self.calculation.to_dict(),
            'advanced': self.advanced.to_dict(),
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create from dictionary."""
        obj = cls()
        obj.version = data.get('version', '2.0')
        
        if 'ui' in data:
            obj.ui = UISettings.from_dict(data['ui'])
        
        if 'backup' in data:
            obj.backup = BackupSettings.from_dict(data['backup'])
        
        if 'export' in data:
            obj.export = ExportSettings.from_dict(data['export'])
        
        if 'notifications' in data:
            obj.notifications = NotificationSettings.from_dict(data['notifications'])
        
        if 'calculation' in data:
            obj.calculation = CalculationSettings.from_dict(data['calculation'])
        
        if 'advanced' in data:
            obj.advanced = AdvancedSettings.from_dict(data['advanced'])
        
        if 'created_at' in data:
            obj.created_at = datetime.fromisoformat(data['created_at'])
        
        if 'modified_at' in data:
            obj.modified_at = datetime.fromisoformat(data['modified_at'])
        
        return obj