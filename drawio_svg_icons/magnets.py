from typing import List, Tuple


def create_magnets(vertex: bool, side_count: int, coords_range=(0, 1)) -> List[Tuple[float, float]]:
    coord_min = coords_range[0]
    coord_max = coords_range[1]

    magnets = []
    if vertex:
        magnets.extend(create_vertex_magnets(coord_min, coord_max))
    magnets.extend(create_side_magnets(side_count, coord_min, coord_max))
    return magnets


def create_vertex_magnets(coord_min: float, coord_max: float) -> List[Tuple[float, float]]:
    return [
        (coord_min, coord_min),
        (coord_max, coord_min),
        (coord_max, coord_max),
        (coord_min, coord_max),
    ]


def create_side_magnets(count: int, coord_min: float, coord_max: float) -> List[Tuple[float, float]]:
    factor = (coord_max - coord_min) / (count + 1)

    magnets = []
    for i in range(1, count + 1):
        value = round(coord_min + factor * i, 3)
        magnets += [
            (coord_min, value),
            (value, coord_min),
            (coord_max, value),
            (value, coord_max),
        ]

    return magnets
