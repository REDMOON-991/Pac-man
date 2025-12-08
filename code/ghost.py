# ghost.py
import pygame
import random
import math
from settings import *
from queue import PriorityQueue


class Ghost:
    def __init__(self, grid_x, grid_y, color, ai_mode, scatter_point=None, in_house=False, delay=0, on_log=None, algorithm=ALGO_ASTAR):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.home_pos = (grid_x, grid_y)

        self.pixel_x = (self.grid_x * TILE_SIZE) + (TILE_SIZE // 2)
        self.pixel_y = (self.grid_y * TILE_SIZE) + (TILE_SIZE // 2)
        self.radius = TILE_SIZE // 2 - 2

        self.color = color
        self.default_speed = SPEED
        self.speed = self.default_speed
        self.direction = (1, 0)
        self.all_directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        self.ai_mode = ai_mode
        self.algorithm = algorithm
        self.delay = delay

        if in_house:
            if self.delay > 0:
                self.current_ai_mode = MODE_WAITING
                self.direction = (0, -0.5)  # 等待時稍微上下浮動的初始速度
            else:
                self.current_ai_mode = MODE_EXIT_HOUSE
                self.direction = (0, -1)
        else:
            self.current_ai_mode = ai_mode

        if scatter_point is None:
            self.scatter_path = [(grid_x, grid_y)]
        else:
            self.scatter_path = scatter_point

        self.scatter_index = 0  # 追蹤目前走到路徑的第幾個點
        self.target = (0, 0)

        self.is_frightened = False
        self.is_eaten = False

        self.on_log = on_log

    def draw(self, surface):
        if self.is_eaten:
            eye_radius = self.radius // 2
            eye_offset = self.radius // 3
            pygame.draw.circle(
                surface, WHITE, (self.pixel_x - eye_offset, self.pixel_y), eye_radius)
            pygame.draw.circle(
                surface, WHITE, (self.pixel_x + eye_offset, self.pixel_y), eye_radius)
        else:
            draw_color = self.color
            if self.is_frightened:
                draw_color = FRIGHTENED_BLUE
            pygame.draw.circle(surface, draw_color,
                               (self.pixel_x, self.pixel_y), self.radius)

    def eat(self):
        if self.on_log:
            self.on_log(f"[{self.ai_mode}] Ghost eaten! Returning home.")
        self.is_frightened = False
        self.is_eaten = True
        self.current_ai_mode = MODE_GO_HOME
        self.speed = 2*SPEED
        self.target = self.home_pos
        center_offset = TILE_SIZE // 2

        # 校正 X 軸：確保距離中心點的位移量能被新速度整除
        remainder_x = (self.pixel_x - center_offset) % self.speed
        if remainder_x != 0:
            self.pixel_x -= remainder_x

        # 校正 Y 軸
        remainder_y = (self.pixel_y - center_offset) % self.speed
        if remainder_y != 0:
            self.pixel_y -= remainder_y

    def respawn(self):
        if self.on_log:
            self.on_log(f"[{self.ai_mode}] Ghost respawned! Exiting house.")
        self.is_eaten = False
        self.current_ai_mode = MODE_EXIT_HOUSE
        self.speed = self.default_speed
        self.pixel_x = (self.home_pos[0] * TILE_SIZE) + (TILE_SIZE // 2)
        self.pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)
        self.direction = (0, -1)    # 重生時往上看，避免卡住

    def start_frightened(self):
        if self.is_eaten:
            return
        # 不管位置 一律變成驚嚇狀態
        self.is_frightened = True
        # 但是在家的AI模式不變
        if self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]:
            self.current_ai_mode = MODE_FRIGHTENED
            self.speed = 1
            self.direction = (self.direction[0] * -1, self.direction[1] * -1)

    def end_frightened(self):
        if self.is_frightened:
            self.is_frightened = False
            if self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]:
                self.current_ai_mode = self.ai_mode
            # self.speed = self.default_speed

    # 地圖規則定義
    def get_neighbors(self, node):
        """ 回傳所有合法的相鄰座標 (處理隧道與門) """
        x, y = node
        neighbors = []
        map_width = len(GAME_MAP[0])
        map_height = len(GAME_MAP)

        # 上下左右
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            # 隧道處理 (X軸 Wrap-around)
            nx = (x + dx) % map_width
            ny = y + dy

            # 邊界檢查 (Y軸)
            if 0 <= ny < map_height:
                # ---  Safety Check: X軸邊界檢查 ---
                # 如果 nx 超出了這一行的實際長度 (例如地圖下方的空白區)，視為牆壁，跳過
                if nx >= len(GAME_MAP[ny]):
                    continue
                # 牆壁檢查
                if is_wall(GAME_MAP, nx, ny):
                    continue

                # 門的檢查 (只有回家或出門模式可以過)
                if GAME_MAP[ny][nx] == TILE_DOOR:
                    if self.current_ai_mode not in [MODE_EXIT_HOUSE, MODE_GO_HOME]:
                        continue

                neighbors.append((nx, ny))
        return neighbors

    def heuristic(self, a, b):
        (x1, y1) = a
        (x2, y2) = b
        return abs(x1 - x2) + abs(y1 - y2)

    def get_target_position(self, player, blinky_pos=None):
        """
        根據當前 AI 模式與個性，決定一個 '合法的' 目標格子 (grid_x, grid_y)
        """
        target = (self.grid_x, self.grid_y)  # 預設原地

        # A. 特殊模式
        if self.current_ai_mode == MODE_GO_HOME:
            return self.home_pos
        elif self.current_ai_mode == MODE_EXIT_HOUSE:
            return (13, 11)  # 門口上方
        elif self.current_ai_mode == MODE_FRIGHTENED:
            # 驚嚇模式通常是隨機走，但若要用 A*，可以設一個隨機的遠處空地
            # 簡單做法：隨機選一個非牆壁的點
            #! 這裡用貪婪吧
            while True:
                rx = random.randint(1, 26)
                ry = random.randint(1, 29)
                if not is_wall(GAME_MAP, rx, ry):
                    return (rx, ry)

        # B. 散開模式 (Scatter)
        elif self.current_ai_mode == MODE_SCATTER:
            # 取出當前要去的角落點
            target = self.scatter_path[self.scatter_index]
            # (如果抵達了就換下一個點的邏輯，建議寫在 update 裡更新 index)
            return target

        # C. 追逐模式 (Chase) - 個性化邏輯
        elif self.current_ai_mode == AI_CHASE_BLINKY:
            target = (player.grid_x, player.grid_y)

        elif self.current_ai_mode == AI_CHASE_PINKY:
            # 目標：玩家前方 4 格
            dx, dy = player.direction
            target = (player.grid_x + dx * 4, player.grid_y + dy * 4)

        elif self.current_ai_mode == AI_CHASE_INKY and blinky_pos:
            # 向量夾擊
            px, py = player.grid_x + \
                player.direction[0]*2, player.grid_y + player.direction[1]*2
            bx, by = blinky_pos
            target = (px + (px - bx), py + (py - by))

        elif self.current_ai_mode == AI_CHASE_CLYDE:
            dist = math.hypot(self.grid_x - player.grid_x,
                              self.grid_y - player.grid_y)
            if dist > 8:
                target = (player.grid_x, player.grid_y)
            else:
                target = self.scatter_path[0]  # 離太近就回家

        # --- 關鍵修正：目標合法化 (Clamp Target) ---
        # Pinky/Inky 算出來的目標常常會在牆壁裡或地圖外，導致 A* 失敗。
        # 我們需要把目標「拉回」到地圖內最近的非牆壁點。
        target = self.validate_target(target)
        return target

    def validate_target(self, target):
        """ 確保目標在地圖範圍內且不是牆壁，如果是壞目標，就找最近的好目標 """
        tx, ty = int(target[0]), int(target[1])
        max_y = len(GAME_MAP) - 1
        max_x = len(GAME_MAP[0]) - 1

        # 1. 限制範圍 (Clamp)
        tx = max(1, min(tx, max_x - 1))
        ty = max(1, min(ty, max_y - 1))

        # 2. 如果是牆壁，尋找周圍最近的空地 (簡單 BFS 或 螺旋搜尋)
        if is_wall(GAME_MAP, tx, ty):
            # 簡單搜尋：找上下左右最近的空位
            for dist in range(1, 5):  # 搜尋半徑 5 格
                for dx, dy in [(0, dist), (0, -dist), (dist, 0), (-dist, 0)]:
                    nx, ny = tx + dx, ty + dy
                    if 0 <= nx <= max_x and 0 <= ny <= max_y and not is_wall(GAME_MAP, nx, ny):
                        return (nx, ny)
            # 如果真的找不到，回傳鬼魂自己現在的位置 (停在原地發呆比當機好)
            return (self.grid_x, self.grid_y)

        return (tx, ty)

    # 定義貪婪演算法
    def algo_greedy(self, start, target):
        """ 貪婪：只看鄰居中誰離目標最近，且通常不允許回頭 (除非只有回頭路) """
        neighbors = self.get_neighbors(start)

        # 過濾掉「正後方」的格子 (經典 Pac-Man 規則：不能立即 180 度迴轉)
        # 除非處於死路或特殊狀態，這裡簡化處理：若有其他選擇，就不回頭
        valid_neighbors = []
        reverse_pos = (start[0] - self.direction[0],
                       start[1] - self.direction[1])

        # 處理隧道造成的座標跳躍，導致 reverse_pos 計算誤差 (進階處理略，這裡用簡單過濾)
        for n in neighbors:
            if n != reverse_pos:
                valid_neighbors.append(n)

        # 如果只有死路(只剩回頭路)，就只好回頭
        if not valid_neighbors:
            valid_neighbors = neighbors

        if not valid_neighbors:
            return None

        # 挑選距離目標最近的那個鄰居
        best_next = min(valid_neighbors,
                        key=lambda n: self.heuristic(n, target))
        return best_next

    # 定義BFS
    def algo_bfs(self, start, target):
        """ BFS：地毯式搜索，保證最短路徑 """
        queue = [start]
        came_from = {start: None}

        while queue:
            current = queue.pop(0)

            if current == target:
                break  # 找到目標

            for next_node in self.get_neighbors(current):
                if next_node not in came_from:
                    queue.append(next_node)
                    came_from[next_node] = current

        # 重建路徑，只取第一步
        return self.reconstruct_next_step(came_from, start, target)

    # 定義a*演算法

    def algo_astar(self, start, target):
        """ A*：智慧搜索，兼顧距離與成本 """
        open_set = PriorityQueue()
        open_set.put((0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while not open_set.empty():
            _, current = open_set.get()

            if current == target:
                break

            for next_node in self.get_neighbors(current):
                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self.heuristic(next_node, target)
                    open_set.put((priority, next_node))
                    came_from[next_node] = current

        return self.reconstruct_next_step(came_from, start, target)

    def reconstruct_next_step(self, came_from, start, target):
        """ 從 came_from 字典中回推路徑，並回傳 start 的下一個點 """
        if target not in came_from:
            return None  # 沒路

        curr = target
        path = []
        while curr != start:
            path.append(curr)
            curr = came_from.get(curr)
            if curr is None:  # 防呆
                return None

        # path 是 [終點, ..., 第二步, 下一步]
        # 我們只要回傳 path 的最後一個元素 (也就是 start 的下一步)
        if path:
            return path[-1]
        return None

    def _handle_waiting_bounce(self):
        home_pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)
        limit = 5
        self.pixel_y += self.direction[1]
        if self.pixel_y > home_pixel_y + limit:
            self.direction = (0, -0.5)
        elif self.pixel_y < home_pixel_y - limit:
            self.direction = (0, 0.5)

    def update(self, game_map, player, dt, global_ghost_mode, blinky_tile=None):
        # 1. 狀態與模式檢查 (保持原樣)
        valid_to_switch = (self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]
                           and not self.is_frightened
                           and not self.is_eaten)

        if valid_to_switch:
            if global_ghost_mode == MODE_SCATTER and self.current_ai_mode != MODE_SCATTER:
                self.current_ai_mode = MODE_SCATTER
                self.direction = (
                    self.direction[0] * -1, self.direction[1] * -1)
            elif global_ghost_mode == MODE_CHASE and self.current_ai_mode == MODE_SCATTER:
                # 從散開切回追逐時，通常不用反向，順著跑即可
                self.current_ai_mode = self.ai_mode

        # 處理 WAITING (保持原樣，這段邏輯很獨立)
        if self.current_ai_mode == MODE_WAITING:
            if self.is_frightened:  # 驚嚇時原地彈跳
                self._handle_waiting_bounce()
                return

            self.delay -= dt
            if self.delay <= 0:
                self.current_ai_mode = MODE_EXIT_HOUSE
                self.direction = (0, -1)
                self.pixel_x = (self.home_pos[0]
                                * TILE_SIZE) + (TILE_SIZE // 2)
                self.pixel_y = (self.home_pos[1]
                                * TILE_SIZE) + (TILE_SIZE // 2)
                self.speed = self.default_speed
            else:
                self._handle_waiting_bounce()
            return  # 等待中不執行後續移動

        # --- 移動邏輯開始 ---

        # 位置小數點修正 (保持原樣)
        if abs(self.pixel_x - round(self.pixel_x)) < 0.1:
            self.pixel_x = round(self.pixel_x)
        if abs(self.pixel_y - round(self.pixel_y)) < 0.1:
            self.pixel_y = round(self.pixel_y)

        is_centered_x = (self.pixel_x - (TILE_SIZE // 2)) % TILE_SIZE == 0
        is_centered_y = (self.pixel_y - (TILE_SIZE // 2)) % TILE_SIZE == 0

        # 【決策階段】：只有走到格子正中心時，才動腦思考下一步
        if is_centered_x and is_centered_y:
            self.grid_x = (self.pixel_x - (TILE_SIZE // 2)) // TILE_SIZE
            self.grid_y = (self.pixel_y - (TILE_SIZE // 2)) // TILE_SIZE

            # A. 處理特殊事件 (回家抵達、出門完成)
            if self.current_ai_mode == MODE_GO_HOME and (self.grid_x, self.grid_y) == self.home_pos:
                self.respawn()
                return  # 重生後這一幀先不動

            if self.current_ai_mode == MODE_EXIT_HOUSE:
                if self.grid_y <= 11:  # 已經走出門口
                    self.current_ai_mode = self.ai_mode
                    # 出門後隨機選個方向防止卡頓 (非必要，但順暢點)
                    self.direction = random.choice([(-1, 0), (1, 0)])

            # 設定速度 (驚嚇變慢、回家變快)
            if self.current_ai_mode == MODE_GO_HOME:
                self.speed = 2 * SPEED
            elif self.current_ai_mode == MODE_FRIGHTENED:
                self.speed = 1  # 或 SPEED // 2
            else:
                self.speed = self.default_speed

            # B. 【決策核心】：取得目標 -> 選擇演算法 -> 取得下一步
            # 1. 取得目標 (Target)
            target = self.get_target_position(player, blinky_tile)
            self.target = target  # 存起來方便 debug

            # 散開模式的特殊邏輯：如果到了角落點，切換下一個
            if self.current_ai_mode == MODE_SCATTER:
                if (self.grid_x, self.grid_y) == target:
                    self.scatter_index = (
                        self.scatter_index + 1) % len(self.scatter_path)
                    target = self.get_target_position(
                        player, blinky_tile)  # 更新目標

            # 2. 執行演算法 (Algorithm)
            start_pos = (self.grid_x % len(game_map[0]), self.grid_y)
            next_step = None

            # 根據 settings 設定的演算法來跑
            if self.algorithm == ALGO_GREEDY:
                next_step = self.algo_greedy(start_pos, target)
            elif self.algorithm == ALGO_BFS:
                next_step = self.algo_bfs(start_pos, target)
            elif self.algorithm == ALGO_ASTAR:
                next_step = self.algo_astar(start_pos, target)

            # 3. 計算移動向量 (處理隧道)
            if next_step:
                dx = next_step[0] - self.grid_x
                dy = next_step[1] - self.grid_y
                map_width = len(game_map[0])

                # 隧道判斷：如果水平差距過大，代表是穿過邊界
                if dx > map_width // 2:
                    self.direction = (-1, 0)  # 往左鑽
                elif dx < -map_width // 2:
                    self.direction = (1, 0)  # 往右鑽
                else:
                    self.direction = (dx, dy)
            else:
                valid_neighbors = self.get_neighbors(start_pos)
                if valid_neighbors:
                    # 簡單策略：隨機選一個，或者選和當前方向最接近的
                    fallback_step = random.choice(valid_neighbors)
                    dx = fallback_step[0] - self.grid_x
                    dy = fallback_step[1] - self.grid_y
                    self.direction = (dx, dy)

        # 即使 A* 說可以走，我們還是要檢查下一步會不會撞牆 (雙重保險)
        can_move = True

        # 預測下一步的位置 (只檢查前方一個 TILE 的距離)
        next_check_x = self.grid_x + self.direction[0]
        next_check_y = self.grid_y + self.direction[1]

        # 處理隧道邊界，避免 Index Error
        map_width = len(game_map[0])
        next_check_x = next_check_x % map_width

        # 如果不是在中心點 (正在移動中)，通常允許繼續走，直到下一個中心點
        # 但如果 A* 規劃錯誤導致方向撞牆，這裡要擋下來
        if is_centered_x and is_centered_y:
            if 0 <= next_check_y < len(game_map):

                # 安全讀取地圖格子
                if next_check_x < len(game_map[next_check_y]):
                    next_tile = game_map[next_check_y][next_check_x]

                    # 1. 【優先檢查】如果是門
                    if next_tile == TILE_DOOR:
                        # 如果 "不是" 出門或回家模式，才擋下來
                        if self.current_ai_mode not in [MODE_EXIT_HOUSE, MODE_GO_HOME]:
                            can_move = False

                    # 2. 如果是牆壁 (且上面沒說是可通行的門)
                    elif is_wall(game_map, next_check_x, next_check_y):
                        can_move = False
                else:
                    # 超出該行長度 (虛空)，視為牆壁
                    can_move = False

        if can_move:
            self.pixel_x += self.direction[0] * self.speed
            self.pixel_y += self.direction[1] * self.speed

        # 隧道瞬間移動 (Teleport)
        if self.pixel_x < -TILE_SIZE//2:
            self.pixel_x = SCREEN_WIDTH + TILE_SIZE//2
            self.grid_x = 27
        elif self.pixel_x > SCREEN_WIDTH + TILE_SIZE//2:
            self.pixel_x = -TILE_SIZE//2
            self.grid_x = 0
