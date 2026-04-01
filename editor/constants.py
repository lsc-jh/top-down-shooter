import pygame

TILE_SIZE = 8
SCALE = 4

MAP_WIDTH = 20
MAP_HEIGHT = 15

PALETTE_COLS = 5
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 1000

VIM_KEYS = [pygame.K_h, pygame.K_j, pygame.K_k, pygame.K_l]
NUMBERS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
VIM_NAV_KEYS = {
    pygame.K_h: (-1, 0),
    pygame.K_j: (0, 1),
    pygame.K_k: (0, -1),
    pygame.K_l: (1, 0)
}
