import argparse
from pathlib import Path
from .models import Transaction
from .repository import TransactionRepository

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budget_app")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--date", type=str, required=True)
    add_parser.add_argument("--type", type=str, required=True)
    add_parser.add_argument("--category", type=str, required=True)
    add_parser.add_argument("--amount", type=int, required=True)
    add_parser.add_argument("--memo", type=str, default="")

    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "add":
        repo = TransactionRepository(Path("data/transactions.jsonl"))
        new_id = repo.next_id()
        transaction = Transaction(id=new_id, 
            date=args.date,
            type=args.type, 
            category=args.category, 
            amount=args.amount, 
            memo=args.memo,
        )
        repo.add(transaction)
        print(f"거래가 추가되었습니다: {new_id}")

