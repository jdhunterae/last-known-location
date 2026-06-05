"""
facing.py — Shared FacingDirection enum for Last Known Location.

Used by the NPC model, line_of_sight, and any other system that needs
to reason about cardinal directions.
"""

from enum import Enum


class FacingDirection(Enum):
    """Cardinal directions an entity can face."""
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
