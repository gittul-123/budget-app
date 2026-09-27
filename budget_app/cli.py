import argparse
import sys
from pathlib import Path
from .models import Transaction
from .repository import TransactionRepository, CategoryRepository
from itertools import islice
from datetime import datetime


DEFAULT_CATEGORIES = ["food", "transport", "rent", "salary", "etc"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budget_app")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--limit", type=int, default=10)

    category_parser = subparsers.add_parser("category")
    category_subparsers = category_parser.add_subparsers(dest="category_command")

    category_add = category_subparsers.add_parser("add")
    category_list = category_subparsers.add_parser("list")
    category_remove = category_subparsers.add_parser("remove")
    category_remove.add_argument("--name", type=str, required=True)

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("--id", type=str, required=True)

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
            if amount > 0:
                return amount
            print("[오류] 금액은 양수여야 합니다.")
        except ValueError:
            print("[오류] 숫자로 입력해주세요.")


def prompt_category(cat_repo: CategoryRepository) -> str:
    categories = list(cat_repo.iter_all())
    print(f"등록된 카테고리: {', '.join(categories)}")
    while True:
        text = input("카테고리: ")
        if cat_repo.exists(text):
            return text
        print(f"[오류] 등록되지 않은 카테고리입니다: {text}")
        print("[힌트] category list 로 등록된 카테고리를 확인하거나, category add 로 먼저 등록하세요.")


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

    cat_repo = CategoryRepository(Path("data/categories.jsonl"))
    cat_repo.ensure_default(DEFAULT_CATEGORIES)

    if args.command == "add":
        repo = TransactionRepository(Path("data/transactions.jsonl"))
        date = prompt_date()
        type_ = prompt_type()
        category = prompt_category(cat_repo)
        amount = prompt_amount()
        memo = prompt_memo()
        tags = prompt_tags()

        new_id = repo.next_id()
        transaction = Transaction(
            id=new_id,
            date=date,
            type=type_,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags,
        )
        repo.add(transaction)
        print(f"[저장 완료] id={new_id}")

    elif args.command == "list":
        repo = TransactionRepository(Path("data/transactions.jsonl"))
        transactions = list(repo.iter_all())
        transactions.reverse()
        for transaction in islice(transactions, args.limit):
            print(transaction)

    elif args.command == "category":
        if args.category_command == "add":
            name = input("카테고리명: ")
            cat_repo.add(name)
            print(f"[저장 완료] category={name}")

        elif args.category_command == "list":
            for name in cat_repo.iter_all():
                print(f"- {name}")

        elif args.category_command == "remove":
            print("아직 구현 안 됨")

        else:
            parser.print_help()

    elif args.command == "delete":
        repo = TransactionRepository(Path("data/transactions.jsonl"))
        found = repo.delete(args.id)

        if found:
            print(f"[삭제 완료] id={args.id}")

        else:
            print(f"[오류] 해당 id를 찾을 수 없습니다: {args.id}")
            sys.exit(1)

    else:
        parser.print_help()
