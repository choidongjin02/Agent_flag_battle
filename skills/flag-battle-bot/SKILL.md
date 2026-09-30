---
name: flag-battle-bot
description: "깃발 대항전 봇의 설계·구현·수정·제출 소스 패키징을 돕는다. 제공 스타터와 논문 기반 M1/M7 설계를 사용하며, 성능 측정은 요청 범위에 따라 별도로 수행한다."
---

# 깃발 대항전 봇 개발

작업 폴더나 사용자가 지정한 위치에서 `flag-battle.project.json`을 찾고 `README.md`, `docs/HANDOFF.md`를 읽는다. 프로젝트를 찾지 못하면 SDK 위치를 확인한다. 이 스킬 자체가 M1/M7 구현이나 승률 개선을 완료한 것은 아니다.

## 시작점

- 현재까지 구현된 HMH v1 Strategy를 시작점으로 사용할 때는 `assets/hmh-v1/`을 새 버전 디렉터리로 복사한다. asset 원본은 직접 수정하지 않는다. 구현·검증 범위는 [HMH v1 기록](references/HMH_V1.md)을 확인한다.
- 새 Python 봇: 프로젝트에서 `./fb.ps1 scaffold --dest agents/m1 --entry main`. Python 직접 실행은 `python tools/flag_battle.py scaffold ...`이다.
- C++를 요청하면 `--language cpp`를 사용한다. 실제 컴파일러를 확인하고 컴파일하지 않은 코드를 “GCC 검증됨”으로 표시하지 않는다.
- 기존 봇은 먼저 읽고 유지할 동작·입출력 계약을 확인한다. 새 템플릿으로 덮어쓰지 않는다.
- 스캐폴드는 제공 소스를 복사할 뿐이다. 구현 전 [계약](references/implementation.md), 전략 설계 시 [연구 적용](references/research.md)을 읽는다.

## 구현 경계

1. 사용자가 준비·분석만 요청했다면 계획/코드 계약/테스트 도구까지 완료하고 실제 전략 구현·대전을 시작하지 않는다. 이후 명시적 구현 요청은 그 단계의 진행을 허가한다.
2. 공개 `Init`/`View` 기반 `decide(view, init) -> list[str]`를 유지한다. 반환에 END를 넣지 않고 제공 `run()`이 END와 flush를 처리한다. 인터페이스 변경이 필요하면 소비자를 함께 수정·검증한다.
3. vendor SDK는 기준 사본으로 유지한다. 빠른 전이는 agent 내부 별도 모듈로 만들고 제공 `run_turn`과 차등 검증한다. 봇에 관전자 점수·map seed·상대 이번 명령을 넘기지 않는다.
4. 기본 정책의 유효 행동을 먼저 완성하고 완료된 탐색 결과만 대체한다. END 예외 fallback은 timeout·무한루프·출력한도 문제를 해결하지 않는다. 개발 중 예외를 조용히 삼키지 않는다.
5. M1 목표 할당·F/W 임계값 → M7 중요 집단 국소 탐색을 출발안으로 사용하되 사용자의 방법 선택을 따른다. 알고리즘/가중치/깊이는 실측 전 가설이다.

## 검증·전달

관련 단위 테스트를 실행하고, 사용자가 대전을 요청한 단계에서 `flag-battle-arena` 또는 프로젝트 runner 워크플로를 사용한다. 스킬이 자동으로 장시간 실험을 추가하지 않는다. 기능 추가마다 모든 조합을 튜닝할 필요는 없다.

제출 구조는 `./fb.ps1 pack --source agents/m1 --out exports/m1-v1.zip`, `./fb.ps1 inspect exports/m1-v1.zip`으로 확인한다. 이 명령은 **ZIP 구조 검증**이지 실행·성능·서버 통과 인증이 아니다. `submission.json`과 진입 파일을 ZIP 루트에 둔다. ZIP에는 `submission.json`과 소스(보조 모듈·헤더 포함)만 넣는다. 별도 데이터 파일, 실행 파일, 실행 중 파일·외부 읽기는 금지된다. 오프라인에서 정한 가중치·배열을 소스 상수로 넣는 것은 허용된다(2026-09-28 공지, `docs/SUBMISSION_POLICY_20260928.md`). 이때 첫 턴 import 시간과 메모리를 측정한다.

보고에는 변경, 검증 범위, 미검증 항목, 소스/설정 hash를 남긴다. 근거 없는 “전승”, “수 ms”, “무시 명령 0” 같은 성능 문구를 붙이지 않는다.
