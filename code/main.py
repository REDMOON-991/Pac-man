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
# display_surface 是實際的視窗
WINDOW_WIDTH = int(SCREEN_WIDTH * 1.0)  # 預設視窗寬度
WINDOW_HEIGHT = int(SCREEN_HEIGHT * 1.0)  # 預設視窗高度
display_surface = pygame.display.set_mode(
    (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Pygame Pac-Man (F11: Fullscreen)")

# (改動) 分離畫布：game_content_surface 只包含地圖與遊戲內容
GAME_CONTENT_HEIGHT = MAP_HEIGHT  # 720
game_content_surface = pygame.Surface((SCREEN_WIDTH, GAME_CONTENT_HEIGHT))
clock = pygame.time.Clock()

# --- 日誌系統 ---
game_logs = []  # 儲存字串的列表
MAX_LOGS = 6   # 減少行數以確保不會超出 (Log高度 140, 字體 20, 間距 ~20 -> 7行極限, 保險設6)


def log_message(message, color=WHITE):
    """ 新增一條訊息到日誌區，並保持長度限制 """
    # 加上時間戳記 (秒數)
    ticks = pygame.time.get_ticks() // 1000
    formatted_msg = f"[{ticks}s] {message}"
    print(formatted_msg)  # 保留終端機輸出方便除錯
    game_logs.append((formatted_msg, color))  # 存成 Tuple (文字, 顏色)
    if len(game_logs) > MAX_LOGS:
        game_logs.pop(0)  # 移除最舊的


def draw_controls_on_surface(target_surface, x, y, width, height):
    """ 繪製操作說明面板 """
    # 背景
    rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(target_surface, (20, 20, 20), rect)
    pygame.draw.rect(target_surface, BLUE, rect, 2)  # 藍色外框

    # 標題
    title = SCORE_FONT.render("- CONTROLS -", True, YELLOW)
    target_surface.blit(title, (x + 20, y + 15))

    # 說明列表
    controls = [
        ("ARROW KEYS", "Move"),
        ("P or ESC", "Pause/Resume"),
        ("F11", "Fullscreen"),
        ("Q", "Quit (in Menu/Pause)"),
        ("R", "Restart (End Game)"),
    ]

    start_y = y + 50
    for key, action in controls:
        key_surf = LOG_FONT.render(key, True, CYAN)
        action_surf = LOG_FONT.render(action, True, WHITE)

        target_surface.blit(key_surf, (x + 20, start_y))
        target_surface.blit(action_surf, (x + 20, start_y + 20))
        start_y += 50


def draw_logs_on_surface(target_surface, x, y, width, height):
    """ 
    在指定的 Surface 區域繪製日誌 
    x, y: 相對 target_surface 的起始座標
    """
    # 1. 畫背景框
    log_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(target_surface, (20, 20, 20), log_rect)
    pygame.draw.rect(target_surface, GREY, log_rect, 2)  # 外框

    # 標題
    title = LOG_FONT.render("Game Logs:", True, GREY)
    target_surface.blit(title, (x + 5, y + 5))

    # 2. 繪製文字
    start_y = y + 25
    line_spacing = 20
    for i, (msg, color) in enumerate(game_logs):  # 解包 (msg, color)
        # 防止超出邊界
        if start_y + i * line_spacing > y + height - 10:
            break

        text_surf = LOG_FONT.render(msg, True, color)
        target_surface.blit(text_surf, (x + 10, start_y + i * line_spacing))

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
        game_content_surface.blit(background_surface, (0, 0))

    # 2. 動態繪製豆子
    for y, row in enumerate(GAME_MAP):
        for x, char in enumerate(row):
            rect_x = x * TILE_SIZE
            rect_y = y * TILE_SIZE

            if char == TILE_PELLET:
                center_x = rect_x + TILE_SIZE // 2
                center_y = rect_y + TILE_SIZE // 2
                pygame.draw.circle(game_content_surface,
                                   WHITE, (center_x, center_y), 2)
            elif char == TILE_POWER_PELLET:
                center_x = rect_x + TILE_SIZE // 2
                center_y = rect_y + TILE_SIZE // 2
                pygame.draw.circle(game_content_surface, WHITE,
                                   (center_x, center_y), 6)


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
        log_message(f"--- Level {current_level} Started ---", YELLOW)

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
        log_message(f"Total pellets: {total_pellets}", WHITE)


def reset_game():
    global player_lives, current_level, game_state, player
    player_lives = MAX_LIVES
    current_level = 1
    game_state = GAME_STATE_MENU
    player = None  # 清除舊玩家物件，確保分數重置
    log_message("Game Reset to Menu", YELLOW)


# 計算總豆子數 (勝利條件)
total_pellets = sum(row.count(TILE_PELLET) for row in GAME_MAP)
generate_background()  # 初始生成背景
log_message(f"Game Loaded! Total pellets:{total_pellets}", GREEN)
log_message("Press ARROW KEYS to start...", YELLOW)


# * 主迴圈開始
is_fullscreen = False
while running:
    dt = clock.tick(60)  # dt is milliseconds

    # 處理輸入
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                if is_fullscreen:
                    display_surface = pygame.display.set_mode(
                        (0, 0), pygame.FULLSCREEN)
                else:
                    display_surface = pygame.display.set_mode(
                        (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)

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
        elif game_state == GAME_STATE_PAUSED:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    game_state = GAME_STATE_PLAYING
                    log_message("Game Resumed", GREEN)
                elif event.key == pygame.K_q:
                    game_state = GAME_STATE_MENU
                    reset_game()
                elif event.key == pygame.K_r:
                    # 選項：允許暫停時重新開始
                    reset_game()
        elif game_state == GAME_STATE_PLAYING:
            player.handle_input(event)
            # 暫停鍵偵測
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    game_state = GAME_STATE_PAUSED
                    log_message("Game Paused", YELLOW)

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
                log_message(f"Lives: {player.lives}, Resetting...", YELLOW)
                init_level(new_level=False)
                game_state = GAME_STATE_READY
                ready_animation_start_time = pygame.time.get_ticks()
            else:
                game_state = GAME_STATE_GAME_OVER
                log_message("Game Over.", RED)

    if game_state == GAME_STATE_PLAYING:

        current_time = pygame.time.get_ticks()

        if not frightened_mode:
            time_passed = current_time - last_mode_switch_time

            # 確保初始提示
            if last_mode_switch_time == 0 and time_passed > 100:  # 稍微延遲一點確保顯示
                log_message(f">> Init Mode: {global_ghost_mode}", YELLOW)

            if global_ghost_mode == MODE_SCATTER and time_passed > SCATTER_DURATION:
                global_ghost_mode = MODE_CHASE
                last_mode_switch_time = current_time
                log_message(">> Mode Switch: CHASE", RED)

            elif global_ghost_mode == MODE_CHASE and time_passed > CHASE_DURATION:
                global_ghost_mode = MODE_SCATTER
                last_mode_switch_time = current_time
                log_message(">> Mode Switch: SCATTER", GREEN)

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
                log_message("Frightened mode ended. Ghosts normal.", WHITE)
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
                    log_message("Power Pellet eaten! Ghosts Frightened!", CYAN)
                    for ghost in ghosts:
                        ghost.start_frightened()

        # 勝利檢查
        if total_pellets <= 0:
            game_state = GAME_STATE_WIN
            log_message("VICTORY! All pellets cleared!", GREEN)

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
                    log_message("Ghost collision!", RED)
                    game_state = GAME_STATE_DEATH
                    player.start_death_anim()

    # -------------------------------------------------------------
    # 3. 繪製階段 (Render Phase)
    # -------------------------------------------------------------

    # A. 先將遊戲內容畫到 game_content_surface (560x720)
    game_content_surface.fill(BLACK)

    if game_state == GAME_STATE_MENU:
        title = WIN_FONT.render("PAC-MAN AI SELECT", True, YELLOW)
        t_rect = title.get_rect(
            center=(SCREEN_WIDTH//2, GAME_CONTENT_HEIGHT//3))
        game_content_surface.blit(title, t_rect)

        opt1 = SCORE_FONT.render("Press 1 for Greedy (Shortest)", True, WHITE)
        opt2 = SCORE_FONT.render("Press 2 for BFS (Wide Search)", True, WHITE)
        opt3 = SCORE_FONT.render("Press 3 for A* (Smartest)", True, WHITE)

        game_content_surface.blit(opt1, (50, GAME_CONTENT_HEIGHT//2))
        game_content_surface.blit(opt2, (50, GAME_CONTENT_HEIGHT//2 + 40))
        game_content_surface.blit(opt3, (50, GAME_CONTENT_HEIGHT//2 + 80))

    else:
        # 使用新的繪圖函式
        draw_map()

        if game_state != GAME_STATE_DEATH:
            player.draw(game_content_surface)

        if game_state != GAME_STATE_DEATH:
            for ghost in ghosts:
                ghost.draw(game_content_surface)

        # 移除 draw_logs()，改在最後 Layout 階段繪製

        # 繪製分數 (畫在最下方，因為 game_content_surface 正好包含了原本 HUD 的區域?
        # 等等，MAP_HEIGHT 是 720。但原本 Score 畫在 MAP_HEIGHT + 10。
        # 我們的 game_content_surface 只有 720 高。
        # 所以分數應該要畫在地圖"上" 或是 我們需要稍微加大 game_content_surface?
        # 檢查 setting: SCREEN_WIDTH=560, MAP_HEIGHT=720.
        # 其實原本的設計 Score 是畫在 Log 區塊上方的 (y=730).
        # 讓我們把 game_content_surface 加大一點點，包含 HUD 資訊 (但不包含 Log)
        # 或者直接畫在地圖最上面?
        # 為了美觀，我們將 Score 畫在地圖頂部 (如果有的話) 或底部覆蓋。
        # 這裡決定：把 分數 畫在左上角 (5, 5)
        score_text = SCORE_FONT.render(
            f"SCORE: {int(player.score)}", True, WHITE)
        game_content_surface.blit(score_text, (10, 10))

        # 生命值畫在右上角
        lives_text = SCORE_FONT.render("LIVES:", True, WHITE)
        game_content_surface.blit(lives_text, (SCREEN_WIDTH - 150, 10))
        for i in range(player.lives):
            cx = SCREEN_WIDTH - 90 + i * 25
            cy = 18
            pygame.draw.circle(game_content_surface, YELLOW, (cx, cy), 8)

        # 繪製中心文字
        center_pos = (SCREEN_WIDTH // 2, GAME_CONTENT_HEIGHT // 2)
        if game_state == GAME_STATE_START:
            start_text = WIN_FONT.render("READY!", True, YELLOW)
            hint_text = SCORE_FONT.render(
                "Press ARROW KEYS to Start", True, WHITE)
            r1 = start_text.get_rect(center=center_pos)
            r2 = hint_text.get_rect(center=(center_pos[0], center_pos[1] + 40))
            game_content_surface.blit(start_text, r1)
            game_content_surface.blit(hint_text, r2)
            if player:
                player.draw(game_content_surface)

        elif game_state == GAME_STATE_READY:
            # Ready -> GO 動畫 ... (略，邏輯不變，只需改 blit 目標)
            current_ticks = pygame.time.get_ticks()
            elapsed = current_ticks - ready_animation_start_time
            if elapsed < 2000:
                ready_text = WIN_FONT.render("READY!", True, YELLOW)
                rr = ready_text.get_rect(center=center_pos)
                game_content_surface.blit(ready_text, rr)
            elif elapsed < 3000:
                go_text = WIN_FONT.render("GO!", True, GREEN)
                gr = go_text.get_rect(center=center_pos)
                game_content_surface.blit(go_text, gr)
            else:
                game_state = GAME_STATE_PLAYING
                last_mode_switch_time = pygame.time.get_ticks()
                log_message(
                    f"Level {current_level} Start! Algo: {selected_algorithm}", YELLOW)

        elif game_state == GAME_STATE_DEATH:
            player.draw(game_content_surface)

        elif game_state == GAME_STATE_PAUSED:
            draw_map()
            player.draw(game_content_surface)
            for ghost in ghosts:
                ghost.draw(game_content_surface)

            overlay = pygame.Surface((SCREEN_WIDTH, GAME_CONTENT_HEIGHT))
            overlay.fill(BLACK)
            overlay.set_alpha(128)
            game_content_surface.blit(overlay, (0, 0))

            p_text = WIN_FONT.render("PAUSED", True, YELLOW)
            p_rect = p_text.get_rect(center=center_pos)
            game_content_surface.blit(p_text, p_rect)

            resume_text = SCORE_FONT.render(
                "Press P / ESC to Resume", True, WHITE)
            r_rect = resume_text.get_rect(
                center=(center_pos[0], center_pos[1] + 40))
            game_content_surface.blit(resume_text, r_rect)

            quit_text = SCORE_FONT.render(
                "Press Q to Quit to Menu", True, WHITE)
            q_rect = quit_text.get_rect(
                center=(center_pos[0], center_pos[1] + 70))
            game_content_surface.blit(quit_text, q_rect)

        elif game_state == GAME_STATE_GAME_OVER:
            text = GAME_OVER_FONT.render("GAME OVER", True, RED)
            rect = text.get_rect(center=center_pos)
            game_content_surface.blit(text, rect)
            restart_text = SCORE_FONT.render("Press R to Restart", True, WHITE)
            r_rect = restart_text.get_rect(
                center=(center_pos[0], center_pos[1] + 50))
            game_content_surface.blit(restart_text, r_rect)

        elif game_state == GAME_STATE_WIN:
            text = WIN_FONT.render("YOU WIN!", True, YELLOW)
            rect = text.get_rect(center=center_pos)
            game_content_surface.blit(text, rect)
            restart_text = SCORE_FONT.render(
                "Press R to Play Again", True, WHITE)
            r_rect = restart_text.get_rect(
                center=(center_pos[0], center_pos[1] + 50))
            game_content_surface.blit(restart_text, r_rect)

    # -------------------------------------------------------------
    # B. 響應式佈局 (Responsive Layout)
    # -------------------------------------------------------------
    display_w, display_h = display_surface.get_size()
    display_surface.fill(BLACK)  # 清空底色

    # 判斷長寬比
    aspect_ratio = display_w / display_h

    # 定義佈局閾值 (1.2 表示稍微寬一點的螢幕就切換)
    if aspect_ratio > 1.2:
        # --- 寬螢幕模式 (Wide Mode): 左圖右 Log ---

        # 1. 遊戲畫面縮放至螢幕高度 (留一點邊距)
        target_h = display_h
        scale = target_h / GAME_CONTENT_HEIGHT
        target_w = int(SCREEN_WIDTH * scale)

        # 如果寬度超過螢幕一半太多，限制一下 (非必須，但保險)
        if target_w > display_w * 0.7:
            scale = (display_w * 0.7) / SCREEN_WIDTH
            target_w = int(SCREEN_WIDTH * scale)
            target_h = int(GAME_CONTENT_HEIGHT * scale)

        scaled_game = pygame.transform.scale(
            game_content_surface, (target_w, target_h))

        # 居左顯示 (或置中偏左)
        game_x = (display_w * 0.7 - target_w) // 2
        if game_x < 0:
            game_x = 0
        game_y = (display_h - target_h) // 2

        display_surface.blit(scaled_game, (game_x, game_y))

        # 2. 右側區塊 (分為上下兩塊)
        panel_x = int(display_w * 0.7)
        panel_w = int(display_w * 0.28)

        # 上半部: Controls (佔 320px)
        controls_h = 320
        draw_controls_on_surface(
            display_surface, panel_x, 20, panel_w, controls_h)

        # 下半部: Logs
        log_y = 20 + controls_h + 20  # 留點間距
        log_h = display_h - log_y - 20

        # 繪製 Log
        draw_logs_on_surface(display_surface, panel_x, log_y, panel_w, log_h)

    else:
        # --- 直立/標準模式 (Portrait Mode): 上圖下 Log ---

        # 1. 計算可用高度分配
        # 期望比例: Map 佔 80%, Log 佔 20%
        # 先計算 Map 縮放
        target_w = display_w
        scale = target_w / SCREEN_WIDTH
        target_h = int(GAME_CONTENT_HEIGHT * scale)

        # 如果高度太高，超出螢幕，則以高度為準
        if target_h > display_h * 0.8:
            scale = (display_h * 0.8) / GAME_CONTENT_HEIGHT
            target_h = int(GAME_CONTENT_HEIGHT * scale)
            target_w = int(SCREEN_WIDTH * scale)

        scaled_game = pygame.transform.scale(
            game_content_surface, (target_w, target_h))

        # 置中顯示
        game_x = (display_w - target_w) // 2
        game_y = 0
        display_surface.blit(scaled_game, (game_x, game_y))

        # 2. 底部 Log 區
        log_x = 10
        log_y = target_h + 10
        log_w = display_w - 20
        log_h = display_h - target_h - 20
        if log_h < 100:
            log_h = 100  # 最小高度保障

        draw_logs_on_surface(display_surface, log_x, log_y, log_w, log_h)

    pygame.display.flip()

pygame.quit()
