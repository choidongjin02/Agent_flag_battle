# 깃발 대항전 프로젝트

2026-09-29 추가: 새 작업은 `docs/HMH_0929_SEARCH4.md`도 읽는다. 최신 로컬 검증 후보는 `agents/hmh-v3-0929b`, ZIP은 `exports/HMH_0929_SEARCH4.zip`이며 서버 미업로드다. 이 버전도 보존하고 다음 변경은 새 폴더에서 한다. `agents/hmh-v3-0929`는 미선정 첫 후보다.

새 채팅은 `README.md`와 `docs/HANDOFF.md`부터 읽고 현재 사용자의 작업 범위를 따른다. HMH v1·v2 구현·검증은 완료됐고(최신 제출본 `exports/hmh_0928.zip`, 기록 `docs/HMH_V2.md`), 과거 balanced/economic/tactical 전략과 상세 실험은 정리되어 `docs/LEGACY_STRATEGIES.md`에 요약만 남아 있다. 구현/측정 요청을 받으면 다음 단계로 진행한다.

## 스킬

활성 스킬은 `.agents/skills/`에 있다. 설치 전 staging은 `skills/`이며 설치 후 제거한다. 자동 발견이 안 되면 해당 `SKILL.md`를 직접 읽는다.

- `flag-battle-rules`: 규칙 질문·판정·전이 검증.
- `flag-battle-bot`: 설계·코드 작성·제출 소스 준비.
- `flag-battle-arena`: 실험 계획·실행·집계·리플레이.

## 기준과 폴더

- `vendor/`: 제공 SDK와 샘플 원본. 직접 고치지 말고 adapter/agent를 별도로 작성한다.
- `archives/input/`: 수령 원본. 이전 `.skill`은 검토용이며 활성 스킬이 아니다.
- `docs/`: 인수인계·감사·설계·논문 검토.
- `agents/<version>/`: 봇 소스. `agents/hmh-v1/`, `agents/hmh-v2/`를 보존하고 다음 변경은 새 버전 폴더에서 한다. `agents/raider-v1/`은 제출용이 아닌 arena 스크립트 상대다.
- `tools/`, `tests/`: 개발/검증 기반. 결과·임시 파일을 소스 폴더에 쓰지 않는다.
- `experiments/configs/`: 재현 가능한 실험 설정. `experiments/runs/<id>/`: 실제 결과.
- `artifacts/`: 임시 검증·계획. `exports/`: 배포 ZIP와 개조 `.skill`.

`./fb.ps1 doctor`, `./fb.ps1 verify`는 성능 대전을 하지 않는다. `run`은 실제 대전 요청이 있을 때만 수행한다. 보고에는 수행한 검증과 미수행 측정을 구분한다. SDK 관전자 점수를 봇 관측에 누설하지 않는다. 원본 스킬의 과거 “전승/수 ms” 문구는 검증 근거로 사용하지 않는다.

다른 채팅과 파일을 공유하므로 작업 시작 시 기존 변경을 확인한다. 결과 폴더를 재사용하거나 타 세션의 agent를 덮어쓰지 않는다. 불필요한 root 파일을 늘리지 말고 위 폴더에 배치한다.

제출물 데이터 규정은 2026-09-28 공지로 해석이 바뀌었다(소스 상수는 허용, 데이터 파일·실행 중 읽기는 금지): `docs/SUBMISSION_POLICY_20260928.md`. 코드·도구·스킬을 바꿀 때는 얻는 것과 잃는 것을 함께 보고한다(Claude Code에서는 `.claude/settings.json` 훅이 체크리스트를 준다).
