"""
pathfinding.py — A* pathfinding on the tile grid.

Finds the shortest passable path between two grid positions using the
A* algorithm with a Manhattan distance heuristic.

Movement is cardinal only (N, S, E, W). Diagonal movement is not supported.
Wall tiles are impassable. GROUND and NOISY tiles are treated as equal cost.

Coordinate system:
    (row, col) — row 0 is the top of the map, col 0 is the left edge.
"""

import heapq
from typing import Optional

from app.models.grid import Grid


def manhattan(row_a: int, col_a: int, row_b: int, col_b: int) -> int:
    """
    Manhattan distance heuristic for cardinal-only grid movement.

    Args:
        row_a: Row of the start tile.
        col_a: Column of the start tile.
        row_b: Row of the goal tile.
        col_b: Column of the goal tile.

    Returns:
        Integer Manhattan distance between the two positions.
    """
    return abs(row_a - row_b) + abs(col_a - col_b)


def find_path(
    grid: Grid,
    start: tuple[int, int],
    goal: tuple[int, int],
) -> Optional[list[tuple[int, int]]]:
    """
    Find the shortest path between two tiles using A*.

    All passable tiles (GROUND, NOISY) have uniform movement cost of 1.
    WALL tiles are impassable. The path does not include the start tile
    but does include the goal tile.

    Args:
        grid:  The Grid to search.
        start: (row, col) of the starting tile.
        goal:  (row, col) of the destination tile.

    Returns:
        A list of (row, col) tuples from start (exclusive) to goal
        (inclusive) representing the shortest path, or None if no path
        exists.

    Examples:
        path = find_path(grid, (0, 0), (2, 2))
        # [(0, 1), (1, 1), (2, 1), (2, 2)]  — one possible result
    """
    start_row, start_col = start
    goal_row, goal_col = goal

    # Guard: out of bounds or impassable endpoints
    if not grid.in_bounds(start_row, start_col):
        return None
    if not grid.in_bounds(goal_row, goal_col):
        return None
    if not grid.is_passable(start_row, start_col):
        return None
    if not grid.is_passable(goal_row, goal_col):
        return None

    # Trivial case
    if start == goal:
        return []

    # Priority queue entries: (f_score, g_score, row, col)
    # g_score = cost from start to this tile
    # f_score = g_score + heuristic estimate to goal
    h = manhattan(start_row, start_col, goal_row, goal_col)
    open_heap: list[tuple[int, int, int, int]] = [(h, 0, start_row, start_col)]

    # came_from maps (row, col) -> (row, col) for path reconstruction
    came_from: dict[tuple[int, int], tuple[int, int]] = {}

    # Best known g_score for each visited tile
    g_scores: dict[tuple[int, int], int] = {start: 0}

    while open_heap:
        _f, g, row, col = heapq.heappop(open_heap)

        current = (row, col)

        # Reached the goal — reconstruct path
        if current == goal:
            return _reconstruct_path(came_from, goal)

        # Skip if we've already found a better path to this tile
        if g > g_scores.get(current, float("inf")):
            continue

        for neighbor in grid.neighbors(row, col):
            n = (neighbor.row, neighbor.col)
            tentative_g = g + 1  # uniform cost: all passable tiles cost 1

            if tentative_g < g_scores.get(n, float("inf")):
                g_scores[n] = tentative_g
                f = tentative_g + \
                    manhattan(neighbor.row, neighbor.col, goal_row, goal_col)
                heapq.heappush(open_heap, (f, tentative_g,
                               neighbor.row, neighbor.col))
                came_from[n] = current

    # Open set exhausted with no path found
    return None


def _reconstruct_path(
    came_from: dict[tuple[int, int], tuple[int, int]],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    """
    Walk the came_from map backwards from goal to reconstruct the path.

    The start tile is excluded from the result; the goal tile is included.

    Args:
        came_from: Map of tile -> previous tile built during A* search.
        goal:      The destination tile.

    Returns:
        Ordered list of (row, col) tuples from after-start to goal.
    """
    path = []
    current = goal
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path
