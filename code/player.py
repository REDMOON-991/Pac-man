# player.py
import pygame
from settings import *  # 匯入 TILE_SIZE, YELLOW, SCREEN_WIDTH 等


class Player:
    def __init__(self, grid_x, grid_y):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.pixel_x = (self.grid_x * TILE_SIZE) + (TILE_SIZE // 2)
        self.pixel_y = (self.grid_y * TILE_SIZE) + (TILE_SIZE // 2)
        self.radius = TILE_SIZE // 2 - 2
        self.speed = SPEED
        self.direction = (0, 0)
        self.next_direction = (0, 0)
        self.score = 0

    def draw(self, surface):    # 先畫一個黃色圓形當小精靈
        pygame.draw.circle(
            surface, YELLOW, (self.pixel_x, self.pixel_y), self.radius)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.next_direction = (0, -1)
            elif event.key == pygame.K_DOWN:
                self.next_direction = (0, 1)
            elif event.key == pygame.K_LEFT:
                self.next_direction = (-1, 0)
            elif event.key == pygame.K_RIGHT:
                self.next_direction = (1, 0)

    def update(self, game_map):
        """ 更新玩家狀態。返回 'ATE_PELLET', 'ATE_POWER_PELLET', 或 None """

        # 檢查是否在格子中心 (分開檢查 X 和 Y)
        dist_x = abs((self.pixel_x - (TILE_SIZE // 2)) % TILE_SIZE)
        dist_y = abs((self.pixel_y - (TILE_SIZE // 2)) % TILE_SIZE)

        is_centered_x = dist_x < self.speed
        is_centered_y = dist_y < self.speed

        # 計算目前的整數網格座標
        curr_grid_x = int((self.pixel_x - (TILE_SIZE // 2)) // TILE_SIZE)
        curr_grid_y = int((self.pixel_y - (TILE_SIZE // 2)) // TILE_SIZE)
        self.grid_x = curr_grid_x
        self.grid_y = curr_grid_y

        # 吃豆子邏輯
        # 加入邊界檢查，防止吃豆子時也報錯
        if 0 <= curr_grid_y < len(game_map) and 0 <= curr_grid_x < len(game_map[0]):
            current_tile = game_map[curr_grid_y][curr_grid_x]
            if current_tile == TILE_PELLET:
                game_map[curr_grid_y][curr_grid_x] = TILE_EMPTY
                return EVENT_ATE_PELLET
            elif current_tile == TILE_POWER_PELLET:
                game_map[curr_grid_y][curr_grid_x] = TILE_EMPTY
                return EVENT_ATE_POWER_PELLET

        # 轉彎邏輯 (分軸檢查)
        if self.next_direction != (0, 0):
            # 水平轉彎 (左/右)
            if self.next_direction[1] == 0:
                if is_centered_y:
                    next_grid_x = curr_grid_x + self.next_direction[0]
                    # 檢查邊界，如果在範圍內才檢查牆壁；範圍外(隧道)允許轉彎
                    if not is_wall(game_map, next_grid_x, curr_grid_y) and game_map[curr_grid_y][next_grid_x] != TILE_DOOR:
                        self.direction = self.next_direction
                        self.next_direction = (0, 0)
                        self.pixel_y = (
                            curr_grid_y * TILE_SIZE) + (TILE_SIZE // 2)

            # 垂直轉彎 (上/下)
            elif self.next_direction[0] == 0:
                if is_centered_x:
                    next_grid_y = curr_grid_y + self.next_direction[1]
                    # 檢查邊界
                    if not is_wall(game_map, curr_grid_x, next_grid_y) and game_map[next_grid_y][curr_grid_x] != TILE_DOOR:
                        self.direction = self.next_direction
                        self.next_direction = (0, 0)
                        self.pixel_x = (
                            curr_grid_x * TILE_SIZE) + (TILE_SIZE // 2)

        # 移動與撞牆檢查 (分軸檢查 + 邊界保護)
        can_move = True

        # 如果正在水平移動 (左/右)
        if self.direction[1] == 0 and self.direction[0] != 0:
            if is_centered_x:
                next_grid_x = curr_grid_x + self.direction[0]
                # 只有當 next_g_x 在地圖範圍內時，才檢查是不是牆壁
                # 如果超出範圍 (例如 -1 或 29)，代表正在進隧道，我們允許移動 (不設 can_move = False)
                if 0 <= next_grid_x < len(game_map[0]):
                    if is_wall(game_map, next_grid_x, curr_grid_y) or game_map[curr_grid_y][next_grid_x] == TILE_DOOR:
                        can_move = False
                        self.pixel_x = (
                            curr_grid_x * TILE_SIZE) + (TILE_SIZE // 2)

        # 如果正在垂直移動 (上/下)
        elif self.direction[0] == 0 and self.direction[1] != 0:
            if is_centered_y:
                next_grid_y = curr_grid_y + self.direction[1]
                # 只有當 next_g_y 在地圖範圍內時，才檢查是不是牆壁
                if 0 <= next_grid_y < len(game_map):
                    if is_wall(game_map, curr_grid_x, next_grid_y) or game_map[next_grid_y][curr_grid_x] == TILE_DOOR:
                        can_move = False
                        self.pixel_y = (
                            curr_grid_y * TILE_SIZE) + (TILE_SIZE // 2)

        if can_move:
            self.pixel_x += self.direction[0] * self.speed
            self.pixel_y += self.direction[1] * self.speed

        # 隧道處理 (超出邊界後瞬間移動到另一邊)
        if self.pixel_x < -TILE_SIZE//2:
            self.pixel_x = SCREEN_WIDTH + TILE_SIZE//2
        elif self.pixel_x > SCREEN_WIDTH + TILE_SIZE//2:
            self.pixel_x = -TILE_SIZE//2

        return None
