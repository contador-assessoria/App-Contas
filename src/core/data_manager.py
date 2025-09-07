"""
Data persistence and management for expense tracking system.
"""

import json
import os
import threading
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from decimal import Decimal
import logging

from ..models.expense_models import MonthData, CalculationResult

logger = logging.getLogger(__name__)


class DataManager:
    """
    Thread-safe data manager for expense tracking system.
    Handles data persistence, caching, and integrity validation.
    """
    
    def __init__(self, data_file: str = "data/expense_data.json"):
        """
        Initialize data manager.
        
        Args:
            data_file: Path to main data file
        """
        self.data_file = Path(data_file)
        self.data_dir = self.data_file.parent
        self._cache = {}
        self._lock = threading.RLock()
        self._dirty = False
        self._last_save = None
        
        self._ensure_data_directory()
        self._load_data()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_data(self):
        """Load data from file into cache."""
        with self._lock:
            if self.data_file.exists():
                try:
                    with open(self.data_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Validate and convert data
                    self._cache = self._validate_and_convert_data(data)
                    self._last_save = datetime.now()
                    logger.info(f"Loaded data from {self.data_file}")
                    
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    logger.error(f"Failed to load data: {e}")
                    self._cache = {}
                except Exception as e:
                    logger.error(f"Unexpected error loading data: {e}")
                    # Try to recover from backup
                    if self._recover_from_backup():
                        logger.info("Successfully recovered from backup")
                    else:
                        self._cache = {}
            else:
                self._cache = {}
                logger.info("No existing data file found, starting fresh")
    
    def _validate_and_convert_data(self, data: Dict) -> Dict:
        """Validate and convert loaded data to proper types."""
        validated_data = {}
        
        for year_str, year_data in data.items():
            try:
                year = int(year_str)
                validated_data[year] = {}
                
                for month_name, month_data in year_data.items():
                    if isinstance(month_data, dict):
                        # Convert decimal strings back to Decimal objects in results
                        if 'results' in month_data:
                            month_data['results'] = self._convert_results_to_decimal(
                                month_data['results']
                            )
                        validated_data[year][month_name] = month_data
                        
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid year data {year_str}: {e}")
                continue
        
        return validated_data
    
    def _convert_results_to_decimal(self, results: Dict) -> Dict:
        """Convert numeric values in results to Decimal objects."""
        decimal_fields = [
            'total_expenses', 'casa1_should_pay', 'casa2_should_pay',
            'previous_balance', 'final_house1', 'final_house2', 'month_balance'
        ]
        
        for field in decimal_fields:
            if field in results:
                try:
                    results[field] = Decimal(str(results[field]))
                except (ValueError, TypeError):
                    results[field] = Decimal('0.00')
        
        # Convert nested structures
        if 'electricity' in results:
            for key, value in results['electricity'].items():
                if isinstance(value, (int, float, str)):
                    try:
                        results['electricity'][key] = Decimal(str(value))
                    except (ValueError, TypeError):
                        results['electricity'][key] = Decimal('0.00')
        
        if 'recurring' in results:
            for key, value in results['recurring'].items():
                if isinstance(value, (int, float, str)):
                    try:
                        results['recurring'][key] = Decimal(str(value))
                    except (ValueError, TypeError):
                        results['recurring'][key] = Decimal('0.00')
        
        if 'occasional' in results:
            for expense in results['occasional']:
                for key in ['total', 'casa1', 'casa2']:
                    if key in expense:
                        try:
                            expense[key] = Decimal(str(expense[key]))
                        except (ValueError, TypeError):
                            expense[key] = Decimal('0.00')
        
        return results
    
    def _recover_from_backup(self) -> bool:
        """Attempt to recover from most recent backup."""
        backup_dir = self.data_dir / "backups"
        if not backup_dir.exists():
            return False
        
        backup_files = sorted(
            backup_dir.glob("backup_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for backup_file in backup_files[:3]:  # Try last 3 backups
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._cache = self._validate_and_convert_data(data)
                logger.info(f"Recovered from backup: {backup_file}")
                return True
                
            except Exception as e:
                logger.warning(f"Failed to recover from {backup_file}: {e}")
                continue
        
        return False
    
    def save_data(self, force: bool = False) -> bool:
        """
        Save cached data to file.
        
        Args:
            force: Force save even if data not dirty
            
        Returns:
            True if save successful
        """
        with self._lock:
            if not self._dirty and not force:
                return True
            
            try:
                # Convert Decimal objects to strings for JSON serialization
                serializable_data = self._prepare_data_for_serialization()
                
                # Write to temporary file first
                temp_file = self.data_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(serializable_data, f, indent=2, ensure_ascii=False, default=str)
                
                # Atomic replace
                temp_file.replace(self.data_file)
                
                self._dirty = False
                self._last_save = datetime.now()
                logger.info(f"Data saved to {self.data_file}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save data: {e}")
                # Clean up temp file if it exists
                temp_file = self.data_file.with_suffix('.tmp')
                if temp_file.exists():
                    temp_file.unlink()
                return False
    
    def _prepare_data_for_serialization(self) -> Dict:
        """Prepare data for JSON serialization by converting Decimal to string."""
        def convert_value(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_value(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_value(item) for item in obj]
            else:
                return obj
        
        return convert_value(self._cache)
    
    def get_month_data(self, year: int, month: str) -> Optional[MonthData]:
        """
        Get month data.
        
        Args:
            year: Year
            month: Month name in Portuguese
            
        Returns:
            MonthData object or None if not found
        """
        with self._lock:
            if year not in self._cache:
                return None
            
            if month not in self._cache[year]:
                return None
            
            try:
                month_dict = self._cache[year][month].copy()
                # Remove results as they're calculated separately
                month_dict.pop('results', None)
                return MonthData.from_dict(month_dict)
            except Exception as e:
                logger.error(f"Error loading month data {year}/{month}: {e}")
                return None
    
    def save_month_data(
        self, 
        year: int, 
        month: str, 
        month_data: MonthData, 
        results: CalculationResult
    ) -> bool:
        """
        Save month data and calculation results.
        
        Args:
            year: Year
            month: Month name
            month_data: Month data to save
            results: Calculation results
            
        Returns:
            True if save successful
        """
        with self._lock:
            try:
                if year not in self._cache:
                    self._cache[year] = {}
                
                # Convert to dict and add results
                month_dict = month_data.to_dict()
                month_dict['results'] = results.to_dict()
                month_dict['modified_at'] = datetime.now().isoformat()
                
                self._cache[year][month] = month_dict
                self._dirty = True
                
                logger.info(f"Month data saved: {year}/{month}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to save month data {year}/{month}: {e}")
                return False
    
    def get_year_data(self, year: int) -> Dict:
        """Get all data for a specific year."""
        with self._lock:
            return self._cache.get(year, {}).copy()
    
    def get_all_years(self) -> List[int]:
        """Get list of all years with data."""
        with self._lock:
            return sorted(self._cache.keys())
    
    def get_months_for_year(self, year: int) -> List[str]:
        """Get list of months with data for a specific year."""
        with self._lock:
            if year not in self._cache:
                return []
            return list(self._cache[year].keys())
    
    def delete_month(self, year: int, month: str) -> bool:
        """
        Delete month data.
        
        Args:
            year: Year
            month: Month name
            
        Returns:
            True if deletion successful
        """
        with self._lock:
            try:
                if year in self._cache and month in self._cache[year]:
                    del self._cache[year][month]
                    
                    # Clean up empty year
                    if not self._cache[year]:
                        del self._cache[year]
                    
                    self._dirty = True
                    logger.info(f"Deleted month data: {year}/{month}")
                    return True
                else:
                    logger.warning(f"Month data not found for deletion: {year}/{month}")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to delete month data {year}/{month}: {e}")
                return False
    
    def get_previous_balance(self, year: int, month_number: int) -> Decimal:
        """
        Get balance carried from previous month.
        
        Args:
            year: Current year
            month_number: Current month number (1-12)
            
        Returns:
            Previous month balance as Decimal
        """
        months = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        
        # Calculate previous month
        prev_month_num = month_number - 1
        prev_year = year
        
        if prev_month_num == 0:
            prev_month_num = 12
            prev_year = year - 1
        
        prev_month_name = months[prev_month_num - 1]
        
        with self._lock:
            if prev_year in self._cache and prev_month_name in self._cache[prev_year]:
                month_data = self._cache[prev_year][prev_month_name]
                results = month_data.get('results', {})
                balance = results.get('month_balance', 0)
                
                if isinstance(balance, (int, float, str)):
                    return Decimal(str(balance))
                elif isinstance(balance, Decimal):
                    return balance
            
            return Decimal('0.00')
    
    def get_accumulated_balance(self, year: int, up_to_month: int) -> Decimal:
        """
        Calculate accumulated balance up to specific month.
        
        Args:
            year: Year
            up_to_month: Month number to calculate up to (1-12)
            
        Returns:
            Accumulated balance as Decimal
        """
        months = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        
        accumulated = Decimal('0.00')
        
        with self._lock:
            # Sum balances from previous years (last 5 years max)
            for y in range(max(2020, year - 5), year):
                if y in self._cache:
                    for month_name in months:
                        if month_name in self._cache[y]:
                            results = self._cache[y][month_name].get('results', {})
                            balance = results.get('month_balance', 0)
                            if isinstance(balance, (int, float, str)):
                                accumulated += Decimal(str(balance))
                            elif isinstance(balance, Decimal):
                                accumulated += balance
            
            # Sum balances from current year up to specified month
            if year in self._cache:
                for i in range(up_to_month):
                    month_name = months[i]
                    if month_name in self._cache[year]:
                        results = self._cache[year][month_name].get('results', {})
                        balance = results.get('month_balance', 0)
                        if isinstance(balance, (int, float, str)):
                            accumulated += Decimal(str(balance))
                        elif isinstance(balance, Decimal):
                            accumulated += balance
        
        return accumulated
    
    def get_data_statistics(self) -> Dict:
        """Get statistics about stored data."""
        with self._lock:
            stats = {
                'total_years': len(self._cache),
                'total_months': 0,
                'years_range': [],
                'data_size_mb': 0,
                'last_modified': None,
                'integrity_status': 'unknown'
            }
            
            if self._cache:
                stats['years_range'] = [min(self._cache.keys()), max(self._cache.keys())]
                
                for year_data in self._cache.values():
                    stats['total_months'] += len(year_data)
                
                # Estimate data size
                try:
                    data_str = json.dumps(self._prepare_data_for_serialization())
                    stats['data_size_mb'] = len(data_str.encode('utf-8')) / (1024 * 1024)
                except:
                    stats['data_size_mb'] = 0
                
                stats['last_modified'] = self._last_save.isoformat() if self._last_save else None
            
            # Check data integrity
            stats['integrity_status'] = self._check_data_integrity()
            
            return stats
    
    def _check_data_integrity(self) -> str:
        """Check data integrity and return status."""
        try:
            total_months = 0
            corrupted_months = 0
            
            for year, year_data in self._cache.items():
                if not isinstance(year, int) or year < 2000 or year > 2100:
                    return 'corrupted'
                
                for month_name, month_data in year_data.items():
                    total_months += 1
                    
                    if not isinstance(month_data, dict):
                        corrupted_months += 1
                        continue
                    
                    # Check required fields
                    required_fields = ['electricity', 'recurring_bills', 'payments']
                    if not all(field in month_data for field in required_fields):
                        corrupted_months += 1
                        continue
                    
                    # Check results structure if present
                    if 'results' in month_data:
                        results = month_data['results']
                        if not isinstance(results, dict):
                            corrupted_months += 1
                            continue
            
            if total_months == 0:
                return 'empty'
            elif corrupted_months == 0:
                return 'healthy'
            elif corrupted_months / total_months < 0.1:
                return 'minor_issues'
            else:
                return 'corrupted'
                
        except Exception:
            return 'unknown'
    
    def repair_data(self) -> Tuple[bool, List[str]]:
        """
        Attempt to repair corrupted data.
        
        Returns:
            Tuple of (success, list of repair messages)
        """
        with self._lock:
            repair_messages = []
            repairs_made = False
            
            try:
                # Remove invalid years
                invalid_years = []
                for year in list(self._cache.keys()):
                    if not isinstance(year, int) or year < 2000 or year > 2100:
                        invalid_years.append(year)
                
                for year in invalid_years:
                    del self._cache[year]
                    repair_messages.append(f"Removed invalid year: {year}")
                    repairs_made = True
                
                # Repair month data
                months_order = [
                    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                ]
                
                for year, year_data in self._cache.items():
                    invalid_months = []
                    
                    for month_name, month_data in year_data.items():
                        if month_name not in months_order:
                            invalid_months.append(month_name)
                            continue
                        
                        if not isinstance(month_data, dict):
                            invalid_months.append(month_name)
                            continue
                        
                        # Repair missing required fields
                        if 'electricity' not in month_data:
                            month_data['electricity'] = {
                                'total_kwh': 0.0,
                                'casa2_kwh': 0.0,
                                'total_bill': 0.0
                            }
                            repair_messages.append(f"Added missing electricity data: {year}/{month_name}")
                            repairs_made = True
                        
                        if 'recurring_bills' not in month_data:
                            month_data['recurring_bills'] = {
                                'water': 0.0,
                                'internet': 0.0,
                                'casa2_percentage': 67
                            }
                            repair_messages.append(f"Added missing recurring bills data: {year}/{month_name}")
                            repairs_made = True
                        
                        if 'payments' not in month_data:
                            month_data['payments'] = {
                                'casa1_paid': 0.0,
                                'casa2_paid': 0.0,
                                'payment_method': '',
                                'notes': ''
                            }
                            repair_messages.append(f"Added missing payments data: {year}/{month_name}")
                            repairs_made = True
                        
                        if 'occasional_expenses' not in month_data:
                            month_data['occasional_expenses'] = []
                            repair_messages.append(f"Added missing occasional expenses: {year}/{month_name}")
                            repairs_made = True
                        
                        # Add timestamps if missing
                        if 'created_at' not in month_data:
                            month_data['created_at'] = datetime.now().isoformat()
                            repairs_made = True
                        
                        if 'modified_at' not in month_data:
                            month_data['modified_at'] = datetime.now().isoformat()
                            repairs_made = True
                    
                    # Remove invalid months
                    for month_name in invalid_months:
                        del year_data[month_name]
                        repair_messages.append(f"Removed invalid month: {year}/{month_name}")
                        repairs_made = True
                
                if repairs_made:
                    self._dirty = True
                    repair_messages.append("Data repairs completed successfully")
                
                return True, repair_messages
                
            except Exception as e:
                repair_messages.append(f"Repair failed: {str(e)}")
                return False, repair_messages
    
    def optimize_data(self) -> Tuple[bool, Dict]:
        """
        Optimize data storage and performance.
        
        Returns:
            Tuple of (success, optimization stats)
        """
        with self._lock:
            try:
                stats = {
                    'before_size': 0,
                    'after_size': 0,
                    'months_optimized': 0,
                    'space_saved_percent': 0
                }
                
                # Calculate before size
                before_data = self._prepare_data_for_serialization()
                stats['before_size'] = len(json.dumps(before_data).encode('utf-8'))
                
                # Optimize data
                for year, year_data in self._cache.items():
                    for month_name, month_data in year_data.items():
                        # Remove redundant decimal places
                        self._optimize_month_data(month_data)
                        stats['months_optimized'] += 1
                
                # Calculate after size
                after_data = self._prepare_data_for_serialization()
                stats['after_size'] = len(json.dumps(after_data).encode('utf-8'))
                
                # Calculate space saved
                if stats['before_size'] > 0:
                    stats['space_saved_percent'] = (
                        (stats['before_size'] - stats['after_size']) / stats['before_size'] * 100
                    )
                
                self._dirty = True
                logger.info(f"Data optimization completed: {stats}")
                return True, stats
                
            except Exception as e:
                logger.error(f"Data optimization failed: {e}")
                return False, {'error': str(e)}
    
    def _optimize_month_data(self, month_data: Dict):
        """Optimize individual month data."""
        # Round financial values to 2 decimal places
        financial_paths = [
            ['electricity', 'total_bill'],
            ['recurring_bills', 'water'],
            ['recurring_bills', 'internet'],
            ['payments', 'casa1_paid'],
            ['payments', 'casa2_paid']
        ]
        
        for path in financial_paths:
            obj = month_data
            for key in path[:-1]:
                if key in obj and isinstance(obj[key], dict):
                    obj = obj[key]
                else:
                    break
            else:
                final_key = path[-1]
                if final_key in obj and isinstance(obj[final_key], (int, float)):
                    obj[final_key] = round(obj[final_key], 2)
        
        # Optimize occasional expenses
        if 'occasional_expenses' in month_data:
            for expense in month_data['occasional_expenses']:
                if 'amount' in expense:
                    expense['amount'] = round(expense['amount'], 2)
                if 'casa1_value' in expense:
                    expense['casa1_value'] = round(expense['casa1_value'], 2)
                if 'casa2_value' in expense:
                    expense['casa2_value'] = round(expense['casa2_value'], 2)
    
    def is_dirty(self) -> bool:
        """Check if data has unsaved changes."""
        with self._lock:
            return self._dirty
    
    def get_last_save_time(self) -> Optional[datetime]:
        """Get timestamp of last save operation."""
        with self._lock:
            return self._last_save
    
    def close(self):
        """Close data manager and save any pending changes."""
        with self._lock:
            if self._dirty:
                self.save_data(force=True)
            logger.info("Data manager closed")