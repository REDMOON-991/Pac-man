# settings.py
import pygame

# * 遊戲架構有關常數
# 遊戲視窗
TILE_SIZE = 20
MAP_HEIGHT = 36 * TILE_SIZE
LOG_HEIGHT = 140
SCREEN_WIDTH = 28 * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT + LOG_HEIGHT

# 顏色定義
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 184, 82)
GREY = (150, 150, 150)
FRIGHTENED_BLUE = (0, 0, 139)

# 字型設定
# 初始化字型模組
pygame.font.init()
SCORE_FONT = pygame.font.Font(None, 24)
GAME_OVER_FONT = pygame.font.Font(None, 64)
WIN_FONT = pygame.font.Font(None, 64)
LOG_FONT = pygame.font.Font(None, 20)

# * 運作常數

# 時間與速度常數
SPEED = 2  # 玩家與鬼的基本速度
FRIGHTENED_DURATION = 7000  # 7 秒
SCATTER_DURATION = 7000   # 散開 7 秒
CHASE_DURATION = 20000    # 追逐 20 秒

# 分數資料
PELLELETS_POINT = 10
POWER_PELLET_POINT = 50
GHOST_POINT = 200

# 遊戲狀態常數 (Game States)
GAME_STATE_START = "START"
GAME_STATE_PLAYING = "PLAYING"
GAME_STATE_GAME_OVER = "GAME_OVER"
GAME_STATE_WIN = "WIN"

# 鬼魂全域/行為模式 (Ghost AI Modes)
# 全域控制
MODE_SCATTER = "SCATTER"
MODE_CHASE = "CHASE"
MODE_FRIGHTENED = "FRIGHTENED"

# 特殊狀態
MODE_GO_HOME = "GO_HOME"
MODE_EXIT_HOUSE = "EXIT_HOUSE"
MODE_WAITING = "WAITING"

# 個性化追逐模式 (Personalities)
AI_CHASE_BLINKY = "CHASE_BLINKY"
AI_CHASE_PINKY = "CHASE_PINKY"
AI_CHASE_INKY = "CHASE_INKY"
AI_CHASE_CLYDE = "CHASE_CLYDE"

# --- 地圖物件符號 (Map Tiles) ---
TILE_WALL = "W"
TILE_DOOR = "="
TILE_PELLET = "."
TILE_POWER_PELLET = "O"
TILE_EMPTY = " "

# --- 玩家事件回傳 (Player Events) ---
EVENT_ATE_PELLET = "ATE_PELLET"
EVENT_ATE_POWER_PELLET = "ATE_POWER_PELLET"

# 將字串地圖轉換成可修改的列表 (List)
# 我們先給一個空的預設值，實際內容會由 map_generator 填入
# 這是一個 36列 x 28行的空陣列
GAME_MAP = [[TILE_EMPTY for _ in range(28)] for _ in range(36)]

# 地圖生成參數
MAP_COLS = 28
MAP_ROWS = 31  # 遊戲主要區域高度 (不含下方的 Log padding)


def is_wall(game_map, x, y):
    """
    檢查給定座標是否為牆壁。
    如果座標超出地圖範圍 (例如左右隧道)，回傳 False (表示可通行)。
    """
    # 檢查是否在地圖範圍內
    if 0 <= y < len(game_map) and 0 <= x < len(game_map[0]):
        return game_map[y][x] == TILE_WALL
    # 超出範圍 (例如隧道口)，視為非牆壁，可通行
    return False
