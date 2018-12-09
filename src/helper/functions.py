import math
from math import floor

from src.helper.Misc import constants


def get_hexagonal_manhattan_distance(start, end):
    dx = abs(start[0] - end[0])
    dy = abs(start[1] - end[1])
    # first go up/down, then go left/right
    if end[0] < start[0]:
        hor_part = dx - floor((dy + 1) / 2)
    else:
        hor_part = dx - floor(dy / 2)
    if hor_part < 0:
        hor_part = 0
    dist = dy * 1.001 + hor_part
    return dist


def get_hexagonal_euclidian_distance(start, end):
    start_x, start_y = start
    end_x, end_y = end
    start_is_shifted = start_y % 2
    end_is_shifted = end_y % 2
    if start_is_shifted:
        start_x += 0.5
    if end_is_shifted:
        end_x += 0.5
    dx = abs(start_x - end_x)
    dy = abs(start_y - end_y) * constants.grid_height_factor

    dist = math.sqrt(math.pow(dx, 2) + math.pow(dy, 2))
    return dist
