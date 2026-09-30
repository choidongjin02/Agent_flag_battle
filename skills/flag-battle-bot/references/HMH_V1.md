# HMH v1 — 구현·검증·제출 기록

2026-09-28. 신규 봇은 `agents/hmh-v1/`, 실제 업로드 파일은 **`exports/hmh-v1.zip`**이다. 기존 tactical/balanced/economic 및 vendor 파일은 수정하지 않았다.

## 구현한 동작

- **전역 F 임무 배정**: Hungarian 최대가중 배정. F를 1명 임무로 나누고, 건물 가치·도착거리·이전 임무 유지 보너스·남은 턴을 반영한다. 최대 17개 슬롯으로 계산량을 제한하고 초과 F는 별도로 안전 이동한다.
- **공동 병력 배분**: 생산 후 출발 풀, 예약 도착분, TELE 사용권을 분리한다. F의 실제 도착지에 W를 예약하고 남은 W로 요격·영토 방어·증원을 수행한다. 동수 생존과 1명 우세 공격을 구분한다.
- **경제와 생산지**: ENG/HALL/HOSPITAL/LIBRARY/DEPOT/STATION의 서로 다른 가치를 반영한다. 본진과 소유 병원 중 도착시간·긴급 위협으로 생산지를 선택한다. 당일 신규 병력도 움직인다.
- **공개 정보 메모리**: 관측 점수와 180도 대칭으로 얻는 합법 추론, 보급소 수령·소유 누적 이력, 이전 임무를 보존한다. 미공개 점수는 지역 2/중앙 3의 대표값으로 계획하며 실제 점수나 map seed를 읽지 않는다. 추론 점수와 엔진 공개 플래그는 분리한다.
- **짧은 동시행동 탐색**: 기본/경제/습격/예측형 내 후보와 균형/습격/경제/대기 상대 후보를 비교한다. 같은 명령 목록은 중복 평가하지 않는다. 제공 전이로 1턴을 계산하고 여유가 있으면 상위 2개 후보를 2턴까지 평가한다. 평가값은 0.6×평균+0.4×최악이다. 두 후보의 깊은 평가가 모두 완료됐을 때만 깊이 2 결과로 교체한다.
- **시간 제어**: 의사결정 시작 기준 내부 예산 135ms. 먼저 기본 합법 계획을 만들고 완료한 평가만 채택한다. 135ms가 서버 deadline을 보장한다는 뜻은 아니다.

이 구현은 완전한 PGS coordinate descent, MCTS, Nash/CCE solver, 자동 정책 합성 또는 학습형 모델이 아니다. **전역 할당 + 작은 행동 portfolio의 최대 2턴 rollout**이다. 광장 고정 집결 규칙은 없다.

## 전이 모듈 출처

`simcore/state.py`, `simcore/commands.py`, `simcore/pipeline.py`는 제공 `vendor/development/engine/`의 같은 파일을 바이트 변경 없이 복사했다. vendor를 수정하거나 서버 엔진을 교체하지 않았다. 30개 무작위 합성 상태에서 SDK 명령 파싱·생산·이동·전체 전이 및 승패 결과를 대조했다. 이는 제공 SDK와의 일치 검증이며 서버의 별도 ruleset 구현까지 인증하지 않는다.

## 로컬 대전 결과

| 상대 | 개발 0~7, 양 진영 | 검증 1000~1007, 양 진영 | 합계 |
|---|---:|---:|---:|
| tactical | 16승 0패 | 16승 0패 | 32승 0패 |
| economic | 16승 0패 | 16승 0패 | 32승 0패 |
| balanced | 16승 0패 | 16승 0패 | 32승 0패 |
| example_lv2 | 16승 0패 | 16승 0패 | 32승 0패 |
| 전체 | **64승 0패** | **64승 0패** | **128승 0패** |

무승부·몰수·HMH 출력 오류·HMH stderr는 모두 0. 이 128경기는 이름 변경 전 `atlas-v1` 소스로 실행했으며, 당시 12개 실행 manifest와 당시 제출 소스 hash가 일치했다. 이후 사용자 요청으로 이름·모듈 경로를 `hmh`로 변경했다. 이전 패키지와 식별자를 정규화한 Python AST를 비교하여 실행 로직이 동일함을 확인했다. 현재 소스 hash는 이름 변경으로 달라졌으며, 128경기를 다시 실행하지 않았다. 검증 결과를 보고 파라미터를 조정하지 않았다. holdout 2000~2199는 사용하지 않았다.

