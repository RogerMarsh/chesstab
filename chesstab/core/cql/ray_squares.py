# ray_squares.py
# Copyright 2022 Roger Marsh
# Licence: See LICENCE (BSD licence)

"""Define squares in rays in terms of the pgn_read *_ATTACKS dicts.

There are eight basic ray directions, and five compound ray directions.

"""
from pgn_read.core.constants import (
    FILE_ATTACKS,
    RANK_ATTACKS,
    LRD_DIAGONAL_ATTACKS,
    RLD_DIAGONAL_ATTACKS,
)

from .directions import (
    Up,
    Down,
    Right,
    Left,
    Northeast,
    Northwest,
    Southeast,
    Southwest,
    Diagonal,
    Orthogonal,
    Vertical,
    Horizontal,
    AnyDirection,
    MainDiagonal,
    OffDiagonal,
)


def _build(direction1, direction2, source):
    """Populate direction1 and direction2 sets from source.

    The two directions are opposite directions in the same line.

    """
    for start, sqr_list in source.items():
        base, line = sqr_list
        for end in line:
            offset = line.index(end)
            if offset > base:
                direction1.add((start, end))
            elif offset < base:
                direction2.add((start, end))


_up = set()
_down = set()
_build(_up, _down, FILE_ATTACKS)
_up = frozenset(_up)
_down = frozenset(_down)

_right = set()
_left = set()
_build(_right, _left, RANK_ATTACKS)
_right = frozenset(_right)
_left = frozenset(_left)

_northwest = set()
_southeast = set()
_build(_northwest, _southeast, LRD_DIAGONAL_ATTACKS)
_northwest = frozenset(_northwest)
_southeast = frozenset(_southeast)

_northeast = set()
_southwest = set()
_build(_northeast, _southwest, RLD_DIAGONAL_ATTACKS)
_northeast = frozenset(_northeast)
_southwest = frozenset(_southwest)

del _build

_ray = {}
_ray[_up] = FILE_ATTACKS
_ray[_down] = FILE_ATTACKS
_ray[_right] = RANK_ATTACKS
_ray[_left] = RANK_ATTACKS
_ray[_northwest] = LRD_DIAGONAL_ATTACKS
_ray[_southeast] = LRD_DIAGONAL_ATTACKS
_ray[_northeast] = RLD_DIAGONAL_ATTACKS
_ray[_southwest] = RLD_DIAGONAL_ATTACKS

_directions = {}
_directions[Up] = (_up,)
_directions[Down] = (_down,)
_directions[Right] = (_right,)
_directions[Left] = (_left,)
_directions[Northeast] = (_northeast,)
_directions[Northwest] = (_northwest,)
_directions[Southeast] = (_southeast,)
_directions[Southwest] = (_southwest,)
_directions[Diagonal] = (_northwest, _southeast, _northeast, _southwest)
_directions[Orthogonal] = (_up, _down, _right, _left)
_directions[Vertical] = (_up, _down)
_directions[Horizontal] = (_right, _left)
_directions[AnyDirection] = (
    _up,
    _down,
    _right,
    _left,
    _northwest,
    _southeast,
    _northeast,
    _southwest,
)
_directions[MainDiagonal] = (_northeast, _southwest)
_directions[OffDiagonal] = (_northwest, _southeast)

_name_direction = {
    "up": Up,
    "down": Down,
    "right": Right,
    "left": Left,
    "northwest": Northwest,
    "northeast": Northeast,
    "southwest": Southwest,
    "southeast": Southeast,
    "diagonal": Diagonal,
    "orthogonal": Orthogonal,
    "vertical": Vertical,
    "horizontal": Horizontal,
    "anydirection": AnyDirection,
    "maindiagonal": MainDiagonal,
    "offdiagonal": OffDiagonal,
}


def get_ray_squares(*args, direction_parameters=None):
    """Return list of squares in ray defined by start and end in args.

    args must contain exactly two square names, ("c1", "f4") for example,
    where the first name is the start of the ray and the second name is the
    end of the ray, returning ['c1', 'd2', 'e3', 'f4'].  The two squares in
    ("c2", "a5") are not on the same diagonal, file, or rank, so [] is
    returned.

    direction_parameters must an iterable of the eight basic direction or
    five compound direction classes defined in directions module.  Default
    is [AnyDirection].

    There is no direction containing just 'up' and 'left', but it can be
    chosen by 'direction_parameters=(Up, Left)' for example.

    """
    if not direction_parameters:
        direction_parameters = [AnyDirection]
    for direction_class in direction_parameters:
        for direction in _directions[direction_class]:
            if args in direction:
                start, end = args
                start_index, vector = _ray[direction][start]
                end_index = vector.index(end)
                if end_index > start_index:
                    return vector[start_index : end_index + 1]
                return tuple(reversed(vector[end_index : start_index + 1]))
    return ()


def get_direction_class(direction_name):
    """Return direction class associated with direction_name or None."""
    return _name_direction.get(direction_name)


# del everything except _directions, get_ray_squares, get_direction_class,
# _name_direction, and AnyDirection.
del FILE_ATTACKS, RANK_ATTACKS, LRD_DIAGONAL_ATTACKS, RLD_DIAGONAL_ATTACKS
del Up
del Down
del Right
del Left
del Northeast
del Northwest
del Southeast
del Southwest
del Diagonal
del Orthogonal
del Vertical
del Horizontal
del MainDiagonal
del OffDiagonal
del _up
del _down
del _right
del _left
del _northwest
del _southeast
del _northeast
del _southwest
