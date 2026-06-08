"""
test_sound.py — Unit tests for the sound propagation system.
"""

import pytest
from app.models.grid import Grid, TileType
from app.systems.sound import get_sound_radius_tiles, can_hear, check_sound_event

G = TileType.GROUND
W = TileType.WALL
N = TileType.NOISY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def open_grid(rows=12, cols=12):
    return Grid(rows, cols)


# ---------------------------------------------------------------------------
# Sound radius shape tests
# ---------------------------------------------------------------------------

class TestSoundRadiusTiles:
    def test_range1_shape(self):
        """
        Range=1 should produce a 3x3 square minus 4 corners minus origin = 4 tiles.
        The 4 cardinal neighbors only.

             X
            XEX
             X
        """
        tiles = set(get_sound_radius_tiles((5, 5), 1))
        expected = {(4, 5), (6, 5), (5, 4), (5, 6)}
        assert tiles == expected

    def test_range2_shape(self):
        """
        Range=2, entity at (5,5).
        Full 5x5 square minus 4 corners minus origin.

             XXX
            XXXXX
            XXEXX
            XXXXX
             XXX
        """
        tiles = set(get_sound_radius_tiles((5, 5), 2))

        # Corners should be excluded
        assert (3, 3) not in tiles  # top-left corner
        assert (3, 7) not in tiles  # top-right corner
        assert (7, 3) not in tiles  # bottom-left corner
        assert (7, 7) not in tiles  # bottom-right corner

        # Origin excluded
        assert (5, 5) not in tiles

        # Cardinal extremes included
        assert (3, 5) in tiles  # top center
        assert (7, 5) in tiles  # bottom center
        assert (5, 3) in tiles  # left center
        assert (5, 7) in tiles  # right center

        # Middle ring included
        assert (4, 3) in tiles
        assert (4, 7) in tiles
        assert (6, 3) in tiles
        assert (6, 7) in tiles

    def test_range2_tile_count(self):
        """
        Range=2: 5x5=25 minus 4 corners minus 1 origin = 20 tiles.
        """
        tiles = get_sound_radius_tiles((5, 5), 2)
        assert len(tiles) == 20

    def test_range3_tile_count(self):
        """
        Range=3: 7x7=49 minus 4 corners minus 1 origin = 44 tiles.
        """
        tiles = get_sound_radius_tiles((5, 5), 3)
        assert len(tiles) == 44

    def test_range1_tile_count(self):
        """
        Range=1: 3x3=9 minus 4 corners minus 1 origin = 4 tiles.
        """
        tiles = get_sound_radius_tiles((5, 5), 1)
        assert len(tiles) == 4

    def test_origin_never_included(self):
        for r in range(1, 5):
            tiles = get_sound_radius_tiles((5, 5), r)
            assert (5, 5) not in tiles

    def test_corners_never_included(self):
        origin = (5, 5)
        for sound_range in range(1, 5):
            tiles = set(get_sound_radius_tiles(origin, sound_range))
            corners = [
                (5 - sound_range, 5 - sound_range),
                (5 - sound_range, 5 + sound_range),
                (5 + sound_range, 5 - sound_range),
                (5 + sound_range, 5 + sound_range),
            ]
            for corner in corners:
                assert corner not in tiles, \
                    f"Corner {corner} should be clipped at range={sound_range}"

    def test_radius_grows_with_range(self):
        r1 = get_sound_radius_tiles((5, 5), 1)
        r2 = get_sound_radius_tiles((5, 5), 2)
        r3 = get_sound_radius_tiles((5, 5), 3)
        assert len(r1) < len(r2) < len(r3)


# ---------------------------------------------------------------------------
# can_hear tests
# ---------------------------------------------------------------------------

class TestCanHear:
    def test_adjacent_tile_audible(self):
        grid = open_grid()
        assert can_hear(grid, (5, 5), 2, (5, 6)) is True

    def test_origin_tile_not_audible(self):
        """Entity cannot hear sounds on its own tile."""
        grid = open_grid()
        assert can_hear(grid, (5, 5), 2, (5, 5)) is False

    def test_corner_tile_not_audible(self):
        """Clipped corners are outside hearing range."""
        grid = open_grid()
        assert can_hear(grid, (5, 5), 2, (3, 3)) is False
        assert can_hear(grid, (5, 5), 2, (3, 7)) is False
        assert can_hear(grid, (5, 5), 2, (7, 3)) is False
        assert can_hear(grid, (5, 5), 2, (7, 7)) is False

    def test_tile_beyond_range_not_audible(self):
        grid = open_grid()
        assert can_hear(grid, (5, 5), 2, (5, 10)) is False

    def test_wall_does_not_block_sound(self):
        """Walls should NOT block sound propagation."""
        layout = [
            [G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G],
            [G, G, G, W, W, W, G, G],
            [G, G, G, W, G, W, G, G],
            [G, G, G, W, G, W, G, G],
            [G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G],
        ]
        grid = Grid.from_layout(layout)
        # Listener inside a walled room, source outside — still audible
        assert can_hear(grid, (4, 4), 3, (1, 4)) is True

    def test_noisy_tile_audible_within_range(self):
        layout = [[G] * 10 for _ in range(10)]
        layout[3][5] = N
        grid = Grid.from_layout(layout)
        assert can_hear(grid, (5, 5), 3, (3, 5)) is True

    def test_out_of_bounds_source_not_audible(self):
        grid = open_grid(5, 5)
        assert can_hear(grid, (2, 2), 3, (-1, 2)) is False
        assert can_hear(grid, (2, 2), 3, (2, 99)) is False

    def test_all_cardinal_extremes_audible_at_exact_range(self):
        grid = open_grid()
        listener = (5, 5)
        sound_range = 3
        extremes = [
            (5 - sound_range, 5),  # north
            (5 + sound_range, 5),  # south
            (5, 5 + sound_range),  # east
            (5, 5 - sound_range),  # west
        ]
        for tile in extremes:
            assert can_hear(grid, listener, sound_range, tile) is True

    def test_one_beyond_range_not_audible(self):
        grid = open_grid()
        assert can_hear(grid, (5, 5), 2, (5, 8)) is False


# ---------------------------------------------------------------------------
# check_sound_event tests
# ---------------------------------------------------------------------------

class TestCheckSoundEvent:
    def test_heard_returns_true_and_source_tile(self):
        grid = open_grid()
        heard, target = check_sound_event(grid, (5, 5), 2, (5, 6))
        assert heard is True
        assert target == (5, 6)

    def test_not_heard_returns_false_and_none(self):
        grid = open_grid()
        heard, target = check_sound_event(grid, (5, 5), 2, (5, 10))
        assert heard is False
        assert target is None

    def test_target_is_source_tile_not_entity(self):
        """The investigation target is the tile, not adjusted in any way."""
        grid = open_grid()
        source = (4, 7)
        heard, target = check_sound_event(grid, (5, 5), 3, source)
        assert heard is True
        assert target == source

    def test_own_tile_sound_not_heard(self):
        """Entity stepping on its own noisy tile should not trigger alert."""
        grid = open_grid()
        heard, target = check_sound_event(grid, (5, 5), 2, (5, 5))
        assert heard is False
        assert target is None

    def test_corner_sound_not_heard(self):
        grid = open_grid()
        heard, target = check_sound_event(grid, (5, 5), 2, (3, 3))
        assert heard is False
        assert target is None
