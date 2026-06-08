"""
entity.py — Base Entity class for Last Known Location.

All entities (Player, NPC) share common position and facing mechanics.
An entity occupies a single tile on the grid and faces one of the four
cardinal directions. Movement updates both position and facing.

Coordinate system:
    (row, col) — row 0 is top of map, col 0 is left edge.

Movement rules:
    - Entities move one tile per step, cardinal only (N, S, E, W)
    - A move is blocked if the destination is a wall or out of bounds
    - A blocked move returns (False, current_position) and does not
      update position or facing
    - A successful move returns (True, new_position) and updates both
      position and facing to match the direction of movement
"""

from app.models.grid import Grid
from app.systems.facing import FacingDirection


# Cardinal direction -> (row_delta, col_delta)
DIRECTION_DELTAS: dict[FacingDirection, tuple[int, int]] = {
    FacingDirection.NORTH: (-1,  0),
    FacingDirection.SOUTH: (1,  0),
    FacingDirection.EAST:  (0,  1),
    FacingDirection.WEST:  (0, -1),
}


class Entity:
    """
    Base class for all grid entities.

    Tracks position and facing direction. Provides cardinal movement
    with wall and bounds checking. Subclasses add perception, state
    machines, and other entity-specific behavior.

    Attributes:
        position (tuple[int, int]): Current (row, col) on the grid.
        facing (FacingDirection):   Direction the entity is facing.
        grid (Grid):                The grid this entity occupies.
    """

    def __init__(
        self,
        grid: Grid,
        position: tuple[int, int],
        facing: FacingDirection = FacingDirection.NORTH,
    ):
        """
        Initialize an entity on the grid.

        Args:
            grid:     The Grid this entity belongs to.
            position: Starting (row, col).
            facing:   Initial facing direction. Defaults to NORTH.

        Raises:
            ValueError: If the starting position is out of bounds or
                        on an impassable tile.
        """
        row, col = position
        if not grid.in_bounds(row, col):
            raise ValueError(
                f"Starting position {position} is out of bounds."
            )
        if not grid.is_passable(row, col):
            raise ValueError(
                f"Starting position {position} is not passable."
            )

        self.grid = grid
        self.position = position
        self.facing = facing

    def move(
        self,
        direction: FacingDirection,
        occupants: set[tuple[int, int]] | None = None,
    ) -> tuple[bool, tuple[int, int]]:
        """
        Attempt to move one tile in the given direction.

        Updates position and facing on success. Does nothing on failure.

        Args:
            direction: The cardinal direction to move.
            occupants: Optional set of (row, col) positions occupied by
                       other entities. Movement into an occupied tile is
                       blocked. Defaults to None (no occupancy checking).

        Returns:
            (success, position) where:
                success  — True if the move was completed.
                position — New position if successful, current if blocked.
        """
        dr, dc = DIRECTION_DELTAS[direction]
        row, col = self.position
        new_row, new_col = row + dr, col + dc
        new_position = (new_row, new_col)

        # Bounds check
        if not self.grid.in_bounds(new_row, new_col):
            return False, self.position

        # Passability check (wall)
        if not self.grid.is_passable(new_row, new_col):
            return False, self.position

        # Occupancy check (another entity)
        if occupants and new_position in occupants:
            return False, self.position

        # Move succeeds — update position and facing
        self.position = new_position
        self.facing = direction
        return True, self.position

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"pos={self.position}, "
            f"facing={self.facing.value})"
        )
