"""
player.py — Player entity for Last Known Location.

The Player is a human-controlled entity. It shares all movement and
facing mechanics with the base Entity class. It has no perception
system — no hearing or sight checks are performed on the player.

Sound events triggered by the player entering noisy tiles are handled
by the game loop, not the player itself. The tile is what emits the
sound; the player is just the entity that stepped on it.
"""

from app.models.entity import Entity
from app.models.grid import Grid
from app.systems.facing import FacingDirection


class Player(Entity):
    """
    The human-controlled player entity.

    Inherits position, facing, and movement from Entity. No additional
    state is tracked at this layer — perception and sound emission are
    handled externally by the game loop.

    Attributes:
        position (tuple[int, int]): Current (row, col) on the grid.
        facing (FacingDirection):   Direction the player is facing.
        grid (Grid):                The grid this player occupies.
    """

    def __init__(
        self,
        grid: Grid,
        position: tuple[int, int],
        facing: FacingDirection = FacingDirection.NORTH,
    ):
        """
        Initialize the player on the grid.

        Args:
            grid:     The Grid the player belongs to.
            position: Starting (row, col).
            facing:   Initial facing direction. Defaults to NORTH.

        Raises:
            ValueError: If the starting position is out of bounds or
                        on an impassable tile.
        """
        super().__init__(grid, position, facing)
