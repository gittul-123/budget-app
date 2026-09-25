import json
from pathlib import Path
from typing import Iterator
from .models import Transaction

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