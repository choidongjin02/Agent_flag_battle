# 방법 선택

프로젝트 `docs/research/AGENT_METHODS.md`: M1 임무 할당, M2 강건 MPC, M3 PGS, M4 동시행동 행렬게임, M5 CMAB, M6 RHCA와 공통 모델.

`docs/research/RESEARCH_PRIORITIES.md`: M7 비대칭 국소 탐색, O1 행동 fingerprint, O2 상대 archive, O3 NTBEA. 추천 출발점은 M1→M7. 전체 탐색기를 모두 구현할 요구가 아니다.

핵심 논문:

- [Moraes et al., 2022](https://webdocs.cs.ualberta.ca/~santanad/papers/2022/moraesNL22.pdf): 중요 유닛만 자유도를 높이는 비대칭 추상화.
- [Churchill & Buro, 2013](https://davechurchill.ca/publications/pdf/combat13.pdf): 스크립트 조합 PGS.
- [Moraes & Lelis, 2024](https://arxiv.org/abs/2405.05431): 실제 행동이 다른 정책 후보의 탐색 효율.
- [Moraes et al., 2023](https://arxiv.org/abs/2307.04893): 유용한 참조 상대 선택.
- [Lucas et al., 2018](https://arxiv.org/abs/1802.05991): 잡음 있는 대전 결과의 파라미터 튜닝.

논문 성능을 이 게임의 측정치로 옮기지 않는다. 게임별 HP·사거리·충돌 규칙도 복사하지 않는다. 전체 전략의 목적은 실제 종료 승패이며, 경제·누적 점수·영향력은 비종료 상태의 대리 평가다. 동일 후보·평가·예산에서 planner 차이를 비교한다.
