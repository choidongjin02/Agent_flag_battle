# 제공 자료와 판정 범위

프로젝트 root는 `flag-battle.project.json`이 있는 폴더다. `vendor/`는 사용자 제공 ZIP의 보존 사본이며 `docs/sdk-lock.json`의 SHA-256으로 검사한다.

| 주제 | 프로젝트 내 근거 |
|---|---|
| 공개 규칙 | `vendor/development/docs/rulebook.md` |
| 수치 | `vendor/development/config/balance.json` |
| 형식/직렬화 | `vendor/development/runner/protocol.py` |
| 이동·전투·점령 | `vendor/development/engine/pipeline.py` |
| 상태·이력 | `vendor/development/engine/state.py` |
| 맵 | `vendor/development/mapgen/generator.py`, `rng.py` |
| 프로세스/시간 | `vendor/development/runner/bots.py` |
| 서버와 로컬 차이 | `vendor/development/docs/PLATFORM_OPERATIONS.md` |
| 실행/출력 제한 | `vendor/development/bots/dist/starter/limits.json` |
| ZIP 구조 | `vendor/development/bots/dist/starter/submission.py` |

제공 플랫폼 문서는 게임 커밋 `88a77d888a1562e52ca2b21b2363d52bb8ce307c`를 기록한다. 이 출처가 현재 서버 배포와 영원히 같다는 보장은 없다. 새 SDK가 오면 별도 버전으로 수령하고 lock과 회귀 결과를 갱신한다.

일반 턴 300ms, 첫 턴 3000ms. Python 3.12.14 / NumPy 2.3.3 / C++20 gcc 12.2.0. 메모리 384 MiB, 프로세스 32, CPU 전용은 **제공 snapshot**의 값이다. 출력은 턴당 64 KiB/4096줄, 한 줄 1 KiB, stderr 경기당 1 MiB이다. 로컬 제공 출력 검사는 경고지만 서버는 초과 시 몰수 처리한다고 명시한다.

제공 SDK에는 5 MiB ZIP/20 MiB 해제/200파일/ASCII 파일명이라는 제한이 확인되지 않는다. 다른 최신 공지에서 확인하기 전에는 자체 검사기의 필수 오류 조건으로 추가하지 않는다. `.cc`, `.cxx`는 제공 제출 검사기의 C++ 허용 확장자가 아니다. Python import 정적 제한 검사는 제거되었지만 실제 사용 가능 라이브러리는 제공 환경 범위로 제한된다.
