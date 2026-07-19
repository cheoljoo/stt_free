#!/data/data/com.termux/files/usr/bin/bash
# Termux에서 실행: 녹음/통화녹음 폴더의 새 파일을 stt_free/inbox 에 넣고 commit & push.
# DESIGN.md 3-1 참고. termux-job-scheduler 또는 crontab(termux-services)으로 주기 실행.
#
# 사전 준비:
#   pkg install git termux-api openssh
#   termux-setup-storage
#   REPO_DIR 에 stt_free 를 git clone 해두고 SSH deploy key 등록
#
# 설정 (환경에 맞게 수정):
REPO_DIR="${STT_FREE_REPO:-$HOME/stt_free}"
SOURCE_DIRS=(
  "/sdcard/Music/Recordings"       # 삼성 기본 음성 녹음
  "/sdcard/Recordings/Call"        # 통화 녹음 (기기별 경로 다름)
)
AUDIO_EXT_REGEX='\.(m4a|mp3|wav|aac|3gp|amr)$'

set -euo pipefail

INBOX="$REPO_DIR/inbox"
mkdir -p "$INBOX"

classify_kind() {
  # 경로에 "call"이 포함되면 통화, 아니면 메모로 분류
  case "$1" in
    *[Cc]all*) echo "call" ;;
    *) echo "memo" ;;
  esac
}

moved_any=0

for src in "${SOURCE_DIRS[@]}"; do
  [ -d "$src" ] || continue
  kind="$(classify_kind "$src")"

  find "$src" -maxdepth 1 -type f | grep -Ei "$AUDIO_EXT_REGEX" | while read -r f; do
    base="$(basename "$f")"
    ext="${base##*.}"

    # 이미 inbox/archive 어딘가로 옮겨진 적 있는 파일은 건너뜀 (파일명 기준 중복 방지)
    if find "$REPO_DIR/inbox" "$REPO_DIR/archive" -name "*${base%.*}*" 2>/dev/null | grep -q .; then
      continue
    fi

    ts="$(date -r "$f" '+%Y-%m-%d_%H%M')"
    new_name="${ts}_${kind}_$(echo "${base%.*}" | tr ' ' '_').${ext}"

    cp "$f" "$INBOX/$new_name"
    echo "[auto_push] 추가: $new_name"
    moved_any=1
  done
done

if [ "$moved_any" -eq 0 ]; then
  echo "[auto_push] 새 파일 없음"
  exit 0
fi

cd "$REPO_DIR"
git add inbox/
if git diff --cached --quiet; then
  echo "[auto_push] 변경 사항 없음"
  exit 0
fi

git commit -m "inbox: 새 음성 파일 추가 ($(date '+%Y-%m-%d %H:%M'))"
git push
echo "[auto_push] push 완료"
