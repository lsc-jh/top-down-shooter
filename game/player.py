from lib import world_to_tile
import pygame
import math
from bullet import Bullet


class Player:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size

    @property
    def center_x(self):
        return self.x + self.size / 2

    @property
    def center_y(self):
        return self.y + self.size / 2

    def tile_position(self, game_map):
        return world_to_tile(self.center_x, self.center_y, game_map.tile_size)

    def move(self, dx, dy, game_map):
        self.try_move(dx, 0, game_map)
        self.try_move(0, dy, game_map)

    def try_move(self, dx, dy, game_map):
        new_x = self.x + dx
        new_y = self.y + dy

        if self.collides(new_x, new_y, game_map):
            return

        self.x = new_x
        self.y = new_y

    def collides(self, x, y, game_map):
        tile_size = game_map.tile_size

        corners = [
            (x, y),
            (x + self.size - 1, y),
            (x, y + self.size - 1),
            (x + self.size - 1, y + self.size - 1),
        ]

        for corner_x, corner_y in corners:
            tile_x = int(corner_x // tile_size)
            tile_y = int(corner_y // tile_size)

            if game_map.is_blocked(tile_x, tile_y):
                return True

        return False

    def shoot(self, target_x, target_y):
        dx = target_x - self.center_x
        dy = target_y - self.center_y

        distance = math.hypot(dx, dy)

        if distance == 0:
            return None

        dx /= distance
        dy /= distance

        return Bullet(
            self.center_x,
            self.center_y,
            dx,
            dy,
        )

    def draw(self, screen, camera):
        pygame.draw.rect(
            screen,
            (255, 50, 50),
            (
                self.x - camera.x,
                self.y - camera.y,
                self.size,
                self.size,
            ),
        )
