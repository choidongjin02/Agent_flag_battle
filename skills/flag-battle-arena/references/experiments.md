# 실험 계약

프로젝트 도구는 표준 라이브러리로 실행하며 `vendor/development`를 import한다. 타 프로젝트로 skill만 복사하면 도구와 SDK는 자동 생성되지 않는다. `exports/flag-battle-workspace.zip` 전체를 풀거나 제공 SDK 프로젝트 위치를 명시한다.

## 명령 범위

| 명령 | 효과 |
|---|---|
| doctor | 원본 SDK/ZIP hash·환경·스킬 위치 읽기 |
| verify | 규칙·합성 I/O·패키징·집계 도구 테스트; 대전 없음 |
| scaffold | 공식 Python/C++ 진입점 복사; 새 전략 구현 없음 |
| pack / inspect | 공식 제출 코드로 ZIP 생성/구조 확인; 임의 C++ 소스를 자동 실행하지 않음 |
| plan | argv/소스/SDK hash와 진영 교대 스케줄 저장; 실행 없음 |
| run | 계획된 실제 경기 실행; 새 결과 디렉터리 생성 |
| summarize | 저장된 결과만 집계 |
| bundle | 수정 스킬 3개와 이동 가능한 프로젝트 ZIP 갱신 |

## 재현성

실험 설정은 `experiments/configs/`에 저장한다. agents의 argv는 문자열 배열이며 셸 문법을 지원하지 않는다. `{python}`은 현재 실행 Python, `{policy_seed}`는 계획 seed로 치환된다. 정책 난수 seed를 실제로 받지 않는 봇에 seed 라벨만 바꾸어 반복 실험하지 않는다. C++는 먼저 빌드한 실행 파일의 argv를 지정한다.

결과에는 원시 replay와 결과 JSON을 보존한다. timing은 실제 정상 END 수신까지의 응답값이다. timeout은 정상 응답시간 표본이 아니므로 실패 수와 함께 해석한다. 초기 응답과 일반 턴의 시간을 따로 분석한다. stderr는 총 바이트를 추적하되 내용은 제한된 prefix만 보관한다.

`summarize`의 CI는 한 matchup의 seed-cluster bootstrap이다. 후보 A와 이전 버전 B를 동일 상대 풀에 붙인 결과 차이를 측정할 때는 (A_credit−B_credit)를 같은 seed 묶음에서 구해 별도 paired bootstrap을 한다. 이 둘을 혼용하지 않는다. 통계상 불확실하면 추가 검증 또는 판단 보류로 남긴다.

## 정보 누설

리플레이 map에는 실제 점수가 있다. 디버깅·판정 검증에는 사용할 수 있지만 정책의 실제 관측으로 주지 않는다. 정책 테스트에는 `serialize_turn(state, team, turn)`으로 필터링한 입력을 사용한다. 상대 이번 명령은 simultaneous 의사결정 때 볼 수 없다.

## 출력·시간

SDK 원본 프로세스 writer는 selector를 사용한다. Windows의 pipe 지원 차이 때문에 프로젝트에는 별도 byte-I/O adapter를 둔다. 공식 게임/맵/명령 파서/턴 파이프라인은 바꾸지 않는다. adapter는 출력 한도 초과를 `invalid_output`으로 보고하는 로컬 strict 모드이다. 제공 SDK의 출력 경고 모드와 다른 점을 결과에 표시한다. 서버에서의 CPU·메모리·프로세스·총 인프라 시간 제한은 이 도구가 인증하지 않는다.
