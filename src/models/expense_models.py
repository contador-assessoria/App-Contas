"""
Core expense data models with enhanced validation and business logic.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class SplitMethod(Enum):
    """Methods for splitting occasional expenses."""
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    EQUAL = "equal"


class PaymentMethod(Enum):
    """Payment methods."""
    PIX = "pix"
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    OTHER = "other"


class ExpenseCategory(Enum):
    """Categories for occasional expenses."""
    MAINTENANCE = "maintenance"
    GROCERIES = "groceries"
    CLEANING = "cleaning"
    UTILITIES = "utilities"
    FURNITURE = "furniture"
    ELECTRONICS = "electronics"
    GARDEN = "garden"
    REPAIRS = "repairs"
    SECURITY = "security"
    OTHER = "other"


@dataclass
class ElectricityData:
    """
    Electricity consumption and billing data.
    
    Attributes:
        total_kwh: Total kWh consumed
        casa2_kwh: kWh consumed by Casa 2
        total_bill: Total bill amount
        rate_per_kwh: Optional rate per kWh for calculation verification
        meter_reading_date: Date of meter reading
        due_date: Bill due date
        notes: Additional notes
    """
    total_kwh: Decimal = field(default_factory=lambda: Decimal('0.00'))
    casa2_kwh: Decimal = field(default_factory=lambda: Decimal('0.00'))
    total_bill: Decimal = field(default_factory=lambda: Decimal('0.00'))
    rate_per_kwh: Optional[Decimal] = None
    meter_reading_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    notes: str = ""
    
    def __post_init__(self):
        """Convert input values to Decimal."""
        self.total_kwh = self._to_decimal(self.total_kwh)
        self.casa2_kwh = self._to_decimal(self.casa2_kwh)
        self.total_bill = self._to_decimal(self.total_bill)
        if self.rate_per_kwh is not None:
            self.rate_per_kwh = self._to_decimal(self.rate_per_kwh)
    
    @staticmethod
    def _to_decimal(value: Union[int, float, str, Decimal]) -> Decimal:
        """Convert value to Decimal safely."""
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            return Decimal('0.00')
    
    @property
    def casa1_kwh(self) -> Decimal:
        """Calculate Casa 1 kWh consumption."""
        return max(Decimal('0.00'), self.total_kwh - self.casa2_kwh)
    
    @property
    def is_valid(self) -> bool:
        """Check if data is valid."""
        return (
            self.total_kwh >= 0 and
            self.casa2_kwh >= 0 and
            self.casa2_kwh <= self.total_kwh and
            self.total_bill >= 0
        )
    
    @property
    def casa2_percentage(self) -> Decimal:
        """Calculate Casa 2 consumption percentage."""
        if self.total_kwh == 0:
            return Decimal('0.00')
        return (self.casa2_kwh / self.total_kwh * 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    @property
    def estimated_rate_per_kwh(self) -> Decimal:
        """Calculate estimated rate per kWh."""
        if self.total_kwh == 0:
            return Decimal('0.00')
        return (self.total_bill / self.total_kwh).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )
    
    def validate(self) -> List[str]:
        """Validate electricity data."""
        errors = []
        
        if self.total_kwh < 0:
            errors.append("Total kWh cannot be negative")
        
        if self.casa2_kwh < 0:
            errors.append("Casa 2 kWh cannot be negative")
        
        if self.casa2_kwh > self.total_kwh:
            errors.append("Casa 2 kWh cannot exceed total kWh")
        
        if self.total_bill < 0:
            errors.append("Total bill cannot be negative")
        
        if self.rate_per_kwh is not None and self.rate_per_kwh < 0:
            errors.append("Rate per kWh cannot be negative")
        
        # Check for unrealistic values
        if self.total_kwh > 10000:
            errors.append("Total kWh seems unrealistically high")
        
        if self.total_bill > 50000:
            errors.append("Total bill seems unrealistically high")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_kwh': str(self.total_kwh),
            'casa2_kwh': str(self.casa2_kwh),
            'total_bill': str(self.total_bill),
            'rate_per_kwh': str(self.rate_per_kwh) if self.rate_per_kwh else None,
            'meter_reading_date': self.meter_reading_date.isoformat() if self.meter_reading_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ElectricityData':
        """Create from dictionary."""
        obj = cls()
        obj.total_kwh = cls._to_decimal(data.get('total_kwh', 0))
        obj.casa2_kwh = cls._to_decimal(data.get('casa2_kwh', 0))
        obj.total_bill = cls._to_decimal(data.get('total_bill', 0))
        
        if data.get('rate_per_kwh'):
            obj.rate_per_kwh = cls._to_decimal(data['rate_per_kwh'])
        
        if data.get('meter_reading_date'):
            obj.meter_reading_date = datetime.fromisoformat(data['meter_reading_date'])
        
        if data.get('due_date'):
            obj.due_date = datetime.fromisoformat(data['due_date'])
        
        obj.notes = data.get('notes', '')
        
        return obj


@dataclass
class RecurringBills:
    """
    Recurring monthly bills with percentage-based splitting.
    
    Attributes:
        water: Water bill amount
        internet: Internet bill amount
        gas: Gas bill amount
        casa2_percentage: Percentage allocated to Casa 2
        notes: Additional notes
    """
    water: Decimal = field(default_factory=lambda: Decimal('0.00'))
    internet: Decimal = field(default_factory=lambda: Decimal('0.00'))
    gas: Decimal = field(default_factory=lambda: Decimal('0.00'))
    casa2_percentage: Decimal = field(default_factory=lambda: Decimal('67.00'))
    notes: str = ""
    
    def __post_init__(self):
        """Convert input values to Decimal."""
        self.water = self._to_decimal(self.water)
        self.internet = self._to_decimal(self.internet)
        self.gas = self._to_decimal(self.gas)
        self.casa2_percentage = self._to_decimal(self.casa2_percentage)
    
    @staticmethod
    def _to_decimal(value: Union[int, float, str, Decimal]) -> Decimal:
        """Convert value to Decimal safely."""
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            return Decimal('0.00')
    
    @property
    def casa1_percentage(self) -> Decimal:
        """Calculate Casa 1 percentage."""
        return Decimal('100.00') - self.casa2_percentage
    
    @property
    def total_amount(self) -> Decimal:
        """Calculate total recurring bills amount."""
        return self.water + self.internet + self.gas
    
    @property
    def casa1_total(self) -> Decimal:
        """Calculate Casa 1 total amount."""
        return (self.total_amount * self.casa1_percentage / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    @property
    def casa2_total(self) -> Decimal:
        """Calculate Casa 2 total amount."""
        return self.total_amount - self.casa1_total
    
    def get_casa1_amount(self, bill_type: str) -> Decimal:
        """Get Casa 1 amount for specific bill type."""
        amount = getattr(self, bill_type, Decimal('0.00'))
        return (amount * self.casa1_percentage / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def get_casa2_amount(self, bill_type: str) -> Decimal:
        """Get Casa 2 amount for specific bill type."""
        amount = getattr(self, bill_type, Decimal('0.00'))
        return amount - self.get_casa1_amount(bill_type)
    
    def validate(self) -> List[str]:
        """Validate recurring bills data."""
        errors = []
        
        if self.water < 0:
            errors.append("Water bill cannot be negative")
        
        if self.internet < 0:
            errors.append("Internet bill cannot be negative")
        
        if self.gas < 0:
            errors.append("Gas bill cannot be negative")
        
        if not 0 <= self.casa2_percentage <= 100:
            errors.append("Casa 2 percentage must be between 0 and 100")
        
        # Check for unrealistic values
        if self.water > 10000:
            errors.append("Water bill seems unrealistically high")
        
        if self.internet > 5000:
            errors.append("Internet bill seems unrealistically high")
        
        if self.gas > 10000:
            errors.append("Gas bill seems unrealistically high")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'water': str(self.water),
            'internet': str(self.internet),
            'gas': str(self.gas),
            'casa2_percentage': str(self.casa2_percentage),
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecurringBills':
        """Create from dictionary."""
        obj = cls()
        obj.water = cls._to_decimal(data.get('water', 0))
        obj.internet = cls._to_decimal(data.get('internet', 0))
        obj.gas = cls._to_decimal(data.get('gas', 0))
        obj.casa2_percentage = cls._to_decimal(data.get('casa2_percentage', 67))
        obj.notes = data.get('notes', '')
        return obj


@dataclass
class OccasionalExpense:
    """
    Occasional expense with flexible splitting methods.
    
    Attributes:
        id: Unique identifier
        description: Expense description
        amount: Total expense amount
        split_method: How to split the expense
        casa1_value: Fixed value for Casa 1 (if using fixed split)
        casa2_value: Fixed value for Casa 2 (if using fixed split)
        percentage: Custom percentage for Casa 2 (if using percentage split)
        category: Expense category
        date_added: When expense was added
        due_date: When expense is due
        paid_by: Who paid the expense initially
        notes: Additional notes
        receipt_path: Path to receipt file
        is_recurring: Whether this expense repeats
        recurrence_months: How many months it recurs
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    amount: Decimal = field(default_factory=lambda: Decimal('0.00'))
    split_method: SplitMethod = SplitMethod.PERCENTAGE
    casa1_value: Decimal = field(default_factory=lambda: Decimal('0.00'))
    casa2_value: Decimal = field(default_factory=lambda: Decimal('0.00'))
    percentage: Optional[Decimal] = None
    category: ExpenseCategory = ExpenseCategory.OTHER
    date_added: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    paid_by: str = ""
    notes: str = ""
    receipt_path: str = ""
    is_recurring: bool = False
    recurrence_months: int = 1
    
    def __post_init__(self):
        """Convert input values to Decimal."""
        self.amount = self._to_decimal(self.amount)
        self.casa1_value = self._to_decimal(self.casa1_value)
        self.casa2_value = self._to_decimal(self.casa2_value)
        if self.percentage is not None:
            self.percentage = self._to_decimal(self.percentage)
        
        # Convert string enums
        if isinstance(self.split_method, str):
            self.split_method = SplitMethod(self.split_method)
        if isinstance(self.category, str):
            self.category = ExpenseCategory(self.category)
    
    @staticmethod
    def _to_decimal(value: Union[int, float, str, Decimal]) -> Decimal:
        """Convert value to Decimal safely."""
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            return Decimal('0.00')
    
    def calculate_split(self, default_casa2_percentage: Decimal = None) -> tuple[Decimal, Decimal]:
        """
        Calculate expense split based on method.
        
        Args:
            default_casa2_percentage: Default percentage if not specified
            
        Returns:
            Tuple of (casa1_amount, casa2_amount)
        """
        if self.split_method == SplitMethod.FIXED:
            return self.casa1_value, self.casa2_value
        
        elif self.split_method == SplitMethod.EQUAL:
            half = (self.amount / 2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            return half, self.amount - half
        
        else:  # PERCENTAGE
            if self.percentage is not None:
                casa2_percent = self.percentage
            elif default_casa2_percentage is not None:
                casa2_percent = default_casa2_percentage
            else:
                casa2_percent = Decimal('50.00')
            
            casa2_amount = (self.amount * casa2_percent / 100).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            casa1_amount = self.amount - casa2_amount
            
            return casa1_amount, casa2_amount
    
    @property
    def is_overdue(self) -> bool:
        """Check if expense is overdue."""
        if self.due_date is None:
            return False
        return datetime.now() > self.due_date
    
    @property
    def days_until_due(self) -> Optional[int]:
        """Calculate days until due date."""
        if self.due_date is None:
            return None
        delta = self.due_date - datetime.now()
        return delta.days
    
    def validate(self) -> List[str]:
        """Validate occasional expense data."""
        errors = []
        
        if not self.description.strip():
            errors.append("Description is required")
        
        if self.amount <= 0:
            errors.append("Amount must be greater than zero")
        
        if self.split_method == SplitMethod.FIXED:
            total_fixed = self.casa1_value + self.casa2_value
            if abs(total_fixed - self.amount) > Decimal('0.01'):
                errors.append("Sum of fixed values must equal total amount")
        
        if self.percentage is not None and not 0 <= self.percentage <= 100:
            errors.append("Percentage must be between 0 and 100")
        
        if self.recurrence_months < 1:
            errors.append("Recurrence months must be at least 1")
        
        # Check for unrealistic values
        if self.amount > 100000:
            errors.append("Amount seems unrealistically high")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'description': self.description,
            'amount': str(self.amount),
            'split_method': self.split_method.value,
            'casa1_value': str(self.casa1_value),
            'casa2_value': str(self.casa2_value),
            'percentage': str(self.percentage) if self.percentage else None,
            'category': self.category.value,
            'date_added': self.date_added.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_by': self.paid_by,
            'notes': self.notes,
            'receipt_path': self.receipt_path,
            'is_recurring': self.is_recurring,
            'recurrence_months': self.recurrence_months
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OccasionalExpense':
        """Create from dictionary."""
        obj = cls()
        obj.id = data.get('id', str(uuid.uuid4()))
        obj.description = data.get('description', '')
        obj.amount = cls._to_decimal(data.get('amount', 0))
        obj.split_method = SplitMethod(data.get('split_method', 'percentage'))
        obj.casa1_value = cls._to_decimal(data.get('casa1_value', 0))
        obj.casa2_value = cls._to_decimal(data.get('casa2_value', 0))
        
        if data.get('percentage'):
            obj.percentage = cls._to_decimal(data['percentage'])
        
        obj.category = ExpenseCategory(data.get('category', 'other'))
        obj.date_added = datetime.fromisoformat(data.get('date_added', datetime.now().isoformat()))
        
        if data.get('due_date'):
            obj.due_date = datetime.fromisoformat(data['due_date'])
        
        obj.paid_by = data.get('paid_by', '')
        obj.notes = data.get('notes', '')
        obj.receipt_path = data.get('receipt_path', '')
        obj.is_recurring = data.get('is_recurring', False)
        obj.recurrence_months = data.get('recurrence_months', 1)
        
        return obj


@dataclass
class Payment:
    """
    Payment information for a month.
    
    Attributes:
        casa1_paid: Amount paid by Casa 1
        casa2_paid: Amount paid by Casa 2
        payment_date: When payment was made
        payment_method: How payment was made
        transaction_id: Transaction reference
        notes: Additional notes
        attachments: List of attachment file paths
    """
    casa1_paid: Decimal = field(default_factory=lambda: Decimal('0.00'))
    casa2_paid: Decimal = field(default_factory=lambda: Decimal('0.00'))
    payment_date: datetime = field(default_factory=datetime.now)
    payment_method: PaymentMethod = PaymentMethod.PIX
    transaction_id: str = ""
    notes: str = ""
    attachments: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Convert input values to Decimal."""
        self.casa1_paid = self._to_decimal(self.casa1_paid)
        self.casa2_paid = self._to_decimal(self.casa2_paid)
        
        # Convert string enum
        if isinstance(self.payment_method, str):
            self.payment_method = PaymentMethod(self.payment_method)
    
    @staticmethod
    def _to_decimal(value: Union[int, float, str, Decimal]) -> Decimal:
        """Convert value to Decimal safely."""
        if isinstance(value, Decimal):
            return value
        try:
            return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except:
            return Decimal('0.00')
    
    @property
    def total_paid(self) -> Decimal:
        """Calculate total amount paid."""
        return self.casa1_paid + self.casa2_paid
    
    def validate(self) -> List[str]:
        """Validate payment data."""
        errors = []
        
        if self.casa1_paid < 0:
            errors.append("Casa 1 payment cannot be negative")
        
        if self.casa2_paid < 0:
            errors.append("Casa 2 payment cannot be negative")
        
        if self.total_paid == 0:
            errors.append("At least one payment must be greater than zero")
        
        # Check for unrealistic values
        if self.casa1_paid > 100000:
            errors.append("Casa 1 payment seems unrealistically high")
        
        if self.casa2_paid > 100000:
            errors.append("Casa 2 payment seems unrealistically high")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'casa1_paid': str(self.casa1_paid),
            'casa2_paid': str(self.casa2_paid),
            'payment_date': self.payment_date.isoformat(),
            'payment_method': self.payment_method.value,
            'transaction_id': self.transaction_id,
            'notes': self.notes,
            'attachments': self.attachments
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Payment':
        """Create from dictionary."""
        obj = cls()
        obj.casa1_paid = cls._to_decimal(data.get('casa1_paid', 0))
        obj.casa2_paid = cls._to_decimal(data.get('casa2_paid', 0))
        obj.payment_date = datetime.fromisoformat(data.get('payment_date', datetime.now().isoformat()))
        obj.payment_method = PaymentMethod(data.get('payment_method', 'pix'))
        obj.transaction_id = data.get('transaction_id', '')
        obj.notes = data.get('notes', '')
        obj.attachments = data.get('attachments', [])
        return obj


@dataclass
class MonthData:
    """
    Complete month expense data.
    
    Attributes:
        id: Unique identifier
        year: Year
        month: Month name
        electricity: Electricity data
        recurring_bills: Recurring bills data
        occasional_expenses: List of occasional expenses
        payments: Payment information
        notes: General notes
        reminders: List of reminders
        tags: List of tags for categorization
        created_at: Creation timestamp
        modified_at: Last modification timestamp
        is_locked: Whether month is locked for editing
        calculation_cache: Cached calculation results
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    year: int = field(default_factory=lambda: datetime.now().year)
    month: str = ""
    electricity: ElectricityData = field(default_factory=ElectricityData)
    recurring_bills: RecurringBills = field(default_factory=RecurringBills)
    occasional_expenses: List[OccasionalExpense] = field(default_factory=list)
    payments: Payment = field(default_factory=Payment)
    notes: str = ""
    reminders: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    is_locked: bool = False
    calculation_cache: Optional[Dict] = None
    
    def __post_init__(self):
        """Initialize nested objects if they are dicts."""
        if isinstance(self.electricity, dict):
            self.electricity = ElectricityData.from_dict(self.electricity)
        
        if isinstance(self.recurring_bills, dict):
            self.recurring_bills = RecurringBills.from_dict(self.recurring_bills)
        
        if isinstance(self.payments, dict):
            self.payments = Payment.from_dict(self.payments)
        
        # Convert occasional expenses
        converted_expenses = []
        for expense in self.occasional_expenses:
            if isinstance(expense, dict):
                converted_expenses.append(OccasionalExpense.from_dict(expense))
            else:
                converted_expenses.append(expense)
        self.occasional_expenses = converted_expenses
    
    @property
    def total_occasional_amount(self) -> Decimal:
        """Calculate total occasional expenses amount."""
        return sum(expense.amount for expense in self.occasional_expenses)
    
    @property
    def has_overdue_expenses(self) -> bool:
        """Check if month has overdue expenses."""
        return any(expense.is_overdue for expense in self.occasional_expenses)
    
    @property
    def overdue_expenses(self) -> List[OccasionalExpense]:
        """Get list of overdue expenses."""
        return [expense for expense in self.occasional_expenses if expense.is_overdue]
    
    def add_occasional_expense(self, expense: OccasionalExpense):
        """Add an occasional expense."""
        self.occasional_expenses.append(expense)
        self.modified_at = datetime.now()
        self.calculation_cache = None  # Invalidate cache
    
    def remove_occasional_expense(self, expense_id: str) -> bool:
        """Remove an occasional expense by ID."""
        for i, expense in enumerate(self.occasional_expenses):
            if expense.id == expense_id:
                del self.occasional_expenses[i]
                self.modified_at = datetime.now()
                self.calculation_cache = None  # Invalidate cache
                return True
        return False
    
    def get_expense_by_id(self, expense_id: str) -> Optional[OccasionalExpense]:
        """Get occasional expense by ID."""
        for expense in self.occasional_expenses:
            if expense.id == expense_id:
                return expense
        return None
    
    def get_expenses_by_category(self, category: ExpenseCategory) -> List[OccasionalExpense]:
        """Get expenses by category."""
        return [expense for expense in self.occasional_expenses if expense.category == category]
    
    def validate(self) -> List[str]:
        """Validate all month data."""
        errors = []
        
        # Validate year and month
        if not 2000 <= self.year <= 2100:
            errors.append("Year must be between 2000 and 2100")
        
        if not self.month:
            errors.append("Month name is required")
        
        # Validate nested objects
        errors.extend(self.electricity.validate())
        errors.extend(self.recurring_bills.validate())
        errors.extend(self.payments.validate())
        
        # Validate occasional expenses
        for i, expense in enumerate(self.occasional_expenses):
            expense_errors = expense.validate()
            for error in expense_errors:
                errors.append(f"Expense {i+1}: {error}")
        
        # Business logic validation
        if self.is_locked and self.modified_at > self.created_at:
            errors.append("Cannot modify locked month data")
        
        return errors
    
    def invalidate_cache(self):
        """Invalidate calculation cache."""
        self.calculation_cache = None
        self.modified_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'year': self.year,
            'month': self.month,
            'electricity': self.electricity.to_dict(),
            'recurring_bills': self.recurring_bills.to_dict(),
            'occasional_expenses': [expense.to_dict() for expense in self.occasional_expenses],
            'payments': self.payments.to_dict(),
            'notes': self.notes,
            'reminders': self.reminders,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat(),
            'is_locked': self.is_locked,
            'calculation_cache': self.calculation_cache
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonthData':
        """Create from dictionary."""
        obj = cls()
        obj.id = data.get('id', str(uuid.uuid4()))
        obj.year = data.get('year', datetime.now().year)
        obj.month = data.get('month', '')
        
        # Handle nested objects
        if 'electricity' in data:
            obj.electricity = ElectricityData.from_dict(data['electricity'])
        
        if 'recurring_bills' in data:
            obj.recurring_bills = RecurringBills.from_dict(data['recurring_bills'])
        
        if 'payments' in data:
            obj.payments = Payment.from_dict(data['payments'])
        
        # Handle occasional expenses
        if 'occasional_expenses' in data:
            obj.occasional_expenses = [
                OccasionalExpense.from_dict(expense_data) 
                for expense_data in data['occasional_expenses']
            ]
        
        obj.notes = data.get('notes', '')
        obj.reminders = data.get('reminders', [])
        obj.tags = data.get('tags', [])
        
        if 'created_at' in data:
            obj.created_at = datetime.fromisoformat(data['created_at'])
        
        if 'modified_at' in data:
            obj.modified_at = datetime.fromisoformat(data['modified_at'])
        
        obj.is_locked = data.get('is_locked', False)
        obj.calculation_cache = data.get('calculation_cache')
        
        return obj


@dataclass
class CalculationResult:
    """
    Result of expense calculations for a month.
    
    Attributes:
        id: Unique identifier
        month_data_id: ID of associated month data
        electricity: Electricity calculation results
        recurring: Recurring bills calculation results
        occasional: Occasional expenses calculation results
        totals: Total amounts
        balances: Balance calculations
        breakdown: Detailed breakdown
        metadata: Calculation metadata
        calculated_at: When calculation was performed
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    month_data_id: str = ""
    electricity: Dict[str, Decimal] = field(default_factory=dict)
    recurring: Dict[str, Decimal] = field(default_factory=dict)
    occasional: List[Dict[str, Decimal]] = field(default_factory=list)
    totals: Dict[str, Decimal] = field(default_factory=dict)
    balances: Dict[str, Decimal] = field(default_factory=dict)
    breakdown: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    calculated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_expenses(self) -> Decimal:
        """Get total expenses amount."""
        return self.totals.get('total_expenses', Decimal('0.00'))
    
    @property
    def casa1_should_pay(self) -> Decimal:
        """Get Casa 1 obligation amount."""
        return self.totals.get('casa1_should_pay', Decimal('0.00'))
    
    @property
    def casa2_should_pay(self) -> Decimal:
        """Get Casa 2 obligation amount."""
        return self.totals.get('casa2_should_pay', Decimal('0.00'))
    
    @property
    def month_balance(self) -> Decimal:
        """Get month balance."""
        return self.balances.get('month_balance', Decimal('0.00'))
    
    @property
    def previous_balance(self) -> Decimal:
        """Get previous balance."""
        return self.balances.get('previous_balance', Decimal('0.00'))
    
    @property
    def final_house1(self) -> Decimal:
        """Get Casa 1 final amount."""
        return self.balances.get('final_house1', Decimal('0.00'))
    
    @property
    def final_house2(self) -> Decimal:
        """Get Casa 2 final amount."""
        return self.balances.get('final_house2', Decimal('0.00'))
    
    def get_breakdown_by_type(self, breakdown_type: str) -> List[Dict[str, Any]]:
        """Get breakdown items by type."""
        return [item for item in self.breakdown if item.get('type') == breakdown_type]
    
    def get_expense_breakdown(self) -> List[Dict[str, Any]]:
        """Get expense breakdown items."""
        return self.get_breakdown_by_type('expense')
    
    def get_payment_breakdown(self) -> List[Dict[str, Any]]:
        """Get payment breakdown items."""
        return self.get_breakdown_by_type('payment')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        def convert_decimal(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal(item) for item in obj]
            else:
                return obj
        
        return {
            'id': self.id,
            'month_data_id': self.month_data_id,
            'electricity': convert_decimal(self.electricity),
            'recurring': convert_decimal(self.recurring),
            'occasional': convert_decimal(self.occasional),
            'totals': convert_decimal(self.totals),
            'balances': convert_decimal(self.balances),
            'breakdown': convert_decimal(self.breakdown),
            'metadata': self.metadata,
            'calculated_at': self.calculated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationResult':
        """Create from dictionary."""
        def convert_to_decimal(obj):
            if isinstance(obj, str):
                try:
                    return Decimal(obj)
                except:
                    return obj
            elif isinstance(obj, dict):
                return {k: convert_to_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_decimal(item) for item in obj]
            else:
                return obj
        
        obj = cls()
        obj.id = data.get('id', str(uuid.uuid4()))
        obj.month_data_id = data.get('month_data_id', '')
        obj.electricity = convert_to_decimal(data.get('electricity', {}))
        obj.recurring = convert_to_decimal(data.get('recurring', {}))
        obj.occasional = convert_to_decimal(data.get('occasional', []))
        obj.totals = convert_to_decimal(data.get('totals', {}))
        obj.balances = convert_to_decimal(data.get('balances', {}))
        obj.breakdown = convert_to_decimal(data.get('breakdown', []))
        obj.metadata = data.get('metadata', {})
        
        if 'calculated_at' in data:
            obj.calculated_at = datetime.fromisoformat(data['calculated_at'])
        
        return obj