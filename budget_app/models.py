from dataclasses import dataclass, field
from typing import List

@dataclass
class Transaction:
    id: str
    date: str
    type: str
    category: str
    amount: int
    memo: str = ""
    tags: List[str] = field(default_factory=list)