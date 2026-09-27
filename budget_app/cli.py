import argparse
from pathlib import Path
from .models import Transaction
from .repository import TransactionRepository
from itertools import islice
from datetime import datetime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budget_app")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add")
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--limit", type=int, default=10)

    return parser

def prompt_date() -> str:
    while True:
        text = input("날짜(YYYY-MM-DD): ")
        try:
            datetime.strptime(text, '%Y-%m-%d')
            return text
        except ValueError:
            print("[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).")
            print("[힌트] 예: 2024-01-15")

def prompt_type() -> str:
    while True:
        text = input("타입(income/expense): ")
        if text in ["income", "expense"]:
            return text
        print("[오류] type은 income 또는 expense만 가능합니다.")

def prompt_amount() -> int:
    while True:
        text = input("금액(양수): ")
        try:
            amount = int(text)
            if amount >0:
                return amount
            print("[오류] 금액은 양수여야 합니다.")
        except ValueError:
            print("[오류] 숫자로 입력해주세요.")

def prompt_memo() -> str:
    return input("메모(선택): ")

def prompt_tags() -> list[str]:
    text = input("태그(쉼표로 구분, 없으면 엔터): ")
    if text.strip() == "":
        return []
    return [tag.strip() for tag in text.split(",")]


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "add":
        repo = TransactionRepository(Path("data/transactions.jsonl"))
        date = prompt_date()
        type_ = prompt_type()
        category = input("카테고리: ") # 임시
        amount = prompt_amount()
        memo = prompt_memo()
        tags = prompt_tags()
        
        new_id = repo.next_id()
        transaction = Transaction(id=new_id, 
            date=date,
            type=type_, 
            category=category, 
            amount=amount, 
            memo=memo,
            tags=tags
        )
        repo.add(transaction)
        print(f"[저장 완료] id={new_id}")

    elif args.command == "list":
        repo = TransactionRepository(Path("data/transactions.jsonl"))
        for transaction in islice(repo.iter_all(), args.limit):
            print(transaction)

