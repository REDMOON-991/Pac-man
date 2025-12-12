# ghost.py
import pygame
import random
import math
from settings import *
from entity import Entity
from queue import PriorityQueue


class Ghost(Entity):
    def __init__(self, grid_x, grid_y, color, ai_mode, speed=SPEED, scatter_point=None, in_house=False, delay=0, on_log=None, algorithm=ALGO_ASTAR):
        # 初始化 Entity
        super().__init__(grid_x, grid_y, speed)

        self.home_pos = (grid_x, grid_y)
        self.radius = TILE_SIZE // 2 - 2
        self.color = color

        self.default_speed = SPEED
        self.direction = (1, 0)

        # 繼承自 Entity 的 pixel_x/y 用來繪圖

        self.ai_mode = ai_mode
        self.algorithm = algorithm
        self.delay = delay

        self.current_ai_mode = ai_mode
        if in_house:
            if self.delay > 0:
                self.current_ai_mode = MODE_WAITING
                self.direction = (0, -0.5)
            else:
                self.current_ai_mode = MODE_EXIT_HOUSE
                self.direction = (0, -1)

        self.scatter_path = scatter_point if scatter_point else [
            (grid_x, grid_y)]
        self.scatter_index = 0
        self.target = (0, 0)

        self.is_frightened = False
        self.is_eaten = False
        self.on_log = on_log

    def draw(self, surface, flash_white=False):
        if self.is_eaten:
            # 只畫眼睛
            self._draw_eyes(surface)
        else:
            # 1. 畫身體 (上半圓 + 下半方)
            if self.is_frightened:
                draw_color = WHITE if flash_white else FRIGHTENED_BLUE
            else:
                draw_color = self.color

            center = (int(self.pixel_x), int(self.pixel_y))

            # 頭部
            pygame.draw.circle(surface, draw_color, center, self.radius)

            # 身體底部 (矩形向下延伸)
            rect_top = center[1]
            rect_h = self.radius
            rect_w = self.radius * 2
            body_rect = pygame.Rect(
                center[0] - self.radius, rect_top, rect_w, rect_h)
            pygame.draw.rect(surface, draw_color, body_rect)

            # 腳 (波浪) - 簡單畫三個小圓當腳
            leg_radius = self.radius // 3
            for i in range(3):
                lx = center[0] - self.radius + \
                    (i * 2 * leg_radius) + leg_radius
                ly = center[1] + self.radius

                # 簡單動畫: 根據 pixel_x 做一點起伏
                offset = math.sin(pygame.time.get_ticks() * 0.01 + i) * 2
                pygame.draw.circle(surface, draw_color,
                                   (int(lx), int(ly + offset)), leg_radius)

            # 2. 畫眼睛 (如果不是驚嚇模式)
            if not self.is_frightened:
                self._draw_eyes(surface)
            else:
                # 驚嚇模式畫嘴巴或簡單的驚恐眼
                # 這裡簡單畫驚嚇眼 (小方塊)
                pygame.draw.rect(surface, (255, 200, 200),
                                 (center[0]-4, center[1]-2, 2, 2))
                pygame.draw.rect(surface, (255, 200, 200),
                                 (center[0]+2, center[1]-2, 2, 2))

    def _draw_eyes(self, surface):
        """ 繪製眼睛與眼珠 (Helper) """
        center = (int(self.pixel_x), int(self.pixel_y))
        eye_radius = 4
        pupil_radius = 2
        eye_offset_x = 4
        eye_offset_y = -2

        # 眼珠偏移量 (看方向)
        look_x = self.direction[0] * 2
        look_y = self.direction[1] * 2

        # 左眼
        left_eye_pos = (center[0] - eye_offset_x, center[1] + eye_offset_y)
        pygame.draw.circle(surface, WHITE, left_eye_pos, eye_radius)
        pygame.draw.circle(surface, BLUE, (int(
            left_eye_pos[0] + look_x), int(left_eye_pos[1] + look_y)), pupil_radius)

        # 右眼
        right_eye_pos = (center[0] + eye_offset_x, center[1] + eye_offset_y)
        pygame.draw.circle(surface, WHITE, right_eye_pos, eye_radius)
        pygame.draw.circle(surface, BLUE, (int(
            right_eye_pos[0] + look_x), int(right_eye_pos[1] + look_y)), pupil_radius)

    def eat(self):
        if self.on_log:
            self.on_log(
                f"[{self.ai_mode}] Ghost eaten! Returning home.", GREY)
        self.is_frightened = False
        self.is_eaten = True
        self.current_ai_mode = MODE_GO_HOME
        self.speed = 2 * SPEED  # 回家速度快
        self.target = self.home_pos
        self.snap_to_grid()  # 簡單校正，避免未對齊

    def respawn(self):
        if self.on_log:
            self.on_log(
                f"[{self.ai_mode}] Ghost respawned! Exiting house.", self.color)
        self.is_eaten = False
        self.current_ai_mode = MODE_EXIT_HOUSE
        self.speed = self.default_speed

        # 重置回家的位置
        self.grid_x, self.grid_y = self.home_pos
        self.snap_to_grid()  # 強制同步 pixel
        self.direction = (0, -1)

    def start_frightened(self):
        if self.is_eaten:
            return
        if self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]:
            self.is_frightened = True
            self.current_ai_mode = MODE_FRIGHTENED
            self.speed = 1  # 變慢 (如果用 dt 架構，這裡應該是 0.5 * SPEED)
            self.direction = (self.direction[0] * -1, self.direction[1] * -1)
            if self.on_log:
                self.on_log(
                    f"[{self.ai_mode}] Ghost frightened!", FRIGHTENED_BLUE)

    def end_frightened(self):
        if self.is_frightened:
            self.is_frightened = False
            if self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]:
                self.current_ai_mode = self.ai_mode
                self.speed = self.default_speed
                if self.on_log:
                    self.on_log(
                        f"[{self.ai_mode}] Ghost unfrightened.", self.color)

    def get_neighbors(self, node):
        x, y = node
        neighbors = []
        map_width = len(GAME_MAP[0])
        map_height = len(GAME_MAP)

        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nx = (x + dx) % map_width
            ny = y + dy

            if 0 <= ny < map_height:
                if nx >= len(GAME_MAP[ny]):
                    continue
                if is_wall(GAME_MAP, nx, ny):
                    continue

                if GAME_MAP[ny][nx] == TILE_DOOR:
                    if self.current_ai_mode not in [MODE_EXIT_HOUSE, MODE_GO_HOME]:
                        continue
                neighbors.append((nx, ny))
        return neighbors

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_target_position(self, player, blinky_pos=None):
        target = (self.grid_x, self.grid_y)

        if self.current_ai_mode == MODE_GO_HOME:
            return self.home_pos
        elif self.current_ai_mode == MODE_EXIT_HOUSE:
            return GHOST_HOUSE_EXIT_POS
        elif self.current_ai_mode == MODE_FRIGHTENED:
            # 隨機漫步: 其實不需要特定的 global target，只要 local 隨機選
            # 但為了 unified logic，我們隨機選一個合法的點
            while True:
                rx = random.randint(1, 26)
                ry = random.randint(1, 29)
                if not is_wall(GAME_MAP, rx, ry):
                    return (rx, ry)

        elif self.current_ai_mode == MODE_SCATTER:
            target = self.scatter_path[self.scatter_index]
            return target  # Scatter 點通常是合法的，直接回傳

        elif self.current_ai_mode == AI_CHASE_BLINKY:
            target = (player.grid_x, player.grid_y)
        elif self.current_ai_mode == AI_CHASE_PINKY:
            dx, dy = player.direction
            target = (player.grid_x + dx * 4, player.grid_y + dy * 4)
        elif self.current_ai_mode == AI_CHASE_INKY and blinky_pos:
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
                target = self.scatter_path[0]

        return self.validate_target(target)

    def validate_target(self, target):
        tx, ty = int(target[0]), int(target[1])
        max_y = len(GAME_MAP) - 1

        # 修正：確保 max_x 是基於該行的長度 (雖然有 padding 了，但還是檢查一下 safe)
        if 0 <= ty <= max_y:
            max_x = len(GAME_MAP[ty]) - 1
        else:
            return (self.grid_x, self.grid_y)  # Out of bounds badly

        tx = max(1, min(tx, max_x - 1))
        ty = max(1, min(ty, max_y - 1))

        if is_wall(GAME_MAP, tx, ty):
            # 增強版 Fallback: 螺旋搜尋最近的空地
            for dist in range(1, 10):  # 增加搜尋範圍
                for dx, dy in [(0, dist), (0, -dist), (dist, 0), (-dist, 0),
                               (dist, dist), (dist, -dist), (-dist, dist), (-dist, -dist)]:
                    nx, ny = tx + dx, ty + dy
                    if 0 <= ny <= max_y and 0 <= nx < len(GAME_MAP[ny]):
                        if not is_wall(GAME_MAP, nx, ny):
                            return (nx, ny)
            return (self.grid_x, self.grid_y)

        return (tx, ty)

    # ... Algo methods (Greedy, BFS, A*) ...
    # 簡化：為節省篇幅，這裡我只放由 A* 代表，其他可以沿用

    def algo_greedy(self, start, target):
        neighbors = self.get_neighbors(start)
        # 禁止回頭邏輯 (Pac-Man standard)
        reverse_pos = (start[0] - self.direction[0],
                       start[1] - self.direction[1])
        valid_neighbors = [n for n in neighbors if n != reverse_pos]
        if not valid_neighbors:
            valid_neighbors = neighbors
        if not valid_neighbors:
            return None
        return min(valid_neighbors, key=lambda n: self.heuristic(n, target))

    def algo_bfs(self, start, target):
        queue = [start]
        came_from = {start: None}
        while queue:
            current = queue.pop(0)
            if current == target:
                break
            for next_node in self.get_neighbors(current):
                if next_node not in came_from:
                    queue.append(next_node)
                    came_from[next_node] = current
        return self.reconstruct_next_step(came_from, start, target)

    def algo_astar(self, start, target):
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
        if target not in came_from:
            return None
        curr = target
        path = []
        while curr != start:
            path.append(curr)
            curr = came_from.get(curr)
            if curr is None:
                return None
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
        dt_seconds = dt / 1000.0 if dt > 0 else 0

        # 狀態切換邏輯
        valid_to_switch = (self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]
                           and not self.is_frightened and not self.is_eaten)
        if valid_to_switch:
            if global_ghost_mode == MODE_SCATTER and self.current_ai_mode != MODE_SCATTER:
                self.current_ai_mode = MODE_SCATTER
                self.direction = (
                    self.direction[0] * -1, self.direction[1] * -1)
            elif global_ghost_mode == MODE_CHASE and self.current_ai_mode == MODE_SCATTER:
                self.current_ai_mode = self.ai_mode

        if self.current_ai_mode == MODE_WAITING:
            if self.is_frightened:
                self._handle_waiting_bounce()
                return
            self.delay -= dt  # dt is ms
            if self.delay <= 0:
                self.current_ai_mode = MODE_EXIT_HOUSE
                self.direction = (0, -1)
                self.snap_to_grid()
                self.speed = self.default_speed
            else:
                self._handle_waiting_bounce()
            return

        # 核心移動邏輯
        centered = self.is_centered()

        # 只有在中心點時才思考下一步
        if centered:
            self.get_grid_pos()  # Update grid_x/y

            # 特殊事件檢查
            if self.current_ai_mode == MODE_GO_HOME and (self.grid_x, self.grid_y) == self.home_pos:
                self.is_eaten = False
                self.is_frightened = False  # 重生後不再驚嚇
                self.current_ai_mode = MODE_EXIT_HOUSE
                if self.on_log:
                    self.on_log(
                        f"[{self.ai_mode}] Ghost respawned! Exiting house.", self.color)
                self.direction = (0, -1)  # Reset direction to exit house

            if self.current_ai_mode == MODE_EXIT_HOUSE:
                if self.grid_y <= GHOST_HOUSE_Y_THRESHOLD:
                    self.current_ai_mode = self.ai_mode
                    self.direction = random.choice([(-1, 0), (1, 0)])

            # 速度設定
            if self.current_ai_mode == MODE_GO_HOME:
                self.speed = 2 * SPEED
            elif self.current_ai_mode == MODE_FRIGHTENED:
                self.speed = 1.0  # 減速
            else:
                self.speed = self.default_speed

            # 決策
            target = self.get_target_position(player, blinky_tile)
            if self.current_ai_mode == MODE_SCATTER and (self.grid_x, self.grid_y) == target:
                self.scatter_index = (
                    self.scatter_index + 1) % len(self.scatter_path)
                target = self.get_target_position(player, blinky_tile)

            # 執行演算法
            start_pos = (self.grid_x % len(game_map[0]), self.grid_y)
            next_step = None

            if self.algorithm == ALGO_GREEDY:
                next_step = self.algo_greedy(start_pos, target)
            elif self.algorithm == ALGO_BFS:
                next_step = self.algo_bfs(start_pos, target)
            elif self.algorithm == ALGO_ASTAR:
                next_step = self.algo_astar(start_pos, target)

            if next_step:
                dx = next_step[0] - self.grid_x
                dy = next_step[1] - self.grid_y
                map_width = len(game_map[0])
                if dx > map_width // 2:
                    self.direction = (-1, 0)
                elif dx < -map_width // 2:
                    self.direction = (1, 0)
                else:
                    self.direction = (dx, dy)
            else:
                # Fallback: Just keep moving or random valid neighbor
                valid = self.get_neighbors(start_pos)
                if valid:
                    step = random.choice(valid)
                    self.direction = (step[0]-self.grid_x, step[1]-self.grid_y)

            # 決策完畢，修正位置
            self.snap_to_grid()

        # 移動 (Move)
        # 用 Entity move
        self.move(dt_seconds)
