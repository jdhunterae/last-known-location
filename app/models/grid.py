"""
grid.py — Tile types and Grid model.

The Grid is the foundational data structure for last-known-position.
It is a 2D array of Tiles addressed by (row, col), where row 0 is the
top of the map and col 0 is the left edge.

    grid[row][col]  →  grid[y][x] on the canvas

Tile types:
    GROUND      — passable, silent
    NOISY       — passable, emits a sound event when entered
    WALL        — impassable, blocks line of sight
"""

from enum import Enum, auto
from typing import Optional


class TileType(Enum):
    """Enumeration of all valid tile types."""
    GROUND = auto()
    NOISY = auto()
    WALL = auto()


class Tile:
    """
    A single cell on the grid.

    Attributes:
        tile_type (TileType): The type of this tile.
        row (int): Row index of this tile (y position).
        col (int): Column index of this tile (x position).
    """

    def __init__(self, tile_type: TileType, row: int, col: int):
        self.tile_type = tile_type
        self.row = row
        self.col = col

    @property
    def passable(self) -> bool:
        """Returns True if entities can move onto this tile."""
        return self.tile_type != TileType.WALL

    @property
    def noisy(self) -> bool:
        """Returns True if entering this tile emits a sound event."""
        return self.tile_type == TileType.NOISY

    @property
    def blocks_sight(self) -> bool:
        """Returns True if this tile blocks line of sight."""
        return self.tile_type == TileType.WALL

    def __repr__(self) -> str:
        return f"Tile({self.tile_type.name}, row={self.row}, col={self.col})"


class Grid:
    """
    A 2D grid of Tiles representing the game map.

    Addressed as grid[row][col], equivalent to grid[y][x] on the canvas.
    Row 0 is the top of the map. Col 0 is the left edge.

    Attributes:
        rows (int): Number of rows in the grid.
        cols (int): Number of columns in the grid.

    Example:
        layout = [
            [W, G, G],
            [G, N, G],
            [G, G, W],
        ]
        grid = Grid.from_layout(layout)
    """

    # Shorthand constants for building layouts
    GROUND = TileType.GROUND
    NOISY = TileType.NOISY
    WALL = TileType.WALL

    def __init__(self, rows: int, cols: int):
        """
        Initialize an empty grid filled with GROUND tiles.

        Args:
            rows (int): Number of rows.
            cols (int): Number of columns.
        """
        if rows <= 0 or cols <= 0:
            raise ValueError(
                f"Grid dimensions must be positive, got ({rows}, {cols})")

        self.rows = rows
        self.cols = cols
        self._tiles: list[list[Tile]] = [
            [Tile(TileType.GROUND, r, c) for c in range(cols)]
            for r in range(rows)
        ]

    @classmethod
    def from_layout(cls, layout: list[list[TileType]]) -> "Grid":
        """
        Construct a Grid from a 2D list of TileType values.

        Args:
            layout: A 2D list where each element is a TileType.
                    layout[row][col] maps directly to grid position.

        Returns:
            A fully constructed Grid instance.

        Raises:
            ValueError: If the layout is empty or rows have inconsistent lengths.
        """
        if not layout or not layout[0]:
            raise ValueError("Layout must be a non-empty 2D list.")

        rows = len(layout)
        cols = len(layout[0])

        if any(len(row) != cols for row in layout):
            raise ValueError(
                "All rows in the layout must have the same number of columns.")

        grid = cls(rows, cols)
        for r, row in enumerate(layout):
            for c, tile_type in enumerate(row):
                grid._tiles[r][c] = Tile(tile_type, r, c)

        return grid

    def get(self, row: int, col: int) -> Optional[Tile]:
        """
        Retrieve a tile by position.

        Args:
            row (int): Row index.
            col (int): Column index.

        Returns:
            The Tile at (row, col), or None if out of bounds.
        """
        if not self.in_bounds(row, col):
            return None
        return self._tiles[row][col]

    def in_bounds(self, row: int, col: int) -> bool:
        """
        Check whether a (row, col) coordinate is within the grid.

        Args:
            row (int): Row index.
            col (int): Column index.

        Returns:
            True if the coordinate is valid, False otherwise.
        """
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_passable(self, row: int, col: int) -> bool:
        """
        Check whether an entity can move onto a tile.

        Args:
            row (int): Row index.
            col (int): Column index.

        Returns:
            True if the tile exists and is passable, False otherwise.
        """
        tile = self.get(row, col)
        return tile is not None and tile.passable

    def is_noisy(self, row: int, col: int) -> bool:
        """
        Check whether a tile emits sound when entered.

        Args:
            row (int): Row index.
            col (int): Column index.

        Returns:
            True if the tile exists and is noisy, False otherwise.
        """
        tile = self.get(row, col)
        return tile is not None and tile.noisy

    def blocks_sight(self, row: int, col: int) -> bool:
        """
        Check whether a tile blocks line of sight.

        Args:
            row (int): Row index.
            col (int): Column index.

        Returns:
            True if the tile exists and blocks sight, False otherwise.
        """
        tile = self.get(row, col)
        return tile is not None and tile.blocks_sight

    def neighbors(self, row: int, col: int) -> list[Tile]:
        """
        Return the passable cardinal neighbors of a tile (N, S, E, W).

        Args:
            row (int): Row index.
            col (int): Column index.

        Returns:
            List of passable adjacent Tile objects.
        """
        candidates = [
            (row - 1, col),  # North
            (row + 1, col),  # South
            (row, col + 1),  # East
            (row, col - 1),  # West
        ]
        return [
            self._tiles[r][c]
            for r, c in candidates
            if self.in_bounds(r, c) and self._tiles[r][c].passable
        ]

    def __repr__(self) -> str:
        symbols = {TileType.GROUND: ".",
                   TileType.NOISY: "N", TileType.WALL: "#"}
        rows = ["".join(symbols[self._tiles[r][c].tile_type] for c in range(self.cols))
                for r in range(self.rows)]
        return "\n".join(rows)
