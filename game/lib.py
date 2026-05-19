def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def world_to_tile(x, y, tile_size):
    return int(x // tile_size), int(y // tile_size)


def tile_to_world_center(tile_x, tile_y, tile_size):
    return (
        tile_x * tile_size + tile_size / 2,
        tile_y * tile_size + tile_size / 2,
    )
