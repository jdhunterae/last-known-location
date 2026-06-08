"""
test_entity.py — Unit tests for the base Entity class.

Covers shared position, facing, and movement behavior that all
entities (Player, NPC) inherit.
"""

import pytest
from app.models.grid import Grid, TileType
from app.models.entity import Entity
from app.systems.facing import FacingDirection

G = TileType.GROUND
W = TileType.WALL
N = TileType.NOISY


def make_grid(layout):
    return Grid.from_layout(layout)


def open_grid(rows=5, cols=5):
    return Grid(rows, cols)


# ---------------------------------------------------------------------------
# Construction tests
# ---------------------------------------------------------------------------

class TestEntityConstruction:
    def test_valid_construction(self):
        grid = open_grid()
        e = Entity(grid, (2, 2))
        assert e.position == (2, 2)
        assert e.facing == FacingDirection.NORTH

    def test_custom_facing(self):
        grid = open_grid()
        e = Entity(grid, (0, 0), FacingDirection.EAST)
        assert e.facing == FacingDirection.EAST

    def test_out_of_bounds_raises(self):
        grid = open_grid()
        with pytest.raises(ValueError):
            Entity(grid, (-1, 0))
        with pytest.raises(ValueError):
            Entity(grid, (99, 99))

    def test_wall_position_raises(self):
        layout = [[W, G], [G, G]]
        grid = make_grid(layout)
        with pytest.raises(ValueError):
            Entity(grid, (0, 0))

    def test_noisy_tile_is_valid_start(self):
        layout = [[N, G], [G, G]]
        grid = make_grid(layout)
        e = Entity(grid, (0, 0))
        assert e.position == (0, 0)

    def test_grid_reference_stored(self):
        grid = open_grid()
        e = Entity(grid, (0, 0))
        assert e.grid is grid


# ---------------------------------------------------------------------------
# Movement tests
# ---------------------------------------------------------------------------

class TestEntityMovement:
    @pytest.fixture
    def grid(self):
        return open_grid()

    def test_move_north(self, grid):
        e = Entity(grid, (2, 2))
        success, pos = e.move(FacingDirection.NORTH)
        assert success is True
        assert pos == (1, 2)
        assert e.position == (1, 2)

    def test_move_south(self, grid):
        e = Entity(grid, (2, 2))
        success, pos = e.move(FacingDirection.SOUTH)
        assert success is True
        assert pos == (3, 2)

    def test_move_east(self, grid):
        e = Entity(grid, (2, 2))
        success, pos = e.move(FacingDirection.EAST)
        assert success is True
        assert pos == (2, 3)

    def test_move_west(self, grid):
        e = Entity(grid, (2, 2))
        success, pos = e.move(FacingDirection.WEST)
        assert success is True
        assert pos == (2, 1)

    def test_successful_move_updates_facing(self, grid):
        e = Entity(grid, (2, 2), FacingDirection.NORTH)
        e.move(FacingDirection.EAST)
        assert e.facing == FacingDirection.EAST

    def test_failed_move_does_not_update_facing(self):
        layout = [[G, G], [G, W]]
        grid = make_grid(layout)
        e = Entity(grid, (0, 0), FacingDirection.NORTH)
        e.move(FacingDirection.SOUTH)  # (1,0) is passable
        e.move(FacingDirection.EAST)   # (1,1) is wall — blocked
        assert e.facing == FacingDirection.SOUTH

    def test_failed_move_does_not_update_position(self):
        layout = [[G, W], [G, G]]
        grid = make_grid(layout)
        e = Entity(grid, (0, 0))
        success, pos = e.move(FacingDirection.EAST)
        assert success is False
        assert pos == (0, 0)
        assert e.position == (0, 0)

    def test_move_blocked_by_wall(self):
        layout = [[G, W], [G, G]]
        grid = make_grid(layout)
        e = Entity(grid, (0, 0))
        success, pos = e.move(FacingDirection.EAST)
        assert success is False

    def test_move_blocked_by_out_of_bounds(self, grid):
        e = Entity(grid, (0, 0))
        success, pos = e.move(FacingDirection.NORTH)
        assert success is False
        assert pos == (0, 0)

    def test_move_through_noisy_tile_succeeds(self):
        layout = [[G, N, G], [G, G, G]]
        grid = make_grid(layout)
        e = Entity(grid, (0, 0))
        success, pos = e.move(FacingDirection.EAST)
        assert success is True
        assert pos == (0, 1)

    def test_sequential_moves(self, grid):
        e = Entity(grid, (0, 0))
        e.move(FacingDirection.SOUTH)
        e.move(FacingDirection.EAST)
        assert e.position == (1, 1)


# ---------------------------------------------------------------------------
# Occupancy tests
# ---------------------------------------------------------------------------

class TestEntityOccupancy:
    def test_move_blocked_by_occupant(self):
        grid = open_grid()
        e = Entity(grid, (2, 2))
        occupants = {(1, 2)}  # another entity is at (1,2)
        success, pos = e.move(FacingDirection.NORTH, occupants=occupants)
        assert success is False
        assert pos == (2, 2)

    def test_move_succeeds_when_occupant_elsewhere(self):
        grid = open_grid()
        e = Entity(grid, (2, 2))
        occupants = {(3, 3)}  # occupant is not in the path
        success, pos = e.move(FacingDirection.NORTH, occupants=occupants)
        assert success is True
        assert pos == (1, 2)

    def test_no_occupants_passed_defaults_to_no_check(self):
        grid = open_grid()
        e = Entity(grid, (2, 2))
        success, pos = e.move(FacingDirection.NORTH)
        assert success is True

    def test_occupant_does_not_block_facing_update(self):
        """Facing should NOT update when blocked by occupant."""
        grid = open_grid()
        e = Entity(grid, (2, 2), FacingDirection.NORTH)
        occupants = {(2, 3)}
        e.move(FacingDirection.EAST, occupants=occupants)
        assert e.facing == FacingDirection.NORTH
