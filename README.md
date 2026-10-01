# 나만의 용돈 기입장 (budget_app)

콘솔 기반 가계부 프로그램. 파일 기반(JSONL)으로 거래 내역을 영구 저장하며,
추가/조회/검색/수정/삭제/월별 요약/예산 관리/카테고리 관리/CSV 가져오기·내보내기를 지원한다.

## 개발 환경

- Python 3.10 이상
- 외부 라이브러리 없이 표준 라이브러리만 사용

## 실행 방법

프로젝트 루트(`budget_app/` 폴더가 보이는 위치)에서 실행한다.

```
python -m budget_app <command> [options]
```

모든 명령어는 `--help`로 사용법을 확인할 수 있다.

```
python -m budget_app --help
python -m budget_app add --help
```

## 저장 파일 위치 / 형식

- 기본 저장 폴더: `./data` (전역 옵션 `--datadir`로 변경 가능, 서브커맨드보다 앞에 지정)
  ```
  python -m budget_app --datadir /path/to/mydata list
  ```
  지정한 폴더가 없으면 자동으로 생성한다.
- 저장 포맷: **JSONL** (한 줄에 레코드 하나씩 JSON으로 저장)

| 파일 | 내용 |
|---|---|
| `data/transactions.jsonl` | 거래 내역 |
| `data/categories.jsonl` | 등록된 카테고리 목록 |
| `data/budgets.jsonl` | 월별 예산 |

최초 실행 시 `data/categories.jsonl`이 비어 있으면 기본 카테고리(`food`, `transport`, `rent`, `salary`, `etc`)를 자동으로 생성한다.

### JSONL을 선택한 이유

- 제너레이터 기반 스트리밍 읽기(`for line in file: yield ...`)와 포맷 자체가 1:1로 대응되어 구현이 단순하다.
- 숫자·리스트 등 타입이 그대로 보존되어 매번 수동 형변환할 필요가 없다 (CSV는 전부 문자열로 저장됨).
- `tags`처럼 다중값 필드를 리스트로 자연스럽게 표현할 수 있다.
- CSV는 import/export 요구사항에 따라 "외부 교환 포맷"으로만 사용하고, 내부 저장은 JSONL 하나로 단순화했다.

## 주요 명령어 예시

### 거래 추가 (대화형)

```
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000012
```

### 거래 목록 (최신순, 옵션 기반)

```
$ python -m budget_app list --limit 3
```

### 거래 검색 (옵션 기반)

```
$ python -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food
$ python -m budget_app search --q 점심 --tag meal
```

### 거래 수정 / 삭제 (옵션 기반, `--id` 필수)

update는 **옵션 기반**으로 고정했다. `--id`를 제외한 나머지 옵션은 입력한 필드만 수정되고, 입력하지 않은 필드는 기존 값이 유지된다.

```
$ python -m budget_app update --id TX-000012 --amount 20000
$ python -m budget_app delete --id TX-000012
```

### 월별 요약

```
$ python -m budget_app summary --month 2024-01 --top 3
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
지출 TOP 3
1) rent 150000원
2) food 45000원
3) transport 20000원
예산: 500000원 (사용률 43.0%)
```

데이터가 없는 달은 `[2024-01] 데이터 없음`으로 출력한다.

### 예산 설정

```
$ python -m budget_app budget set --month 2024-01 --amount 500000
```

### 카테고리 관리

```
$ python -m budget_app category add
$ python -m budget_app category list
$ python -m budget_app category remove --name food
```

사용 중인(거래 내역이 존재하는) 카테고리는 삭제가 거부된다.

### CSV 내보내기 / 가져오기

```
$ python -m budget_app export --out export.csv --month 2024-01
[완료] export.csv (12 records)

$ python -m budget_app export --out export.csv --from 2024-01-01 --to 2024-03-31

$ python -m budget_app import --from import.csv
[가져오기 완료] 성공 5건, 실패 0건
```

`export`는 `--month` 또는 `--from`/`--to` 중 하나 이상의 조건을 반드시 지정해야 한다.
`import`는 행 단위로 검증하며, 유효하지 않은 행은 건너뛰고 나머지는 계속 처리한다(부분 성공 허용).

## import/export CSV 스키마

| column | required | 설명 |
|---|---|---|
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(,)로 구분된 문자열 |

공통: UTF-8 인코딩, 헤더 포함.

## 구조

```
budget_app/
    __init__.py
    __main__.py      # 진입점 (python -m budget_app)
    models.py         # Transaction dataclass
    repository.py      # 파일 I/O (TransactionRepository / CategoryRepository / BudgetRepository)
    service.py          # 비즈니스 로직 (검색 / 요약 / CSV 입출력)
    cli.py                # argparse 기반 CLI, 대화형 입력, 에러 처리 데코레이터
data/
    transactions.jsonl
    categories.jsonl
    budgets.jsonl
```

- **모델**: `Transaction`은 `dataclass`로 정의하며, `memo`/`tags`는 선택 필드로 기본값을 가진다.
- **저장소**: 파일 읽기는 전부 제너레이터(`yield`) 기반으로 구현하여, 파일을 한 번에 메모리에 올리지 않는다.
- **서비스**: 검색/요약/CSV 변환 등 "판단이 필요한" 로직을 저장소와 분리했다.
- **CLI**: 사용자 입력/출력만 담당하고, 저장소나 서비스의 내부 구현은 알지 못한다.

## 데코레이터

`cli.py`의 `handle_errors`가 `main()`을 감싸서, 예상치 못한 예외(파일 손상, 손상된 JSON 줄 등)를
스택트레이스 대신 `[오류] ...` 형태의 메시지로 출력하고 exit code 1로 종료시킨다.
의도적인 검증 실패(날짜 형식 오류 등)는 각 명령어 처리 로직에서 별도로 메시지를 출력하고
`sys.exit(1)`로 종료한다.

## 알려진 제약 / 설계상 트레이드오프

- **"최신순" 정렬과 완전한 스트리밍의 트레이드오프**: `list`/`search`/`export`는 파일을 제너레이터로
  한 줄씩 읽지만, 최신순 정렬을 위해 결과를 리스트로 모은 뒤 뒤집는다. 파일 끝에서부터 역방향으로
  읽는 완전한 스트리밍 정렬은 UTF-8 멀티바이트 문자 경계 처리 등 복잡도가 높아 이번 과제 규모
  (개인 가계부, 수천 건 수준)에서는 실익이 적다고 판단해 제외했다.
- `update`/`delete`는 전체 재작성(파일 전체를 읽어 메모리에서 수정 후 덮어쓰기) 방식으로 구현했다.
  임시 파일에 먼저 쓰고 `rename`으로 교체하는 원자적 쓰기는 적용하지 않았다 (보너스 과제 항목).
- `category remove`는 사용 중인 카테고리의 삭제를 거부하며, 대체 카테고리 지정 기능은 구현하지 않았다.