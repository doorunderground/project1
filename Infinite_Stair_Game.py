'''
###################################################################
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

[난이도 설계]
 - STAGE_STEP마다 스테이지 상승
 - 스테이지가 올라갈수록
   · 입력 제한 시간 감소
   · Gap 생성 확률 증가
   · 배경색 변화로 시각적 압박 증가
   
[시간 압박 시스템]
 - 각 입력마다 제한 시간 존재
 - 제한 시간 초과 시 즉시 낙하 (TIME OVER)

 [낙하 & Game Over 처리]
 - 입력 실패 / 시간 초과 시 캐릭터 낙하
 - 화면 밖으로 완전히 벗어났을 때 Game Over 확정

 [이스터에그 시스템]
 - 특정 점수(EASTER_EGG_SCORE) 이상 도달 후
 - 해당 판에서 '죽었을 때만' 이스터에그 엔딩 출력
 - 프로그램 실행 중 1회만 표시되도록 상태 분리 관리
   (easter_egg_unlocked / easter_egg_consumed)

 [시각 효과]
 - 착지한 계단에 상하·좌우 흔들림(Wobble) 효과 적용
 - 상단 Time Bar로 남은 입력 시간 시각화   
###################################################################
'''

import cv2
import numpy as np
import random
import time
import math

#기본설정
WIDTH, HEIGHT = 800, 600
STAIR_W, STAIR_H = 130, 30
CHAR_W, CHAR_H = 40, 40

NUM_STEPS = 10000
STAGE_STEP = 10
BASE_TIME_LIMIT = 2

#이스터에그 추가
EASTER_EGG_SCORE = 300
GIFTICON_SERIAL = "9246-9351-5784"
easter_egg_unlocked = False
easter_egg_consumed = False


#BGR 배경화면
BG_COLORS = [
    (240, 240, 240), #white
    (0, 255, 255), #yellow
    (0, 255, 0), #green
    (120, 0, 250), #pink
    (40, 40, 250), #red
    (255, 0, 0), #blue
    (90, 90, 90), #black
    (70, 70, 70),
    (65, 65, 65),
    (62, 62, 62)
]

def get_bg_color(stage: int):
    i = min(stage - 1, len(BG_COLORS) - 1)
    return BG_COLORS[i]


#계단 흔들림
WOBBLE_DURATION = 0.30  
WOBBLE_X_AMP = 2 
WOBBLE_Y_AMP = 5  

WOBBLE_X_FREQ = 55      
WOBBLE_Y_FREQ = 48        
 

# 현재 출렁이는 계단 정보(착지한 계단만 흔들리게)
wobble_stair_idx = None
wobble_start_time = 0.0

def get_wobble_offsets(step_index):
    if wobble_stair_idx is None or step_index != wobble_stair_idx:
        return 0, 0

    t = time.time() - wobble_start_time
    if t < 0 or t > WOBBLE_DURATION:
        return 0, 0

    p = t / WOBBLE_DURATION
    decay = (1.0 - p)  # 선형 감쇠

    oy = WOBBLE_Y_AMP * math.sin(2 * math.pi * WOBBLE_Y_FREQ * t) * decay #위아래 흔들림
    ox = WOBBLE_X_AMP * math.sin(2 * math.pi * WOBBLE_X_FREQ * t + math.pi / 2) * decay #좌우로 흔들림

    return int(ox), int(oy)



# =====================
#        Func()
# =====================
def get_stage(idx):
    return idx // STAGE_STEP + 1
'''
    몇번째 stage인지 계산해주는 함수
    0~9번째 계단? -> stage 1
    10~19번째 계단? -> stage 2
'''

def time_limit(stage):
    return max(0.6, BASE_TIME_LIMIT - 0.15 * (stage - 1))
'''
    stage가 올라갈수록, 허용 입력 시간이 점점 줄어듦
    stage 1 -> 2초
    stage 2 -> 1.85초
    stage 3 -> 1.6초
    최소 0.6초로 설정
'''

