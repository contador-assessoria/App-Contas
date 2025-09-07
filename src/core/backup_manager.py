"""
Backup and restore functionality for expense data.
"""

import json
import shutil
import gzip
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
import hashlib
import threading

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Manages backup creation, rotation, and restoration for expense data.
    """
    
    def __init__(
        self, 
        backup_dir: str = "data/backups",
        max_backups: int = 10,
        compress: bool = True
    ):
        """
        Initialize backup manager.
        
        Args:
            backup_dir: Directory to store backups
            max_backups: Maximum number of backups to keep
            compress: Whether to compress backups
        """
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.compress = compress
        self._lock = threading.Lock()
        
        self._ensure_backup_directory()
    
    def _ensure_backup_directory(self):
        """Ensure backup directory exists."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(
        self, 
        source_file: Path, 
        backup_type: str = "manual",
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Create a backup of the source file.
        
        Args:
            source_file: File to backup
            backup_type: Type of backup (manual, auto, scheduled)
            metadata: Additional metadata to include
            
        Returns:
            Tuple of (success, backup_file_path or error_message)
        """
        with self._lock:
            try:
                if not source_file.exists():
                    return False, f"Source file does not exist: {source_file}"
                
                # Generate backup filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{backup_type}_{timestamp}"
                
                if self.compress:
                    backup_file = self.backup_dir / f"{backup_name}.json.gz"
                else:
                    backup_file = self.backup_dir / f"{backup_name}.json"
                
                # Read source data
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Add backup metadata
                backup_data = {
                    'metadata': {
                        'created_at': datetime.now().isoformat(),
                        'source_file': str(source_file),
                        'backup_type': backup_type,
                        'version': '2.0',
                        'checksum': self._calculate_checksum(data),
                        **(metadata or {})
                    },
                    'data': data
                }
                
                # Write backup
                if self.compress:
                    with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
                        json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
                else:
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
                
                logger.info(f"Backup created: {backup_file}")
                
                # Cleanup old backups
                self._cleanup_old_backups()
                
                return True, str(backup_file)
                
            except Exception as e:
                error_msg = f"Failed to create backup: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
    
    def restore_backup(
        self, 
        backup_file: Path, 
        target_file: Path,
        verify_checksum: bool = True
    ) -> Tuple[bool, str]:
        """
        Restore data from backup file.
        
        Args:
            backup_file: Backup file to restore from
            target_file: Target file to restore to
            verify_checksum: Whether to verify data integrity
            
        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            try:
                if not backup_file.exists():
                    return False, f"Backup file does not exist: {backup_file}"
                
                # Read backup data
                if backup_file.suffix == '.gz':
                    with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                        backup_data = json.load(f)
                else:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                
                # Validate backup structure
                if 'data' not in backup_data:
                    return False, "Invalid backup file format: missing data section"
                
                data = backup_data['data']
                metadata = backup_data.get('metadata', {})
                
                # Verify checksum if requested
                if verify_checksum and 'checksum' in metadata:
                    calculated_checksum = self._calculate_checksum(data)
                    stored_checksum = metadata['checksum']
                    
                    if calculated_checksum != stored_checksum:
                        return False, f"Checksum verification failed. Data may be corrupted."
                
                # Create backup of current file before restoration
                if target_file.exists():
                    current_backup_name = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    current_backup_path = self.backup_dir / current_backup_name
                    shutil.copy2(target_file, current_backup_path)
                    logger.info(f"Created pre-restore backup: {current_backup_path}")
                
                # Write restored data
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
                success_msg = f"Successfully restored from backup: {backup_file}"
                logger.info(success_msg)
                return True, success_msg
                
            except Exception as e:
                error_msg = f"Failed to restore backup: {str(e)}"
                logger.error(error_msg)
                return False, error_msg
    
    def list_backups(self) -> List[Dict]:
        """
        List all available backups with metadata.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        
        try:
            backup_files = sorted(
                self.backup_dir.glob("backup_*.json*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            for backup_file in backup_files:
                try:
                    # Read metadata
                    if backup_file.suffix == '.gz':
                        with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                            backup_data = json.load(f)
                    else:
                        with open(backup_file, 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)
                    
                    metadata = backup_data.get('metadata', {})
                    file_stats = backup_file.stat()
                    
                    backup_info = {
                        'filename': backup_file.name,
                        'filepath': str(backup_file),
                        'size_bytes': file_stats.st_size,
                        'size_mb': file_stats.st_size / (1024 * 1024),
                        'created_at': metadata.get('created_at', 'Unknown'),
                        'backup_type': metadata.get('backup_type', 'Unknown'),
                        'source_file': metadata.get('source_file', 'Unknown'),
                        'version': metadata.get('version', 'Unknown'),
                        'compressed': backup_file.suffix == '.gz',
                        'has_checksum': 'checksum' in metadata
                    }
                    
                    backups.append(backup_info)
                    
                except Exception as e:
                    logger.warning(f"Failed to read backup metadata from {backup_file}: {e}")
                    # Add basic info even if metadata reading fails
                    file_stats = backup_file.stat()
                    backups.append({
                        'filename': backup_file.name,
                        'filepath': str(backup_file),
                        'size_bytes': file_stats.st_size,
                        'size_mb': file_stats.st_size / (1024 * 1024),
                        'created_at': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                        'backup_type': 'Unknown',
                        'source_file': 'Unknown',
                        'version': 'Unknown',
                        'compressed': backup_file.suffix == '.gz',
                        'has_checksum': False,
                        'error': str(e)
                    })
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def verify_backup(self, backup_file: Path) -> Tuple[bool, Dict]:
        """
        Verify backup integrity and return analysis.
        
        Args:
            backup_file: Backup file to verify
            
        Returns:
            Tuple of (is_valid, verification_report)
        """
        try:
            # Read backup
            if backup_file.suffix == '.gz':
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    backup_data = json.load(f)
            else:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            
            report = {
                'filename': backup_file.name,
                'file_size': backup_file.stat().st_size,
                'structure_valid': False,
                'checksum_valid': False,
                'data_analysis': {},
                'errors': []
            }
            
            # Check structure
            if 'data' in backup_data and 'metadata' in backup_data:
                report['structure_valid'] = True
            else:
                report['errors'].append("Invalid backup structure")
            
            # Verify checksum
            if report['structure_valid']:
                metadata = backup_data['metadata']
                data = backup_data['data']
                
                if 'checksum' in metadata:
                    calculated_checksum = self._calculate_checksum(data)
                    stored_checksum = metadata['checksum']
                    report['checksum_valid'] = calculated_checksum == stored_checksum
                    
                    if not report['checksum_valid']:
                        report['errors'].append("Checksum verification failed")
                else:
                    report['errors'].append("No checksum available for verification")
                
                # Analyze data
                report['data_analysis'] = self._analyze_backup_data(data)
            
            is_valid = report['structure_valid'] and (
                report['checksum_valid'] or 'No checksum available' in str(report['errors'])
            )
            
            return is_valid, report
            
        except Exception as e:
            return False, {
                'filename': backup_file.name,
                'errors': [f"Failed to verify backup: {str(e)}"]
            }
    
    def _analyze_backup_data(self, data: Dict) -> Dict:
        """Analyze backup data structure and content."""
        analysis = {
            'total_years': 0,
            'total_months': 0,
            'year_range': [],
            'data_completeness': 'unknown'
        }
        
        try:
            if isinstance(data, dict):
                years = [int(year) for year in data.keys() if str(year).isdigit()]
                analysis['total_years'] = len(years)
                
                if years:
                    analysis['year_range'] = [min(years), max(years)]
                
                total_months = 0
                for year_data in data.values():
                    if isinstance(year_data, dict):
                        total_months += len(year_data)
                
                analysis['total_months'] = total_months
                
                # Determine data completeness
                if total_months == 0:
                    analysis['data_completeness'] = 'empty'
                elif total_months < 12:
                    analysis['data_completeness'] = 'partial'
                else:
                    analysis['data_completeness'] = 'complete'
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _cleanup_old_backups(self):
        """Remove old backups to maintain max_backups limit."""
        try:
            backup_files = sorted(
                self.backup_dir.glob("backup_*.json*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if len(backup_files) > self.max_backups:
                files_to_remove = backup_files[self.max_backups:]
                
                for file_to_remove in files_to_remove:
                    file_to_remove.unlink()
                    logger.info(f"Removed old backup: {file_to_remove}")
        
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
    
    def _calculate_checksum(self, data: Dict) -> str:
        """Calculate SHA256 checksum of data."""
        # Convert to consistent JSON string for hashing
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def create_scheduled_backup(
        self, 
        source_file: Path,
        schedule_type: str = "daily"
    ) -> Tuple[bool, str]:
        """
        Create a scheduled backup with appropriate metadata.
        
        Args:
            source_file: File to backup
            schedule_type: Type of schedule (daily, weekly, monthly)
            
        Returns:
            Tuple of (success, message)
        """
        metadata = {
            'schedule_type': schedule_type,
            'auto_created': True
        }
        
        return self.create_backup(source_file, "scheduled", metadata)
    
    def get_backup_statistics(self) -> Dict:
        """Get statistics about backup storage and health."""
        try:
            backups = self.list_backups()
            
            if not backups:
                return {
                    'total_backups': 0,
                    'total_size_mb': 0,
                    'oldest_backup': None,
                    'newest_backup': None,
                    'backup_types': {},
                    'health_status': 'no_backups'
                }
            
            total_size = sum(backup['size_mb'] for backup in backups)
            backup_types = {}
            
            for backup in backups:
                backup_type = backup.get('backup_type', 'unknown')
                backup_types[backup_type] = backup_types.get(backup_type, 0) + 1
            
            # Determine health status
            health_status = 'healthy'
            if len(backups) < 3:
                health_status = 'low_redundancy'
            elif any('error' in backup for backup in backups):
                health_status = 'has_errors'
            
            return {
                'total_backups': len(backups),
                'total_size_mb': round(total_size, 2),
                'oldest_backup': backups[-1]['created_at'] if backups else None,
                'newest_backup': backups[0]['created_at'] if backups else None,
                'backup_types': backup_types,
                'health_status': health_status,
                'compression_enabled': self.compress,
                'max_backups_limit': self.max_backups
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup statistics: {e}")
            return {'error': str(e)}
    
    def cleanup_corrupted_backups(self) -> Tuple[int, List[str]]:
        """
        Remove corrupted or invalid backup files.
        
        Returns:
            Tuple of (number_removed, list_of_removed_files)
        """
        removed_files = []
        
        try:
            backup_files = list(self.backup_dir.glob("backup_*.json*"))
            
            for backup_file in backup_files:
                is_valid, report = self.verify_backup(backup_file)
                
                if not is_valid:
                    try:
                        backup_file.unlink()
                        removed_files.append(str(backup_file))
                        logger.info(f"Removed corrupted backup: {backup_file}")
                    except Exception as e:
                        logger.error(f"Failed to remove corrupted backup {backup_file}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to cleanup corrupted backups: {e}")
        
        return len(removed_files), removed_files
    
    def export_backup_manifest(self, output_file: Path) -> bool:
        """
        Export a manifest of all backups for documentation.
        
        Args:
            output_file: File to write manifest to
            
        Returns:
            True if successful
        """
        try:
            backups = self.list_backups()
            statistics = self.get_backup_statistics()
            
            manifest = {
                'generated_at': datetime.now().isoformat(),
                'backup_directory': str(self.backup_dir),
                'statistics': statistics,
                'backups': backups
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Backup manifest exported to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export backup manifest: {e}")
            return False