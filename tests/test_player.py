"""
test_player.py — Unit tests for the Player entity.

Player-specific behavior only. Shared movement and facing behavior
is covered by test_entity.py.
"""

import pytest
from app.models.grid import Grid, TileType
from app.models.player import Player
from app.models.entity import Entity
from app.systems.facing import FacingDirection

G = TileType.GROUND
W = TileType.WALL
N = TileType.NOISY


def open_grid(rows=5, cols=5):
    return Grid(rows, cols)


# ---------------------------------------------------------------------------
# Player construction tests
# ---------------------------------------------------------------------------

class TestPlayerConstruction:
    def test_player_is_entity(self):
        grid = open_grid()
        p = Player(grid, (2, 2))
        assert isinstance(p, Entity)

    def test_default_facing_north(self):
        grid = open_grid()
        p = Player(grid, (2, 2))
        assert p.facing == FacingDirection.NORTH

    def test_custom_facing(self):
        grid = open_grid()
        p = Player(grid, (2, 2), FacingDirection.WEST)
        assert p.facing == FacingDirection.WEST

    def test_invalid_position_raises(self):
        layout = [[W, G], [G, G]]
        grid = Grid.from_layout(layout)
        with pytest.raises(ValueError):
            Player(grid, (0, 0))

    def test_player_on_noisy_tile(self):
        layout = [[N, G], [G, G]]
        grid = Grid.from_layout(layout)
        p = Player(grid, (0, 0))
        assert p.position == (0, 0)


# ---------------------------------------------------------------------------
# Player movement tests
# ---------------------------------------------------------------------------

class TestPlayerMovement:
    def test_move_updates_position(self):
        grid = open_grid()
        p = Player(grid, (2, 2))
        success, pos = p.move(FacingDirection.SOUTH)
        assert success is True
        assert pos == (3, 2)
        assert p.position == (3, 2)

    def test_move_updates_facing(self):
        grid = open_grid()
        p = Player(grid, (2, 2))
        p.move(FacingDirection.EAST)
        assert p.facing == FacingDirection.EAST

    def test_move_into_wall_blocked(self):
        layout = [[G, W], [G, G]]
        grid = Grid.from_layout(layout)
        p = Player(grid, (0, 0))
        success, pos = p.move(FacingDirection.EAST)
        assert success is False
        assert p.position == (0, 0)

    def test_move_onto_noisy_tile_succeeds(self):
        layout = [[G, N, G], [G, G, G]]
        grid = Grid.from_layout(layout)
        p = Player(grid, (0, 0))
        success, pos = p.move(FacingDirection.EAST)
        assert success is True
        assert p.position == (0, 1)
        assert grid.is_noisy(p.position[0], p.position[1])

    def test_move_blocked_by_occupant(self):
        grid = open_grid()
        p = Player(grid, (2, 2))
        occupants = {(2, 3)}
        success, pos = p.move(FacingDirection.EAST, occupants=occupants)
        assert success is False
        assert p.position == (2, 2)
