"""
line_of_sight.py — Sight cone and wall-blocked LOS for Last Known Location.

The NPC has a directional sight cone that widens with distance:
- At distance d from the NPC, the cone covers tiles within ±d perpendicular
  to the facing direction.
- At range=2, the farthest row has width 5; at range=3, width 7.
- Walls block LOS. A tile is visible only if the ray from the NPC to that
  tile is not interrupted by a wall tile.

Cone shape example (facing North, range=2, entity at E):
    XXXXX   <- distance 2, width 5
     XXX    <- distance 1, width 3
      E

Coordinate system:
    (row, col) — row 0 is top of map, col 0 is left edge.
"""

from app.models.grid import Grid
from app.systems.facing import FacingDirection


def get_cone_tiles(
    origin: tuple[int, int],
    facing: FacingDirection,
    sight_range: int,
) -> list[tuple[int, int]]:
    """
    Return all tiles within the NPC's sight cone, ignoring walls.

    The cone widens with distance: at distance d, tiles within ±d
    perpendicular to the facing direction are included.

    Args:
        origin:      (row, col) of the NPC.
        facing:      The direction the NPC is facing.
        sight_range: Maximum tile distance the NPC can see.

    Returns:
        List of (row, col) tuples within the cone (unsorted, unfiltered
        for walls or grid bounds).
    """
    r, c = origin

    if facing == FacingDirection.NORTH:
        return [(r - i, c + j)
                for i in range(1, sight_range + 1)
                for j in range(-i, i + 1)]

    if facing == FacingDirection.SOUTH:
        return [(r + i, c - j)
                for i in range(1, sight_range + 1)
                for j in range(-i, i + 1)]

    if facing == FacingDirection.EAST:
        return [(r - j, c + i)
                for i in range(1, sight_range + 1)
                for j in range(-i, i + 1)]

    if facing == FacingDirection.WEST:
        return [(r + j, c - i)
                for i in range(1, sight_range + 1)
                for j in range(-i, i + 1)]

    return []


def _ray_clear(
    grid: Grid,
    origin: tuple[int, int],
    target: tuple[int, int],
) -> bool:
    """
    Check whether the ray from origin to target is unobstructed by walls.

    Uses a tile-stepped Bresenham-style walk. The origin tile itself is
    never checked (the NPC's own tile). The target tile is checked last —
    if the target itself is a wall, the ray is considered blocked.

    Args:
        grid:   The Grid to check against.
        origin: (row, col) of the viewer (NPC).
        target: (row, col) of the tile being checked.

    Returns:
        True if no wall tiles interrupt the ray, False otherwise.
    """
    or_, oc = origin
    tr, tc = target

    dr = tr - or_
    dc = tc - oc
    steps = max(abs(dr), abs(dc))

    if steps == 0:
        return True

    for step in range(1, steps + 1):
        # Interpolate along the ray, rounding to nearest tile centre
        r = round(or_ + dr * step / steps)
        c = round(oc + dc * step / steps)
        if grid.blocks_sight(r, c):
            return False

    return True


def get_visible_tiles(
    grid: Grid,
    origin: tuple[int, int],
    facing: FacingDirection,
    sight_range: int,
) -> list[tuple[int, int]]:
    """
    Return all tiles visible to the NPC after applying wall occlusion.

    A tile is visible if:
    1. It falls within the sight cone.
    2. It is within the grid bounds.
    3. The ray from the NPC to that tile is not blocked by a wall.

    Args:
        grid:        The Grid to check against.
        origin:      (row, col) of the NPC.
        facing:      The direction the NPC is facing.
        sight_range: Maximum tile distance the NPC can see.

    Returns:
        List of (row, col) tuples the NPC can currently see.
    """
    cone = get_cone_tiles(origin, facing, sight_range)
    return [
        tile for tile in cone
        if grid.in_bounds(tile[0], tile[1])
        and _ray_clear(grid, origin, tile)
    ]


def can_see(
    grid: Grid,
    origin: tuple[int, int],
    facing: FacingDirection,
    sight_range: int,
    target: tuple[int, int],
) -> bool:
    """
    Return whether the NPC at origin can see the target tile.

    Args:
        grid:        The Grid to check against.
        origin:      (row, col) of the NPC.
        facing:      The direction the NPC is facing.
        sight_range: Maximum tile distance the NPC can see.
        target:      (row, col) of the tile to check visibility for.

    Returns:
        True if the target is within the visible cone and not wall-blocked.
    """
    cone = set(get_cone_tiles(origin, facing, sight_range))
    if target not in cone:
        return False
    if not grid.in_bounds(target[0], target[1]):
        return False
    return _ray_clear(grid, origin, target)