import pygame
import random
import math

from lib import world_to_tile, tile_to_world_center, clamp
from pathfinding import find_path
from constants import *


class Enemy:
    def __init__(self, x, y, game_map, size=ENEMY_SIZE):
        self.x = x
        self.y = y
        self.size = size
        self.alive = True
        self.game_map = game_map

        self.path = []
        self.last_path_update = 0

        self.offset_x = random.uniform(
            -game_map.tile_size * 0.15,
            game_map.tile_size * 0.15,
        )
        self.offset_y = random.uniform(
            -game_map.tile_size * 0.15,
            game_map.tile_size * 0.15,
        )

    @property
    def center_x(self):
        return self.x + self.size / 2

    @property
    def center_y(self):
        return self.y + self.size / 2

    def tile_position(self, game_map):
        return world_to_tile(self.center_x, self.center_y, game_map.tile_size)

    def update(self, player, game_map):
        now = pygame.time.get_ticks()

        if now - self.last_path_update >= ENEMY_PATH_UPDATE_INTERVAL:
            self.path = find_path(
                self.tile_position(game_map),
                player.tile_position(game_map),
                game_map,
            )
            self.last_path_update = now

        self.follow_path(game_map)

    def follow_path(self, game_map):
        if not self.path:
            return

        next_tile_x, next_tile_y = self.path[0]

        target_x, target_y = tile_to_world_center(
            next_tile_x,
            next_tile_y,
            game_map.tile_size,
        )

        target_x += self.offset_x
        target_y += self.offset_y

        dx = target_x - self.center_x
        dy = target_y - self.center_y

        distance = math.hypot(dx, dy)

        if distance <= ENEMY_SPEED:
            self.path.pop(0)
            return

        dx /= distance
        dy /= distance

        self.x += dx * ENEMY_SPEED
        self.y += dy * ENEMY_SPEED

    def collides_with_bullet(self, bullet):
        closest_x = clamp(bullet.x, self.x, self.x + self.size)
        closest_y = clamp(bullet.y, self.y, self.y + self.size)

        dx = bullet.x - closest_x
        dy = bullet.y - closest_y

        return dx * dx + dy * dy <= BULLET_SIZE * BULLET_SIZE

    def collides_with_player(self, player):
        return (
                self.x < player.x + player.size
                and self.x + self.size > player.x
                and self.y < player.y + player.size
                and self.y + self.size > player.y
        )

    def draw(self, screen, camera):
        pygame.draw.rect(
            screen,
            (80, 180, 80),
            (
                self.x - camera.x,
                self.y - camera.y,
                self.size,
                self.size,
            ),
        )

        if SHOW_ENEMY_PATHS:
            self.draw_path(screen, camera)

    def draw_path(self, screen, camera):
        for tile_x, tile_y in self.path:
            world_x, world_y = tile_to_world_center(
                tile_x,
                tile_y,
                self.game_map.tile_size,
            )

            pygame.draw.circle(
                screen,
                (80, 120, 255),
                (
                    int(world_x - camera.x),
                    int(world_y - camera.y),
                ),
                3,
            )
