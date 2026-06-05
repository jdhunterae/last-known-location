"""
sound.py — Sound propagation system for Last Known Location.

Sound radiates outward from a source tile in a rounded-square pattern.
Unlike line of sight, sound is omnidirectional and is not blocked by walls.

The hearing radius forms a square of size (2r+1) with the 4 outer corners
clipped, and the origin tile excluded (the "eye of the storm").

Shape example (range=2, entity at E):
     XXX
    XXXXX
    XXEXX
    XXXXX
     XXX

Rules:
    - A tile is within hearing range if |dr| <= r AND |dc| <= r
    - EXCEPT the 4 corners where |dr| == r AND |dc| == r (clipped)
    - EXCEPT the origin tile itself (dr == 0, dc == 0)
    - Walls do NOT block sound propagation
    - The sound target is always the tile coordinate where the sound
      originated, not the entity that caused it

Coordinate system:
    (row, col) — row 0 is top of map, col 0 is left edge.
"""

from app.models.grid import Grid


def get_sound_radius_tiles(
    origin: tuple[int, int],
    sound_range: int,
) -> list[tuple[int, int]]:
    """
    Return all tiles within hearing range of the origin.

    The pattern is a square with the 4 outer corners clipped and the
    origin tile excluded.

    Args:
        origin:      (row, col) of the listening entity.
        sound_range: Maximum tile distance the entity can hear.

    Returns:
        List of (row, col) tuples within hearing range (unfiltered for
        grid bounds).
    """
    er, ec = origin
    tiles = []

    for dr in range(-sound_range, sound_range + 1):
        for dc in range(-sound_range, sound_range + 1):
            # Exclude origin — the "eye of the storm"
            if dr == 0 and dc == 0:
                continue
            # Clip the 4 outer corners
            if abs(dr) == sound_range and abs(dc) == sound_range:
                continue
            tiles.append((er + dr, ec + dc))

    return tiles


def can_hear(
    grid: Grid,
    listener: tuple[int, int],
    sound_range: int,
    source: tuple[int, int],
) -> bool:
    """
    Return whether a sound at source can be heard by the listener.

    Sound is not blocked by walls. The listener cannot hear sounds
    originating from their own tile. The source must be within the
    grid bounds.

    Args:
        grid:        The Grid (used for bounds checking).
        listener:    (row, col) of the listening entity.
        sound_range: Maximum tile distance the entity can hear.
        source:      (row, col) of the tile where the sound originated.

    Returns:
        True if the source tile is within hearing range, False otherwise.
    """
    sr, sc = source
    lr, lc = listener

    # Source must be in bounds
    if not grid.in_bounds(sr, sc):
        return False

    dr = sr - lr
    dc = sc - lc

    # Exclude origin tile
    if dr == 0 and dc == 0:
        return False

    # Exclude the 4 outer corners
    if abs(dr) == sound_range and abs(dc) == sound_range:
        return False

    # Within the bounding square
    return abs(dr) <= sound_range and abs(dc) <= sound_range


def check_sound_event(
    grid: Grid,
    listener: tuple[int, int],
    sound_range: int,
    source: tuple[int, int],
) -> tuple[bool, tuple[int, int] | None]:
    """
    Process a sound event and return whether the listener heard it.

    If the listener can hear the sound, returns the source tile as the
    investigation target. The target is always the tile coordinate where
    the sound occurred — not the entity that caused it.

    Args:
        grid:        The Grid (used for bounds checking).
        listener:    (row, col) of the listening entity.
        sound_range: Maximum tile distance the entity can hear.
        source:      (row, col) of the tile where the sound originated.

    Returns:
        (heard, target) where:
            heard  — True if the listener detected the sound
            target — (row, col) of the source tile if heard, else None
    """
    if can_hear(grid, listener, sound_range, source):
        return True, source
    return False, None
