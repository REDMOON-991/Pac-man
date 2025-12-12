# settings.py
import pygame

# * 遊戲架構有關常數
# 遊戲視窗
TILE_SIZE = 20
MAP_HEIGHT = 36 * TILE_SIZE  # 720
LOG_HEIGHT = 140
SCREEN_WIDTH = 28 * TILE_SIZE  # 560
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
GREEN = (0, 255, 0)

# 字型設定
# 初始化字型模組
pygame.font.init()
SCORE_FONT = pygame.font.Font(None, 24)
GAME_OVER_FONT = pygame.font.Font(None, 64)
WIN_FONT = pygame.font.Font(None, 64)
LOG_FONT = pygame.font.Font(None, 20)

# * 運作常數

# 時間與速度常數
SPEED = 2  # 玩家與鬼的基本速度 (每幀像素)
# 註: 若改為 dt 基礎移動，需重新校正速度值 (例如: 120 pixels/sec)

FRIGHTENED_DURATION = 7000  # 7 秒
SCATTER_DURATION = 7000   # 散開 7 秒
CHASE_DURATION = 20000    # 追逐 20 秒


# 新增生命值常數
MAX_LIVES = 3

# 分數資料
PELLELETS_POINT = 10
POWER_PELLET_POINT = 50
GHOST_POINT = 200

# 遊戲狀態常數 (Game States)
GAME_STATE_MENU = "MENU"      # 選單
GAME_STATE_START = "START"
GAME_STATE_PLAYING = "PLAYING"
GAME_STATE_GAME_OVER = "GAME_OVER"
GAME_STATE_WIN = "WIN"
GAME_STATE_READY = "READY_ANIMATION"  # 新增 Ready 動畫狀態
GAME_STATE_DEATH = "DEATH_ANIMATION"  # 新增死亡動畫狀態

# 鬼魂全域/行為模式 (Ghost AI Modes)
# 鬼演算法

ALGO_GREEDY = "GREEDY"
ALGO_BFS = "BFS"
ALGO_ASTAR = "ASTAR"

# 全域控制
MODE_SCATTER = "SCATTER"
MODE_CHASE = "CHASE"
MODE_FRIGHTENED = "FRIGHTENED"

# 特殊狀態
MODE_GO_HOME = "GO_HOME"
MODE_EXIT_HOUSE = "EXIT_HOUSE"
MODE_WAITING = "WAITING"

# Magic Numbers (地點常數)
GHOST_HOUSE_EXIT_POS = (13, 11)  # 鬼屋出口座標 (grid_x, grid_y)
GHOST_HOUSE_Y_THRESHOLD = 11     # 判定是否出門的 Y 軸門檻
TUNNEL_LEFT_GRID_X = 0
TUNNEL_RIGHT_GRID_X = 27

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

# 地圖資料 (Layout)
MAP_STRINGS = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WOWWWW.WWWWW.WW.WWWWW.WWWWOW",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W..........................W",
    "W.WWWW.WW.WWWWWWWW.WWWW.WW.W",
    "W.WWWW.WW.WWWWWWWW.WWWW.WW.W",
    "W......WW....WW....WW......W",
    "WWWWWW.WWWWW WW WWWWW.WWWWWW",
    "     W.WWWWW WW WWWWW.W     ",
    "     W.WW          WW.W     ",
    "     W.WW WWW==WWW WW.W     ",     # <--- 加入門 '='
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
    "WO..WW.......  .......WW..OW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "W......WW....WW....WW......W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W..........................W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    " ", " ", " ", " ", " "
]

# 2. 自動補齊地圖字串長度 (避免 IndexError)
MAX_MAP_WIDTH = max(len(row) for row in MAP_STRINGS)
MAP_STRINGS = [row.ljust(MAX_MAP_WIDTH, ' ') for row in MAP_STRINGS]

# 將字串地圖轉換成可修改的列表 (List)
GAME_MAP = [list(row) for row in MAP_STRINGS]


def is_wall(game_map, x, y):
    """
    檢查給定座標是否為牆壁。
    如果座標超出地圖範圍 (例如左右隧道)，回傳 False (表示可通行)。
    """
    # 檢查是否在地圖範圍內
    if 0 <= y < len(game_map):
        if 0 <= x < len(game_map[y]):
            return game_map[y][x] == TILE_WALL
    # 超出範圍 (例如隧道口)，視為非牆壁，可通行
    return False