def gap_probability(stage):
    return min(0.1 * (stage - 1), 0.6)
'''
    Gap(빈칸)이 나올 학률 조절
    stage 1 -> 0%        
    stage 2 -> 10%
    stage 3 -> 20%
    stage 4 -> 30$ 
    최대 확률은 60%로 설정
'''


#랜덤된 계단 생성
def create_step(prev, stage):
    if prev["type"] == "gap":  #이전 계단이 '빈칸' 이었어??
        d = prev["dir"]        #그럼 '무조건' 정상 계단을 만들어  왼쪽-1, 오른쪽+1 인 계단을 만들어
        return {
            "x": prev["x"] + d * STAIR_W, 
            "y": prev["y"] + STAIR_H,
            "dir": d,
            "type": "normal"
        }
    '''
        pre : 이전 계단의 정보  "x(위치)": 230, "y(위치)": 80, "dir(정답)": 1/-1, "type":빈칸/그냥
        stage : stage 번호 - 난이도
        연속된 '빈칸'을 방지하는 것이 목적
    '''
    
    
    
    '''
        Random으로 Gap(빈칸)이 나오게 된다면  
        ㅁ
            [??]
                   ㅁ
          +1칸   +2칸
        gap_x : 빈칸이 생길 위치
        land_x : 점프 후 착지할 위치
    '''
    is_gap = random.random() < gap_probability(stage)
    if is_gap:
        candidates = []
        for d in (-1, 1): # Gap을 왼쪽으로 만들지, 오른쪽으로 만들지 check
            gap_x = prev["x"] + d * STAIR_W
            land_x = prev["x"] + d * STAIR_W * 2
            if 0 <= gap_x <= WIDTH - STAIR_W and 0 <= land_x <= WIDTH - STAIR_W: #화면 밖으로 안나가게 check
                candidates.append(d)

        if candidates:  #이를 만족하는 후보가 하나라도 있어??? 그럼 빈칸 만들어
            d = random.choice(candidates)
            return {
                "x": prev["x"] + d * STAIR_W,
                "y": prev["y"] + STAIR_H,
                "dir": d,
                "type": "gap"
            }
            
            
    while True: #정상계단 생성
        d = random.choice([-1, 1])  #왼쪽이든 오른쪽이든 화면 안에 들어오는 방향을 골라서 계단 만들어 
        new_x = prev["x"] + d * STAIR_W 
        if 0 <= new_x <= WIDTH - STAIR_W:
            break

    return {
        "x": new_x,
        "y": prev["y"] + STAIR_H,
        "dir": d,
        "type": "normal"
    }
    
    
'''
    'R' 눌렀을 때 RESTART
'''
def reset_game():
    global stairs, idx, scroll_offset
    global char_x, char_y
    global input_time, game_over, game_over_reason
    global high_score
    global wobble_stair_idx, wobble_start_time
    global is_falling, fall_speed
    global easter_egg_unlocked
    
    easter_egg_unlocked = False

    is_falling = False
    fall_speed = 0
    
    stairs = []
    idx = 0
    scroll_offset = 0
    game_over = False
    game_over_reason = " "

    start_x = WIDTH // 2 - STAIR_W // 2
    start_y = 200

    stairs.append({
        "x": start_x,
        "y": start_y,
        "dir": None,
        "type": "normal"
    })

    for i in range(NUM_STEPS - 1):
        stairs.append(create_step(stairs[-1], get_stage(i)))

    char_x = stairs[0]["x"] + STAIR_W // 2 - CHAR_W // 2
    char_y = stairs[0]["y"] - CHAR_H

    input_time = time.time()

    wobble_stair_idx = None
    wobble_start_time = 0.0
    

high_score = 0
reset_game()


'''
    main -> 시작 
'''
while True:
    stage = get_stage(idx)
    bg = get_bg_color(stage)
    img = np.full((HEIGHT, WIDTH, 3), bg, dtype=np.uint8)    
