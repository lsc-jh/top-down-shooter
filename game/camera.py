from lib import clamp

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
