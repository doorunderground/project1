Infinite Stair Game (OpenCv/Python). 2026.01.09
  문지하, 김진수, 구효제

  - 방향 입력(A / D)과 점프(SPACE)를 이용해
    무한히 생성되는 계단을 내려가는 타이밍 게임

[핵심 게임 로직]
1. 계단은 이전 계단 기준으로 좌/우(-1, +1) 중 하나로 랜덤 생성
2. 일정 확률로 'Gap(빈칸)' 계단 생성
   - Gap 다음에는 반드시 정상 계단이 오도록 설계
   - 연속 Gap 발생 방지
3. 플레이어 입력은 각 계단이 요구하는 방향(dir)과 일치해야 성공
4. SPACE 입력 시, Gap을 뛰어넘는 2칸 점프 가능
5. 
<img width="1192" height="877" alt="스크린샷 2026-01-12 094429" src="https://github.com/user-attachments/assets/ce1fa93a-d1bd-4ec9-a29e-cae6fd12be26" width="200" height="200"/>
