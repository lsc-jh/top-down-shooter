import asyncio
import json
import math
import time
import uuid

from tileforge import Map, Tileset

HOST = "0.0.0.0"
PORT = 8080

TICK_RATE = 60
PLAYER_SPEED = 180
BULLET_SPEED = 520
SHOOT_COOLDOWN = 0.25

PLAYER_SIZE = 24
BULLET_SIZE = 6
PLAYER_HP = 3

MAP_PATH = "tileset-editor-export.json"
MAP_SCALE = 2


def now():
    return time.monotonic()


def load_map_data():
    with open(MAP_PATH) as f:
        return json.load(f)


class GameMap:
    def __init__(self, data):
        self.data = data

        self.tileset = Tileset(data["tileset"], data["tile_size"])
        self.tileset.add_property_set(1, set(data["blocked_tiles"]))

        width = len(data["layers"][0][0])
        height = len(data["layers"][0])

        self.map = Map(width, height)
        self.map.set_layers(data["layers"])

        self.tile_size = data["tile_size"] * MAP_SCALE
        self.width_px = width * self.tile_size
        self.height_px = height * self.tile_size

    def is_blocked(self, tile_x, tile_y):
        if tile_x < 0 or tile_y < 0:
            return True

        if tile_x >= self.map.width or tile_y >= self.map.height:
            return True

        return self.map.cell_has_property(self.tileset, (tile_x, tile_y), 1)

    def world_to_tile(self, x, y):
        return int(x // self.tile_size), int(y // self.tile_size)


def rect_circle_collision(rect_x, rect_y, rect_size, circle_x, circle_y, radius):
    closest_x = max(rect_x, min(circle_x, rect_x + rect_size))
    closest_y = max(rect_y, min(circle_y, rect_y + rect_size))

    dx = circle_x - closest_x
    dy = circle_y - closest_y

    return dx * dx + dy * dy <= radius * radius


class GameServer:
    def __init__(self):
        self.map_data = load_map_data()
        self.game_map = GameMap(self.map_data)

        self.clients = {}
        self.players = {}
        self.inputs = {}
        self.bullets = []

    async def handle_client(self, reader, writer):
        player_id = str(uuid.uuid4())

        self.players[player_id] = {
            "x": 100 + len(self.players) * 120,
            "y": 100,
            "hp": PLAYER_HP,
            "alive": True,
            "last_shot": 0,
        }

        self.inputs[player_id] = self.empty_input()
        self.clients[player_id] = writer

        await self.send(writer, {
            "type": "init",
            "player_id": player_id,
            "map": self.map_data,
        })

        print(f"Player connected: {player_id}")

        try:
            while True:
                line = await reader.readline()

                if not line:
                    break

                try:
                    message = json.loads(line.decode())
                except json.JSONDecodeError:
                    print(f"Invalid JSON from player: {player_id}")
                    continue

                if message.get("type") == "input":
                    self.inputs[player_id] = {
                        "up": bool(message.get("up", False)),
                        "down": bool(message.get("down", False)),
                        "left": bool(message.get("left", False)),
                        "right": bool(message.get("right", False)),
                        "shoot": bool(message.get("shoot", False)),
                        "mouse_x": float(message.get("mouse_x", 0)),
                        "mouse_y": float(message.get("mouse_y", 0)),
                    }

        except ConnectionError:
            pass
        finally:
            print(f"Player disconnected: {player_id}")

            self.clients.pop(player_id, None)
            self.players.pop(player_id, None)
            self.inputs.pop(player_id, None)

            writer.close()
            await writer.wait_closed()

    def empty_input(self):
        return {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "shoot": False,
            "mouse_x": 0,
            "mouse_y": 0,
        }

    async def send(self, writer, message):
        data = json.dumps(message).encode() + b"\n"
        writer.write(data)
        await writer.drain()

    async def broadcast(self, message):
        disconnected = []

        for player_id, writer in list(self.clients.items()):
            try:
                await self.send(writer, message)
            except ConnectionError:
                disconnected.append(player_id)

        for player_id in disconnected:
            self.clients.pop(player_id, None)
            self.players.pop(player_id, None)
            self.inputs.pop(player_id, None)

    def can_player_move_to(self, x, y):
        corners = [
            (x, y),
            (x + PLAYER_SIZE, y),
            (x, y + PLAYER_SIZE),
            (x + PLAYER_SIZE, y + PLAYER_SIZE),
        ]

        for corner_x, corner_y in corners:
            tile_x, tile_y = self.game_map.world_to_tile(corner_x, corner_y)

            if self.game_map.is_blocked(tile_x, tile_y):
                return False

        return True

    def move_player(self, player, dx, dy, dt):
        new_x = player["x"] + dx * PLAYER_SPEED * dt
        new_y = player["y"] + dy * PLAYER_SPEED * dt

        if self.can_player_move_to(new_x, new_y):
            player["x"] = new_x
            player["y"] = new_y

    def update_players(self, dt):
        current_time = now()

        for player_id, player in list(self.players.items()):
            if not player["alive"]:
                continue

            input_state = self.inputs.get(player_id, self.empty_input())

            dx = 0
            dy = 0

            if input_state["up"]:
                dy -= 1
            if input_state["down"]:
                dy += 1
            if input_state["left"]:
                dx -= 1
            if input_state["right"]:
                dx += 1

            length = math.hypot(dx, dy)

            if length > 0:
                dx /= length
                dy /= length

            self.move_player(player, dx, dy, dt)

            if input_state["shoot"] and current_time - player["last_shot"] >= SHOOT_COOLDOWN:
                self.spawn_bullet(player_id, player, input_state)
                player["last_shot"] = current_time

    def update_bullets(self, dt):
        for bullet in self.bullets:
            if not bullet["alive"]:
                continue

            bullet["x"] += bullet["dir_x"] * BULLET_SPEED * dt
            bullet["y"] += bullet["dir_y"] * BULLET_SPEED * dt

            tile_x, tile_y = self.game_map.world_to_tile(bullet["x"], bullet["y"])

            if self.game_map.is_blocked(tile_x, tile_y):
                bullet["alive"] = False

    def update_bullet_hits(self):
        for bullet in self.bullets:
            if not bullet["alive"]:
                continue

            for player_id, player in self.players.items():
                if player_id == bullet["owner_id"]:
                    continue

                if not player["alive"]:
                    continue

                if rect_circle_collision(
                        player["x"],
                        player["y"],
                        PLAYER_SIZE,
                        bullet["x"],
                        bullet["y"],
                        BULLET_SIZE,
                ):
                    bullet["alive"] = False
                    player["hp"] -= 1

                    if player["hp"] <= 0:
                        player["alive"] = False

                    break

    def update(self, dt):
        self.update_players(dt)
        self.update_bullets(dt)
        self.update_bullet_hits()

        self.bullets = [
            bullet for bullet in self.bullets
            if bullet["alive"]
        ]

    def spawn_bullet(self, owner_id, player, input_state):
        start_x = player["x"] + PLAYER_SIZE / 2
        start_y = player["y"] + PLAYER_SIZE / 2

        dx = input_state["mouse_x"] - start_x
        dy = input_state["mouse_y"] - start_y

        length = math.hypot(dx, dy)

        if length == 0:
            return

        dx /= length
        dy /= length

        self.bullets.append({
            "owner_id": owner_id,
            "x": start_x,
            "y": start_y,
            "dir_x": dx,
            "dir_y": dy,
            "alive": True,
        })

    def get_state(self):
        return {
            "type": "state",
            "players": self.players,
            "bullets": [
                {
                    "x": bullet["x"],
                    "y": bullet["y"],
                    "owner_id": bullet["owner_id"],
                }
                for bullet in self.bullets
            ],
        }

    async def game_loop(self):
        last_time = now()

        while True:
            current_time = now()
            dt = current_time - last_time
            last_time = current_time

            self.update(dt)
            await self.broadcast(self.get_state())

            await asyncio.sleep(1 / TICK_RATE)

    async def start(self):
        server = await asyncio.start_server(
            self.handle_client,
            HOST,
            PORT,
            limit=10 * 1024 * 1024,
        )
        print(f"Server running on {HOST}:{PORT}")

        async with server:
            await asyncio.gather(
                server.serve_forever(),
                self.game_loop(),
            )


if __name__ == "__main__":
    game_server = GameServer()
    asyncio.run(game_server.start())
