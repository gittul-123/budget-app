import argparse
import sys
from pathlib import Path
from .models import Transaction
from .repository import TransactionRepository, CategoryRepository, BudgetRepository
from itertools import islice
from datetime import datetime
from .service import TransactionService
import functools


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

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--from", dest="date_from", type=str, default=None)
    search_parser.add_argument("--to", dest="date_to", type=str, default=None)
    search_parser.add_argument("--category", type=str, default=None)
    search_parser.add_argument("--type", type=str, default=None)
    search_parser.add_argument("--q", type=str, default=None)
    search_parser.add_argument("--tag", type=str, default=None)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--id", type=str, required=True)
    update_parser.add_argument("--date", type=str, default=None)
    update_parser.add_argument("--type", type=str, default=None)
    update_parser.add_argument("--category", type=str, default=None)
    update_parser.add_argument("--amount", type=int, default=None)
    update_parser.add_argument("--memo", type=str, default=None)
    update_parser.add_argument("--tags", type=str, default=None)

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("--month", type=str, required=True)
    summary_parser.add_argument("--top", type=int, default=3)

    budget_parser = subparsers.add_parser("budget")
    budget_subparsers = budget_parser.add_subparsers(dest="budget_command")

    budget_set = budget_subparsers.add_parser("set")
    budget_set.add_argument("--month", type=str, required=True)
    budget_set.add_argument("--amount", type=int, required=True)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--out", type=str, required=True)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--in", dest="csv_in", type=str, required=True)

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

def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[오류] 예상치 못한 문제가 발생했습니다: {e}")
            sys.exit(1)
    return wrapper

@handle_errors
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
            repo = TransactionRepository(Path("data/transactions.jsonl"))
            in_use = any(t.category == args.name for t in repo.iter_all())

            if in_use:
                print(f"[오류] '{args.name}' 카테고리를 사용 중인 거래가 있어 삭제할 수 없습니다.")
                sys.exit(1)

            found = cat_repo.remove(args.name)
            if found:
                print(f"[삭제 완료] category={args.name}")
            else:
                print(f"[오류] 등록되지 않은 카테고리입니다: {args.name}")
                sys.exit(1)

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

    elif args.command == "search":
        repo = TransactionRepository(Path("data/transactions.jsonl"))
        service = TransactionService(repo)
        results = list(service.search(
            date_from=args.date_from,
            date_to=args.date_to,
            category=args.category,
            type_=args.type,
            q=args.q,
            tag=args.tag,
        ))
        results.reverse()
        for transaction in results:
            print(transaction)

    elif args.command == "update":
        repo = TransactionRepository(Path("data/transactions.jsonl"))

        if args.date is not None:
            try:
                datetime.strptime(args.date, '%Y-%m-%d')
            except ValueError:
                print(f"[오류] 날짜 형식이 올바르지 않습니다: {args.date}")
                sys.exit(1)

        if args.type is not None and args.type not in ["income", "expense"]:
            print(f"[오류] type은 income 또는 expense만 가능합니다: {args.type}")
            sys.exit(1)

        if args.category is not None and not cat_repo.exists(args.category):
            print(f"[오류] 등록되지 않은 카테고리입니다: {args.category}")
            sys.exit(1)

        if args.amount is not None and args.amount <= 0:
            print(f"[오류] 금액은 양수여야 합니다: {args.amount}")
            sys.exit(1)

        tags = None
        if args.tags is not None:
            tags = [tag.strip() for tag in args.tags.split(",")]

        found = repo.update(
            args.id,
            date=args.date,
            type=args.type,
            category=args.category,
            amount=args.amount,
            memo=args.memo,
            tags=tags,
        )

        if found:
            print(f"[수정 완료] id={args.id}")

        else:
            print(f"[오류] 해당 id를 찾을 수 없습니다: {args.id}")
            sys.exit(1)

    elif args.command == "summary":
        repo = TransactionRepository(Path("data/transactions.jsonl"))
        service = TransactionService(repo)
        result = service.summary(args.month)

        if not result["has_data"]:
            print(f"[{args.month}] 데이터 없음")

        else:
            print(f"총 수입: {result['total_income']}원")
            print(f"총 지출: {result['total_expense']}원")
            print(f"잔액: {result['balance']}원")

            items = list(result["category_totals"].items())
            top_items = sorted(items, key=lambda item: item[1], reverse=True)[:args.top]

            print(f"지출 TOP {args.top}")
            for i, (category, amount) in enumerate(top_items, start=1):
                print(f"{i}) {category} {amount}원")

            budget_repo = BudgetRepository(Path("data/budgets.jsonl"))
            budget_amount = budget_repo.get(args.month)

            if budget_amount is not None:
                usage_rate = (result['total_expense'] / budget_amount) * 100
                print(f"예산: {budget_amount}원 (사용률 {usage_rate:.1f}%)")
                if result["total_expense"] > budget_amount:
                    print("[경고] 예산을 초과했습니다!")

    elif args.command == "budget":
        budget_repo = BudgetRepository(Path("data/budgets.jsonl"))
        if args.budget_command == "set":
            budget_repo.set(args.month, args.amount)
            print(f"[저장 완료] {args.month} 예산 {args.amount}원")
        else:
            parser.print_help()

    elif args.command == "export":
        repo = TransactionRepository(Path("data/transactions.jsonl"))
        service = TransactionService(repo)
        count = service.export_csv(args.out)
        print(f"[내보내기 완료] {count}건을 {args.out}에 저장했습니다.")

    elif args.command == "import":
        repo = TransactionRepository(Path("data/transactions.jsonl"))
        service = TransactionService(repo)
        result = service.import_csv(args.csv_in, cat_repo)
        print(f"[가져오기 완료] 성공 {result['success']}건, 실패 {result['failed']}건")

    else:
        parser.print_help()

