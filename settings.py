# settings.py
import pygame

# --- 1. 遊戲視窗與常數 ---
TILE_SIZE = 20
SCREEN_WIDTH = 28 * TILE_SIZE
SCREEN_HEIGHT = 36 * TILE_SIZE
FRIGHTENED_DURATION = 7000 # 7 秒

# --- 2. 顏色定義 ---
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)       
PINK = (255, 184, 255)  
CYAN = (0, 255, 255)    
ORANGE = (255, 184, 82)
FRIGHTENED_BLUE = (0, 0, 139)

# --- 3. 地圖資料 (Layout) ---
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

# 將字串地圖轉換成可修改的列表 (List)
GAME_MAP = [list(row) for row in MAP_STRINGS]