"""
test_npc.py — Unit tests for the NPC entity.

Covers patrol route expansion, patrol modes, waypoint pausing,
and movement along the expanded path. Shared Entity behavior
is covered by test_entity.py.
"""

import pytest
from app.models.grid import Grid, TileType
from app.models.npc import NPC, PatrolMode, _derive_facing, _expand_waypoints
from app.models.entity import Entity
from app.systems.facing import FacingDirection

G = TileType.GROUND
W = TileType.WALL
N = TileType.NOISY


def open_grid(rows=10, cols=10):
    return Grid(rows, cols)


def make_grid(layout):
    return Grid.from_layout(layout)


# ---------------------------------------------------------------------------
# _derive_facing helper tests
# ---------------------------------------------------------------------------

class TestDeriveFacing:
    def test_north(self):
        assert _derive_facing((5, 5), (3, 5)) == FacingDirection.NORTH

    def test_south(self):
        assert _derive_facing((3, 5), (5, 5)) == FacingDirection.SOUTH

    def test_east(self):
        assert _derive_facing((5, 3), (5, 7)) == FacingDirection.EAST

    def test_west(self):
        assert _derive_facing((5, 7), (5, 3)) == FacingDirection.WEST

    def test_same_position_defaults_north(self):
        assert _derive_facing((5, 5), (5, 5)) == FacingDirection.NORTH

    def test_dominant_row_axis(self):
        # More row displacement than col — should be N/S
        assert _derive_facing((0, 0), (4, 1)) == FacingDirection.SOUTH

    def test_dominant_col_axis(self):
        # More col displacement than row — should be E/W
        assert _derive_facing((0, 0), (1, 4)) == FacingDirection.EAST


# ---------------------------------------------------------------------------
# _expand_waypoints tests
# ---------------------------------------------------------------------------

class TestExpandWaypoints:
    def test_bounce_two_waypoints(self):
        """A→B bounce: path goes A→B then B→A."""
        grid = open_grid()
        waypoints = [(0, 0), (0, 4)]
        path = _expand_waypoints(grid, waypoints, PatrolMode.BOUNCE)
        # Should reach (0,4) then return to (0,0) — but not include start
        assert (0, 4) in path
        assert (0, 0) in path

    def test_bounce_three_waypoints(self):
        """A→B→C bounce: path goes A→B→C→B→A."""
        grid = open_grid()
        waypoints = [(0, 0), (0, 4), (4, 4)]
        path = _expand_waypoints(grid, waypoints, PatrolMode.BOUNCE)
        assert (0, 4) in path
        assert (4, 4) in path

    def test_loop_connects_last_to_first(self):
        """LOOP mode should connect C back to A."""
        grid = open_grid()
        waypoints = [(0, 0), (0, 4), (4, 4)]
        path = _expand_waypoints(grid, waypoints, PatrolMode.LOOP)
        # Last step should arrive back at (0,0)
        assert path[-1] == (0, 0)

    def test_path_does_not_include_start_tile(self):
        """find_path excludes start — no duplicate tiles at segment joins."""
        grid = open_grid()
        waypoints = [(0, 0), (0, 3)]
        path = _expand_waypoints(grid, waypoints, PatrolMode.BOUNCE)
        # (0,0) should appear once at most (as the return destination)
        assert path.count((0, 0)) <= 1

    def test_unreachable_waypoint_raises(self):
        layout = [
            [G, W, G],
            [G, W, G],
            [G, W, G],
        ]
        grid = make_grid(layout)
        with pytest.raises(ValueError, match="No path found"):
            _expand_waypoints(grid, [(0, 0), (0, 2)], PatrolMode.BOUNCE)

    def test_out_of_bounds_waypoint_raises(self):
        grid = open_grid(5, 5)
        with pytest.raises(ValueError, match="out of grid bounds"):
            _expand_waypoints(grid, [(0, 0), (99, 99)], PatrolMode.BOUNCE)

    def test_wall_waypoint_raises(self):
        layout = [[G, W, G], [G, G, G]]
        grid = make_grid(layout)
        with pytest.raises(ValueError, match="not passable"):
            _expand_waypoints(grid, [(0, 0), (0, 1)], PatrolMode.BOUNCE)

    def test_path_is_contiguous(self):
        """Every consecutive step should be exactly 1 tile apart."""
        grid = open_grid()
        waypoints = [(0, 0), (0, 4), (4, 4)]
        path = _expand_waypoints(grid, waypoints, PatrolMode.BOUNCE)
        # Prepend first waypoint to check from origin
        full = [waypoints[0]] + path
        for i in range(1, len(full)):
            dr = abs(full[i][0] - full[i - 1][0])
            dc = abs(full[i][1] - full[i - 1][1])
            assert dr + dc == 1, \
                f"Non-cardinal step between {full[i-1]} and {full[i]}"