실행 환경: Windows 11, Intel64 Family 6 Model 170 Stepping 4, Python 3.12.14, `local-portable-strict-output-v1`. 일반 턴 응답 최댓값 약 **79ms**, 첫 턴 최댓값 약 **140ms**. 이는 로컬 프로세스 adapter의 END 수신 측정값이다. Windows timer 해상도의 계단형 값이 있으며 서버의 300ms/첫 턴 3초 실행 환경과 동일하다는 뜻은 아니다. 대전 프로세스들은 병렬로 겹쳐 실행하지 않았다.

기존 상대 3종은 비슷한 탐욕 구조를 공유하고 Lv2도 강한 대회 상대의 대체물이 아니다. **128전 전승을 대회 승률 100%로 일반화할 수 없다.** 실제 사용자 benchmark 상대의 소스·당일 명령이 없으므로 1승 5패했던 시리즈를 그대로 재대전하지 못했다. 탐색 on/off 분리 대전은 수행하지 않았으므로 개선 전체를 탐색 단독 효과로 해석하지 않는다.

원시 자료:

- `experiments/runs/atlas-dev01-vs-*`: seed 2,3, 상대별 4경기.
- `experiments/runs/atlas-dev02-vs-*`: seed 0,1,4,5,6,7, 상대별 12경기.
- `experiments/runs/atlas-validation01-vs-*`: seed 1000~1007, 상대별 16경기. 원시 결과는 당시 이름으로 보존했다.
- 각 폴더: 원시 replay, 결과, 입력 설정 및 소스 hash를 가진 manifest, 환경, 응답시간, stderr 기록.
- `artifacts/atlas-v1-results.json`: 이름 변경 전 경기·시간·ZIP 집계.
- `artifacts/hmh-v1-delivery-manifest.json`: 최종 파일별 hash, SDK lock hash, 격리 압축해제 실행 기록.

## 검증 범위

- `fb.ps1 doctor`: 원본 SDK hash/실행 환경 검사 통과.
- `fb.ps1 verify`: **39/39 테스트 통과**. 기존 29개 + HMH 10개. 배정 최적성, 원천/도착 풀 분리, TELE 공유, 관전자 점수 비누설, spawn 예산 중복 방지, SDK 차등 전이, replay 병원 우회 회귀, 회전 대칭, 시간 예산 0 fallback을 포함한다.
- 첨부 5 replay의 **216개 관측**에서 예외 없이 명령 생성·파싱. 중앙값 28.6ms, p95 49.1ms, 최대 55.1ms(프로세스 내부 측정). 탐색이 기본 계획을 바꾼 턴은 56개. 이는 원래 경기의 새 승패 측정이 아니다.
- ZIP 구조 검사 통과. 별도 `artifacts/hmh-v1-package-smoke/`(2026-09-28 2차 정리로 삭제. `docs/CLEANUP_20260928.md` 참조)에 압축을 풀고 해당 디렉터리에서 진입점을 실행하여 지속 프로토콜 2턴·EOF 종료·stderr 없음 확인.
- ZIP 내부의 모든 파일이 최종 소스와 바이트 단위로 일치한다.

## Export

- 파일: `exports/hmh-v1.zip`
- ZIP 크기: **22,777 bytes**
- 압축 해제 크기: **60,611 bytes**, 14개 파일
- SHA-256: `73830bd6ed8ca340319ceedf7523b2e49f0bd6336326241f6bb4c3f5c4782bd6`
- 루트 `submission.json` + `main.py`, Python 표준 라이브러리만 사용. 학습 가중치·실행 파일·임의 데이터 없음.
- 사용자 제공 소스 5MB 한도보다 작다. 서버 업로드/승인은 수행하지 않았다.

## 재현 명령

```powershell
./fb.ps1 doctor
./fb.ps1 verify
# Python은 fb.ps1이 사용하는 번들 Python 3.12 이상을 사용
# python -B tools/probe_hmh_replays.py  (2026-09-28 2차 정리로 삭제. `docs/CLEANUP_20260928.md` 참조)
python -B -u tools/benchmark_hmh.py --tag NEW_UNIQUE_TAG --seeds 8 9 --run
./fb.ps1 pack --source agents/hmh-v1 --out exports/NEW_UNIQUE_NAME.zip
./fb.ps1 inspect exports/NEW_UNIQUE_NAME.zip
```

probe는 기존 결과 파일을 덮어쓰지 않으므로 재실행하려면 출력 경로를 새 버전으로 바꾼다. benchmark도 새 tag를 사용한다. 시드 분할과 기존 출력 보호는 유지한다.

최근 문헌 20편과 기반 문헌 4편의 검토 범위·채택/보류 판단은 [문헌 선별 기록](research/HMH_LITERATURE_SCREEN_20260928.md)에 있다. 후속 작업은 실제 강한 상대의 replay를 받아 후보 생성·평가·상대 모델 중 무엇이 실패했는지 구분하는 것이 우선이다.
