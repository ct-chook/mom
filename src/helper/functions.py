import math

from src.helper.Misc import constants


def get_hexagonal_manhattan_distance(start, end):
    """Get the manhattan difference between two hexes on a hexagonal grid

    Going diagnally is possible which shortens distances considerably.
    Manhattan distance is: diagonal distance plus horizontal or vertical
    adjustment
    For vertical adjustment, beware that you may jump left or right when going
    up or down on the grid
    """
    assert len(start) == 2
    assert len(end) == 2
    dx = abs(start[0] - end[0])
    dy = abs(start[1] - end[1])

    # when traveling from even to odd: you may move left
    # when traveling odd to even: you may go right
    # odd to odd or even to even: you may go left or right for every 2 vertical
    # spaces
    # for multi-row movements: you may do both
    # odd to even: stay or right
    # odd to even to odd: left, stay, right
    # odd to even to odd to even: leftx2, rightx2
    # so there is a horizontal move budget that increases as you got vertically
    if start[1] % 2 == 1:
        start_at_even = False
    else:
        start_at_even = True

    if start_at_even:
        max_left = math.ceil(dy / 2)
        max_right = math.floor(dy / 2)
    else:
        max_right = math.ceil(dy / 2)
        max_left = math.floor(dy / 2)

    if end[0] > start[0]:
        # moving to the right
        hor_part = dx - max_right
    else:
        # moving to the left
        hor_part = dx - max_left
    if hor_part < 0:
        hor_part = 0
    dist = dy + hor_part
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