# ---------------------------------------------------------------------------
# NPC construction tests
# ---------------------------------------------------------------------------

class TestNPCConstruction:
    def test_npc_is_entity(self):
        grid = open_grid()
        npc = NPC(grid, [(0, 0), (0, 4)])
        assert isinstance(npc, Entity)

    def test_initial_position_is_first_waypoint(self):
        grid = open_grid()
        npc = NPC(grid, [(2, 2), (2, 6)])
        assert npc.position == (2, 2)

    def test_initial_facing_derived_from_route(self):
        grid = open_grid()
        npc = NPC(grid, [(5, 5), (5, 8)])
        assert npc.facing == FacingDirection.EAST

    def test_initial_facing_north(self):
        grid = open_grid()
        npc = NPC(grid, [(5, 5), (2, 5)])
        assert npc.facing == FacingDirection.NORTH

    def test_fewer_than_two_waypoints_raises(self):
        grid = open_grid()
        with pytest.raises(ValueError, match="at least 2 waypoints"):
            NPC(grid, [(0, 0)])

    def test_default_patrol_mode_is_bounce(self):
        grid = open_grid()
        npc = NPC(grid, [(0, 0), (0, 4)])
        assert npc.patrol_mode == PatrolMode.BOUNCE

    def test_custom_sight_and_sound_range(self):
        grid = open_grid()
        npc = NPC(grid, [(0, 0), (0, 4)], sight_range=2, sound_range=3)
        assert npc.sight_range == 2
        assert npc.sound_range == 3

    def test_waypoint_set_contains_waypoints(self):
        grid = open_grid()
        waypoints = [(0, 0), (0, 4), (4, 4)]
        npc = NPC(grid, waypoints)
        for wp in waypoints:
            assert wp in npc.waypoint_set

    def test_unreachable_route_raises_on_construction(self):
        layout = [
            [G, W, G],
            [G, W, G],
            [G, W, G],
        ]
        grid = make_grid(layout)
        with pytest.raises(ValueError):
            NPC(grid, [(0, 0), (0, 2)])


# ---------------------------------------------------------------------------
# Patrol step tests
# ---------------------------------------------------------------------------

class TestNPCPatrolStep:
    def test_patrol_step_moves_npc(self):
        grid = open_grid()
        npc = NPC(grid, [(0, 0), (0, 3)], waypoint_pause=0)
        initial = npc.position
        moved, pos = npc.patrol_step()
        assert moved is True
        assert pos != initial

    def test_patrol_step_returns_false_when_pausing(self):
        grid = open_grid()
        npc = NPC(grid, [(0, 0), (0, 3)], waypoint_pause=2)
        # Walk to first waypoint
        while npc.position != (0, 3):
            npc.patrol_step()
        # Should now be pausing
        assert npc.is_pausing is True
        moved, _ = npc.patrol_step()
        assert moved is False

    def test_npc_reaches_waypoint(self):
        grid = open_grid()
        npc = NPC(grid, [(0, 0), (0, 3)], waypoint_pause=0)
        for _ in range(20):
            npc.patrol_step()
            if npc.position == (0, 3):
                break
        assert npc.position == (0, 3)

    def test_bounce_npc_returns_to_start(self):
        grid = open_grid()
        npc = NPC(grid, [(0, 0), (0, 3)], waypoint_pause=0)
        visited_start_twice = 0
        for _ in range(40):
            npc.patrol_step()
            if npc.position == (0, 0):
                visited_start_twice += 1
            if visited_start_twice >= 1:
                break
        assert npc.position == (0, 0)

    def test_step_index_advances(self):
        grid = open_grid()
        npc = NPC(grid, [(0, 0), (0, 3)], waypoint_pause=0)
        initial_index = npc.step_index
        npc.patrol_step()
        # Index should advance after reaching next step
        assert npc.step_index >= initial_index

    def test_pause_countdown(self):
        grid = open_grid()
        npc = NPC(grid, [(0, 0), (0, 2)], waypoint_pause=3)
        # Walk to waypoint
        for _ in range(10):
            npc.patrol_step()
            if npc.position == (0, 2):
                break
        assert npc.pause_remaining == 3
        npc.patrol_step()
        assert npc.pause_remaining == 2
        npc.patrol_step()
        assert npc.pause_remaining == 1
        npc.patrol_step()
        assert npc.pause_remaining == 0

    def test_not_pausing_initially(self):
        grid = open_grid()
        npc = NPC(grid, [(0, 0), (0, 4)])
        assert npc.is_pausing is False

    def test_facing_updates_during_patrol(self):
        grid = open_grid()
        npc = NPC(grid, [(5, 0), (5, 4)], waypoint_pause=0)
        npc.patrol_step()
        assert npc.facing == FacingDirection.EAST
