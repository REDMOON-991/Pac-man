# code/map_generator.py
import random
from settings import *


class MapGenerator:
    def __init__(self):
        self.grid = []
        self.visited = []
        self.config = {}

    def generate(self):
        # 初始化 (全牆壁)
        self.grid = [[TILE_WALL for _ in range(
            MAP_COLS)] for _ in range(MAP_ROWS)]
        self.visited = [[False for _ in range(
            MAP_COLS)] for _ in range(MAP_ROWS)]

        # 決定關鍵結構位置
        self._place_structures()

        # 生成迷宮 (只生成左半邊 Col 1~13)
        self._generate_maze(1, 1)

        # 修飾鬼屋出口：在鏡像前，先挖出一條漂亮的橫向走廊
        self._clean_house_exit()

        # 補漏：確保四個角落與關鍵路徑暢通
        self._ensure_corners()

        # 鏡像複製到右半邊
        self._mirror_grid()

        # 打通死路 (Braiding)
        self._remove_dead_ends()

        # 確保牆壁都在
        self._enforce_borders()

        # 放置豆子與大力丸
        self._place_items()

        # 7. 格式轉換 (補上底部 padding 給 UI 顯示用)
        # 回傳格式：字串列表 (為了相容舊邏輯，其實 list[list] 也可以，但這裡統一轉字串)
        # ! 之後來調整這塊
        map_strings = ["".join(row) for row in self.grid]
        for _ in range(5):  # 補 5 行空白
            map_strings.append(" " * MAP_COLS)

        return map_strings, self.config

    def _place_structures(self):
        """ 隨機配置：鬼屋、玩家、隧道 """

        # A. 鬼屋 (House)
        # 高度 5 (含牆), 寬度 8
        # 限制 Y 範圍：不要太貼頂 (6)，也不要太貼底 (18)
        house_top_y = random.randint(6, 18)
        house_h = 5
        house_w = 8
        house_center_x = MAP_COLS // 2  # 14
        house_left_x = house_center_x - (house_w // 2)  # 10

        # B. 玩家 (Player)
        # 必須在鬼屋下方，至少隔 3 格，且不能超出地圖底部
        # ! 之後改成可以在上方
        player_y = random.randint(house_top_y + house_h + 2, MAP_ROWS - 3)
        player_x = house_center_x

        # C. 隧道 (Tunnels)
        # 隨機產生 1 到 2 條隧道
        # 隧道不能切過鬼屋，也不能切過玩家出生點
        num_tunnels = random.choice([1, 2])
        tunnel_rows = []

        # 嘗試尋找合法的隧道行
        attempts = 0
        while len(tunnel_rows) < num_tunnels and attempts < 50:
            attempts += 1
            ty = random.randint(4, MAP_ROWS - 4)  # 不要太邊緣

            # 檢查衝突：
            # 1. 不能撞到鬼屋 (包含鬼屋上下各保留 1 格緩衝)
            if (house_top_y - 1) <= ty <= (house_top_y + house_h + 1):
                continue
            # 2. 不能剛好在玩家頭上 (防止重生即被傳送)
            if abs(ty - player_y) < 2:
                continue
            # 3. 兩條隧道不能太近
            if any(abs(ty - other) < 4 for other in tunnel_rows):
                continue

            tunnel_rows.append(ty)

        # --- 開始挖空地圖 ---

        # 鬼屋內部
        for y in range(house_top_y + 1, house_top_y + house_h - 1):
            for x in range(house_left_x + 1, house_left_x + house_w - 1):
                self.grid[y][x] = TILE_EMPTY
                self.visited[y][x] = True  # 保護區域

        # 鬼屋門 (位於上方 Top Y) -> 背對下方玩家
        self.grid[house_top_y][house_center_x - 1] = TILE_DOOR
        self.grid[house_top_y][house_center_x] = TILE_DOOR

        # 修正: 強制挖空門口正上方的兩格，確保鬼魂出得去
        self.grid[house_top_y - 1][house_center_x - 1] = TILE_EMPTY
        self.grid[house_top_y - 1][house_center_x] = TILE_EMPTY
        self.visited[house_top_y - 1][house_center_x - 1] = True
        self.visited[house_top_y - 1][house_center_x] = True

        # 標記鬼屋整體範圍為「已訪問」(包含牆壁，避免迷宮演算法破壞牆壁)
        for y in range(house_top_y, house_top_y + house_h):
            for x in range(house_left_x, house_left_x + house_w):
                self.visited[y][x] = True

        # 挖玩家出生點
        # 只標記水平位置，並加上「保護層」
        self.grid[player_y][player_x] = TILE_EMPTY
        self.grid[player_y][player_x-1] = TILE_EMPTY
        self.visited[player_y][player_x] = True
        self.visited[player_y][player_x-1] = True

        # 修正: 強制打通玩家出生點往左的通道，防止玩家被關禁閉
        # 往左挖直到碰到 x=6 (大約迷宮的一半)，確保連通
        for x in range(6, player_x):
            self.grid[player_y][x] = TILE_EMPTY
            self.visited[player_y][x] = True  # 標記這條路已存在
            # 【新增註解】保護上下牆壁：將玩家走廊的「上」與「下」格子標記為 Visited
            # 這樣迷宮演算法就不會來挖這兩排，確保玩家上下是實心牆壁
            if player_y - 1 > 0:
                self.visited[player_y - 1][x] = True
            if player_y + 1 < MAP_ROWS - 1:
                self.visited[player_y + 1][x] = True

        # 挖隧道
        for ty in tunnel_rows:
            # 左半邊挖通 (右半邊會鏡像)
            # 我們挖得深一點 (0~5)，確保開口明顯
            for x in range(0, 6):
                self.grid[ty][x] = TILE_EMPTY
                self.visited[ty][x] = True

        # --- 儲存設定 ---
        self.config = {
            "house_center_x": house_center_x,
            "ghost_spawn_y": house_top_y + 2,  # 鬼出生在屋內中間
            "door_row": house_top_y,          # 門在屋頂
            "player_start": (player_x - 0.5, player_y),  # 修正為像素中心
            "tunnel_rows": tunnel_rows
        }

    def _generate_maze(self, start_x, start_y):
        """ 遞迴回溯迷宮算法 """
        stack = [(start_x, start_y)]
        if not self.visited[start_y][start_x]:
            self.grid[start_y][start_x] = TILE_EMPTY
            self.visited[start_y][start_x] = True

        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        while stack:
            cx, cy = stack[-1]
            neighbors = []

            for dx, dy in directions:
                nx, ny = cx + dx*2, cy + dy*2

                # 邊界檢查：只生成左半邊 (Col 1 ~ 13)
                if 1 <= nx <= 13 and 1 <= ny < MAP_ROWS - 1:
                    if not self.visited[ny][nx]:
                        neighbors.append((nx, ny, dx, dy))

            if neighbors:
                nx, ny, dx, dy = random.choice(neighbors)
                # 打通中間牆
                self.grid[cy + dy][cx + dx] = TILE_EMPTY
                self.visited[cy + dy][cx + dx] = True
                # 打通目標格
                self.grid[ny][nx] = TILE_EMPTY
                self.visited[ny][nx] = True
                stack.append((nx, ny))
            else:
                stack.pop()

    def _clean_house_exit(self):
        """ 【新增】修飾鬼屋出口，使其美觀且連通 """
        hx = self.config["house_center_x"]
        hy = self.config["door_row"]

        # 目標行：門的上方第二格 (hy - 2)
        # 我們在這一行挖一條橫向通道，形成一個 T 字路口
        # 因為稍後會執行 _mirror_grid，我們只需要挖左半邊 (Col 13 往左)
        target_row = hy - 2

        # 邊界檢查 (雖然 house_top_y >= 6，但保險起見)
        if target_row > 1:
            # 挖開 Col 11, 12, 13 (鏡像後會變成 11-16 的橫條)
            # 這樣保證門口出來是開闊的，而且會截斷任何垂直的牆壁，強制連通
            for x in range(hx - 3, hx):  # x = 11, 12, 13
                self.grid[target_row][x] = TILE_EMPTY
                self.visited[target_row][x] = True

            # 確保門口正上方 (hy-1) 也是通的
            self.grid[hy-1][hx-1] = TILE_EMPTY

            # 這樣結構就是：
            #      ...  (hy-2 橫向通道)
            #       |   (hy-1 門口通道)
            #     ==|== (hy   門)

    def _ensure_corners(self):
        """ 確保角落有空間，方便 Scatter 模式 """
        corners = [(1, 1), (1, MAP_ROWS-2)]  # 左上、左下
        for cx, cy in corners:
            limit_y = cy + 1
            if cy < 10:
                limit_y = cy + 2
            for y in range(cy-1, limit_y):
                for x in range(cx, cx+3):
                    if 0 < y < MAP_ROWS and 0 < x < 14:
                        self.grid[y][x] = TILE_EMPTY
                        self.visited[y][x] = True

    def _enforce_borders(self):
        """ 【新增】強制修復地圖邊界，防止角落破洞 """
        # 1. 上下邊界封死
        for x in range(MAP_COLS):
            self.grid[0][x] = TILE_WALL
            self.grid[MAP_ROWS-1][x] = TILE_WALL

        # 2. 左右邊界封死 (除了隧道口)
        for y in range(MAP_ROWS):
            if y not in self.config["tunnel_rows"]:
                self.grid[y][0] = TILE_WALL
                self.grid[y][MAP_COLS-1] = TILE_WALL

    def _mirror_grid(self):
        """ 左鏡像到右 """
        for y in range(MAP_ROWS):
            for x in range(MAP_COLS // 2):
                val = self.grid[y][x]
                # 對稱位置
                right_x = MAP_COLS - 1 - x
                self.grid[y][right_x] = val

    def _remove_dead_ends(self):
        """ 去除死路，增加連通性 """
        # 執行多次掃描
        for _ in range(200):
            dead_ends = []
            for y in range(1, MAP_ROWS-1):
                for x in range(1, MAP_COLS-1):
                    if self.grid[y][x] == TILE_EMPTY:
                        # 計算周圍牆壁數
                        walls = 0
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            if self.grid[y+dy][x+dx] == TILE_WALL:
                                walls += 1
                        if walls >= 3:
                            dead_ends.append((x, y))

            if not dead_ends:
                break

            # 隨機選一個死路打通
            dx, dy = random.choice(dead_ends)
            possibles = []
            for mx, my in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = dx + mx, dy + my
                # 檢查打通後是否出界
                if 1 <= nx < MAP_COLS-1 and 1 <= ny < MAP_ROWS-1:
                    # 避免打通鬼屋的牆壁 (鬼屋周圍已經被 visited 保護，但迷宮路徑是 empty)
                    # 簡單檢查：如果目標格是牆壁且周圍有 TILE_DOOR 則禁止
                    # 這裡直接檢查是否為鬼屋座標範圍 (根據 config) 比較安全
                    hx, hy = self.config["house_center_x"], self.config["door_row"]
                    # 鬼屋範圍約 x:10-17, y:door_row-5 ~ door_row+5
                    if 9 <= nx <= 18 and (hy <= ny <= hy + 5):
                        continue

                    possibles.append((mx, my))

            if possibles:
                bx, by = random.choice(possibles)
                # 打通 (包含鏡像點)
                self.grid[dy+by][dx+bx] = TILE_EMPTY
                self.grid[dy+by][MAP_COLS-1-(dx+bx)] = TILE_EMPTY

    def _place_items(self):
        """ 放置豆子與大力丸 """
        for y in range(MAP_ROWS):
            for x in range(MAP_COLS):
                if self.grid[y][x] == TILE_EMPTY:
                    # 檢查是否在禁區 (鬼屋、玩家起始點、隧道)

                    # 1. 鬼屋禁區
                    hx = self.config["house_center_x"]
                    hy = self.config["door_row"]
                    # 門以下 height 範圍都是鬼屋
                    if (hx - 5 <= x <= hx + 4) and (hy <= y <= hy + 5):
                        continue

                    # 2. 玩家禁區
                    px, py = self.config["player_start"]
                    if int(py) - 2 <= y <= int(py) + 2 and int(px) - 2 <= x <= int(px) + 2:
                        continue

                    # 3. 隧道禁區
                    if y in self.config["tunnel_rows"]:
                        # 隧道兩側開口不放豆子
                        if x < 5 or x > MAP_COLS - 6:
                            continue

                    self.grid[y][x] = TILE_PELLET

        # 放置大力丸 (四個角落)
        self.grid[3][1] = TILE_POWER_PELLET
        self.grid[3][MAP_COLS-2] = TILE_POWER_PELLET
        self.grid[MAP_ROWS-4][1] = TILE_POWER_PELLET
        self.grid[MAP_ROWS-4][MAP_COLS-2] = TILE_POWER_PELLET
