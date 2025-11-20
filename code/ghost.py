# ghost.py
import pygame
import random
import math
from settings import *

class Ghost:
    def __init__(self, grid_x, grid_y, color, ai_mode, scatter_path=None, in_house=False,delay=0):
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

        self.delay = delay

        if in_house:
            if self.delay > 0:
                self.current_ai_mode = "WAITING"
                self.direction = (0, -0.5) # 等待時稍微上下浮動的初始速度
            else:
                self.current_ai_mode = "EXIT_HOUSE"
                self.direction = (0, -1)
        else:
            self.current_ai_mode = ai_mode
        
        if scatter_path is None:
            self.scatter_path = [(grid_x, grid_y)]
        else:
            self.scatter_path = scatter_path

        self.scatter_index = 0  # 追蹤目前走到路徑的第幾個點
        self.target = (0, 0)

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
        print("一隻鬼重生了！準備出門")
        self.is_eaten = False
        self.current_ai_mode = "EXIT_HOUSE"
        self.speed = self.default_speed
        self.pixel_x = (self.home_pos[0] * TILE_SIZE) + (TILE_SIZE // 2)
        self.pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)
        self.direction = (0, -1)    # 重生時往上看，避免卡住

    def start_frightened(self):
        if  self.is_eaten:
            return
        # 不管位置 一律變成驚嚇狀態
        self.is_frightened = True
        #但是在家的AI模式不變
        if self.current_ai_mode not in ["GO_HOME", "EXIT_HOUSE", "WAITING"]:
            self.current_ai_mode = "FRIGHTENED"
            self.speed = 1
            self.direction = (self.direction[0] * -1, self.direction[1] * -1)

    def end_frightened(self):
        if self.is_frightened:
            self.is_frightened = False
            if self.current_ai_mode not in ["GO_HOME", "EXIT_HOUSE", "WAITING"]:
                self.current_ai_mode = self.ai_mode
            #self.speed = self.default_speed

    def get_distance(self, pos1, pos2):
        return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

    def get_valid_directions(self, game_map, others):
        valid_moves = []
        reverse_dir = (self.direction[0] * -1, self.direction[1] * -1)
        
        for move_dir in self.all_directions:
            # 某些模式下不能回頭
            no_rev = (self.current_ai_mode.startswith("CHASE_") or self.current_ai_mode == "GO_HOME" or self.current_ai_mode == "SCATTER")
            if no_rev and move_dir == reverse_dir:
                continue

            next_g_x = int(self.grid_x + move_dir[0])
            next_g_y = int(self.grid_y + move_dir[1])

            if 0 <= next_g_y < len(game_map) :
                check_x = next_g_x % len(game_map[0])
                tile = game_map[next_g_y][check_x]
                
                # 門的通行邏輯
                if tile == "W":
                    continue # 牆壁不能過
                elif tile == "=":
                    # 只有出門或回家(死掉)模式可以過門
                    if self.current_ai_mode not in ["EXIT_HOUSE", "GO_HOME"]:
                        continue

                # 鬼重疊檢查 (等待中或出門中的鬼不視為障礙)
                is_blocked_by_ghost = False
                if self.current_ai_mode not in ["EXIT_HOUSE", "GO_HOME", "WAITING"]:
                    for ghost in others:
                        if ghost is not self and ghost.current_ai_mode not in ["EXIT_HOUSE", "GO_HOME", "WAITING"]:
                            if ghost.grid_x == next_g_x and ghost.grid_y == next_g_y:
                                is_blocked_by_ghost = True
                                break
                
                if is_blocked_by_ghost:
                    continue

                # 如果通過上述檢查，則為合法方向
                valid_moves.append(move_dir)
                    
        if not valid_moves:
            valid_moves.append(reverse_dir)

        return valid_moves

    def update(self, game_map, player, all_ghosts, dt, blinky_tile=None):
        # 處理 WAITING 狀態
        if self.current_ai_mode == "WAITING":
            # 如果現在是驚嚇模式，就暫停倒數，直接 return 
            # 因為我們在 start_frightened 裡有設定 "就算在家也會變 is_frightened=True"
            if self.is_frightened:
                # 選擇讓它繼續 bounce，但不扣時間
                home_pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)
                limit = 5
                self.pixel_y += self.direction[1]
                if self.pixel_y > home_pixel_y + limit:
                    self.direction = (0, -0.5)
                elif self.pixel_y < home_pixel_y - limit:
                    self.direction = (0, 0.5)
                return
            
            self.delay -= dt
            # 檢查時間是否到了
            if self.delay <= 0:
                self.current_ai_mode = "EXIT_HOUSE"
                self.direction = (0, -1) # 往上衝
                # 修正位置到格子中心，確保出門路徑準確
                self.pixel_x = (self.home_pos[0] * TILE_SIZE) + (TILE_SIZE // 2)
                self.pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)
                self.speed = self.default_speed
            else:
                # 等待時的動畫：在原地上下輕微浮動 (Bounce)
                home_pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)
                limit = 5
                
                self.pixel_y += self.direction[1]
                if self.pixel_y > home_pixel_y + limit:
                    self.direction = (0, -0.5)
                elif self.pixel_y < home_pixel_y - limit:
                    self.direction = (0, 0.5)
            
            # WAITING 狀態不執行後面的移動邏輯
            return
        # 位置整數保證
        if abs(self.pixel_x - round(self.pixel_x)) < 0.1:
            self.pixel_x = round(self.pixel_x)
        if abs(self.pixel_y - round(self.pixel_y)) < 0.1:
            self.pixel_y = round(self.pixel_y)
        # 正常的移動狀態
        is_centered_x = (self.pixel_x - (TILE_SIZE // 2)) % TILE_SIZE == 0
        is_centered_y = (self.pixel_y - (TILE_SIZE // 2)) % TILE_SIZE == 0

        if is_centered_x and is_centered_y:
            self.grid_x = (self.pixel_x - (TILE_SIZE // 2)) // TILE_SIZE
            self.grid_y = (self.pixel_y - (TILE_SIZE // 2)) // TILE_SIZE


            if self.current_ai_mode == "GO_HOME" and (self.grid_x, self.grid_y) == self.home_pos:
                self.respawn()

            if self.current_ai_mode == "EXIT_HOUSE":
                # 如果 Y 座標小於等於 11 (門在 12)，代表已經出去了
                if self.grid_y <= 11:
                    self.current_ai_mode = self.ai_mode # 切換回正常追蹤模式
                    self.direction = random.choice([(-1, 0), (1, 0)])    #隨機往左往右

            if not self.is_frightened and self.current_ai_mode not in ["GO_HOME", "EXIT_HOUSE", "WAITING"]:
                self.speed = self.default_speed

            valid_directions = self.get_valid_directions(game_map, all_ghosts)

            player_dir_x = player.direction[0]
            player_dir_y = player.direction[1]
            player_stopped = (player_dir_x == 0 and player_dir_y == 0)
            
            self.target = (player.grid_x, player.grid_y)
            
            # 設定AI模式
            # 共通模式 離家 回家 驚嚇
            if self.current_ai_mode == "EXIT_HOUSE": self.target = (13.5, 10) 
            elif self.current_ai_mode == "FRIGHTENED": self.target = (player.grid_x, player.grid_y)
            elif self.current_ai_mode == "GO_HOME": self.target = self.home_pos
            # 新增散開模式
            elif self.current_ai_mode == "SCATTER":
                current_target_point = self.scatter_path[self.scatter_index]
                if (self.grid_x, self.grid_y) == current_target_point:
                    self.scatter_index += 1
                    if self.scatter_index >= len(self.scatter_path):
                        self.scatter_index = 0  # 回到第一個點，形成迴圈
                
                self.target = self.scatter_path[self.scatter_index]
            # 四個鬼的獨立AI
            # PINKY 追著玩家
            elif self.current_ai_mode == "CHASE_BLINKY": self.target = (player.grid_x, player.grid_y)
            # BLINKY 預測玩家未來的位置 追那裡
            #? 如果超出、是牆壁的話要怎麼追
            elif self.current_ai_mode == "CHASE_PINKY":
                if player_stopped: self.target = (player.grid_x, player.grid_y)
                else: self.target = (player.grid_x + (player_dir_x * 4), player.grid_y + (player_dir_y * 4))
            # CLYDE 裝忙 快追到就跑
            elif self.current_ai_mode == "CHASE_CLYDE":
                distance = self.get_distance((self.grid_x, self.grid_y), (player.grid_x, player.grid_y))
                if distance > 8: self.target = (player.grid_x, player.grid_y)
                else: self.target = self.scatter_path[0]
            # INKY 由blinky和玩家的位置決定要怎麼追
            elif self.current_ai_mode == "CHASE_INKY":
                if blinky_tile is None or player_stopped: self.target = (player.grid_x, player.grid_y)
                else:
                    trigger_x = player.grid_x + (player_dir_x * 2)
                    trigger_y = player.grid_y + (player_dir_y * 2)
                    blinky_x, blinky_y = blinky_tile
                    vec_x = trigger_x - blinky_x; vec_y = trigger_y - blinky_y
                    self.target = (trigger_x + vec_x, trigger_y + vec_y)

        
            if self.target and valid_directions:
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
            
        if self.pixel_x < -TILE_SIZE//2: self.pixel_x = SCREEN_WIDTH + TILE_SIZE//2
        elif self.pixel_x > SCREEN_WIDTH + TILE_SIZE//2: self.pixel_x = -TILE_SIZE//2