#   img = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8) * 240 #흰배경 (1,1,1)*240 -> (240, 240, 240)
#   img = np.full((HEIGHT, WIDTH, 3), 255, dtype = np.uint8) -> (255, 255, 255)
#   img = np.zeros((HEIGHT, WIDTH, 3), dtype = np,uint8) (0, 0, 0) -> 검은 화면
    
    key = cv2.waitKey(40) & 0xFF #입력값(key)을 이용해서 ('q', 'r', 'spacebar') 값을 다룸 

    if key == ord('q'): # ord = 키보드 입력값을 유니코드로 바꿔줌 
        break
    
    '''
        이스터에그 화면
    '''
    if game_over_reason == "EASTER_EGG":
        cv2.putText(img, "CONGRATULATIONS!", (WIDTH//2 - 250, HEIGHT//2 - 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 0), 4)
        cv2.putText(img, f"YOU PASSED {EASTER_EGG_SCORE}!", (WIDTH//2 - 160, HEIGHT//2 - 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)

        cv2.putText(img, "GIFTICON SERIAL", (WIDTH//2 - 165, HEIGHT//2 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        cv2.putText(img, GIFTICON_SERIAL, (WIDTH//2 - 210, HEIGHT//2 + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 255), 4)

        cv2.putText(img, f"FINAL SCORE: {idx}", (WIDTH//2 - 150, HEIGHT//2 + 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        cv2.putText(img, f"HIGH SCORE: {high_score}", (WIDTH//2 - 145, HEIGHT//2 + 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

        cv2.putText(img, "[R] TO RESTART", (WIDTH//2 - 150, HEIGHT//2 + 210),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
        cv2.putText(img, "[Q] TO QUIT", (WIDTH//2 - 150, HEIGHT//2 + 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

        cv2.imshow("Infinite Stair", img)

        if key == ord('r'):
            high_score = max(high_score, idx)
            reset_game()
        continue
    '''
        Game over 화면
    '''
    if game_over:
        if game_over_reason == "TIME OVER":
            title = "'TIME OVER'"
        else:
            title = "'GAME OVER'"

        cv2.putText(img, title, (WIDTH//2 - 300, HEIGHT//2 - 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 6)                         
        cv2.putText(img, f"FINAL SCORE: {idx}", (WIDTH//2 - 170, HEIGHT//3 + 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
        cv2.putText(img, f"HIGH SCORE: {high_score}", (WIDTH//2 - 170, HEIGHT//3 + 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
        cv2.putText(img, "[R] TO RESTART", (WIDTH//2 - 180, HEIGHT//2 + 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        cv2.putText(img, "[Q] TO QUIT", (WIDTH//2 - 180, HEIGHT//2 + 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
        cv2.imshow("Infinite Stair", img)

        if key == ord('r'):
            high_score = max(high_score, idx) #현재 기록과 high_score를 비교하겠지?
            reset_game()
        continue
    
    
    '''
        낙하 로직
    '''
    if is_falling:
        # 키 입력 무시하고 떨어지기만 함
        char_y += fall_speed
        fall_speed += 3  # 중력 가속도
        
        # 화면 밖으로 완전히 나갔는지 확인
        if char_y > HEIGHT:
            if easter_egg_unlocked and (not easter_egg_consumed):
                game_over_reason = "EASTER_EGG"
                easter_egg_consumed = True
            game_over = True   
    else:
        # 1. 시간 계산 먼저 수행
        elapsed = time.time() - input_time
        limit = time_limit(stage)
        
        # 2. 시간 초과 체크
        if elapsed > limit: 
            is_falling = True      # 떨어지기 시작! (Game Over 아님)
            fall_speed = 5
            game_over_reason = "TIME OVER"
    
    
            '''
            우리가 key를 눌렀을 때 그 입력이 맞는지/틀렸는지 판단하고,
            다음 계단으로 이동시키는 '핵심 로직'
            '''
        elif key in (ord('a'), ord('d'), ord(' ')):
            success = True #이번 입력이 실패 or 성공인지 판단하기 위한 flag

            if key == ord(' '): 
                if idx + 2 >= len(stairs) or stairs[idx + 1]["type"] != "gap":             
                    success = False # 실패
                # 점프하면 2칸 앞으로 가야하는데 그 위치가 계단 배열 범위를 넘으면 안됨      
                # or 다음 계단은 반드시 빈칸('Gap')이여야 함
                    '''
                        블럭 
                            ?(Gap)
                                  블럭
                    '''                   
                else:
                    idx += 2 # 현재 계단 -> 2칸 앞으로 이동
                    scroll_offset += STAIR_H * 2
                    
            else:
                if key == ord('a'):  #이제부터 'a' 키를 = -1로 볼거임 
                    input_dir = -1
                else:                # 'd' 키를 1로 볼거임
                    input_dir = 1
                    
                if idx+1 < len(stairs): # 다음 계단이 존재하는지 확인
                    next_step = stairs[idx + 1] #있으면? 이동
                else:
                    next_step = None 
                
                if not next_step or next_step["type"] == "gap" or input_dir != next_step["dir"]:  
                    success = False
                # 다음 계단이 없거나?, 빈계단이다?, 내가 누른 방향이 계단이 요구하는 방향과 다르다? -> 실패    
                else:
                    idx += 1
                    scroll_offset += STAIR_H

            if success == False: 
                is_falling = True   # 떨어지기 시작!
                fall_speed = 5 
                game_over_reason = "WRONG"
            
            else:
                #흔들릴 계단 정보
                wobble_stair_idx = idx  
                wobble_start_time = time.time()
            
                #캐릭터가 계단 중앙에 정확히 위치하기
                char_x = stairs[idx]["x"] + STAIR_W // 2 - CHAR_W // 2
                char_y = stairs[idx]["y"] - scroll_offset - CHAR_H

                input_time = time.time() #키보드 입력 타임어택 시작 -> 일정 시간 안에 입력 못 하면 Game over
        
        
        
                # =========================
                # Stage = 300 돌파 
                # =========================
                if (idx >= EASTER_EGG_SCORE) and (not easter_egg_consumed):
                    easter_egg_unlocked = True
        
        
        if not is_falling:
            char_y = stairs[idx]["y"] - scroll_offset - CHAR_H
        
        if is_falling:
            elapsed = time.time() - input_time
            limit = time_limit(stage)
    
    cur_ox, cur_oy = get_wobble_offsets(idx)
    
    
    
    #계단 그려주는
    for i, s in enumerate(stairs):
        if s["type"] == "gap":    #type : 빈칸?? -> 그릴 계단이 아니니깐
            continue              #for 전체 skip

        draw_y = s["y"] - scroll_offset

        ox, oy = get_wobble_offsets(i)
        draw_x = s["x"] + ox
        draw_y = draw_y + oy
        
        #계단 그려주는
        if -STAIR_H < draw_y < HEIGHT:
            cv2.rectangle(img, (draw_x, draw_y), 
                        (draw_x + STAIR_W, draw_y + STAIR_H), (60, 60, 60), -1)
        

    '''
        게임 중 UI
    '''
    #캐릭터
    cv2.rectangle(img, (char_x, char_y), (char_x + CHAR_W, char_y + CHAR_H), (255, 120, 50), -1)

    #상단 '시간바'
    remain_ratio = max(0.0, 1.0 - elapsed / limit)
    cv2.rectangle(img, (0, 0), (int(WIDTH * remain_ratio), 15), (50, 200, 50), -1)

    cv2.putText(img, f"STEP: {idx}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(img, f"HIGH: {high_score}", (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

    cv2.imshow("Infinite Stair", img)

cv2.destroyAllWindows()
a