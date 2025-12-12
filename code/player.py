# player.py
import pygame
from settings import *
from entity import Entity
import math


class Player(Entity):
    def __init__(self, grid_x, grid_y, speed=SPEED):
        super().__init__(grid_x, grid_y, speed)
        self.radius = TILE_SIZE // 2 - 2
        self.next_direction = (0, 0)
        self.score = 0
        self.lives = MAX_LIVES

        # 動畫變數
        self.current_mouth_angle = 45  # 嘴巴張開角度 (0~45)
        self.anim_speed = 5  # 開合速度
        self.mouth_opening = True  # 是否正在張開
        self.rotation_angle = 0  # 身體旋轉角度

        # 死亡動畫變數
        self.is_dying = False
        self.death_anim_angle = 0
        self.death_anim_scale = 1.0

    def start_death_anim(self):
        self.is_dying = True
        self.death_anim_angle = 0
        self.death_anim_scale = 1.0

    def update_death_anim(self):
        """ 更新死亡動畫: 旋轉並縮小 """
        if self.is_dying:
            self.death_anim_angle += 10
            self.death_anim_scale -= 0.02
            if self.death_anim_scale < 0:
                self.death_anim_scale = 0
                return True  # 動畫結束
        return False

    def draw(self, surface):
        if self.is_dying:
            # 死亡動畫繪製: 旋轉 + 縮小
            current_radius = int(self.radius * self.death_anim_scale)
            if current_radius > 0:
                center = (int(self.pixel_x), int(self.pixel_y))
                # 繪製簡單的黃色圓形，隨scale變小
                pygame.draw.circle(surface, YELLOW, center, current_radius)
                # 可以加個叉叉眼或其他效果，這裡先做簡單的縮小消失
            return

        # 計算嘴巴角度
        start_angle = self.rotation_angle + self.current_mouth_angle
        end_angle = self.rotation_angle + 360 - self.current_mouth_angle

        # Pygame draw.arc 是畫線，畫實心小精靈比較適合用:
        # 1. 畫滿版黃圓
        # 2. 畫黑色三角形 (嘴巴) 蓋上去 -> 簡單有效

        # 繪製黃色身體
        center = (int(self.pixel_x), int(self.pixel_y))
        pygame.draw.circle(surface, YELLOW, center, self.radius)

        # 計算嘴巴三角形的三個頂點
        # 頂點 1: 圓心
        # 頂點 2: 上嘴唇外緣
        # 頂點 3: 下嘴唇外緣

        # 轉換角度為弧度 (Pygame 座標系: 0度是右邊, 順時針增加? 不, 數學是逆時針, Pygame 是順時針嗎?
        # Pygame 的 math.cos/sin 通常吃弧度。
        # 這裡簡單處理：
        # 0 度 = 右 (1, 0)
        # 90 度 = 下 (0, 1)
        # 180 度 = 左 (-1, 0)
        # 270 度 = 上 (0, -1)

        p2_angle_rad = math.radians(
            self.rotation_angle + self.current_mouth_angle)
        p3_angle_rad = math.radians(
            self.rotation_angle - self.current_mouth_angle)

        p2_x = center[0] + self.radius * math.cos(p2_angle_rad)
        p2_y = center[1] + self.radius * math.sin(p2_angle_rad)

        p3_x = center[0] + self.radius * math.cos(p3_angle_rad)
        p3_y = center[1] + self.radius * math.sin(p3_angle_rad)

        # 繪製黑色三角形蓋住嘴巴
        pygame.draw.polygon(
            surface, BLACK, [center, (p2_x, p2_y), (p3_x, p3_y)])

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

    def update(self, game_map, dt=0):
        """ 
        更新玩家狀態
        dt: delta time in milliseconds (如果有的話)
        回傳: 事件字串 (ATE_PELLET, etc) 或 None
        """
        dt_seconds = dt / 1000.0 if dt > 0 else None

        # --- 動畫更新 ---
        # 只有在移動時才動嘴巴
        if self.direction != (0, 0):
            if self.mouth_opening:
                self.current_mouth_angle += self.anim_speed
                if self.current_mouth_angle >= 45:
                    self.mouth_opening = False
            else:
                self.current_mouth_angle -= self.anim_speed
                if self.current_mouth_angle <= 0:
                    self.mouth_opening = True

            # 更新旋轉角度
            if self.direction == (1, 0):
                self.rotation_angle = 0
            elif self.direction == (0, 1):
                self.rotation_angle = 90
            elif self.direction == (-1, 0):
                self.rotation_angle = 180
            elif self.direction == (0, -1):
                self.rotation_angle = 270

        # 1. 檢查是否在格子中心 (用於轉彎判定)
        centered = self.is_centered()

        # 2. 嘗試轉彎 (如果玩家有按下方向鍵)
        if self.next_direction != (0, 0):
            # 只有在中心點附近才能轉彎，或者是在反向移動
            # 目前 Pac-Man 規則通常允許隨時反向，但轉彎需要對齊

            # 檢查是否反向 (Reversing)
            is_reverse = (self.next_direction[0] == -self.direction[0] and
                          self.next_direction[1] == -self.direction[1])

            if is_reverse or centered:
                # 檢查轉彎後的目標是否為牆
                curr_x, curr_y = self.get_grid_pos()  # 確保是整數
                next_grid_x = curr_x + self.next_direction[0]
                next_grid_y = curr_y + self.next_direction[1]

                can_turn = True
                if is_wall(game_map, next_grid_x, next_grid_y):
                    can_turn = False

                # 特殊檢查: 門不能進 (除非有特定邏輯，一般 Play 不能進鬼屋)
                if 0 <= next_grid_y < len(game_map) and 0 <= next_grid_x < len(game_map[0]):
                    if game_map[next_grid_y][next_grid_x] == TILE_DOOR:
                        can_turn = False

                if can_turn:
                    self.direction = self.next_direction
                    self.next_direction = (0, 0)
                    # 如果不是反向，而是轉彎，強制對齊網格
                    if not is_reverse:
                        self.snap_to_grid()

        # 3. 移動前檢查前方障礙
        can_move = True
        curr_x, curr_y = self.get_grid_pos()

        # 預測下一步的網格位置
        # 注意：這裡不只檢查相鄰，而是檢查「前方」
        # 如果已經貼牆，就不移動

        # 簡單判定：如果 "不在中心"，通常允許走到中心
        if centered:
            next_grid_x = curr_x + self.direction[0]
            next_grid_y = curr_y + self.direction[1]

            # 邊界檢查 (防止 Index Error) - 雖然 move 會 wrap，但這裡檢查牆壁
            if 0 <= next_grid_y < len(game_map) and 0 <= next_grid_x < len(game_map[0]):
                # 撞牆或撞門
                if is_wall(game_map, next_grid_x, next_grid_y):
                    can_move = False
                if game_map[next_grid_y][next_grid_x] == TILE_DOOR:
                    can_move = False
            else:
                # 超出地圖範圍，如果是隧道 (左右) 則允許
                # 若是上下超出則不允許 (照理說不會發生)
                if not (next_grid_x < 0 or next_grid_x >= len(game_map[0])):
                    can_move = False

        if can_move:
            self.move(dt_seconds)
        else:
            # 撞牆時，強制對齊中心避免微小飄移
            self.snap_to_grid()

        # 4. 吃豆子判定 (不修改地圖，只回傳事件)
        # 取得最新的 grid 座標
        gx, gy = self.get_grid_pos()

        # 邊界保護
        if 0 <= gy < len(game_map) and 0 <= gx < len(game_map[0]):
            tile = game_map[gy][gx]
            if tile == TILE_PELLET:
                return EVENT_ATE_PELLET
            elif tile == TILE_POWER_PELLET:
                return EVENT_ATE_POWER_PELLET

        return None
