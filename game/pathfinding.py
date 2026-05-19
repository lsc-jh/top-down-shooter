import heapq
import math

DIAGONAL_COST = math.sqrt(2)

def heuristic(a, b):
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])

    straight = abs(dx - dy)
    diagonal = min(dx, dy)

    return straight + diagonal * DIAGONAL_COST


def get_neighbors(tile, game_map):
    x, y = tile

    directions = [
        (1, 0, 1),
        (-1, 0, 1),
        (0, 1, 1),
        (0, -1, 1),

        (1, 1, DIAGONAL_COST),
        (1, -1, DIAGONAL_COST),
        (-1, 1, DIAGONAL_COST),
        (-1, -1, DIAGONAL_COST),
    ]

    valid_neighbors = []

    for dx, dy, cost in directions:
        neighbor_x = x + dx
        neighbor_y = y + dy

        if game_map.is_blocked(neighbor_x, neighbor_y):
            continue

        if dx != 0 and dy != 0:
            horizontal_blocked = game_map.is_blocked(x + dx, y)
            vertical_blocked = game_map.is_blocked(x, y + dy)

            if horizontal_blocked or vertical_blocked:
                continue

        valid_neighbors.append(((neighbor_x, neighbor_y), cost))

    return valid_neighbors


def find_path(start, goal, game_map):
    if game_map.is_blocked(start[0], start[1]):
        return []

    if game_map.is_blocked(goal[0], goal[1]):
        return []

    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}
    visited = set()

    while open_set:
        _, current = heapq.heappop(open_set)

        if current in visited:
            continue

        visited.add(current)

        if current == goal:
            path = []

            while current in came_from:
                path.append(current)
                current = came_from[current]

            path.reverse()
            return path

        for neighbor, movement_cost in get_neighbors(current, game_map):
            new_score = g_score[current] + movement_cost

            if neighbor not in g_score or new_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = new_score

                priority = new_score + heuristic(neighbor, goal)
                heapq.heappush(open_set, (priority, neighbor))

    return []
