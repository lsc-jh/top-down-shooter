import json
import math

import pygame
from tileforge import Renderer, Map, Tileset, get_from_home

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

PLAYER_SPEED = 3
BULLET_SPEED = 8
BULLET_SIZE = 6
SHOOT_COOLDOWN = 200


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


class GameMap:
    def __init__(self, path):
        with open(path) as f:
            data = json.load(f)

        self.tileset = Tileset(data["tileset"], data["tile_size"])
        self.tileset.add_property_set(1, set(data["blocked_tiles"]))

        width = len(data["layers"][0][0])
        height = len(data["layers"][0])

        self.map = Map(width, height)
        self.map.set_layers(data["layers"])

        self.renderer = Renderer(self.tileset, self.map, 2)

    @property
    def tile_size(self):
        return self.renderer.render_tile_size

    @property
    def width_px(self):
        return self.map.width * self.tile_size

    @property
    def height_px(self):
        return self.map.height * self.tile_size

    def load(self):
        self.tileset.load()

    def draw(self, screen, camera):
        def callback(x, y, draw_x, draw_y):
            if self.renderer.cell_has_property((x, y), 1):
                pygame.draw.rect(
                    screen,
                    (255, 0, 0),
                    (
                        draw_x,
                        draw_y,
                        self.tile_size,
                        self.tile_size,
                    ),
                    2,
                )

        self.renderer.render(screen, (-camera.x, -camera.y), callback=callback)

    def is_blocked(self, tile_x, tile_y):
        if tile_x < 0 or tile_y < 0:
            return True

        if tile_x >= self.map.width or tile_y >= self.map.height:
            return True

        return self.map.cell_has_property(self.tileset, (tile_x, tile_y), 1)


class Camera:
    def __init__(self, screen_width, screen_height, map_width, map_height):
        self.x = 0
        self.y = 0

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.map_width = map_width
        self.map_height = map_height

    def follow(self, target):
        wanted_x = target.center_x - self.screen_width // 2
        wanted_y = target.center_y - self.screen_height // 2

        if self.map_width > self.screen_width:
            self.x = clamp(wanted_x, 0, self.map_width - self.screen_width)
        else:
            self.x = -(self.screen_width - self.map_width) // 2

        if self.map_height > self.screen_height:
            self.y = clamp(wanted_y, 0, self.map_height - self.screen_height)
        else:
            self.y = -(self.screen_height - self.map_height) // 2

    def screen_to_world(self, screen_x, screen_y):
        return screen_x + self.x, screen_y + self.y


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


def get_player_movement():
    keys = pygame.key.get_pressed()

    dx = 0
    dy = 0

    if keys[pygame.K_w]:
        dy -= PLAYER_SPEED
    if keys[pygame.K_s]:
        dy += PLAYER_SPEED
    if keys[pygame.K_a]:
        dx -= PLAYER_SPEED
    if keys[pygame.K_d]:
        dx += PLAYER_SPEED

    return dx, dy


def main():
    pygame.init()

    game_map = GameMap(get_from_home("tileset-editor-export.json"))

    screen_width = clamp(game_map.width_px, SCREEN_WIDTH, 1000)
    screen_height = clamp(game_map.height_px, SCREEN_HEIGHT, 800)

    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Top Down Shooter")

    game_map.load()

    clock = pygame.time.Clock()

    player = Player(
        game_map.tile_size * 4,
        game_map.tile_size * 1,
        game_map.tile_size // 2,
    )

    camera = Camera(
        screen_width,
        screen_height,
        game_map.width_px,
        game_map.height_px,
    )

    bullets = []
    last_shot_time = 0

    running = True

    while running:
        screen.fill((20, 20, 20))
        clock.tick(60)

        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if current_time - last_shot_time >= SHOOT_COOLDOWN:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        target_x, target_y = camera.screen_to_world(mouse_x, mouse_y)

                        bullet = player.shoot(target_x, target_y)

                        if bullet is not None:
                            bullets.append(bullet)
                            last_shot_time = current_time

        dx, dy = get_player_movement()
        player.move(dx, dy, game_map)

        for bullet in bullets:
            bullet.update(game_map)

        bullets = [bullet for bullet in bullets if bullet.alive]

        camera.follow(player)

        game_map.draw(screen, camera)

        for bullet in bullets:
            bullet.draw(screen, camera)

        player.draw(screen, camera)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()