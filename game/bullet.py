from constants import *
import pygame

class Bullet:
    def __init__(self, x, y, direction_x, direction_y):
        self.x = x
        self.y = y
        self.direction_x = direction_x
        self.direction_y = direction_y
        self.alive = True

    def update(self, game_map):
        self.x += self.direction_x * BULLET_SPEED
        self.y += self.direction_y * BULLET_SPEED

        tile_x = int(self.x // game_map.tile_size)
        tile_y = int(self.y // game_map.tile_size)

        if game_map.is_blocked(tile_x, tile_y):
            self.alive = False

    def draw(self, screen, camera):
        pygame.draw.circle(
            screen,
            (255, 230, 100),
            (
                int(self.x - camera.x),
                int(self.y - camera.y),
            ),
            BULLET_SIZE,
        )
