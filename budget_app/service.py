import csv
from datetime import datetime
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
            "has_data": has_data,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "category_totals": category_totals,
        }

    def export_csv(self, path, date_from: Optional[str] = None, date_to: Optional[str] = None) -> int:
        transactions = list(self.search(date_from=date_from, date_to=date_to))
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "type", "category", "amount", "memo", "tags"])
            writer.writeheader()
            for t in transactions:
                writer.writerow({
                    "date": t.date,
                    "type": t.type,
                    "category": t.category,
                    "amount": t.amount,
                    "memo": t.memo,
                    "tags": ",".join(t.tags),
                })
        return len(transactions)

    def import_csv(self, path, cat_repo) -> dict:
        success = 0
        failed = 0

        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date = row["date"]
                    datetime.strptime(date, "%Y-%m-%d")

                    type_ = row["type"]
                    if type_ not in ["income", "expense"]:
                        raise ValueError("invalid type")

                    category = row["category"]
                    if not cat_repo.exists(category):
                        raise ValueError("invalid category")

                    amount = int(row["amount"])
                    if amount <= 0:
                        raise ValueError("invalid amount")

                    tags_str = row.get("tags", "") or ""
                    tags = [t.strip() for t in tags_str.split(",")] if tags_str.strip() else []

                    new_id = self.repo.next_id()
                    transaction = Transaction(id=new_id, date=date, type=type_, category=category, amount=amount, memo=row.get("memo", ""), tags=tags)
                    self.repo.add(transaction)
                    success += 1
                except (ValueError, KeyError):
                    failed += 1

        return {"success": success, "failed": failed}
