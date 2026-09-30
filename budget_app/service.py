from typing import Iterator, Optional
from .repository import TransactionRepository
from .models import Transaction

class TransactionService:
    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    def search(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        category: Optional[str] = None,
        type_: Optional[str] = None,
        q: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> Iterator[Transaction]:
        for transaction in self.repo.iter_all():
            if date_from and transaction.date < date_from:
                continue
            if date_to and transaction.date > date_to:
                continue
            if category and transaction.category != category:
                continue
            if type_ and transaction.type != type_:
                continue
            if q and q not in transaction.memo:
                continue
            if tag and tag not in transaction.tags:
                continue

            yield transaction
    
    def summary(self, month: str) -> dict:
        total_income = 0
        total_expense = 0
        category_totals = {}
        has_data = False

        for transaction in self.repo.iter_all():
            if transaction.date[:7] != month:
                continue

            has_data = True

            if transaction.type == "income":
                total_income += transaction.amount
            else:
                total_expense += transaction.amount
                category_totals[transaction.category] = category_totals.get(transaction.category, 0) + transaction.amount
            
        return {
            "has_data" : has_data,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "category_totals": category_totals,           
        }