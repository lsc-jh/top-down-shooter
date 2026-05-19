import json
import random
import pygame
from lib import world_to_tile, clamp
from tileforge import Renderer, Map, Tileset, get_from_home
from constants import *
from enemy import Enemy
from player import Player
from camera import Camera


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


def spawn_enemy(game_map, camera):
    for _ in range(50):
        side = random.choice(["top", "bottom", "left", "right"])

        if side == "top":
            x = random.uniform(
                camera.x - ENEMY_SPAWN_PADDING,
                camera.x + camera.screen_width + ENEMY_SPAWN_PADDING,
            )
            y = camera.y - ENEMY_SPAWN_PADDING

        elif side == "bottom":
            x = random.uniform(
                camera.x - ENEMY_SPAWN_PADDING,
                camera.x + camera.screen_width + ENEMY_SPAWN_PADDING,
            )
            y = camera.y + camera.screen_height + ENEMY_SPAWN_PADDING

        elif side == "left":
            x = camera.x - ENEMY_SPAWN_PADDING
            y = random.uniform(
                camera.y - ENEMY_SPAWN_PADDING,
                camera.y + camera.screen_height + ENEMY_SPAWN_PADDING,
            )

        else:
            x = camera.x + camera.screen_width + ENEMY_SPAWN_PADDING
            y = random.uniform(
                camera.y - ENEMY_SPAWN_PADDING,
                camera.y + camera.screen_height + ENEMY_SPAWN_PADDING,
            )

        x = clamp(x, 0, game_map.width_px - ENEMY_SIZE)
        y = clamp(y, 0, game_map.height_px - ENEMY_SIZE)

        tile_x, tile_y = world_to_tile(x, y, game_map.tile_size)

        if not game_map.is_blocked(tile_x, tile_y):
            return Enemy(
                x - ENEMY_SIZE / 2,
                y - ENEMY_SIZE / 2,
                game_map,
            )

    return None


def get_mouse_shot(player, camera):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    target_x, target_y = camera.screen_to_world(mouse_x, mouse_y)

    return player.shoot(target_x, target_y)


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
    enemies = []

    last_shot_time = 0
    last_enemy_spawn_time = 0

    running = True

    while running:
        screen.fill((20, 20, 20))
        clock.tick(60)

        current_time = pygame.time.get_ticks()

        def shoot():
            nonlocal last_shot_time, current_time

            if current_time - last_shot_time >= SHOOT_COOLDOWN:
                b = get_mouse_shot(player, camera)

                if b is not None:
                    bullets.append(b)
                    last_shot_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    shoot()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                shoot()

        dx, dy = get_player_movement()
        player.move(dx, dy, game_map)

        camera.follow(player)

        if current_time - last_enemy_spawn_time >= ENEMY_SPAWN_INTERVAL:
            enemy = spawn_enemy(game_map, camera)

            if enemy is not None:
                enemies.append(enemy)

            last_enemy_spawn_time = current_time

        for bullet in bullets:
            bullet.update(game_map)

        for enemy in enemies:
            enemy.update(player, game_map)

        for bullet in bullets:
            for enemy in enemies:
                if enemy.alive and bullet.alive and enemy.collides_with_bullet(bullet):
                    enemy.alive = False
                    bullet.alive = False

        for enemy in enemies:
            if enemy.collides_with_player(player):
                print("Player hit!")

        bullets = [bullet for bullet in bullets if bullet.alive]
        enemies = [enemy for enemy in enemies if enemy.alive]

        game_map.draw(screen, camera)

        for bullet in bullets:
            bullet.draw(screen, camera)

        for enemy in enemies:
            enemy.draw(screen, camera)

        player.draw(screen, camera)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
