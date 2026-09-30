---
name: flag-battle-arena
description: "깃발 대항전 제공 엔진으로 재현 가능한 대전 계획, 버전 비교, 승률 집계와 리플레이 분석을 수행한다. 테스트 기반만 준비하는 요청에서는 대전을 실행하지 않는다."
---

# 깃발 대항전 실험

`flag-battle.project.json`이 있는 프로젝트를 찾고 `docs/HANDOFF.md`와 [실험 계약](references/experiments.md)을 읽는다. 이전 채팅의 결과를 기억한다고 가정하지 않는다.

## 기준 구현

게임·맵·판정은 `vendor/development`의 제공 SDK를 사용한다. 과거 `.skill`의 자체 `engine.py`/`mapgen.py`는 사용하지 않는다. 공식 SDK 버전을 모르는 상태에서 “공식과 동일”이라는 표현을 쓰지 않는다.

`./fb.ps1 doctor`는 출처 hash와 환경을 확인하고, `./fb.ps1 verify`는 규칙·프로토콜·도구 단위 검증을 한다. verify는 전략 대전이나 승률 평가를 하지 않는다.

## 실행 모드

- **준비만:** 설정·스케줄·manifest를 완성하고 `plan`까지만 실행한다. `run`은 실행하지 않는다.
- **대전 요청:** 기준선과 상대·시드·예산 범위를 정하고 `plan` 후 `run`한다. 이미 충분히 지정되어 있으면 재확인을 요구하지 않는다.
- **원인 분석:** 제공 리플레이 JSON의 `turns`, `commands`, `applied`, `events`, `state`를 본다. `applied`는 파싱된 명령이며 실제 전량 실행을 보장하지 않는다. 자체 JSONL의 `ignored` 필드가 있다고 가정하지 않는다.

```powershell
./fb.ps1 plan --config experiments/configs/baseline.json --out artifacts/plans/baseline.json
./fb.ps1 run --plan artifacts/plans/baseline.json --out experiments/runs/baseline-001
./fb.ps1 summarize --run-dir experiments/runs/baseline-001 --agent lv2
```

Python 직접 호출: `python tools/flag_battle.py` 뒤에 같은 인자를 붙인다. 계획은 두 진영을 항상 교대한다. 기존 결과를 덮어쓰지 않는다. 계획 이후 소스 hash가 바뀌면 새 계획을 생성한다.

## 타당성

공통 seed와 진영 교대, 고정 검증 상대 풀, 개발/검증/보류 분할을 유지한다. 몰수 경기도 포함해 승리 credit=(승+0.5×무)/경기를 보고한다. 단일 대전이나 무작위 봇 전승을 일반 성능 개선으로 해석하지 않는다. 분산은 seed 단위로 묶고, champion 대비 개선 CI와 한 matchup의 승리 credit CI를 구별한다.

로컬 adapter는 `tools/transport.py`이며 shell 없이 argv로 실행하고 Windows pipe와 deadline을 처리한다. 게임 로직은 제공 `run_match`를 사용하나, 로컬 adapter의 출력 초과 처리와 측정은 서버 격리 환경의 재현이 아니다. 성능 보고에는 transport 이름과 실제 Python/CPU 환경을 남긴다.

완료 보고에는 설정·소스·SDK hash, 실제 경기 수, 오류, 원시 결과 경로, 검증하지 않은 항목을 포함한다. 엔진 규칙 변경으로 봇의 실패를 없애지 않는다.
