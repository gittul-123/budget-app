#!/bin/bash
# 평가 체크리스트 7개 항목을 순서대로 시연하는 스크립트
# 실행: bash demo_checklist.sh   (Windows: Git Bash에서 실행)
# demo_data 폴더를 따로 써서 실제 ./data와 분리됩니다.

set -e

# Windows(Git Bash)에서 한글이 깨지지 않도록 파이썬을 UTF-8 모드로 강제
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

# Windows에서는 python3가 없고 python만 있는 경우가 많아서 자동으로 찾습니다.
if python3 -c "import sys" >/dev/null 2>&1; then
    PY=python3
else
    PY=python
fi

DATADIR="./demo_data"
RUN="$PY -m budget_app --datadir $DATADIR"

pause() {
    echo ""
    read -p ">>> 엔터를 누르면 계속합니다..." _
    echo ""
}

section() {
    echo ""
    echo "================================================================"
    echo "  $1"
    echo "================================================================"
}

rm -rf "$DATADIR"
clear
echo "budget_app 평가 체크리스트 시연 (사용 Python: $PY)"
echo "총 7개 항목을 순서대로 확인합니다."
pause

# ============================================================
section "체크 1. add / list / search / summary / update / delete 동작"
# ============================================================
echo "-- 거래 2건을 추가합니다 (add는 대화형, 라이브로 입력) --"
echo "(날짜: 2024-01-15 / expense / food / 15000 / 점심 / meal)"
$RUN add
echo ""
echo "(날짜: 2024-01-20 / income / salary / 3000000 / 월급 / 엔터)"
$RUN add
pause

echo "-- list (최신순) --"
$RUN list --limit 5
pause

echo "-- search --category food --"
$RUN search --category food
pause

echo "-- summary --month 2024-01 --"
$RUN summary --month 2024-01
pause

echo "-- update --id TX-000001 --amount 20000 (방금 추가한 첫 거래의 금액만 수정) --"
$RUN update --id TX-000001 --amount 20000
echo ""
echo "(수정 결과 확인)"
$RUN search --category food
pause

echo "-- delete --id TX-000002 --"
$RUN delete --id TX-000002
echo "exit code: $?"
$RUN list --limit 5
pause

# ============================================================
section "체크 2. 재실행 후에도 데이터가 유지되는가 (저장 파일 3개 이상)"
# ============================================================
$RUN category add << 'INNER'
game
INNER
$RUN budget set --month 2024-01 --amount 500000 > /dev/null

echo "-- data 폴더 안 파일 목록 (3개 이상이어야 함) --"
ls -la "$DATADIR"
pause

echo "-- 완전히 새로운 프로세스로 다시 실행해서 데이터가 그대로인지 확인 --"
$RUN list --limit 5
$RUN category list
pause

# ============================================================
section "체크 3. category add / list / remove (사용 중인 카테고리 삭제 방지)"
# ============================================================
echo "-- 사용 중인 food 삭제 시도 (막혀야 함) --"
set +e
$RUN category remove --name food
echo "(exit code: $?)"
set -e
pause

echo "-- 사용 안 하는 game 삭제 (성공해야 함) --"
$RUN category remove --name game
echo "exit code: $?"
pause

echo "-- 중복 카테고리 추가 시도 (막혀야 함) --"
set +e
$RUN category add << 'INNER'
food
INNER
echo "(exit code: $?)"
set -e
pause

# ============================================================
section "체크 4. budget set 저장 + summary에서 사용률/초과 경고"
# ============================================================
echo "-- 예산을 지출보다 작게 설정해서 초과 상황을 만듭니다 --"
$RUN budget set --month 2024-01 --amount 10000
$RUN summary --month 2024-01
pause

# ============================================================
section "체크 5. import/export CSV 스키마 (UTF-8, 헤더, 컬럼)"
# ============================================================
echo "-- export --month 2024-01 --"
$RUN export --out "$DATADIR/export.csv" --month 2024-01
echo ""
echo "-- 인코딩 확인 (UTF-8로 정상 읽히는지) --"
$PY -c "open('$DATADIR/export.csv', encoding='utf-8').read(); print('UTF-8 디코딩 성공')"
echo ""
echo "-- 파일 내용 (헤더 + 데이터) --"
cat "$DATADIR/export.csv"
pause

echo "-- import: 정상 1건 + 잘못된 날짜 1건을 섞어서 --"
cat > "$DATADIR/import_sample.csv" << 'INNER'
date,type,category,amount,memo,tags
2024-02-01,expense,food,8000,간식,snack
2024-13-99,expense,food,1000,잘못된날짜,
INNER
$RUN import --from "$DATADIR/import_sample.csv"
pause

# ============================================================
section "체크 6-7. 오류 메시지(스택트레이스 없음) + exit code 비정상 종료"
# ============================================================
echo "-- (1) 잘못된 입력값: 음수 금액 --"
set +e
$RUN update --id TX-000001 --amount -500
echo "(exit code: $?)"
set -e
echo ""

echo "-- (2) 존재하지 않는 id 삭제 --"
set +e
$RUN delete --id TX-999999
echo "(exit code: $?)"
set -e
echo ""

echo "-- (3) 필수 조건 누락: export 조건 없이 --"
set +e
$RUN export --out "$DATADIR/x.csv"
echo "(exit code: $?)"
set -e
echo ""

echo "-- (4) 예상치 못한 파일 손상 상황 (데코레이터가 처리) --"
echo "깨진 데이터" >> "$DATADIR/categories.jsonl"
set +e
$RUN category list
echo "(exit code: $?)"
set -e
$PY -c "
import pathlib
p = pathlib.Path('$DATADIR/categories.jsonl')
lines = p.read_text(encoding='utf-8').splitlines()
p.write_text('\n'.join(lines[:-1]) + '\n', encoding='utf-8')
"
echo ""

echo "-- (5) 비교: 정상 종료는 exit code 0 --"
$RUN list --limit 1 > /dev/null
echo "exit code: $?"
pause

echo "체크리스트 시연 끝. 7개 항목 모두 확인했습니다."
