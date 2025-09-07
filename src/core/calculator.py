"""
Expense calculation engine for splitting costs between houses.
"""

from typing import Dict, List, Tuple, Optional
from decimal import Decimal, ROUND_HALF_UP
import logging
from datetime import datetime

from ..models.expense_models import MonthData, CalculationResult

logger = logging.getLogger(__name__)


class ExpenseCalculator:
    """
    Core calculation engine for expense splitting and balance tracking.
    """
    
    def __init__(self, precision: int = 2):
        """
        Initialize calculator with precision settings.
        
        Args:
            precision: Number of decimal places for calculations
        """
        self.precision = precision
        self._decimal_context = f"0.{'0' * precision}"
    
    def calculate_month(
        self, 
        month_data: MonthData, 
        previous_balance: Decimal = Decimal('0.0')
    ) -> CalculationResult:
        """
        Calculate complete month expense breakdown.
        
        Args:
            month_data: Month data to calculate
            previous_balance: Carried balance from previous month
            
        Returns:
            CalculationResult with all calculations
            
        Raises:
            ValueError: If data validation fails
        """
        try:
            # Validate input data
            validation_errors = month_data.validate()
            if validation_errors:
                raise ValueError(f"Data validation failed: {', '.join(validation_errors)}")
            
            result = CalculationResult(previous_balance=previous_balance)
            
            # Calculate electricity split
            result.electricity = self._calculate_electricity(month_data.electricity)
            
            # Calculate recurring bills split
            result.recurring = self._calculate_recurring_bills(month_data.recurring_bills)
            
            # Calculate occasional expenses split
            result.occasional = self._calculate_occasional_expenses(
                month_data.occasional_expenses,
                month_data.recurring_bills.casa2_percentage
            )
            
            # Calculate totals
            self._calculate_totals(result, month_data)
            
            # Calculate balances
            self._calculate_balances(result, month_data.payments)
            
            # Generate breakdown
            result.breakdown = self._generate_breakdown(result, month_data)
            
            logger.info(f"Month calculation completed. Total expenses: {result.total_expenses}")
            return result
            
        except Exception as e:
            logger.error(f"Calculation failed: {str(e)}")
            raise
    
    def _calculate_electricity(self, electricity_data) -> Dict[str, Decimal]:
        """Calculate electricity cost split based on consumption."""
        if electricity_data.total_kwh == 0:
            return {
                'casa1': Decimal('0.00'),
                'casa2': Decimal('0.00'),
                'total': Decimal('0.00')
            }
        
        total_kwh = Decimal(str(electricity_data.total_kwh))
        casa2_kwh = Decimal(str(electricity_data.casa2_kwh))
        casa1_kwh = total_kwh - casa2_kwh
        total_bill = Decimal(str(electricity_data.total_bill))
        
        # Proportional split based on consumption
        casa1_percentage = casa1_kwh / total_kwh
        casa2_percentage = casa2_kwh / total_kwh
        
        casa1_value = (total_bill * casa1_percentage).quantize(
            Decimal(self._decimal_context), rounding=ROUND_HALF_UP
        )
        casa2_value = total_bill - casa1_value  # Ensure exact total
        
        return {
            'casa1': casa1_value,
            'casa2': casa2_value,
            'total': total_bill,
            'casa1_kwh': casa1_kwh,
            'casa2_kwh': casa2_kwh,
            'casa1_percentage': float(casa1_percentage * 100),
            'casa2_percentage': float(casa2_percentage * 100)
        }
    
    def _calculate_recurring_bills(self, recurring_bills) -> Dict[str, Decimal]:
        """Calculate recurring bills split based on percentage."""
        results = {}
        
        casa2_percentage = Decimal(str(recurring_bills.casa2_percentage)) / Decimal('100')
        casa1_percentage = Decimal('1') - casa2_percentage
        
        # Water
        if recurring_bills.water > 0:
            water_total = Decimal(str(recurring_bills.water))
            water_casa2 = (water_total * casa2_percentage).quantize(
                Decimal(self._decimal_context), rounding=ROUND_HALF_UP
            )
            water_casa1 = water_total - water_casa2
            
            results.update({
                'water_casa1': water_casa1,
                'water_casa2': water_casa2,
                'water_total': water_total
            })
        
        # Internet
        if recurring_bills.internet > 0:
            internet_total = Decimal(str(recurring_bills.internet))
            internet_casa2 = (internet_total * casa2_percentage).quantize(
                Decimal(self._decimal_context), rounding=ROUND_HALF_UP
            )
            internet_casa1 = internet_total - internet_casa2
            
            results.update({
                'internet_casa1': internet_casa1,
                'internet_casa2': internet_casa2,
                'internet_total': internet_total
            })
        
        return results
    
    def _calculate_occasional_expenses(
        self, 
        expenses: List, 
        default_casa2_percentage: float
    ) -> List[Dict]:
        """Calculate occasional expenses split."""
        results = []
        
        for expense in expenses:
            if expense.split_method == "fixed":
                casa1_value = Decimal(str(expense.casa1_value))
                casa2_value = Decimal(str(expense.casa2_value))
            else:  # percentage split
                total_amount = Decimal(str(expense.amount))
                casa2_percentage = Decimal(str(default_casa2_percentage)) / Decimal('100')
                
                casa2_value = (total_amount * casa2_percentage).quantize(
                    Decimal(self._decimal_context), rounding=ROUND_HALF_UP
                )
                casa1_value = total_amount - casa2_value
            
            results.append({
                'description': expense.description,
                'total': Decimal(str(expense.amount)),
                'casa1': casa1_value,
                'casa2': casa2_value,
                'method': expense.split_method,
                'category': expense.category
            })
        
        return results
    
    def _calculate_totals(self, result: CalculationResult, month_data: MonthData):
        """Calculate total amounts owed by each house."""
        # Sum electricity
        casa1_total = result.electricity.get('casa1', Decimal('0'))
        casa2_total = result.electricity.get('casa2', Decimal('0'))
        
        # Sum recurring bills
        casa1_total += result.recurring.get('water_casa1', Decimal('0'))
        casa1_total += result.recurring.get('internet_casa1', Decimal('0'))
        casa2_total += result.recurring.get('water_casa2', Decimal('0'))
        casa2_total += result.recurring.get('internet_casa2', Decimal('0'))
        
        # Sum occasional expenses
        for expense in result.occasional:
            casa1_total += expense['casa1']
            casa2_total += expense['casa2']
        
        result.casa1_should_pay = casa1_total
        result.casa2_should_pay = casa2_total
        result.total_expenses = casa1_total + casa2_total
    
    def _calculate_balances(self, result: CalculationResult, payments):
        """Calculate month and final balances."""
        casa1_paid = Decimal(str(payments.casa1_paid))
        casa2_paid = Decimal(str(payments.casa2_paid))
        
        # Calculate what each house owes after payments
        casa1_balance = result.casa1_should_pay - casa1_paid
        casa2_balance = result.casa2_should_pay - casa2_paid
        
        # Month balance = how much Casa 2 owes relative to Casa 1
        # Positive means Casa 2 owes money, negative means Casa 2 has credit
        result.month_balance = casa2_balance - casa1_balance
        
        # Final balances including previous balance
        result.final_house1 = casa1_balance - result.previous_balance
        result.final_house2 = casa2_balance + result.previous_balance
    
    def _generate_breakdown(
        self, 
        result: CalculationResult, 
        month_data: MonthData
    ) -> List[Dict]:
        """Generate detailed breakdown for display."""
        breakdown = []
        
        # Electricity
        if result.electricity.get('total', Decimal('0')) > 0:
            breakdown.append({
                'type': 'expense',
                'description': 'Energia Elétrica',
                'casa1': result.electricity['casa1'],
                'casa2': result.electricity['casa2'],
                'total': result.electricity['total'],
                'details': {
                    'casa1_kwh': result.electricity.get('casa1_kwh', 0),
                    'casa2_kwh': result.electricity.get('casa2_kwh', 0),
                    'casa1_percentage': result.electricity.get('casa1_percentage', 0),
                    'casa2_percentage': result.electricity.get('casa2_percentage', 0)
                }
            })
        
        # Water
        if 'water_total' in result.recurring:
            breakdown.append({
                'type': 'expense',
                'description': 'Água',
                'casa1': result.recurring['water_casa1'],
                'casa2': result.recurring['water_casa2'],
                'total': result.recurring['water_total']
            })
        
        # Internet
        if 'internet_total' in result.recurring:
            breakdown.append({
                'type': 'expense',
                'description': 'Internet',
                'casa1': result.recurring['internet_casa1'],
                'casa2': result.recurring['internet_casa2'],
                'total': result.recurring['internet_total']
            })
        
        # Occasional expenses
        for expense in result.occasional:
            breakdown.append({
                'type': 'expense',
                'description': expense['description'],
                'casa1': expense['casa1'],
                'casa2': expense['casa2'],
                'total': expense['total'],
                'category': expense.get('category', ''),
                'method': expense.get('method', 'percentage')
            })
        
        # Total obligations
        breakdown.append({
            'type': 'total',
            'description': 'TOTAL OBRIGAÇÕES',
            'casa1': result.casa1_should_pay,
            'casa2': result.casa2_should_pay,
            'total': result.total_expenses
        })
        
        # Payments made
        breakdown.append({
            'type': 'payment',
            'description': 'PAGAMENTOS REALIZADOS',
            'casa1': Decimal(str(month_data.payments.casa1_paid)),
            'casa2': Decimal(str(month_data.payments.casa2_paid)),
            'total': Decimal(str(month_data.payments.casa1_paid + month_data.payments.casa2_paid))
        })
        
        # Month balance
        breakdown.append({
            'type': 'balance',
            'description': 'SALDO DO MÊS',
            'casa1': result.casa1_should_pay - Decimal(str(month_data.payments.casa1_paid)),
            'casa2': result.casa2_should_pay - Decimal(str(month_data.payments.casa2_paid)),
            'total': result.month_balance
        })
        
        return breakdown
    
    def calculate_annual_summary(self, year_data: Dict) -> Dict:
        """Calculate annual statistics and trends."""
        summary = {
            'total_months': 0,
            'total_expenses': Decimal('0'),
            'total_casa1': Decimal('0'),
            'total_casa2': Decimal('0'),
            'total_paid_casa1': Decimal('0'),
            'total_paid_casa2': Decimal('0'),
            'final_balance': Decimal('0'),
            'monthly_averages': {},
            'trends': {},
            'months': []
        }
        
        monthly_expenses = []
        cumulative_balance = Decimal('0')
        
        months_order = [
            "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        
        for month in months_order:
            if month not in year_data:
                continue
                
            month_data = year_data[month]
            results = month_data.get('results', {})
            
            total_expenses = Decimal(str(results.get('total_expenses', 0)))
            casa1_should = Decimal(str(results.get('casa1_should_pay', 0)))
            casa2_should = Decimal(str(results.get('casa2_should_pay', 0)))
            month_balance = Decimal(str(results.get('month_balance', 0)))
            
            payments = month_data.get('payments', {})
            casa1_paid = Decimal(str(payments.get('casa1_paid', 0)))
            casa2_paid = Decimal(str(payments.get('casa2_paid', 0)))
            
            cumulative_balance += month_balance
            monthly_expenses.append(float(total_expenses))
            
            month_summary = {
                'month': month,
                'total_expenses': total_expenses,
                'casa1_should': casa1_should,
                'casa2_should': casa2_should,
                'casa1_paid': casa1_paid,
                'casa2_paid': casa2_paid,
                'balance': month_balance,
                'cumulative_balance': cumulative_balance
            }
            
            summary['months'].append(month_summary)
            summary['total_expenses'] += total_expenses
            summary['total_casa1'] += casa1_should
            summary['total_casa2'] += casa2_should
            summary['total_paid_casa1'] += casa1_paid
            summary['total_paid_casa2'] += casa2_paid
            summary['total_months'] += 1
        
        # Calculate averages
        if summary['total_months'] > 0:
            summary['monthly_averages'] = {
                'expenses': summary['total_expenses'] / summary['total_months'],
                'casa1': summary['total_casa1'] / summary['total_months'],
                'casa2': summary['total_casa2'] / summary['total_months']
            }
        
        # Calculate trends
        if len(monthly_expenses) >= 2:
            summary['trends'] = self._calculate_trends(monthly_expenses)
        
        summary['final_balance'] = cumulative_balance
        
        return summary
    
    def _calculate_trends(self, monthly_expenses: List[float]) -> Dict:
        """Calculate expense trends."""
        if len(monthly_expenses) < 2:
            return {}
        
        # Simple linear trend
        n = len(monthly_expenses)
        x_sum = sum(range(n))
        y_sum = sum(monthly_expenses)
        xy_sum = sum(i * monthly_expenses[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        return {
            'direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
            'slope': slope,
            'average': sum(monthly_expenses) / len(monthly_expenses),
            'highest': max(monthly_expenses),
            'lowest': min(monthly_expenses),
            'volatility': self._calculate_volatility(monthly_expenses)
        }
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate coefficient of variation as volatility measure."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        std_dev = variance ** 0.5
        
        return std_dev / mean if mean != 0 else 0.0
    
    def project_next_month(
        self, 
        historical_data: List[Dict], 
        current_balance: Decimal
    ) -> Dict:
        """Project expenses for next month based on historical data."""
        if not historical_data:
            return {
                'estimated_total': Decimal('0'),
                'estimated_casa1': Decimal('0'),
                'estimated_casa2': Decimal('0'),
                'confidence': 0.0,
                'basis': 'no_data'
            }
        
        # Use weighted average of last 3 months (more recent = higher weight)
        weights = [0.5, 0.3, 0.2]  # Most recent gets 50%
        weighted_total = Decimal('0')
        weighted_casa1 = Decimal('0')
        weighted_casa2 = Decimal('0')
        total_weight = Decimal('0')
        
        for i, month_data in enumerate(historical_data[-3:]):
            weight = Decimal(str(weights[min(i, 2)]))
            results = month_data.get('results', {})
            
            weighted_total += Decimal(str(results.get('total_expenses', 0))) * weight
            weighted_casa1 += Decimal(str(results.get('casa1_should_pay', 0))) * weight
            weighted_casa2 += Decimal(str(results.get('casa2_should_pay', 0))) * weight
            total_weight += weight
        
        if total_weight > 0:
            estimated_total = weighted_total / total_weight
            estimated_casa1 = weighted_casa1 / total_weight
            estimated_casa2 = weighted_casa2 / total_weight
        else:
            estimated_total = estimated_casa1 = estimated_casa2 = Decimal('0')
        
        # Calculate confidence based on historical volatility
        recent_totals = [
            float(month.get('results', {}).get('total_expenses', 0)) 
            for month in historical_data[-6:]
        ]
        volatility = self._calculate_volatility(recent_totals)
        confidence = max(0.0, min(1.0, 1.0 - volatility))
        
        return {
            'estimated_total': estimated_total,
            'estimated_casa1': estimated_casa1,
            'estimated_casa2': estimated_casa2,
            'estimated_casa1_with_balance': estimated_casa1 - current_balance,
            'estimated_casa2_with_balance': estimated_casa2 + current_balance,
            'confidence': confidence,
            'basis': f'last_{len(historical_data[-3:])}months',
            'volatility': volatility
        }