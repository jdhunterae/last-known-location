"""
test_line_of_sight.py — Unit tests for the line of sight system.
"""

import pytest
from app.models.grid import Grid, TileType
from app.systems.facing import FacingDirection
from app.systems.line_of_sight import get_cone_tiles, get_visible_tiles, can_see

G = TileType.GROUND
W = TileType.WALL
N = TileType.NOISY


# ---------------------------------------------------------------------------
# Cone geometry tests (no walls, matches documented examples)
# ---------------------------------------------------------------------------

class TestConeGeometry:
    """Verify cone shape matches the spec in the design doc."""

    def test_north_range2(self):
        cone = set(get_cone_tiles((4, 4), FacingDirection.NORTH, 2))
        expected = {(2, 2), (2, 3), (2, 4), (2, 5),
                    (2, 6), (3, 3), (3, 4), (3, 5)}
        assert cone == expected

    def test_north_range3(self):
        cone = set(get_cone_tiles((4, 4), FacingDirection.NORTH, 3))
        expected = {
            (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
            (2, 2), (2, 3), (2, 4), (2, 5), (2, 6),
            (3, 3), (3, 4), (3, 5),
        }
        assert cone == expected

    def test_south_range2(self):
        cone = set(get_cone_tiles((1, 4), FacingDirection.SOUTH, 2))
        expected = {(3, 2), (3, 3), (3, 4), (3, 5),
                    (3, 6), (2, 3), (2, 4), (2, 5)}
        assert cone == expected

    def test_south_range3(self):
        cone = set(get_cone_tiles((1, 4), FacingDirection.SOUTH, 3))
        expected = {
            (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
            (3, 2), (3, 3), (3, 4), (3, 5), (3, 6),
            (2, 3), (2, 4), (2, 5),
        }
        assert cone == expected

    def test_west_range2(self):
        cone = set(get_cone_tiles((3, 6), FacingDirection.WEST, 2))
        expected = {(1, 4), (2, 4), (3, 4), (4, 4),
                    (5, 4), (2, 5), (3, 5), (4, 5)}
        assert cone == expected

    def test_west_range3(self):
        cone = set(get_cone_tiles((3, 6), FacingDirection.WEST, 3))
        expected = {
            (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3),
            (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
            (2, 5), (3, 5), (4, 5),
        }
        assert cone == expected

    def test_east_range2(self):
        cone = set(get_cone_tiles((3, 2), FacingDirection.EAST, 2))
        expected = {(1, 4), (2, 4), (3, 4), (4, 4),
                    (5, 4), (2, 3), (3, 3), (4, 3)}
        assert cone == expected

    def test_east_range3(self):
        cone = set(get_cone_tiles((3, 2), FacingDirection.EAST, 3))
        expected = {
            (0, 5), (1, 5), (2, 5), (3, 5), (4, 5), (5, 5), (6, 5),
            (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
            (2, 3), (3, 3), (4, 3),
        }
        assert cone == expected

    def test_cone_does_not_include_origin(self):
        for facing in FacingDirection:
            cone = get_cone_tiles((5, 5), facing, 3)
            assert (5, 5) not in cone

    def test_cone_range1_north(self):
        """Range 1 produces 3 tiles: forward-left, forward, forward-right."""
        cone = set(get_cone_tiles((4, 4), FacingDirection.NORTH, 1))
        assert cone == {(3, 3), (3, 4), (3, 5)}

    def test_cone_grows_with_range(self):
        r2 = get_cone_tiles((5, 5), FacingDirection.NORTH, 2)
        r3 = get_cone_tiles((5, 5), FacingDirection.NORTH, 3)
        assert len(r3) > len(r2)


# ---------------------------------------------------------------------------
# Visible tiles — open grid (no walls)
# ---------------------------------------------------------------------------

class TestVisibleTilesOpenGrid:
    def test_all_cone_tiles_visible_on_open_grid(self):
        grid = Grid(12, 12)
        origin = (6, 6)
        cone = set(get_cone_tiles(origin, FacingDirection.NORTH, 3))
        visible = set(get_visible_tiles(
            grid, origin, FacingDirection.NORTH, 3))
        # All in-bounds cone tiles should be visible
        in_bounds_cone = {t for t in cone if grid.in_bounds(t[0], t[1])}
        assert visible == in_bounds_cone

    def test_out_of_bounds_tiles_excluded(self):
        grid = Grid(5, 5)
        # Entity near top edge — some north cone tiles will be out of bounds
        visible = get_visible_tiles(grid, (1, 2), FacingDirection.NORTH, 3)
        for r, c in visible:
            assert grid.in_bounds(r, c)


# ---------------------------------------------------------------------------
# Wall occlusion tests
# ---------------------------------------------------------------------------

class TestWallOcclusion:
    def test_wall_directly_ahead_blocks_all_behind_it(self):
        """
        Wall at distance 1 should block tiles at distance 2 behind it
        on the same column.

        Grid (NPC faces North from row 4):
            . . . . .
            . . . . .   <- row 0
            . . . . .   <- row 1 (should be blocked)
            . . W . .   <- row 2 wall
            . . . . .   <- row 3
            . . E . .   <- row 4 NPC
        """
        layout = [
            [G, G, G, G, G],
            [G, G, G, G, G],
            [G, G, W, G, G],
            [G, G, G, G, G],
            [G, G, G, G, G],
        ]
        grid = Grid.from_layout(layout)
        visible = set(get_visible_tiles(
            grid, (4, 2), FacingDirection.NORTH, 3))
        # Wall tile itself is blocked
        assert (2, 2) not in visible

    def test_wall_does_not_block_tiles_beside_it(self):
        """Tiles at same distance but offset from the wall should still be visible."""
        layout = [
            [G, G, G, G, G],
            [G, G, G, G, G],
            [G, G, W, G, G],
            [G, G, G, G, G],
            [G, G, G, G, G],
        ]
        grid = Grid.from_layout(layout)
        visible = set(get_visible_tiles(
            grid, (4, 2), FacingDirection.NORTH, 2))
        # Tiles beside the wall at the same row should be visible
        assert (2, 1) in visible or (2, 3) in visible

    def test_player_behind_wall_not_visible(self):
        """
        Wall between NPC and player — player should not be visible.

        . W .
        . . .
        . E .
        """
        layout = [
            [G, W, G],
            [G, G, G],
            [G, G, G],
            [G, G, G],
            [G, G, G],
        ]
        grid = Grid.from_layout(layout)
        # NPC at (4,1) facing north, player at (0,1) behind wall at (0,1)
        assert can_see(grid, (4, 1), FacingDirection.NORTH, 3, (0, 1)) is False

    def test_player_visible_with_no_wall_between(self):
        grid = Grid(8, 8)
        npc = (6, 4)
        player = (4, 4)
        assert can_see(grid, npc, FacingDirection.NORTH, 3, player) is True

    def test_wall_beside_ray_does_not_block(self):
        """A wall tile that is not on the ray path should not block LOS."""
        layout = [
            [G, G, G, G, G],
            [G, G, G, G, G],
            [G, W, G, G, G],
            [G, G, G, G, G],
            [G, G, G, G, G],
        ]
        grid = Grid.from_layout(layout)
        # NPC at (4,2) facing north — wall at (2,1) is beside the forward ray
        assert can_see(grid, (4, 2), FacingDirection.NORTH, 2, (2, 2)) is True


# ---------------------------------------------------------------------------
# can_see convenience function
# ---------------------------------------------------------------------------

class TestCanSee:
    def test_target_outside_cone_not_visible(self):
        """Target directly behind the NPC should never be visible."""
        grid = Grid(12, 12)
        npc = (6, 6)
        # Facing north — tile directly south is outside the cone
        behind = (7, 6)
        assert can_see(grid, npc, FacingDirection.NORTH, 3, behind) is False

    def test_target_in_cone_and_clear_is_visible(self):
        grid = Grid(12, 12)
        npc = (6, 6)
        ahead = (4, 6)
        assert can_see(grid, npc, FacingDirection.NORTH, 3, ahead) is True

    def test_target_out_of_bounds_not_visible(self):
        grid = Grid(5, 5)
        assert can_see(grid, (1, 1), FacingDirection.NORTH,
                       3, (-1, 1)) is False

    def test_all_four_directions_see_immediate_forward_tile(self):
        grid = Grid(12, 12)
        npc = (6, 6)
        cases = [
            (FacingDirection.NORTH, (5, 6)),
            (FacingDirection.SOUTH, (7, 6)),
            (FacingDirection.EAST,  (6, 7)),
            (FacingDirection.WEST,  (6, 5)),
        ]
        for facing, target in cases:
            assert can_see(grid, npc, facing, 2, target) is True, \
                f"Expected to see {target} facing {facing}"
