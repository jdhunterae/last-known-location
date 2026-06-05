"""
test_pathfinding.py — Unit tests for the A* pathfinding system.
"""

import pytest
from app.models.grid import Grid, TileType
from app.systems.pathfinding import find_path, manhattan


# ---------------------------------------------------------------------------
# Heuristic tests
# ---------------------------------------------------------------------------

class TestManhattan:
    def test_same_tile(self):
        assert manhattan(2, 3, 2, 3) == 0

    def test_same_row(self):
        assert manhattan(0, 0, 0, 4) == 4

    def test_same_col(self):
        assert manhattan(0, 0, 3, 0) == 3

    def test_diagonal(self):
        assert manhattan(0, 0, 3, 4) == 7

    def test_symmetry(self):
        assert manhattan(1, 2, 5, 6) == manhattan(5, 6, 1, 2)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

G = TileType.GROUND
N = TileType.NOISY
W = TileType.WALL


def open_grid(rows=5, cols=5):
    """A fully open grid with no walls."""
    return Grid(rows, cols)


def make_grid(layout):
    return Grid.from_layout(layout)


# ---------------------------------------------------------------------------
# Basic pathfinding tests
# ---------------------------------------------------------------------------

class TestFindPathBasic:
    def test_same_start_and_goal_returns_empty(self):
        grid = open_grid()
        assert find_path(grid, (2, 2), (2, 2)) == []

    def test_adjacent_tiles(self):
        grid = open_grid()
        path = find_path(grid, (0, 0), (0, 1))
        assert path == [(0, 1)]

    def test_straight_horizontal_path(self):
        grid = open_grid()
        path = find_path(grid, (0, 0), (0, 4))
        assert path is not None
        assert path[-1] == (0, 4)
        assert len(path) == 4

    def test_straight_vertical_path(self):
        grid = open_grid()
        path = find_path(grid, (0, 0), (4, 0))
        assert path is not None
        assert path[-1] == (4, 0)
        assert len(path) == 4

    def test_path_does_not_include_start(self):
        grid = open_grid()
        path = find_path(grid, (0, 0), (2, 0))
        assert (0, 0) not in path

    def test_path_includes_goal(self):
        grid = open_grid()
        path = find_path(grid, (0, 0), (2, 2))
        assert path[-1] == (2, 2)

    def test_path_is_contiguous(self):
        """Each step in the path is exactly 1 tile away (cardinal only)."""
        grid = open_grid()
        start = (0, 0)
        path = find_path(grid, start, (4, 4))
        assert path is not None
        full = [start] + path
        for i in range(1, len(full)):
            dr = abs(full[i][0] - full[i - 1][0])
            dc = abs(full[i][1] - full[i - 1][1])
            assert dr + \
                dc == 1, f"Non-cardinal step between {full[i-1]} and {full[i]}"

    def test_noisy_tiles_are_passable(self):
        layout = [
            [G, N, G],
            [G, N, G],
            [G, G, G],
        ]
        grid = make_grid(layout)
        path = find_path(grid, (0, 0), (0, 2))
        assert path is not None


# ---------------------------------------------------------------------------
# Wall avoidance tests
# ---------------------------------------------------------------------------

class TestFindPathWalls:
    def test_no_path_through_wall_column(self):
        """A solid wall column with no gap — no path exists."""
        layout = [
            [G, W, G],
            [G, W, G],
            [G, W, G],
        ]
        grid = make_grid(layout)
        path = find_path(grid, (0, 0), (0, 2))
        assert path is None

    def test_path_navigates_around_wall(self):
        """Wall with a gap forces a detour."""
        layout = [
            [G, W, G],
            [G, W, G],
            [G, G, G],
        ]
        grid = make_grid(layout)
        path = find_path(grid, (0, 0), (0, 2))
        assert path is not None
        assert path[-1] == (0, 2)
        # Path must go through the gap at row 2
        assert any(r == 2 for r, c in path)

    def test_path_avoids_wall_tiles(self):
        layout = [
            [G, W, G],
            [G, W, G],
            [G, G, G],
        ]
        grid = make_grid(layout)
        path = find_path(grid, (0, 0), (0, 2))
        assert path is not None
        for row, col in path:
            assert grid.is_passable(
                row, col), f"Path steps on wall at ({row},{col})"

    def test_corridor_path(self):
        """Narrow single-tile corridor between walls."""
        layout = [
            [W, G, W],
            [W, G, W],
            [W, G, W],
            [W, G, W],
        ]
        grid = make_grid(layout)
        path = find_path(grid, (0, 1), (3, 1))
        assert path is not None
        assert path[-1] == (3, 1)
        assert len(path) == 3


# ---------------------------------------------------------------------------
# Edge / guard tests
# ---------------------------------------------------------------------------

class TestFindPathEdgeCases:
    def test_start_out_of_bounds_returns_none(self):
        grid = open_grid()
        assert find_path(grid, (-1, 0), (2, 2)) is None

    def test_goal_out_of_bounds_returns_none(self):
        grid = open_grid()
        assert find_path(grid, (0, 0), (99, 99)) is None

    def test_start_on_wall_returns_none(self):
        layout = [[W, G], [G, G]]
        grid = make_grid(layout)
        assert find_path(grid, (0, 0), (1, 1)) is None

    def test_goal_on_wall_returns_none(self):
        layout = [[G, G], [G, W]]
        grid = make_grid(layout)
        assert find_path(grid, (0, 0), (1, 1)) is None

    def test_completely_enclosed_start_returns_none(self):
        layout = [
            [W, W, W],
            [W, G, W],
            [W, W, W],
        ]
        grid = make_grid(layout)
        assert find_path(grid, (1, 1), (0, 0)) is None

    def test_single_tile_grid_same_start_goal(self):
        grid = Grid(1, 1)
        assert find_path(grid, (0, 0), (0, 0)) == []

    def test_optimal_path_length(self):
        """On an open grid the shortest path length equals Manhattan distance."""
        grid = open_grid(10, 10)
        start, goal = (0, 0), (3, 4)
        path = find_path(grid, start, goal)
        assert path is not None
        assert len(path) == manhattan(*start, *goal)
