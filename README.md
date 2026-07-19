# stt_free

나는 android 폰을 사용한다.
폰을 사용하여 음성 녹음을 한 것이나, 전화 통화가 있은 후에 해당 음성 파일을 정의된 stt_free 에 commit 으로 추가를 한다. 
음성 녹음 파일에서 음성을 추출하고, 그 내용을 AI로 분석해 요약과 1페이지 그림으로 정리한다.

## 설계

전체 아키텍처와 컴포넌트 설계는 [DESIGN.md](DESIGN.md) 참고.

## 사용법

```bash
pip install -r requirements.txt
playwright install --with-deps chromium   # PNG 렌더링용 (선택)

# inbox/ 에 음성 파일(.m4a, .mp3, .wav 등)을 넣고 실행
python pipeline/run.py

# 특정 파일 하나만 처리
python pipeline/run.py --file inbox/2026-07-19_1030_call_홍길동.m4a

# AI 분석 없이 STT만 테스트
python pipeline/run.py --skip-llm
```

처리 결과는 `transcripts/`(전문), `summaries/`(요약), `onepagers/`(1페이지 HTML/PNG)에 생성되고,
원본 음성은 `archive/{연}/{월}/`로 이동한다. 설정은 [pipeline/config.yaml](pipeline/config.yaml).

라이선스: [Apache License 2.0](LICENSE)
