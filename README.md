# stt_free

https://www.youtube.com/watch?v=9m8iMzEBuSU : 5인 회사 운영하며 직접 헤르메스 에이전트 720시간 돌려본 후기 (feat. Slack, Hostinger)
의 내용을 보고 얻은 아이디어 입니다.
https://www.youtube.com/watch?v=j5CIK1pcf3A : 헤르메스 에이전트 처음 써보는 분도 이 영상 하나로 끝납니다, 설치부터 회사 운영 자동화까지
- data centric으로 slack , teams 등 모든 내용을 모으는 작업이 필요 : 메신저 , 이메일 , 노션 ... 그리고, 전화 통화 , 회의 음성  : 무엇보다 사용자들이 매우 쉽게 사용하게 하려면 어떤 것을 더 추가해야 할까요?
- gstack , gbrain : 회사 운영 잘 하는가 YCombinator / 사업 방향성
- Hermes에서 매일 SOP(우리 조직의 뇌) wiki : LLM wiki   -> 해당 회사에서 하는 일을 모아서 매일 무슨 일이 일어나는지 받아볼수 있음
- hermes : 자동화 아이템을 더 뽑아줘


기본 아이디어:
- 나는 android 폰을 사용한다.
- 폰을 사용하여 음성 녹음을 한 것이나, 전화 통화가 있은 후에 해당 음성 파일을 정의된 stt_free 에 commit 으로 추가를 한다. 
- 음성 녹음 파일에서 음성을 추출하고, 그 내용을 AI로 분석해 요약과 1페이지 그림으로 정리한다.

## 설계

전체 아키텍처와 컴포넌트 설계는 [DESIGN.md](DESIGN.md) 참고.

## 사용법

의존성 관리는 [uv](https://docs.astral.sh/uv/)를 사용한다.

```bash
uv sync
uv run playwright install chromium   # PNG 렌더링용 (선택)

# inbox/ 에 음성 파일(.m4a, .mp3, .wav 등)을 넣고 실행
uv run python pipeline/run.py

# 특정 파일 하나만 처리
uv run python pipeline/run.py --file inbox/2026-07-19_1030_call_홍길동.m4a

# AI 분석 없이 STT만 테스트
uv run python pipeline/run.py --skip-llm
```

처리 결과는 `transcripts/`(전문), `summaries/`(요약), `onepagers/`(1페이지 HTML/PNG)에 생성되고,
원본 음성은 `archive/{연}/{월}/`로 이동한다. 설정은 [pipeline/config.yaml](pipeline/config.yaml).

`analyze.backend`를 `claude`/`gemini`/`ollama`로 쓰려면 해당 extra를 함께 설치한다.
예: `uv sync --extra claude`

## 폰에서 음성 업로드하기

Android 폰에서 `inbox/`로 음성 파일을 자동 push하는 방법은 두 가지 중 편한 쪽을 선택한다
(둘 다 같은 파일명 규칙을 쓰고, 이후 파이프라인은 동일하게 동작):

- **네이티브 앱** ([android/](android/)) — 설치 후 저장소 URL과 GitHub PAT만 입력하면 끝. UI에서 동기화 상태 확인 가능.
- **Termux 스크립트** ([phone/auto_push.sh](phone/auto_push.sh)) — 이미 Termux/셸에 익숙하다면 더 가볍게 커스터마이즈 가능.

## 비용 ($0 정책)

API 과금 없이 돌아가도록 기본값을 구성했다.

- **로컬 PC**: `pipeline/config.yaml`의 기본값 `analyze.backend: claude-code`.
  로컬에 로그인된 `claude` CLI(Claude Code Pro/Max 구독)를 헤드리스로 호출 — 구독료 외 추가 비용 없음.
- **GitHub Actions**: CI 러너에는 로그인된 `claude` CLI가 없어 [.github/workflows/process.yml](.github/workflows/process.yml)에서
  `analyze.backend`를 `gemini`(무료 티어)로 오버라이드한다. [aistudio.google.com](https://aistudio.google.com)에서
  API 키를 발급받아 저장소 Settings → Secrets → Actions에 `GEMINI_API_KEY`로 등록하면 된다.
- 유료 `claude`(Anthropic API) 백엔드는 코드상 선택은 가능하지만 기본 경로에서는 사용하지 않는다.

라이선스: [Apache License 2.0](LICENSE)
