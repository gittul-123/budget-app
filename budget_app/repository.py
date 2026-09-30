import json
from pathlib import Path
from typing import Iterator
from .models import Transaction
from dataclasses import asdict, replace


class TransactionRepository:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def iter_all(self) -> Iterator[Transaction]:
        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                transaction = Transaction(**data)
                yield transaction

    def add(self, transaction: Transaction) -> None:
        with open(self.file_path, "a", encoding="utf-8") as f:
            data = asdict(transaction)
            line = json.dumps(data, ensure_ascii=False)
            f.write(line + "\n")

    def next_id(self) -> str:
        count = sum(1 for _ in self.iter_all())
        return f"TX-{count + 1:06d}"

    def write_all(self, transactions) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            for transaction in transactions:
                data = asdict(transaction)
                line = json.dumps(data, ensure_ascii=False)
                f.write(line + "\n")

    def delete(self, id: str) -> bool:
        remaining = []
        found = False
        for transaction in self.iter_all():
            if transaction.id == id:
                found = True
                continue
            remaining.append(transaction)

        self.write_all(remaining)
        return found

    def update(self, id: str, **changes) -> bool:
        changes = {k: v for k, v in changes.items() if v is not None}

        updated = []
        found = False
        for transaction in self.iter_all():
            if transaction.id == id:
                found = True
                transaction = replace(transaction, **changes)
            updated.append(transaction)

        self.write_all(updated)
        return found


class CategoryRepository:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def iter_all(self) -> Iterator[str]:
        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                name = data["name"]
                yield name

    def add(self, name: str) -> None:
        with open(self.file_path, "a", encoding="utf-8") as f:
            data = {"name": name}
            line = json.dumps(data, ensure_ascii=False)
            f.write(line + "\n")

    def exists(self, name: str) -> bool:
        return name in self.iter_all()

    def ensure_default(self, defaults: list[str]) -> None:
        has_any = any(True for _ in self.iter_all())
        if has_any:
            return
        for name in defaults:
            self.add(name)


class BudgetRepository:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def iter_all(self) -> Iterator[dict]:
        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                yield data

    def get(self, month: str) -> int | None:
        for entry in self.iter_all():
            if entry["month"] == month:
                return entry["amount"]
        return None

    def set(self, month: str, amount: int) -> None:
        remaining = [entry for entry in self.iter_all() if entry["month"] != month]
        remaining.append({"month": month, "amount": amount})

        with open(self.file_path, "w", encoding="utf-8") as f:
            for entry in remaining:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")