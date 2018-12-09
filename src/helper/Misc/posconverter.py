from math import floor

from src.helper.Misc.constants import is_odd, is_even, grid_height_factor
from src.helper.Misc.options_game import Options


class PosConverter:
    def __init__(self, camera, x_max, y_max):
        self.camera = camera
        self.x_max = x_max
        self.y_max = y_max

        self.row_height = grid_height_factor * Options.tile_height

    def board_to_surface_pos(self, pos):
        board_x, board_y = pos
        board_x_camera_adjusted = board_x - self.camera.x
        board_y_camera_adjusted = board_y - self.camera.y
        screen_x = self._get_screen_x(board_x_camera_adjusted, board_y)
        screen_y = (board_y_camera_adjusted * self.row_height)
        return screen_x, screen_y

    def _get_screen_x(self, board_x_camera_adjusted, board_y):
        screen_x = board_x_camera_adjusted * Options.tile_width
        screen_x = self._shift_right_if_odd_row(board_y, screen_x)
        return screen_x

    def _shift_right_if_odd_row(self, board_y, screen_x):
        if is_odd(board_y):  # even non-camera-adjusted rows are shifted right
            screen_x += 0.5 * Options.tile_width
        return screen_x

    def board_to_screen(self, pos, x, y):
        surface_x, surface_y = self.board_to_surface_pos(pos)
        screen_x = surface_x + x
        screen_y = surface_y + y
        return screen_x, screen_y

    def mouse_to_board(self, pos):
        mouse_x, mouse_y = pos
        half_tile_width = Options.tile_width / 2
        half_tile_height = Options.tile_height / 2
        # first grid dot has an xy of halfW x halfH
        # the space between the grid is halfW on the x side
        # and 0.7 * H on the y side
        grid_x = (floor((mouse_x + half_tile_width) / half_tile_width) + 2
                  * self.camera.x)
        grid_y = (floor((mouse_y - half_tile_height) / self.row_height + 2)
                  + self.camera.y)
        if grid_y < 0:
            grid_y = 0
        center_x, center_y = (grid_x, grid_y)
        corners = []
        # draw a square that surrounds the mouse_pos,
        # check_pos which corner is closest
        # closest corner is what player clicked on
        # get odd and even indices, odd y's need odd x'es,
        # even y's need even x'es
        if ((is_odd(center_x) and is_even(center_y))
                or
                (is_even(center_x) and is_odd(center_y))):
            corners.append((center_x, center_y - 1))
            corners.append((center_x - 1, center_y))
        else:
            corners.append((center_x, center_y))
            corners.append((center_x - 1, center_y - 1))
        # find which corner has the shorest distance using pythagoras
        dist = []
        for corner in corners:
            corner_x = ((corner[0] - self.camera.x * 2) * half_tile_width)
            a_squared = pow(corner_x - mouse_x, 2)
            corner_y = ((corner[1] - self.camera.y) * self.row_height
                        - Options.tile_height * 0.2)
            b_squared = pow(corner_y - mouse_y, 2)
            c = pow(a_squared + b_squared, 0.5)
            dist.append(c)
        if dist[0] > dist[1]:
            corner = corners[1]
        else:
            corner = corners[0]
        y = floor(corner[1] - 1)
        x = floor((corner[0] - 1) / 2)
        if self._pos_is_outside_boundaries(x, y) or \
                self._pos_is_outside_camera(x, y):
            return -1, -1
        return x, y

    def _pos_is_outside_boundaries(self, x, y):
        return x < 0 or y < 0 or x >= self.x_max or y >= self.y_max

    def _pos_is_outside_camera(self, x, y):
        return (x > self.camera.x + self.camera.width or
                y > self.camera.y + self.camera.height or
                x < self.camera.x or y < self.camera.y)
