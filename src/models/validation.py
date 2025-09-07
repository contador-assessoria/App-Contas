"""
Validation framework for expense data models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union, Callable
from decimal import Decimal
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """
    Represents a validation error.
    
    Attributes:
        field: Field name that failed validation
        message: Error message
        code: Error code for programmatic handling
        severity: Error severity (error, warning, info)
        value: The value that failed validation
        context: Additional context information
    """
    field: str
    message: str
    code: str = "VALIDATION_ERROR"
    severity: str = "error"
    value: Any = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'field': self.field,
            'message': self.message,
            'code': self.code,
            'severity': self.severity,
            'value': str(self.value) if self.value is not None else None,
            'context': self.context
        }


@dataclass
class ValidationResult:
    """
    Result of validation operation.
    
    Attributes:
        is_valid: Whether validation passed
        errors: List of validation errors
        warnings: List of validation warnings
        metadata: Additional validation metadata
    """
    is_valid: bool = True
    errors: List[ValidationError] = None
    warnings: List[ValidationError] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}
        
        # Update is_valid based on errors
        self.is_valid = len(self.errors) == 0
    
    def add_error(self, field: str, message: str, code: str = "VALIDATION_ERROR", **kwargs):
        """Add validation error."""
        error = ValidationError(
            field=field,
            message=message,
            code=code,
            severity="error",
            **kwargs
        )
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, field: str, message: str, code: str = "VALIDATION_WARNING", **kwargs):
        """Add validation warning."""
        warning = ValidationError(
            field=field,
            message=message,
            code=code,
            severity="warning",
            **kwargs
        )
        self.warnings.append(warning)
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.metadata.update(other.metadata)
        self.is_valid = len(self.errors) == 0
    
    def get_errors_by_field(self, field: str) -> List[ValidationError]:
        """Get errors for specific field."""
        return [error for error in self.errors if error.field == field]
    
    def get_errors_by_code(self, code: str) -> List[ValidationError]:
        """Get errors by error code."""
        return [error for error in self.errors if error.code == code]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid,
            'errors': [error.to_dict() for error in self.errors],
            'warnings': [warning.to_dict() for warning in self.warnings],
            'metadata': self.metadata
        }


class BaseValidator(ABC):
    """
    Abstract base class for validators.
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.
        
        Args:
            strict_mode: Whether to use strict validation rules
        """
        self.strict_mode = strict_mode
        self.custom_rules: List[Callable] = []
    
    @abstractmethod
    def validate(self, data: Any) -> ValidationResult:
        """
        Validate data.
        
        Args:
            data: Data to validate
            
        Returns:
            ValidationResult
        """
        pass
    
    def add_custom_rule(self, rule: Callable[[Any], Optional[ValidationError]]):
        """
        Add custom validation rule.
        
        Args:
            rule: Function that takes data and returns ValidationError or None
        """
        self.custom_rules.append(rule)
    
    def _apply_custom_rules(self, data: Any, result: ValidationResult):
        """Apply custom validation rules."""
        for rule in self.custom_rules:
            try:
                error = rule(data)
                if error:
                    result.errors.append(error)
            except Exception as e:
                logger.warning(f"Custom validation rule failed: {e}")
    
    def _validate_decimal_range(
        self,
        value: Decimal,
        field: str,
        min_value: Optional[Decimal] = None,
        max_value: Optional[Decimal] = None,
        allow_zero: bool = True,
        allow_negative: bool = False
    ) -> List[ValidationError]:
        """Validate decimal value range."""
        errors = []
        
        if not allow_negative and value < 0:
            errors.append(ValidationError(
                field=field,
                message=f"{field} cannot be negative",
                code="NEGATIVE_VALUE",
                value=value
            ))
        
        if not allow_zero and value == 0:
            errors.append(ValidationError(
                field=field,
                message=f"{field} cannot be zero",
                code="ZERO_VALUE",
                value=value
            ))
        
        if min_value is not None and value < min_value:
            errors.append(ValidationError(
                field=field,
                message=f"{field} must be at least {min_value}",
                code="VALUE_TOO_LOW",
                value=value,
                context={'min_value': str(min_value)}
            ))
        
        if max_value is not None and value > max_value:
            errors.append(ValidationError(
                field=field,
                message=f"{field} cannot exceed {max_value}",
                code="VALUE_TOO_HIGH",
                value=value,
                context={'max_value': str(max_value)}
            ))
        
        return errors
    
    def _validate_string_format(
        self,
        value: str,
        field: str,
        pattern: Optional[str] = None,
        min_length: int = 0,
        max_length: Optional[int] = None,
        required: bool = False
    ) -> List[ValidationError]:
        """Validate string format."""
        errors = []
        
        if required and not value.strip():
            errors.append(ValidationError(
                field=field,
                message=f"{field} is required",
                code="REQUIRED_FIELD",
                value=value
            ))
            return errors
        
        if value and len(value) < min_length:
            errors.append(ValidationError(
                field=field,
                message=f"{field} must be at least {min_length} characters",
                code="TOO_SHORT",
                value=value,
                context={'min_length': min_length}
            ))
        
        if value and max_length and len(value) > max_length:
            errors.append(ValidationError(
                field=field,
                message=f"{field} cannot exceed {max_length} characters",
                code="TOO_LONG",
                value=value,
                context={'max_length': max_length}
            ))
        
        if value and pattern and not re.match(pattern, value):
            errors.append(ValidationError(
                field=field,
                message=f"{field} format is invalid",
                code="INVALID_FORMAT",
                value=value,
                context={'pattern': pattern}
            ))
        
        return errors
    
    def _validate_percentage(self, value: Decimal, field: str) -> List[ValidationError]:
        """Validate percentage value."""
        return self._validate_decimal_range(
            value, field, 
            min_value=Decimal('0'), 
            max_value=Decimal('100'),
            allow_negative=False
        )


class ElectricityValidator(BaseValidator):
    """Validator for electricity data."""
    
    def validate(self, data) -> ValidationResult:
        """Validate electricity data."""
        from .expense_models import ElectricityData
        
        result = ValidationResult()
        
        if not isinstance(data, ElectricityData):
            result.add_error("data", "Invalid data type for electricity validation", "INVALID_TYPE")
            return result
        
        # Validate kWh values
        result.errors.extend(self._validate_decimal_range(
            data.total_kwh, "total_kwh", 
            min_value=Decimal('0'), max_value=Decimal('10000'),
            allow_negative=False
        ))
        
        result.errors.extend(self._validate_decimal_range(
            data.casa2_kwh, "casa2_kwh",
            min_value=Decimal('0'), max_value=data.total_kwh,
            allow_negative=False
        ))
        
        # Validate bill amount
        result.errors.extend(self._validate_decimal_range(
            data.total_bill, "total_bill",
            min_value=Decimal('0'), max_value=Decimal('50000'),
            allow_negative=False
        ))
        
        # Validate rate per kWh if provided
        if data.rate_per_kwh is not None:
            result.errors.extend(self._validate_decimal_range(
                data.rate_per_kwh, "rate_per_kwh",
                min_value=Decimal('0'), max_value=Decimal('10'),
                allow_negative=False
            ))
        
        # Business logic validation
        if data.total_kwh > 0 and data.total_bill > 0:
            calculated_rate = data.total_bill / data.total_kwh
            if calculated_rate > Decimal('5'):
                result.add_warning(
                    "rate_per_kwh",
                    "Calculated rate per kWh seems unusually high",
                    "HIGH_RATE",
                    value=calculated_rate
                )
        
        # Consistency check
        if data.casa2_kwh > data.total_kwh:
            result.add_error(
                "casa2_kwh",
                "Casa 2 consumption cannot exceed total consumption",
                "INVALID_PROPORTION"
            )
        
        # Strict mode validations
        if self.strict_mode:
            if data.total_kwh == 0 and data.total_bill > 0:
                result.add_error(
                    "total_kwh",
                    "Cannot have bill amount without consumption",
                    "INCONSISTENT_DATA"
                )
            
            if data.total_bill == 0 and data.total_kwh > 0:
                result.add_warning(
                    "total_bill",
                    "Consumption recorded but no bill amount",
                    "MISSING_BILL"
                )
        
        # Apply custom rules
        self._apply_custom_rules(data, result)
        
        return result


class RecurringBillsValidator(BaseValidator):
    """Validator for recurring bills data."""
    
    def validate(self, data) -> ValidationResult:
        """Validate recurring bills data."""
        from .expense_models import RecurringBills
        
        result = ValidationResult()
        
        if not isinstance(data, RecurringBills):
            result.add_error("data", "Invalid data type for recurring bills validation", "INVALID_TYPE")
            return result
        
        # Validate bill amounts
        bill_types = ['water', 'internet', 'gas']
        max_amounts = {'water': 10000, 'internet': 5000, 'gas': 10000}
        
        for bill_type in bill_types:
            amount = getattr(data, bill_type)
            result.errors.extend(self._validate_decimal_range(
                amount, bill_type,
                min_value=Decimal('0'), 
                max_value=Decimal(str(max_amounts[bill_type])),
                allow_negative=False
            ))
        
        # Validate percentage
        result.errors.extend(self._validate_percentage(data.casa2_percentage, "casa2_percentage"))
        
        # Business logic validations
        total_amount = data.total_amount
        if total_amount > Decimal('20000'):
            result.add_warning(
                "total_amount",
                "Total recurring bills seem unusually high",
                "HIGH_TOTAL",
                value=total_amount
            )
        
        # Strict mode validations
        if self.strict_mode:
            if total_amount == 0:
                result.add_warning(
                    "total_amount",
                    "No recurring bills recorded",
                    "NO_BILLS"
                )
        
        # Apply custom rules
        self._apply_custom_rules(data, result)
        
        return result


class OccasionalExpenseValidator(BaseValidator):
    """Validator for occasional expense data."""
    
    def validate(self, data) -> ValidationResult:
        """Validate occasional expense data."""
        from .expense_models import OccasionalExpense, SplitMethod
        
        result = ValidationResult()
        
        if not isinstance(data, OccasionalExpense):
            result.add_error("data", "Invalid data type for occasional expense validation", "INVALID_TYPE")
            return result
        
        # Validate description
        result.errors.extend(self._validate_string_format(
            data.description, "description",
            min_length=1, max_length=200, required=True
        ))
        
        # Validate amount
        result.errors.extend(self._validate_decimal_range(
            data.amount, "amount",
            min_value=Decimal('0.01'), max_value=Decimal('100000'),
            allow_zero=False, allow_negative=False
        ))
        
        # Validate split method specific fields
        if data.split_method == SplitMethod.FIXED:
            result.errors.extend(self._validate_decimal_range(
                data.casa1_value, "casa1_value",
                min_value=Decimal('0'), allow_negative=False
            ))
            
            result.errors.extend(self._validate_decimal_range(
                data.casa2_value, "casa2_value",
                min_value=Decimal('0'), allow_negative=False
            ))
            
            # Validate that fixed values sum to total
            total_fixed = data.casa1_value + data.casa2_value
            if abs(total_fixed - data.amount) > Decimal('0.01'):
                result.add_error(
                    "split_values",
                    "Sum of Casa 1 and Casa 2 values must equal total amount",
                    "INVALID_SPLIT_SUM",
                    context={
                        'total_fixed': str(total_fixed),
                        'amount': str(data.amount)
                    }
                )
        
        elif data.split_method == SplitMethod.PERCENTAGE and data.percentage is not None:
            result.errors.extend(self._validate_percentage(data.percentage, "percentage"))
        
        # Validate recurrence settings
        if data.is_recurring:
            if data.recurrence_months < 1:
                result.add_error(
                    "recurrence_months",
                    "Recurrence months must be at least 1",
                    "INVALID_RECURRENCE"
                )
            
            if data.recurrence_months > 60:
                result.add_warning(
                    "recurrence_months",
                    "Recurrence period seems unusually long",
                    "LONG_RECURRENCE",
                    value=data.recurrence_months
                )
        
        # Validate dates
        if data.due_date and data.due_date < data.date_added:
            result.add_error(
                "due_date",
                "Due date cannot be before date added",
                "INVALID_DATE_ORDER"
            )
        
        # Business logic validations
        if data.amount > Decimal('10000'):
            result.add_warning(
                "amount",
                "Expense amount seems unusually high",
                "HIGH_AMOUNT",
                value=data.amount
            )
        
        # Apply custom rules
        self._apply_custom_rules(data, result)
        
        return result


class PaymentValidator(BaseValidator):
    """Validator for payment data."""
    
    def validate(self, data) -> ValidationResult:
        """Validate payment data."""
        from .expense_models import Payment
        
        result = ValidationResult()
        
        if not isinstance(data, Payment):
            result.add_error("data", "Invalid data type for payment validation", "INVALID_TYPE")
            return result
        
        # Validate payment amounts
        result.errors.extend(self._validate_decimal_range(
            data.casa1_paid, "casa1_paid",
            min_value=Decimal('0'), max_value=Decimal('100000'),
            allow_negative=False
        ))
        
        result.errors.extend(self._validate_decimal_range(
            data.casa2_paid, "casa2_paid",
            min_value=Decimal('0'), max_value=Decimal('100000'),
            allow_negative=False
        ))
        
        # At least one payment must be made
        if data.total_paid == 0:
            result.add_warning(
                "total_paid",
                "No payments recorded",
                "NO_PAYMENTS"
            )
        
        # Validate transaction ID format if provided
        if data.transaction_id:
            result.errors.extend(self._validate_string_format(
                data.transaction_id, "transaction_id",
                max_length=50
            ))
        
        # Business logic validations
        if data.total_paid > Decimal('50000'):
            result.add_warning(
                "total_paid",
                "Total payment amount seems unusually high",
                "HIGH_PAYMENT",
                value=data.total_paid
            )
        
        # Apply custom rules
        self._apply_custom_rules(data, result)
        
        return result


class MonthDataValidator(BaseValidator):
    """Validator for complete month data."""
    
    def __init__(self, strict_mode: bool = False):
        super().__init__(strict_mode)
        self.electricity_validator = ElectricityValidator(strict_mode)
        self.recurring_validator = RecurringBillsValidator(strict_mode)
        self.payment_validator = PaymentValidator(strict_mode)
        self.expense_validator = OccasionalExpenseValidator(strict_mode)
    
    def validate(self, data) -> ValidationResult:
        """Validate complete month data."""
        from .expense_models import MonthData
        
        result = ValidationResult()
        
        if not isinstance(data, MonthData):
            result.add_error("data", "Invalid data type for month data validation", "INVALID_TYPE")
            return result
        
        # Validate year and month
        if not 2000 <= data.year <= 2100:
            result.add_error(
                "year",
                "Year must be between 2000 and 2100",
                "INVALID_YEAR",
                value=data.year
            )
        
        result.errors.extend(self._validate_string_format(
            data.month, "month",
            min_length=1, required=True
        ))
        
        # Validate nested objects
        electricity_result = self.electricity_validator.validate(data.electricity)
        result.merge(electricity_result)
        
        recurring_result = self.recurring_validator.validate(data.recurring_bills)
        result.merge(recurring_result)
        
        payment_result = self.payment_validator.validate(data.payments)
        result.merge(payment_result)
        
        # Validate occasional expenses
        for i, expense in enumerate(data.occasional_expenses):
            expense_result = self.expense_validator.validate(expense)
            # Prefix field names with expense index
            for error in expense_result.errors:
                error.field = f"expense_{i}_{error.field}"
            for warning in expense_result.warnings:
                warning.field = f"expense_{i}_{warning.field}"
            result.merge(expense_result)
        
        # Cross-validation rules
        if self.strict_mode:
            self._validate_month_consistency(data, result)
        
        # Validate locked status
        if data.is_locked and data.modified_at > data.created_at:
            result.add_error(
                "is_locked",
                "Cannot modify locked month data",
                "LOCKED_DATA"
            )
        
        # Apply custom rules
        self._apply_custom_rules(data, result)
        
        return result
    
    def _validate_month_consistency(self, data, result: ValidationResult):
        """Validate consistency across month data."""
        # Check if total expenses seem reasonable compared to payments
        total_estimated = (
            data.electricity.total_bill +
            data.recurring_bills.total_amount +
            data.total_occasional_amount
        )
        
        total_paid = data.payments.total_paid
        
        if total_paid > 0 and total_estimated > 0:
            ratio = total_paid / total_estimated
            if ratio > Decimal('2'):
                result.add_warning(
                    "payment_ratio",
                    "Payments significantly exceed estimated expenses",
                    "HIGH_PAYMENT_RATIO",
                    context={
                        'ratio': str(ratio),
                        'estimated': str(total_estimated),
                        'paid': str(total_paid)
                    }
                )
            elif ratio < Decimal('0.5'):
                result.add_warning(
                    "payment_ratio",
                    "Payments significantly less than estimated expenses",
                    "LOW_PAYMENT_RATIO",
                    context={
                        'ratio': str(ratio),
                        'estimated': str(total_estimated),
                        'paid': str(total_paid)
                    }
                )


class ValidationManager:
    """
    Central validation manager.
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validation manager.
        
        Args:
            strict_mode: Whether to use strict validation
        """
        self.strict_mode = strict_mode
        self.validators = {
            'electricity': ElectricityValidator(strict_mode),
            'recurring_bills': RecurringBillsValidator(strict_mode),
            'occasional_expense': OccasionalExpenseValidator(strict_mode),
            'payment': PaymentValidator(strict_mode),
            'month_data': MonthDataValidator(strict_mode)
        }
    
    def validate(self, data: Any, validator_type: str) -> ValidationResult:
        """
        Validate data using specified validator.
        
        Args:
            data: Data to validate
            validator_type: Type of validator to use
            
        Returns:
            ValidationResult
        """
        if validator_type not in self.validators:
            result = ValidationResult()
            result.add_error(
                "validator_type",
                f"Unknown validator type: {validator_type}",
                "UNKNOWN_VALIDATOR"
            )
            return result
        
        try:
            return self.validators[validator_type].validate(data)
        except Exception as e:
            logger.error(f"Validation error: {e}")
            result = ValidationResult()
            result.add_error(
                "validation",
                f"Validation failed: {str(e)}",
                "VALIDATION_EXCEPTION"
            )
            return result
    
    def add_custom_rule(self, validator_type: str, rule: Callable):
        """Add custom validation rule to specific validator."""
        if validator_type in self.validators:
            self.validators[validator_type].add_custom_rule(rule)
    
    def set_strict_mode(self, strict: bool):
        """Enable or disable strict mode for all validators."""
        self.strict_mode = strict
        for validator in self.validators.values():
            validator.strict_mode = strict