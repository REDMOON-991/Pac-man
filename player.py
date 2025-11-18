# player.py
import pygame
from settings import * # 匯入 TILE_SIZE, YELLOW, SCREEN_WIDTH 等

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
        """ 更新玩家狀態。返回 'ATE_PELLET', 'ATE_POWER_PELLET', 或 None """
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
                return "ATE_PELLET"
            elif current_tile == "O":
                game_map[self.grid_y][self.grid_x] = " "
                self.score += 50
                return "ATE_POWER_PELLET"
            
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
                self.direction = (0, 0)
        
        # 4. 移動
        self.pixel_x += self.direction[0] * self.speed
        self.pixel_y += self.direction[1] * self.speed
        
        # 5. 隧道
        if self.pixel_x < 0: self.pixel_x = SCREEN_WIDTH
        elif self.pixel_x > SCREEN_WIDTH: self.pixel_x = 0
        
        return None