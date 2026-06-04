"""
test_grid.py — Unit tests for the Grid model and Tile types.
"""

import pytest
from app.models.grid import Grid, Tile, TileType


# ---------------------------------------------------------------------------
# Tile tests
# ---------------------------------------------------------------------------

class TestTile:
    def test_ground_is_passable(self):
        tile = Tile(TileType.GROUND, 0, 0)
        assert tile.passable is True

    def test_noisy_is_passable(self):
        tile = Tile(TileType.NOISY, 0, 0)
        assert tile.passable is True

    def test_wall_is_not_passable(self):
        tile = Tile(TileType.WALL, 0, 0)
        assert tile.passable is False

    def test_noisy_tile_is_noisy(self):
        tile = Tile(TileType.NOISY, 0, 0)
        assert tile.noisy is True

    def test_ground_is_not_noisy(self):
        tile = Tile(TileType.GROUND, 0, 0)
        assert tile.noisy is False

    def test_wall_is_not_noisy(self):
        tile = Tile(TileType.WALL, 0, 0)
        assert tile.noisy is False

    def test_wall_blocks_sight(self):
        tile = Tile(TileType.WALL, 0, 0)
        assert tile.blocks_sight is True

    def test_ground_does_not_block_sight(self):
        tile = Tile(TileType.GROUND, 0, 0)
        assert tile.blocks_sight is False

    def test_noisy_does_not_block_sight(self):
        tile = Tile(TileType.NOISY, 0, 0)
        assert tile.blocks_sight is False

    def test_tile_stores_position(self):
        tile = Tile(TileType.GROUND, 3, 7)
        assert tile.row == 3
        assert tile.col == 7


# ---------------------------------------------------------------------------
# Grid construction tests
# ---------------------------------------------------------------------------

class TestGridConstruction:
    def test_empty_grid_fills_with_ground(self):
        grid = Grid(3, 4)
        for r in range(3):
            for c in range(4):
                assert grid.get(r, c).tile_type == TileType.GROUND

    def test_grid_dimensions(self):
        grid = Grid(5, 10)
        assert grid.rows == 5
        assert grid.cols == 10

    def test_invalid_dimensions_raises(self):
        with pytest.raises(ValueError):
            Grid(0, 5)
        with pytest.raises(ValueError):
            Grid(5, 0)
        with pytest.raises(ValueError):
            Grid(-1, 5)

    def test_from_layout_basic(self):
        G, N, W = TileType.GROUND, TileType.NOISY, TileType.WALL
        layout = [
            [G, W, G],
            [N, G, W],
        ]
        grid = Grid.from_layout(layout)
        assert grid.rows == 2
        assert grid.cols == 3
        assert grid.get(0, 1).tile_type == TileType.WALL
        assert grid.get(1, 0).tile_type == TileType.NOISY

    def test_from_layout_empty_raises(self):
        with pytest.raises(ValueError):
            Grid.from_layout([])
        with pytest.raises(ValueError):
            Grid.from_layout([[]])

    def test_from_layout_jagged_raises(self):
        G, W = TileType.GROUND, TileType.WALL
        with pytest.raises(ValueError):
            Grid.from_layout([[G, G, G], [G, W]])

    def test_from_layout_positions_are_correct(self):
        G = TileType.GROUND
        layout = [[G, G], [G, G]]
        grid = Grid.from_layout(layout)
        for r in range(2):
            for c in range(2):
                tile = grid.get(r, c)
                assert tile.row == r
                assert tile.col == c


# ---------------------------------------------------------------------------
# Grid query tests
# ---------------------------------------------------------------------------

class TestGridQueries:
    @pytest.fixture
    def grid(self):
        G, N, W = TileType.GROUND, TileType.NOISY, TileType.WALL
        layout = [
            [G, G, W],
            [N, G, G],
            [W, G, G],
        ]
        return Grid.from_layout(layout)

    def test_in_bounds_valid(self, grid):
        assert grid.in_bounds(0, 0) is True
        assert grid.in_bounds(2, 2) is True

    def test_in_bounds_invalid(self, grid):
        assert grid.in_bounds(-1, 0) is False
        assert grid.in_bounds(0, 3) is False
        assert grid.in_bounds(3, 0) is False

    def test_get_returns_none_out_of_bounds(self, grid):
        assert grid.get(-1, 0) is None
        assert grid.get(0, 99) is None

    def test_is_passable_ground(self, grid):
        assert grid.is_passable(0, 0) is True

    def test_is_passable_noisy(self, grid):
        assert grid.is_passable(1, 0) is True

    def test_is_passable_wall(self, grid):
        assert grid.is_passable(0, 2) is False

    def test_is_passable_out_of_bounds(self, grid):
        assert grid.is_passable(99, 99) is False

    def test_is_noisy(self, grid):
        assert grid.is_noisy(1, 0) is True
        assert grid.is_noisy(0, 0) is False

    def test_blocks_sight_wall(self, grid):
        assert grid.blocks_sight(0, 2) is True

    def test_blocks_sight_ground(self, grid):
        assert grid.blocks_sight(0, 0) is False


# ---------------------------------------------------------------------------
# Neighbors tests
# ---------------------------------------------------------------------------

class TestGridNeighbors:
    @pytest.fixture
    def grid(self):
        G, W = TileType.GROUND, TileType.WALL
        layout = [
            [G, G, G],
            [G, G, W],
            [G, W, G],
        ]
        return Grid.from_layout(layout)

    def test_center_tile_neighbors(self, grid):
        # (1,1) has neighbors N(0,1), S(2,1)=wall, E(1,2)=wall, W(1,0)
        neighbors = grid.neighbors(1, 1)
        positions = {(t.row, t.col) for t in neighbors}
        assert positions == {(0, 1), (1, 0)}

    def test_corner_tile_neighbors(self, grid):
        # (0,0) has neighbors S(1,0) and E(0,1)
        neighbors = grid.neighbors(0, 0)
        positions = {(t.row, t.col) for t in neighbors}
        assert positions == {(1, 0), (0, 1)}

    def test_neighbors_exclude_walls(self, grid):
        neighbors = grid.neighbors(1, 1)
        for tile in neighbors:
            assert tile.passable is True

    def test_neighbors_exclude_out_of_bounds(self, grid):
        # Top-left corner should not try to access row -1 or col -1
        neighbors = grid.neighbors(0, 0)
        for tile in neighbors:
            assert grid.in_bounds(tile.row, tile.col)
