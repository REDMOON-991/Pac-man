# ghost.py
import pygame
import random
import math
from settings import *

class Ghost:
    def __init__(self, grid_x, grid_y, color, ai_mode="RANDOM", scatter_target=(0, 0)):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.home_pos = (grid_x, grid_y)
        
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
        self.is_eaten = False

    def draw(self, surface):
        if self.is_eaten:
            eye_radius = self.radius // 2
            eye_offset = self.radius // 3
            pygame.draw.circle(surface, WHITE, (self.pixel_x - eye_offset, self.pixel_y), eye_radius)
            pygame.draw.circle(surface, WHITE, (self.pixel_x + eye_offset, self.pixel_y), eye_radius)
        else:
            draw_color = self.color
            if self.is_frightened:
                draw_color = FRIGHTENED_BLUE
            pygame.draw.circle(surface, draw_color, (self.pixel_x, self.pixel_y), self.radius)

    def eat(self):
        print("一隻鬼被吃掉了！")
        self.is_frightened = False
        self.is_eaten = True
        self.current_ai_mode = "GO_HOME"
        self.speed = 4 
        self.target = self.home_pos 
        return 200 

    def respawn(self):
        print("一隻鬼重生了！")
        self.is_eaten = False
        self.current_ai_mode = self.ai_mode
        self.speed = self.default_speed
        self.pixel_x = (self.home_pos[0] * TILE_SIZE) + (TILE_SIZE // 2)
        self.pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)

    def start_frightened(self):
        if not self.is_eaten:
            self.is_frightened = True
            self.current_ai_mode = "FRIGHTENED"
            self.speed = 1
            self.direction = (self.direction[0] * -1, self.direction[1] * -1)

    def end_frightened(self):
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
            is_chase_or_random = (self.current_ai_mode.startswith("CHASE_") or self.current_ai_mode == "RANDOM")
            if is_chase_or_random and move_dir == reverse_dir:
                continue

            next_g_x = self.grid_x + move_dir[0]
            next_g_y = self.grid_y + move_dir[1]
            if 0 <= next_g_y < len(game_map) and 0 <= next_g_x < len(game_map[0]):
                if game_map[next_g_y][next_g_x] != "W":
                    valid_moves.append(move_dir)
                    
        if not valid_moves:
            if game_map[self.grid_y + reverse_dir[1]][self.grid_x + reverse_dir[0]] != "W":
                valid_moves.append(reverse_dir)

        return valid_moves

    def update(self, game_map, player, blinky_tile=None):
        is_centered_x = (self.pixel_x - (TILE_SIZE // 2)) % TILE_SIZE == 0
        is_centered_y = (self.pixel_y - (TILE_SIZE // 2)) % TILE_SIZE == 0

        if is_centered_x and is_centered_y:
            self.grid_x = (self.pixel_x - (TILE_SIZE // 2)) // TILE_SIZE
            self.grid_y = (self.pixel_y - (TILE_SIZE // 2)) // TILE_SIZE

            if self.current_ai_mode == "GO_HOME" and (self.grid_x, self.grid_y) == self.home_pos:
                self.respawn()
                
            valid_directions = self.get_valid_directions(game_map)

            player_dir_x = player.direction[0]
            player_dir_y = player.direction[1]
            player_stopped = (player_dir_x == 0 and player_dir_y == 0)
            
            self.target = (player.grid_x, player.grid_y)
            
            if self.current_ai_mode == "RANDOM": self.target = None 
            elif self.current_ai_mode == "FRIGHTENED": self.target = (player.grid_x, player.grid_y)
            elif self.current_ai_mode == "GO_HOME": self.target = self.home_pos
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

            if self.current_ai_mode == "RANDOM":
                if valid_directions: self.direction = random.choice(valid_directions)
            
            elif self.target and valid_directions:
                best_direction = (0, 0)
                if self.current_ai_mode == "FRIGHTENED":
                    best_distance = float('-inf')
                else:
                    best_distance = float('inf')

                for direction in valid_directions:
                    next_g_x = self.grid_x + direction[0]
                    next_g_y = self.grid_y + direction[1]
                    dist = self.get_distance((next_g_x, next_g_y), self.target)
                    
                    if self.current_ai_mode == "FRIGHTENED":
                        if dist > best_distance:
                            best_distance = dist; best_direction = direction
                    else:
                        if dist < best_distance:
                            best_distance = dist; best_direction = direction
                self.direction = best_direction
        
        self.pixel_x += self.direction[0] * self.speed
        self.pixel_y += self.direction[1] * self.speed
        
        if self.pixel_x < 0: self.pixel_x = SCREEN_WIDTH
        elif self.pixel_x > SCREEN_WIDTH: self.pixel_x = 0