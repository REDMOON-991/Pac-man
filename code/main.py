# main.py
import pygame
import math
from settings import *  # 匯入所有設定 (顏色, 大小, 地圖)
from player import Player    # 匯入 Player 類別
from ghost import Ghost      # 匯入 Ghost 類別

# 遊戲初始化
pygame.init()
pygame.font.init()

# 設定視窗 (變數來自 settings.py)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Pac-Man")
clock = pygame.time.Clock()

# --- 日誌系統 ---
game_logs = []  # 儲存字串的列表
MAX_LOGS = 7   # 最多顯示幾行


def log_message(message):
    """ 新增一條訊息到日誌區，並保持長度限制 """
    # 加上時間戳記 (秒數)
    ticks = pygame.time.get_ticks() // 1000
    formatted_msg = f"[{ticks}s] {message}"
    print(formatted_msg)  # 保留終端機輸出方便除錯
    game_logs.append(formatted_msg)
    if len(game_logs) > MAX_LOGS:
        game_logs.pop(0)  # 移除最舊的


def draw_logs(surface):
    """ 繪製底部日誌區 """
    # 1. 畫背景框 (在原本的地圖下方)
    log_area_rect = pygame.Rect(0, MAP_HEIGHT, SCREEN_WIDTH, LOG_HEIGHT)
    pygame.draw.rect(surface, (20, 20, 20), log_area_rect)  # 深灰色背景
    pygame.draw.line(surface, WHITE, (0, MAP_HEIGHT),
                     (SCREEN_WIDTH, MAP_HEIGHT), 2)  # 分隔線

    # 2. 繪製文字
    start_y = MAP_HEIGHT + 10
    for i, msg in enumerate(game_logs):
        text_surf = LOG_FONT.render(msg, True, WHITE)
        surface.blit(text_surf, (10, start_y + i * 18))  # 每行間距 18

# 繪製地圖的函式


# --- 繪圖優化: 靜態背景快取 ---
background_surface = None


