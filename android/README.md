# stt_free Collector (Android 앱)

폰의 음성 녹음/통화 녹음을 감지해 `stt_free` 저장소의 `inbox/`에 자동으로 push하는 네이티브 Android 앱.
`phone/auto_push.sh`(Termux 방식)와 같은 역할을 하는 **대안**이며, 둘 중 편한 쪽을 선택해서 쓰면 된다
(자세한 설계 비교는 [../DESIGN.md](../DESIGN.md) 3-1절 참고).

## 동작 방식

1. `MediaStore.Audio` 쿼리로 녹음 폴더의 새 파일을 감지 (제조사별 절대경로 하드코딩 불필요)
2. `DESIGN.md`의 파일명 규칙(`{YYYY-MM-DD}_{HHMM}_{call|memo}_{이름}.{ext}`)으로 rename
3. 앱에 내장된 **JGit**으로 앱 내부 저장소 clone에 복사 → `git add / commit / push`
4. `WorkManager`로 기본 30분마다 자동 실행 (네트워크 연결 시에만), 앱에서 "지금 동기화" 버튼으로 즉시 실행도 가능

## 필요한 준비물

- **GitHub Personal Access Token (PAT)**: 저장소가 private이므로 `repo` 권한만 있는 fine-grained 또는
  classic PAT 발급 ([github.com/settings/tokens](https://github.com/settings/tokens))
- 저장소 HTTPS clone URL (예: `https://github.com/<user>/stt_free.git`)

SSH 키 방식은 지원하지 않는다 (JGit SSH 세션 팩토리 설정 복잡도 대비 이득이 적어 1차 구현에서 제외).

## 빌드

Android Studio에서 `android/` 폴더를 열거나:

```bash
cd android
gradle wrapper --gradle-version 8.7   # gradle-wrapper.jar가 없다면 최초 1회 생성
./gradlew assembleDebug
```

APK: `app/build/outputs/apk/debug/app-debug.apk`

## 앱 사용법

1. 설치 후 실행 → 미디어/알림 권한 허용
2. "저장소 설정" 화면에서 저장소 URL, GitHub 사용자명, PAT 입력 후 저장
   (Android Keystore로 암호화 저장되며 평문으로 남지 않음)
3. 저장 즉시 최초 clone + 30분 주기 동기화가 예약됨
4. 배터리 최적화로 백그라운드 실행이 막히면, 시스템 설정에서 이 앱을
   "제한 없음(배터리 최적화 무시)"으로 지정 권장

## 제약사항 (1차 구현)

- 인증은 PAT+HTTPS만 지원
- 최초 동기화 시 저장소 전체를 폰에 clone (저장소 용량이 크면 시간이 걸릴 수 있음)
- 화자 분리 등 STT 파이프라인 자체는 다루지 않음 — 이 앱은 순수 "폰 → inbox/ push" 역할만 담당
