import json
from pathlib import Path
from typing import Iterator
from .models import Transaction
from dataclasses import asdict


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

    def delete(self, id:str) -> bool:
        remaining = []
        found = False
        for transaction in self.iter_all():
            if transaction.id == id:
                found = True
                continue
            remaining.append(transaction)

        self.write_all(remaining)
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
