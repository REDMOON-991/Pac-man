import pygame
import random
import math

# 1. 遊戲初始化
pygame.init()
pygame.font.init() 

# 2. 設定遊戲視窗與常數
TILE_SIZE = 20
SCREEN_WIDTH = 28 * TILE_SIZE
SCREEN_HEIGHT = 36 * TILE_SIZE
FRIGHTENED_DURATION = 7000 # 7 秒

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Pac-Man")

# 3. 定義顏色
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)       
PINK = (255, 184, 255)  
CYAN = (0, 255, 255)    
ORANGE = (255, 184, 82)
FRIGHTENED_BLUE = (0, 0, 139)

# 4. 地圖資料 (Layout)
MAP_STRINGS = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WOWWWW.WWWWW.WW.WWWWW.WWWWOW",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W..........................W",
    "W.WWWW.WW.WWWWWW.WW.WWWW.W",
    "W.WWWW.WW.WWWWWW.WW.WWWW.W",
    "W......WW....WW....WW......W",
    "WWWWWW.WWWWW WW WWWWW.WWWWWW",
    "     W.WWWWW WW WWWWW.W     ",
    "     W.WW          WW.W     ",
    "     W.WW WWW  WWW WW.W     ",
    "WWWWWW.WW W      W WW.WWWWWW",
    "      .   W      W   .      ",
    "WWWWWW.WW W      W WW.WWWWWW",
    "     W.WW WWWWWWWW WW.W     ",
    "     W.WW          WW.W     ",
    "     W.WW WWWWWWWW WW.W     ",
    "WWWWWW.WW WWWWWWWW WW.WWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WO..WW................WW..OW",
    "WWW.WW.WW.WWWWWW.WW.WW.WWW",
    "WWW.WW.WW.WWWWWW.WW.WW.WWW",
    "W......WW....WW....WW......W",
    "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
    "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
    "W..........................W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    " ", " ", " ", " ", " "
]
GAME_MAP = [list(row) for row in MAP_STRINGS]

# -----------------------------------------------------------------
# 步驟 13 新增：計算總豆子數量 (勝利條件)
# -----------------------------------------------------------------
total_pellets = 0
for row in GAME_MAP:
    for char in row:
        if char == '.' or char == 'O':
            total_pellets += 1
print(f"遊戲開始！總豆子數：{total_pellets}")

# -----------------------------------------------------------------
# 步驟 13 新增：勝利/遊戲結束的字型
# -----------------------------------------------------------------
SCORE_FONT = pygame.font.Font(None, 24)
GAME_OVER_FONT = pygame.font.Font(None, 64)
WIN_FONT = pygame.font.Font(None, 64)

# 5. 繪製地圖的函式
def draw_map():
    # ... (與之前相同) ...
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

