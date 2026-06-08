"""
npc.py — NPC entity for Last Known Location.

The NPC is a grid entity with a pre-scripted patrol route, perception
ranges, and a state machine (wired in a later step). It inherits
position, facing, and movement from Entity.

Patrol routes are defined as a short list of waypoints. On construction
the NPC expands the waypoints into a full step-by-step path using A*.
Two patrol modes are supported:

    LOOP   — A→B→C→A→B→C... (circular)
    BOUNCE — A→B→C→B→A→B... (back-and-forth, default)

At each waypoint the NPC pauses for a configurable number of ticks,
rotates to face the next waypoint, then resumes walking.

Facing is derived automatically from the first step of the patrol path.
"""

from enum import Enum

from app.models.entity import Entity, DIRECTION_DELTAS
from app.models.grid import Grid
from app.systems.facing import FacingDirection
from app.systems.pathfinding import find_path


class PatrolMode(Enum):
    """How the NPC traverses its waypoints."""
    LOOP = "loop"    # A→B→C→A→B→C...
    BOUNCE = "bounce"  # A→B→C→B→A→B... (default)


def _derive_facing(
    from_pos: tuple[int, int],
    to_pos: tuple[int, int],
) -> FacingDirection:
    """
    Derive a facing direction from one position toward another.

    Uses the dominant axis of the displacement vector. If the two
    positions are identical, defaults to NORTH.

    Args:
        from_pos: Current (row, col).
        to_pos:   Target (row, col).

    Returns:
        The FacingDirection that best points from from_pos toward to_pos.
    """
    dr = to_pos[0] - from_pos[0]
    dc = to_pos[1] - from_pos[1]

    if dr == 0 and dc == 0:
        return FacingDirection.NORTH

    if abs(dr) >= abs(dc):
        return FacingDirection.SOUTH if dr > 0 else FacingDirection.NORTH
    else:
        return FacingDirection.EAST if dc > 0 else FacingDirection.WEST


def _expand_waypoints(
    grid: Grid,
    waypoints: list[tuple[int, int]],
    mode: PatrolMode,
) -> list[tuple[int, int]]:
    """
    Expand a list of waypoints into a full ordered step path using A*.

    For BOUNCE mode the waypoints are mirrored in reverse (excluding the
    endpoints) to produce the return journey. For LOOP mode the last
    waypoint connects back to the first.

    Args:
        grid:      The Grid to path on.
        waypoints: Ordered list of (row, col) waypoint positions.
        mode:      LOOP or BOUNCE patrol mode.

    Returns:
        Full ordered list of (row, col) steps the NPC will follow,
        including all intermediate tiles between waypoints.

    Raises:
        ValueError: If any waypoint is impassable, out of bounds, or
                    if A* cannot find a path between two adjacent waypoints.
    """
    # Validate all waypoints
    for i, wp in enumerate(waypoints):
        r, c = wp
        if not grid.in_bounds(r, c):
            raise ValueError(
                f"Waypoint {i} {wp} is out of grid bounds."
            )
        if not grid.is_passable(r, c):
            raise ValueError(
                f"Waypoint {i} {wp} is not passable (wall tile)."
            )

    # Build ordered segment list based on mode
    if mode == PatrolMode.BOUNCE:
        # A→B→C then C→B→A (drop duplicate endpoints to avoid double-steps)
        # Special case: 2 waypoints A→B bounce is simply A→B→A
        forward = waypoints
        if len(waypoints) > 2:
            backward = list(reversed(waypoints[1:-1]))
        else:
            backward = list(reversed(waypoints))
        sequence = forward + backward
    else:  # LOOP
        sequence = waypoints  # connection from last→first added below

    # Expand each consecutive pair with A*
    full_path: list[tuple[int, int]] = []

    pairs = list(zip(sequence, sequence[1:]))
    if mode == PatrolMode.LOOP:
        pairs.append((sequence[-1], sequence[0]))

    for start, goal in pairs:
        segment = find_path(grid, start, goal)
        if segment is None:
            raise ValueError(
                f"No path found between waypoints {start} and {goal}. "
                f"Check for walls or unreachable tiles."
            )
        # find_path excludes start, includes goal — avoids duplicate tiles
        full_path.extend(segment)

    return full_path