def generate_background():
    """ 生成靜態牆壁背景 """
    global background_surface
    background_surface = pygame.Surface((SCREEN_WIDTH, MAP_HEIGHT))
    background_surface.fill(BLACK)

    for y, row in enumerate(GAME_MAP):
        for x, char in enumerate(row):
            rect_x = x * TILE_SIZE
            rect_y = y * TILE_SIZE

            if char == TILE_WALL:
                pygame.draw.rect(background_surface, BLUE,
                                 (rect_x, rect_y, TILE_SIZE, TILE_SIZE))
            elif char == TILE_DOOR:
                pygame.draw.line(background_surface, GREY, (rect_x, rect_y + TILE_SIZE//2),
                                 (rect_x + TILE_SIZE, rect_y + TILE_SIZE//2), 2)
    # 這裡只畫牆和門，豆子必須動態畫


def draw_map():
    # 1. 貼上預先畫好的牆壁背景
    if background_surface:
        screen.blit(background_surface, (0, 0))

    # 2. 動態繪製豆子
    for y, row in enumerate(GAME_MAP):
        for x, char in enumerate(row):
            rect_x = x * TILE_SIZE
            rect_y = y * TILE_SIZE

            if char == TILE_PELLET:
                center_x = rect_x + TILE_SIZE // 2
                center_y = rect_y + TILE_SIZE // 2
                pygame.draw.circle(screen, WHITE, (center_x, center_y), 2)
            elif char == TILE_POWER_PELLET:
                center_x = rect_x + TILE_SIZE // 2
                center_y = rect_y + TILE_SIZE // 2
                pygame.draw.circle(screen, WHITE, (center_x, center_y), 6)


player_lives = MAX_LIVES
current_level = 1
selected_algorithm = ALGO_ASTAR

player = None
ghosts = []
total_pellets = 0
running = True
game_state = GAME_STATE_MENU
frightened_mode = False
frightened_start_time = 0
global_ghost_mode = MODE_SCATTER
frightened_mode = False
frightened_start_time = 0
global_ghost_mode = MODE_SCATTER
last_mode_switch_time = 0
ready_animation_start_time = 0  # Ready 動畫開始時間

path_blinky = [(26, 1), (26, 5), (21, 5), (21, 1)]
path_pinky = [(1, 1), (1, 5), (6, 5), (6, 1)]
path_inky = [(26, 29), (26, 26), (21, 26), (21, 29)]
path_clyde = [(1, 29), (1, 26), (6, 26), (6, 29)]


def init_level(new_level=False):
    """ 重置遊戲所有狀態，回到初始畫面 """
    global player, ghosts, total_pellets, game_state, frightened_mode, global_ghost_mode, last_mode_switch_time, GAME_MAP, game_logs, frightened_start_time

    # 1. 重置地圖 (必須重新從 settings.MAP_STRINGS 生成，因為原本的被吃掉了)
    # 注意：這裡我們使用 [:] 來原地修改列表內容，確保傳參參照正確
    if new_level:
        # 需確保 MAP_STRINGS 已經與 settings 更新過的一致
        GAME_MAP[:] = [list(row) for row in MAP_STRINGS]
        generate_background()  # 重現地圖時，重繪背景
        log_message(f"--- Level {current_level} Started ---")

    old_score = 0
    old_lives = MAX_LIVES

    if player:
        old_score = player.score
        old_lives = player.lives  # 保留生命

    player = Player(14, 23)  # 使用整數座標確保初始對齊 (14, 23)
    player.score = old_score
    player.lives = old_lives

    # 3. 重置鬼魂 (建立新的物件以重置位置和狀態)
    blinky = Ghost(13, 14, RED, ai_mode=AI_CHASE_BLINKY,
                   scatter_point=path_blinky, in_house=True, delay=0, on_log=log_message, algorithm=selected_algorithm)
    pinky = Ghost(14, 14, PINK, ai_mode=AI_CHASE_PINKY,
                  scatter_point=path_pinky, in_house=True, delay=3000, on_log=log_message, algorithm=selected_algorithm)
    inky = Ghost(12, 14, CYAN, ai_mode=AI_CHASE_INKY, scatter_point=path_inky,
                 in_house=True, delay=6000, on_log=log_message, algorithm=selected_algorithm)
    clyde = Ghost(15, 14, ORANGE, ai_mode=AI_CHASE_CLYDE,
                  scatter_point=path_clyde, in_house=True, delay=9000, on_log=log_message, algorithm=selected_algorithm)

    # 更新全域的 ghosts 列表
    ghosts[:] = [blinky, pinky, inky, clyde]

    if new_level:
        total_pellets = sum(row.count(TILE_PELLET) for row in GAME_MAP)
        log_message(f"Total pellets: {total_pellets}")


def reset_game():
    global player_lives, current_level, game_state
    player_lives = MAX_LIVES
    current_level = 1
    game_state = GAME_STATE_MENU
    log_message("Game Reset to Menu")


# 計算總豆子數 (勝利條件)
total_pellets = sum(row.count(TILE_PELLET) for row in GAME_MAP)
generate_background()  # 初始生成背景
log_message(f"Game Loaded! Total pellets:{total_pellets}")
log_message("Press ARROW KEYS to start...")


# * 主迴圈開始
while running:
    dt = clock.tick(60)  # dt is milliseconds

    # 處理輸入
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == GAME_STATE_MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_algorithm = ALGO_GREEDY
                    game_state = GAME_STATE_START
                    init_level(new_level=True)
                elif event.key == pygame.K_2:
                    selected_algorithm = ALGO_BFS
                    game_state = GAME_STATE_START
                    init_level(new_level=True)
                elif event.key == pygame.K_3:
                    selected_algorithm = ALGO_ASTAR
                    game_state = GAME_STATE_START
                    init_level(new_level=True)

        elif game_state == GAME_STATE_START:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    # 按下方向鍵後，先進入 Ready 動畫
                    game_state = GAME_STATE_READY
                    ready_animation_start_time = pygame.time.get_ticks()

                    # 預先處理第一下輸入 (讓玩家可以先按住方向鍵)
                    player.handle_input(event)
        elif game_state == GAME_STATE_PLAYING:
            player.handle_input(event)
        elif game_state in [GAME_STATE_GAME_OVER, GAME_STATE_WIN]:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # 按下 R 鍵
                    reset_game()

    # 遊戲邏輯更新
    if game_state == GAME_STATE_DEATH:
        # 播放死亡動畫
        anim_done = player.update_death_anim()
        if anim_done:
            player.lives -= 1
            if player.lives > 0:
                log_message(f"Lives: {player.lives}, Resetting...")
                init_level(new_level=False)
                game_state = GAME_STATE_READY
                ready_animation_start_time = pygame.time.get_ticks()
            else:
                game_state = GAME_STATE_GAME_OVER
                log_message("Game Over.")

    if game_state == GAME_STATE_PLAYING:

        current_time = pygame.time.get_ticks()

        if not frightened_mode:
            time_passed = current_time - last_mode_switch_time

            if global_ghost_mode == MODE_SCATTER and time_passed > SCATTER_DURATION:
                global_ghost_mode = MODE_CHASE
                last_mode_switch_time = current_time
                log_message(">> Mode Switch: CHASE")

            elif global_ghost_mode == MODE_CHASE and time_passed > CHASE_DURATION:
                global_ghost_mode = MODE_SCATTER
                last_mode_switch_time = current_time
                log_message(">> Mode Switch: SCATTER")

        # 更新所有鬼的狀態 (將全域模式套用到每隻鬼身上)
        # Inky 需要 Blinky 的位置來計算夾擊
        blinky_pos_for_inky = (ghosts[0].grid_x, ghosts[0].grid_y)
        for ghost in ghosts:
            # 如果鬼處於特殊狀態 (回家、出門、等待、被吃、驚嚇)，則不覆蓋它的模式
            if (not ghost.is_frightened and not ghost.is_eaten and ghost.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]):

                if global_ghost_mode == MODE_SCATTER:
                    ghost.current_ai_mode = MODE_SCATTER
                elif global_ghost_mode == MODE_CHASE:
                    # 切換回它原本的追逐個性 (CHASE_BLINKY 等)
                    ghost.current_ai_mode = ghost.ai_mode

            ghost.update(GAME_MAP, player, dt,
                         global_ghost_mode, blinky_pos_for_inky)

        # Frightened (受驚) 模式計時器
        if frightened_mode:
            if current_time - frightened_start_time > FRIGHTENED_DURATION:
                frightened_mode = False
                log_message("Frightened mode ended. Ghosts normal.")
                for ghost in ghosts:
                    ghost.end_frightened()
                last_mode_switch_time = current_time

        # Player 更新
        # 這裡傳入 dt
        player_event = player.update(GAME_MAP, dt)

        # 處理 Player 回傳的意圖 (SoC: 地圖修改移到這裡)
        if player_event:
            px, py = player.get_grid_pos()

            # Double check (防止多重觸發)
            if GAME_MAP[py][px] in [TILE_PELLET, TILE_POWER_PELLET]:
                # 這裡真正移除豆子
                if player_event == EVENT_ATE_PELLET:
                    GAME_MAP[py][px] = TILE_EMPTY
                    total_pellets -= 1
                    player.score += PELLELETS_POINT

                elif player_event == EVENT_ATE_POWER_PELLET:
                    GAME_MAP[py][px] = TILE_EMPTY
                    player.score += POWER_PELLET_POINT
                    frightened_mode = True
                    frightened_start_time = pygame.time.get_ticks()
                    log_message("Power Pellet eaten! Ghosts Frightened!")
                    for ghost in ghosts:
                        ghost.start_frightened()

        # 勝利檢查
        if total_pellets <= 0:
            game_state = GAME_STATE_WIN
            log_message("VICTORY! All pellets cleared!")

        # 碰撞偵測
        for ghost in ghosts:
            # 這裡還是需要簡單的距離計算，所以 import math
            dx = player.pixel_x - ghost.pixel_x
            dy = player.pixel_y - ghost.pixel_y
            distance = math.hypot(dx, dy)
            collision_distance = player.radius + ghost.radius

            if distance < collision_distance:
                if ghost.is_frightened:
                    # 吃鬼
                    ghost.eat()
                    player.score += GHOST_POINT
                elif not ghost.is_eaten:    # 防止玩家碰到已經被吃掉，正在跑回重生的鬼時誤觸發遊戲結束
                    # 被鬼抓
                    log_message("Ghost collision!")
                    game_state = GAME_STATE_DEATH
                    player.start_death_anim()

    # 畫面繪製
    screen.fill(BLACK)

    if game_state == GAME_STATE_MENU:
        title = WIN_FONT.render("PAC-MAN AI SELECT", True, YELLOW)
        t_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        screen.blit(title, t_rect)

        opt1 = SCORE_FONT.render("Press 1 for Greedy (Shortest)", True, WHITE)
        opt2 = SCORE_FONT.render("Press 2 for BFS (Wide Search)", True, WHITE)
        opt3 = SCORE_FONT.render("Press 3 for A* (Smartest)", True, WHITE)

        screen.blit(opt1, (50, SCREEN_HEIGHT//2))
        screen.blit(opt2, (50, SCREEN_HEIGHT//2 + 40))
        screen.blit(opt3, (50, SCREEN_HEIGHT//2 + 80))

    else:
        # 使用新的繪圖函式 (內部有 cache)
        draw_map()

        # 正常狀態下繪製玩家
        if game_state != GAME_STATE_DEATH:
            player.draw(screen)

        # 只有在非死亡狀態才繪製鬼魂
        if game_state != GAME_STATE_DEATH:
            for ghost in ghosts:
                ghost.draw(screen)

        draw_logs(screen)

        # 繪製分數
        # True: 開啟 anti-aliasing (反鋸齒)
        score_text = SCORE_FONT.render(
            f"SCORE: {int(player.score)}", True, WHITE)
        screen.blit(score_text, (10, MAP_HEIGHT + 10))  # 稍微往下移到 Log 區塊上方

        # 繪製生命值 (圖示)
        lives_text = SCORE_FONT.render("LIVES:", True, WHITE)
        screen.blit(lives_text, (SCREEN_WIDTH - 150, MAP_HEIGHT + 10))
        for i in range(player.lives):
            # 畫黃色小圓代表生命
            cx = SCREEN_WIDTH - 90 + i * 25
            cy = MAP_HEIGHT + 18
            pygame.draw.circle(screen, YELLOW, (cx, cy), 8)
            # 簡單畫個嘴巴缺口 (用黑線蓋掉) - 或是之後用 Sprite
            # 这里先画简单的

        # 繪製中心文字 (開始、勝利、失敗)
        center_pos = (SCREEN_WIDTH // 2, MAP_HEIGHT // 2)
        if game_state == GAME_STATE_START:
            start_text = WIN_FONT.render("READY!", True, YELLOW)
            hint_text = SCORE_FONT.render(
                "Press ARROW KEYS to Start", True, WHITE)

            r1 = start_text.get_rect(center=center_pos)
            r2 = hint_text.get_rect(center=(center_pos[0], center_pos[1] + 40))

            screen.blit(start_text, r1)
            screen.blit(hint_text, r2)

            # Reset Player Position visual bug fix (ensure it draws correctly on start)
            if player:
                player.draw(screen)

        elif game_state == GAME_STATE_READY:
            # Ready -> GO 動畫
            current_ticks = pygame.time.get_ticks()
            elapsed = current_ticks - ready_animation_start_time

            if elapsed < 2000:  # 前 2 秒顯示 READY
                ready_text = WIN_FONT.render("READY!", True, YELLOW)
                rr = ready_text.get_rect(center=center_pos)
                screen.blit(ready_text, rr)
            elif elapsed < 3000:  # 第 2-3 秒顯示 GO!
                go_text = WIN_FONT.render("GO!", True, GREEN)  # 使用綠色
                gr = go_text.get_rect(center=center_pos)
                screen.blit(go_text, gr)
            else:
                # 時間到，正式開始
                game_state = GAME_STATE_PLAYING
                last_mode_switch_time = pygame.time.get_ticks()
                log_message(
                    f"Level {current_level} Start! Algo: {selected_algorithm}")

        elif game_state == GAME_STATE_DEATH:
            # 死亡動畫狀態，只畫地圖和正在變化的 player
            player.draw(screen)

        elif game_state == GAME_STATE_GAME_OVER:
            text = GAME_OVER_FONT.render("GAME OVER", True, RED)
            rect = text.get_rect(center=center_pos)
            screen.blit(text, rect)
            restart_text = SCORE_FONT.render("Press R to Restart", True, WHITE)
            r_rect = restart_text.get_rect(
                center=(center_pos[0], center_pos[1] + 50))
            screen.blit(restart_text, r_rect)

        elif game_state == GAME_STATE_WIN:
            text = WIN_FONT.render("YOU WIN!", True, YELLOW)
            rect = text.get_rect(center=center_pos)
            screen.blit(text, rect)
            restart_text = SCORE_FONT.render(
                "Press R to Play Again", True, WHITE)
            r_rect = restart_text.get_rect(
                center=(center_pos[0], center_pos[1] + 50))
            screen.blit(restart_text, r_rect)

    pygame.display.flip()

pygame.quit()
