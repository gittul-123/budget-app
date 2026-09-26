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