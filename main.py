import pygame
import math
from settings import * # 匯入所有設定 (顏色, 大小, 地圖)
from player import Player    # 匯入 Player 類別
from ghost import Ghost      # 匯入 Ghost 類別

# 1. 遊戲初始化
pygame.init()
pygame.font.init()

# 設定視窗 (變數來自 settings.py)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Pac-Man")
clock = pygame.time.Clock()

# 字型設定
SCORE_FONT = pygame.font.Font(None, 24)
GAME_OVER_FONT = pygame.font.Font(None, 64)
WIN_FONT = pygame.font.Font(None, 64)

# 2. 繪製地圖的函式
# (因為地圖繪製直接畫在 screen 上，放在主程式比較方便)
def draw_map():
    for y, row in enumerate(GAME_MAP):
        for x, char in enumerate(row):
            rect_x = x * TILE_SIZE
            rect_y = y * TILE_SIZE
            if char == "W":
                pygame.draw.rect(screen, BLUE, (rect_x, rect_y, TILE_SIZE, TILE_SIZE))
            elif char == ".":
                center_x = rect_x + TILE_SIZE // 2
                center_y = rect_y + TILE_SIZE // 2
                pygame.draw.circle(screen, WHITE, (center_x, center_y), 2)
            elif char == "O":
                center_x = rect_x + TILE_SIZE // 2
                center_y = rect_y + TILE_SIZE // 2
                pygame.draw.circle(screen, WHITE, (center_x, center_y), 6)

# 3. 建立遊戲物件
player = Player(13, 26)

# 建立四隻鬼，設定不同的顏色與 AI 模式
blinky = Ghost(13, 14, RED, ai_mode="CHASE_BLINKY", scatter_target=(26, 1))
pinky = Ghost(14, 14, PINK, ai_mode="CHASE_PINKY", scatter_target=(1, 1))
inky = Ghost(12, 14, CYAN, ai_mode="CHASE_INKY", scatter_target=(26, 29))
clyde = Ghost(15, 14, ORANGE, ai_mode="CHASE_CLYDE", scatter_target=(1, 29))

ghosts = [blinky, pinky, inky, clyde]

# 計算總豆子數 (勝利條件)
total_pellets = 0
for row in GAME_MAP:
    for char in row:
        if char == '.' or char == 'O':
            total_pellets += 1
print(f"遊戲開始！總豆子數：{total_pellets}")

# 4. 遊戲主迴圈變數
running = True
game_state = "PLAYING"  # "PLAYING", "GAME_OVER", "WIN"
frightened_mode = False
frightened_start_time = 0

# ---------------------------------------------------------
# 主迴圈開始
# ---------------------------------------------------------
while running:
    # --- A. 處理輸入 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if game_state == "PLAYING":
            player.handle_input(event)

    # --- B. 遊戲邏輯更新 ---
    if game_state == "PLAYING":
        
        # 1. Frightened (受驚) 模式計時器
        if frightened_mode:
            current_time = pygame.time.get_ticks()
            if current_time - frightened_start_time > FRIGHTENED_DURATION:
                frightened_mode = False
                for ghost in ghosts:
                    ghost.end_frightened()

        # 2. Player 更新
        player_status = player.update(GAME_MAP)
        
        if player_status == "ATE_PELLET":
            total_pellets -= 1
        elif player_status == "ATE_POWER_PELLET":
            total_pellets -= 1
            frightened_mode = True
            frightened_start_time = pygame.time.get_ticks()
            for ghost in ghosts:
                ghost.start_frightened()
        
        # 3. 勝利檢查
        if total_pellets <= 0:
            game_state = "WIN"

        # 4. 鬼的更新 (Inky 需要 Blinky 的位置來計算夾擊)
        blinky_pos_for_inky = (blinky.grid_x, blinky.grid_y)
        for ghost in ghosts:
            ghost.update(GAME_MAP, player, blinky_pos_for_inky) 
        
        # 5. 碰撞偵測
        for ghost in ghosts:
            # 這裡還是需要簡單的距離計算，所以 import math
            dx = player.pixel_x - ghost.pixel_x
            dy = player.pixel_y - ghost.pixel_y
            distance = math.hypot(dx, dy)
            collision_distance = player.radius + ghost.radius
            
            if distance < collision_distance:
                if ghost.is_frightened:
                    # 吃鬼
                    points = ghost.eat()
                    player.score += points
                elif not ghost.is_eaten:
                    # 被鬼抓
                    game_state = "GAME_OVER"
                    print("碰撞發生！遊戲結束。") 

    # --- C. 畫面繪製 ---
    screen.fill(BLACK) 
    draw_map()
    player.draw(screen)
    
    for ghost in ghosts:
        ghost.draw(screen)

    # 繪製分數
    score_text = SCORE_FONT.render(f"SCORE: {player.score}", True, WHITE)
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
    clock.tick(60) 

pygame.quit()