class NPC(Entity):
    """
    An NPC entity with a patrol route, perception ranges, and pause behavior.

    Inherits position, facing, and movement from Entity. Adds:
        - Waypoint-based patrol path (A*-expanded)
        - LOOP or BOUNCE patrol mode
        - Configurable pause at each waypoint
        - Sight and sound perception ranges (used by the state machine)

    The state machine is wired externally and not held by the NPC itself.

    Attributes:
        waypoints       (list[tuple]): Original designer-provided waypoints.
        patrol_mode     (PatrolMode):  LOOP or BOUNCE.
        patrol_path     (list[tuple]): Full A*-expanded step path.
        step_index      (int):         Current position in patrol_path.
        waypoint_set    (set[tuple]):  Fast lookup for waypoint tiles.
        waypoint_pause  (int):         Ticks to pause at each waypoint.
        pause_remaining (int):         Ticks remaining in current pause.
        sight_range     (int):         Tiles the NPC can see.
        sound_range     (int):         Tiles the NPC can hear.
    """

    def __init__(
        self,
        grid: Grid,
        waypoints: list[tuple[int, int]],
        patrol_mode: PatrolMode = PatrolMode.BOUNCE,
        waypoint_pause: int = 1,
        sight_range: int = 3,
        sound_range: int = 4,
    ):
        """
        Initialize the NPC and expand its patrol route.

        Facing is derived from the direction of the first patrol step.

        Args:
            grid:          The Grid the NPC belongs to.
            waypoints:     Ordered list of (row, col) waypoint positions.
                           Minimum 2 waypoints required.
            patrol_mode:   LOOP or BOUNCE. Defaults to BOUNCE.
            waypoint_pause: Ticks to pause at each waypoint. Defaults to 1.
            sight_range:   Sight cone radius in tiles. Defaults to 3.
            sound_range:   Hearing radius in tiles. Defaults to 4.

        Raises:
            ValueError: If fewer than 2 waypoints are provided, any
                        waypoint is invalid, or any path segment is
                        unreachable.
        """
        if len(waypoints) < 2:
            raise ValueError(
                f"NPC requires at least 2 waypoints, got {len(waypoints)}."
            )

        # Expand waypoints before calling super().__init__ so we can
        # derive the initial facing from the first step.
        patrol_path = _expand_waypoints(grid, waypoints, patrol_mode)

        # Derive initial facing from first step
        start = waypoints[0]
        first_step = patrol_path[0] if patrol_path else start
        initial_facing = _derive_facing(start, first_step)

        super().__init__(grid, start, initial_facing)

        self.waypoints = waypoints
        self.patrol_mode = patrol_mode
        self.patrol_path = patrol_path
        self.step_index = 0
        self.waypoint_set = set(waypoints)
        self.waypoint_pause = waypoint_pause
        self.pause_remaining = 0
        self.sight_range = sight_range
        self.sound_range = sound_range

    @property
    def current_waypoint_target(self) -> tuple[int, int]:
        """The next step the NPC is walking toward."""
        return self.patrol_path[self.step_index]

    @property
    def is_pausing(self) -> bool:
        """True if the NPC is currently paused at a waypoint."""
        return self.pause_remaining > 0

    def patrol_step(
        self,
        occupants: set[tuple[int, int]] | None = None,
    ) -> tuple[bool, tuple[int, int]]:
        """
        Advance the NPC one step along its patrol path.

        If pausing at a waypoint, decrements the pause timer and does
        not move. When the pause ends, faces the next target before
        moving on the following tick.

        If not pausing, moves toward the next patrol step. On arrival
        at a waypoint tile, triggers a pause.

        Args:
            occupants: Optional set of occupied tile positions.

        Returns:
            (moved, position) where:
                moved    — True if the NPC physically moved this tick.
                position — Current position after this tick.
        """
        # Currently pausing at a waypoint
        if self.is_pausing:
            self.pause_remaining -= 1
            if self.pause_remaining == 0 and self.step_index < len(self.patrol_path):
                # Face the next step before resuming
                next_step = self.patrol_path[self.step_index]
                self.facing = _derive_facing(self.position, next_step)
            return False, self.position

        # Determine direction toward next patrol step
        target = self.patrol_path[self.step_index]
        direction = _derive_facing(self.position, target)
        success, new_pos = self.move(direction, occupants=occupants)

        if not success:
            return False, self.position

        # Check arrival at next patrol step
        if new_pos == target:
            self.step_index = (self.step_index + 1) % len(self.patrol_path)

            # If we landed on a waypoint, trigger pause
            if new_pos in self.waypoint_set:
                self.pause_remaining = self.waypoint_pause
                # Face toward the next step (set during pause countdown)
                if self.step_index < len(self.patrol_path):
                    next_step = self.patrol_path[self.step_index]
                    self.facing = _derive_facing(new_pos, next_step)

        return True, new_pos