# -----------------------------------------------------------------
# 步驟 13 的重大修改：Ghost 類別
# -----------------------------------------------------------------
class Ghost:
    def __init__(self, grid_x, grid_y, color, ai_mode="RANDOM", scatter_target=(0, 0)):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.home_pos = (grid_x, grid_y) # 記住出生點 (即重生點)
        
        self.pixel_x = (self.grid_x * TILE_SIZE) + (TILE_SIZE // 2)
        self.pixel_y = (self.grid_y * TILE_SIZE) + (TILE_SIZE // 2)
        self.radius = TILE_SIZE // 2 - 2
        
        self.color = color
        self.default_speed = 2
        self.speed = self.default_speed
        self.direction = (1, 0)
        self.all_directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        
        self.ai_mode = ai_mode
        self.current_ai_mode = ai_mode
        self.target = (0, 0)
        self.scatter_target = scatter_target
        
        self.is_frightened = False
        self.is_eaten = False # 新增：是否已被吃掉

    def draw(self, surface):
        """ 繪製鬼：如果被吃, 畫眼睛；如果受驚, 畫藍色；否則畫正常顏色 """
        
        if self.is_eaten:
            # 畫 "眼睛"
            eye_radius = self.radius // 2
            eye_offset = self.radius // 3
            pygame.draw.circle(surface, WHITE, (self.pixel_x - eye_offset, self.pixel_y), eye_radius)
            pygame.draw.circle(surface, WHITE, (self.pixel_x + eye_offset, self.pixel_y), eye_radius)
        else:
            # 畫正常的鬼
            draw_color = self.color
            if self.is_frightened:
                draw_color = FRIGHTENED_BLUE
            pygame.draw.circle(surface, draw_color, (self.pixel_x, self.pixel_y), self.radius)

    def eat(self):
        """ 當鬼被玩家 "吃掉" 時呼叫 """
        print("一隻鬼被吃掉了！")
        self.is_frightened = False
        self.is_eaten = True
        self.current_ai_mode = "GO_HOME"
        self.speed = 4 # 加速回家
        self.target = self.home_pos # 設定目標為重生點
        return 200 # 返回 200 分

    def respawn(self):
        """ 當鬼回到家時呼叫 (重生) """
        print("一隻鬼重生了！")
        self.is_eaten = False
        self.current_ai_mode = self.ai_mode # 恢復預設 AI
        self.speed = self.default_speed
        # 確保它在重生點
        self.pixel_x = (self.home_pos[0] * TILE_SIZE) + (TILE_SIZE // 2)
        self.pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)

    def start_frightened(self):
        # 只有在 "沒有" 被吃掉的狀態下, 才會受驚
        if not self.is_eaten:
            self.is_frightened = True
            self.current_ai_mode = "FRIGHTENED"
            self.speed = 1
            self.direction = (self.direction[0] * -1, self.direction[1] * -1)

    def end_frightened(self):
        # 只有受驚的鬼才需要恢復
        if self.is_frightened:
            self.is_frightened = False
            self.current_ai_mode = self.ai_mode
            self.speed = self.default_speed

    def get_distance(self, pos1, pos2):
        return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

    def get_valid_directions(self, game_map):
        valid_moves = []
        reverse_dir = (self.direction[0] * -1, self.direction[1] * -1)
        
        for move_dir in self.all_directions:
            # 規則 1：AI 掉頭規則
            # 只有 CHASE 和 RANDOM 模式 "不" 允許掉頭 (除非死路)
            is_chase_or_random = (self.current_ai_mode.startswith("CHASE_") or self.current_ai_mode == "RANDOM")
            if is_chase_or_random and move_dir == reverse_dir:
                continue

            # 規則 2：撞牆
            next_g_x = self.grid_x + move_dir[0]
            next_g_y = self.grid_y + move_dir[1]
            if 0 <= next_g_y < len(game_map) and 0 <= next_g_x < len(game_map[0]):
                if game_map[next_g_y][next_g_x] != "W":
                    valid_moves.append(move_dir)
                    
        # 規則 3：死路處理
        if not valid_moves:
            # 如果是死路, 任何模式都 "必須" 允許掉頭
            if game_map[self.grid_y + reverse_dir[1]][self.grid_x + reverse_dir[0]] != "W":
                valid_moves.append(reverse_dir)

        return valid_moves

    def update(self, game_map, player, blinky_tile=None):
        
        is_centered_x = (self.pixel_x - (TILE_SIZE // 2)) % TILE_SIZE == 0
        is_centered_y = (self.pixel_y - (TILE_SIZE // 2)) % TILE_SIZE == 0

        if is_centered_x and is_centered_y:
            self.grid_x = (self.pixel_x - (TILE_SIZE // 2)) // TILE_SIZE
            self.grid_y = (self.pixel_y - (TILE_SIZE // 2)) // TILE_SIZE

            # **步驟 13 新增**：如果 AI 是 "GO_HOME" 且已抵達
            if self.current_ai_mode == "GO_HOME" and (self.grid_x, self.grid_y) == self.home_pos:
                self.respawn()
                
            valid_directions = self.get_valid_directions(game_map)

            # 2. *** AI 決策核心：設定目標 (Target) ***
            player_dir_x = player.direction[0]
            player_dir_y = player.direction[1]
            player_stopped = (player_dir_x == 0 and player_dir_y == 0)
            
            self.target = (player.grid_x, player.grid_y) # 預設目標
            
            if self.current_ai_mode == "RANDOM": self.target = None 
            elif self.current_ai_mode == "FRIGHTENED": self.target = (player.grid_x, player.grid_y)
            elif self.current_ai_mode == "GO_HOME": self.target = self.home_pos # 目標是家
            elif self.current_ai_mode == "CHASE_BLINKY": self.target = (player.grid_x, player.grid_y)
            elif self.current_ai_mode == "CHASE_PINKY":
                if player_stopped: self.target = (player.grid_x, player.grid_y)
                else: self.target = (player.grid_x + (player_dir_x * 4), player.grid_y + (player_dir_y * 4))
            elif self.current_ai_mode == "CHASE_CLYDE":
                distance = self.get_distance((self.grid_x, self.grid_y), (player.grid_x, player.grid_y))
                if distance > 8: self.target = (player.grid_x, player.grid_y)
                else: self.target = self.scatter_target
            elif self.current_ai_mode == "CHASE_INKY":
                if blinky_tile is None or player_stopped: self.target = (player.grid_x, player.grid_y)
                else:
                    trigger_x = player.grid_x + (player_dir_x * 2)
                    trigger_y = player.grid_y + (player_dir_y * 2)
                    blinky_x, blinky_y = blinky_tile
                    vec_x = trigger_x - blinky_x; vec_y = trigger_y - blinky_y
                    self.target = (trigger_x + vec_x, trigger_y + vec_y)

            # 3. *** 根據目標選擇方向 (貪婪演算法) ***
            if self.current_ai_mode == "RANDOM":
                if valid_directions: self.direction = random.choice(valid_directions)
            
            # **修改**：FRIGHTENED (逃跑) vs CHASE/GO_HOME (追逐)
            elif self.target and valid_directions:
                best_direction = (0, 0)
                if self.current_ai_mode == "FRIGHTENED":
                    best_distance = float('-inf') # 找 "最遠"
                else: # CHASE_... or GO_HOME
                    best_distance = float('inf')  # 找 "最近"

                for direction in valid_directions:
                    next_g_x = self.grid_x + direction[0]
                    next_g_y = self.grid_y + direction[1]
                    dist = self.get_distance((next_g_x, next_g_y), self.target)
                    
                    if self.current_ai_mode == "FRIGHTENED":
                        if dist > best_distance: # 找 "最遠"
                            best_distance = dist; best_direction = direction
                    else:
                        if dist < best_distance: # 找 "最近"
                            best_distance = dist; best_direction = direction
                self.direction = best_direction
        
        # 根據最終決定的方向來移動 (使用 self.speed)
        self.pixel_x += self.direction[0] * self.speed
        self.pixel_y += self.direction[1] * self.speed
        
        # 處理 "隧道"
        if self.pixel_x < 0: self.pixel_x = SCREEN_WIDTH
        elif self.pixel_x > SCREEN_WIDTH: self.pixel_x = 0

# -----------------------------------------------------------------
# 步驟 13 的重大修改：Player 類別
# -----------------------------------------------------------------
class Player:
    def __init__(self, grid_x, grid_y):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.pixel_x = (self.grid_x * TILE_SIZE) + (TILE_SIZE // 2)
        self.pixel_y = (self.grid_y * TILE_SIZE) + (TILE_SIZE // 2)
        self.radius = TILE_SIZE // 2 - 2
        self.speed = 2
        self.direction = (0, 0)
        self.next_direction = (0, 0)
        self.score = 0

    def draw(self, surface):
        pygame.draw.circle(surface, YELLOW, (self.pixel_x, self.pixel_y), self.radius)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: self.next_direction = (0, -1)
            elif event.key == pygame.K_DOWN: self.next_direction = (0, 1)
            elif event.key == pygame.K_LEFT: self.next_direction = (-1, 0)
            elif event.key == pygame.K_RIGHT: self.next_direction = (1, 0)

    def update(self, game_map):
        """ 
        更新玩家狀態。
        返回 "ATE_PELLET", "ATE_POWER_PELLET", 或 None
        """
        is_centered_x = (self.pixel_x - (TILE_SIZE // 2)) % TILE_SIZE == 0
        is_centered_y = (self.pixel_y - (TILE_SIZE // 2)) % TILE_SIZE == 0
        if is_centered_x and is_centered_y:
            self.grid_x = (self.pixel_x - (TILE_SIZE // 2)) // TILE_SIZE
            self.grid_y = (self.pixel_y - (TILE_SIZE // 2)) // TILE_SIZE
            
            # 1. 吃豆子 / 大力丸
            current_tile = game_map[self.grid_y][self.grid_x]
            if current_tile == ".":
                game_map[self.grid_y][self.grid_x] = " "
                self.score += 10
                return "ATE_PELLET" # **修改：返回狀態**
            elif current_tile == "O":
                game_map[self.grid_y][self.grid_x] = " "
                self.score += 50
                return "ATE_POWER_PELLET" # **修改：返回狀態**
            
            # 2. 處理轉彎
            if self.next_direction != (0, 0):
                next_g_x = self.grid_x + self.next_direction[0]
                next_g_y = self.grid_y + self.next_direction[1]
                if game_map[next_g_y][next_g_x] != "W":
                    self.direction = self.next_direction
                    self.next_direction = (0, 0)
            
            # 3. 檢查撞牆
            next_g_x = self.grid_x + self.direction[0]
            next_g_y = self.grid_y + self.direction[1]
            if game_map[next_g_y][next_g_x] == "W":
                self.direction = (0, 0) # 玩家停下
        
        # 4. 移動
        self.pixel_x += self.direction[0] * self.speed
        self.pixel_y += self.direction[1] * self.speed
        
        # 5. 隧道
        if self.pixel_x < 0: self.pixel_x = SCREEN_WIDTH
        elif self.pixel_x > SCREEN_WIDTH: self.pixel_x = 0
        
        return None # 預設返回 None

# 6. 建立物件
player = Player(13, 26)
scatter_blinky = (26, 1); scatter_pinky = (1, 1); scatter_inky = (26, 29); scatter_clyde = (1, 29)

# **修改**：鬼的 "home_pos" 就是它們的出生點
blinky = Ghost(13, 14, RED, ai_mode="CHASE_BLINKY", scatter_target=scatter_blinky)    
pinky = Ghost(14, 14, PINK, ai_mode="CHASE_PINKY", scatter_target=scatter_pinky) 
inky = Ghost(12, 14, CYAN, ai_mode="CHASE_INKY", scatter_target=scatter_inky)
clyde = Ghost(15, 14, ORANGE, ai_mode="CHASE_CLYDE", scatter_target=scatter_clyde) 
ghosts = [blinky, pinky, inky, clyde]

# 7. 遊戲主迴圈
running = True
game_state = "PLAYING" # "PLAYING", "GAME_OVER", "WIN"
clock = pygame.time.Clock() 
frightened_mode = False
frightened_start_time = 0

while running:
    # 8. 處理輸入
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT:
            running = False
        # 只有在 PLAYING 狀態才接收遊戲輸入
        if game_state == "PLAYING":
            player.handle_input(event)

    # 9. 遊戲邏輯更新
    if game_state == "PLAYING":
        
        # Frightened 計時器管理
        if frightened_mode:
            current_time = pygame.time.get_ticks()
            if current_time - frightened_start_time > FRIGHTENED_DURATION:
                frightened_mode = False
                for ghost in ghosts:
                    ghost.end_frightened()

        # Player 更新
        player_status = player.update(GAME_MAP)
        
        if player_status == "ATE_PELLET":
            total_pellets -= 1
        elif player_status == "ATE_POWER_PELLET":
            total_pellets -= 1
            frightened_mode = True
            frightened_start_time = pygame.time.get_ticks()
            for ghost in ghosts:
                ghost.start_frightened()
        
        # **步驟 13 新增：勝利檢查**
        if total_pellets <= 0:
            print("所有豆子都吃完了！")
            game_state = "WIN"

        # 鬼的更新
        blinky_pos_for_inky = (blinky.grid_x, blinky.grid_y)
        for ghost in ghosts:
            ghost.update(GAME_MAP, player, blinky_pos_for_inky) 
        
        # 碰撞偵測
        for ghost in ghosts:
            dx = player.pixel_x - ghost.pixel_x
            dy = player.pixel_y - ghost.pixel_y
            distance = math.hypot(dx, dy)
            collision_distance = player.radius + ghost.radius
            
            if distance < collision_distance:
                if ghost.is_frightened:
                    # **步驟 13 新增：吃鬼邏輯**
                    points = ghost.eat()
                    player.score += points
                elif not ghost.is_eaten:
                    # **步驟 13 修改**：只有在鬼 "沒被吃掉" 時才算 GAME OVER
                    game_state = "GAME_OVER"
                    print("碰撞發生！遊戲結束。") 
    
    # 10. 畫面繪製
    screen.fill(BLACK) 
    draw_map()
    player.draw(screen)
    
    for ghost in ghosts:
        ghost.draw(screen) # Ghost.draw() 會自動處理 "眼睛"

    # 繪製分數
    score_text = SCORE_FONT.render(f"SCORE: {player.score}", True, WHITE)
    screen.blit(score_text, (10, 32 * TILE_SIZE))
    
    # 繪製 GAME OVER
    if game_state == "GAME_OVER":
        game_over_text = GAME_OVER_FONT.render("GAME OVER", True, RED)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        screen.blit(game_over_text, text_rect)
    
    # **步驟 13 新增：繪製 "YOU WIN"**
    if game_state == "WIN":
        win_text = WIN_FONT.render("YOU WIN!", True, YELLOW)
        text_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        screen.blit(win_text, text_rect)

    # 11. 更新畫面
    pygame.display.flip() 

    # 12. 控制遊戲速度
    clock.tick(60) 

# 13. 
pygame.quit()
print(f"遊戲結束。 最終分數: {player.score}")