import pygame
import math
from settings import * # 匯入所有設定 (顏色, 大小, 地圖)
from player import Player    # 匯入 Player 類別
from ghost import Ghost      # 匯入 Ghost 類別

# 遊戲初始化
pygame.init()
pygame.font.init()

# 設定視窗 (變數來自 settings.py)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Pac-Man")
clock = pygame.time.Clock()

# 繪製地圖的函式
def draw_map():
    for y, row in enumerate(GAME_MAP):
        for x, char in enumerate(row):
            rect_x = x * TILE_SIZE
            rect_y = y * TILE_SIZE
            if char == "W":     # 牆壁
                pygame.draw.rect(screen, BLUE, (rect_x, rect_y, TILE_SIZE, TILE_SIZE))
            elif char == "=":   # 門
                pygame.draw.line(screen, GREY, (rect_x, rect_y + TILE_SIZE//2), (rect_x + TILE_SIZE, rect_y + TILE_SIZE//2), 2)
            elif char == ".":   # 豆豆
                center_x = rect_x + TILE_SIZE // 2
                center_y = rect_y + TILE_SIZE // 2
                pygame.draw.circle(screen, WHITE, (center_x, center_y), 2)
            elif char == "O":   # 大力丸
                center_x = rect_x + TILE_SIZE // 2
                center_y = rect_y + TILE_SIZE // 2
                pygame.draw.circle(screen, WHITE, (center_x, center_y), 6)

# 建立遊戲物件(讓他置中)
player = Player(13.5, 23)

# 定義散開模式的巡邏路徑 (Scatter Paths)
# 這些座標構成一個迴圈，讓鬼在角落繞圈圈
# Blinky (右上角): 繞行右上方的牆壁塊
path_blinky = [(21, 1), (26, 1), (26, 5), (21, 5)]

# Pinky (左上角): 繞行左上方的牆壁塊 (對稱)
path_pinky = [(6, 1), (1, 1), (1, 5), (6, 5)]

# Inky (右下角): 繞行右下方的牆壁塊
# 注意：右下角地形較複雜，這條路徑繞過 L 型牆壁
path_inky = [(21, 26), (26, 26), (26, 29), (21, 29)]

# Clyde (左下角): 繞行左下方的牆壁塊
path_clyde = [(6, 26), (1, 26), (1, 29), (6, 29)]

# 建立四隻鬼，設定不同的顏色與 AI 模式、等待時間
blinky = Ghost(13, 14, RED, ai_mode="CHASE_BLINKY", scatter_path=path_blinky, in_house=True, delay=0)
pinky = Ghost(14, 14, PINK, ai_mode="CHASE_PINKY", scatter_path=path_pinky, in_house=True, delay=3000)
inky = Ghost(12, 14, CYAN, ai_mode="CHASE_INKY", scatter_path=path_inky, in_house=True, delay=6000)
clyde = Ghost(15, 14, ORANGE, ai_mode="CHASE_CLYDE", scatter_path=path_clyde, in_house=True, delay=9000)


ghosts = [blinky, pinky, inky, clyde]

# 計算總豆子數 (勝利條件)
total_pellets = 0
for row in GAME_MAP:
    for char in row:
        if char == '.':     #只算豆子 大力丸不是通關條件
            total_pellets += 1
print(f"遊戲開始！總豆子數：{total_pellets}")

# 遊戲主迴圈變數
running = True
game_state = "PLAYING"  # "PLAYING", "GAME_OVER", "WIN"
frightened_mode = False
frightened_start_time = 0

global_ghost_mode = "SCATTER"  # 遊戲一開始先散開
mode_timer = 0
last_mode_switch_time = pygame.time.get_ticks()

# * 主迴圈開始
while running:
    dt = clock.tick(60)
    # 處理輸入 
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_state == "PLAYING":
            player.handle_input(event)

    # 遊戲邏輯更新 
    if game_state == "PLAYING":

        current_time = pygame.time.get_ticks()
        
        if not frightened_mode:
            time_passed = current_time - last_mode_switch_time
            
            if global_ghost_mode == "SCATTER" and time_passed > SCATTER_DURATION:
                global_ghost_mode = "CHASE"
                last_mode_switch_time = current_time
                print("切換模式：開始追逐 (CHASE)")

            elif global_ghost_mode == "CHASE" and time_passed > CHASE_DURATION:
                global_ghost_mode = "SCATTER"
                last_mode_switch_time = current_time
                print("切換模式：散開 (SCATTER)")
        
        # 更新所有鬼的狀態 (將全域模式套用到每隻鬼身上)
        for ghost in ghosts:
            # 如果鬼處於特殊狀態 (回家、出門、等待、被吃、驚嚇)，則不覆蓋它的模式
            if (not ghost.is_frightened and not ghost.is_eaten and 
                ghost.current_ai_mode not in ["GO_HOME", "EXIT_HOUSE", "WAITING"]):
                
                if global_ghost_mode == "SCATTER":
                    ghost.current_ai_mode = "SCATTER"
                elif global_ghost_mode == "CHASE":
                    ghost.current_ai_mode = ghost.ai_mode  # 切換回它原本的追逐個性 (CHASE_BLINKY 等)
        
        # Frightened (受驚) 模式計時器
        if frightened_mode:
            if current_time - frightened_start_time > FRIGHTENED_DURATION:
                frightened_mode = False
                for ghost in ghosts:
                    ghost.end_frightened()
                last_mode_switch_time = current_time

        # Player 更新
        # 把加分統一在主程式
        player_status = player.update(GAME_MAP)
        
        if player_status == "ATE_PELLET":
            total_pellets -= 1
            player.score += PELLELETS_POINT 
        elif player_status == "ATE_POWER_PELLET":   #吃到大力丸進入驚嚇模式
            player.score += POWER_PELLET_POINT
            frightened_mode = True
            frightened_start_time = pygame.time.get_ticks()
            for ghost in ghosts:
                ghost.start_frightened()
        
        # 勝利檢查
        if total_pellets <= 0:
            game_state = "WIN"

        # 鬼的更新 (Inky 需要 Blinky 的位置來計算夾擊)
        blinky_pos_for_inky = (blinky.grid_x, blinky.grid_y)
        for ghost in ghosts:
            ghost.update(GAME_MAP, player, ghosts, dt, global_ghost_mode, blinky_pos_for_inky) 
        
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
                    game_state = "GAME_OVER"
                    print("碰撞發生！遊戲結束。") 

    # 畫面繪製 
    screen.fill(BLACK) 
    draw_map()
    player.draw(screen)
    
    for ghost in ghosts:
        ghost.draw(screen)

    # 繪製分數
    score_text = SCORE_FONT.render(f"SCORE: {int(player.score)}", True, WHITE)      # True: 開啟 anti-aliasing (反鋸齒)
    screen.blit(score_text, (10, 32 * TILE_SIZE))
    
    # 繪製 GAME OVER 或 WIN
    if game_state == "GAME_OVER":
        game_over_text = GAME_OVER_FONT.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        screen.blit(game_over_text, text_rect)
    
    elif game_state == "WIN":
        win_text = WIN_FONT.render("YOU WIN!", True, YELLOW)
        text_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        screen.blit(win_text, text_rect)

    pygame.display.flip() 

pygame.quit()