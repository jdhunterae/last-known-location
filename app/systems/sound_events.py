"""
sound_events.py — Sound event objects for Last Known Location.

Sound in LKL is modeled as first-class grid objects, independent of
whatever created them. NPCs perceive sound by checking for active
SoundEvent objects within their hearing radius each tick.

Three classes:

    SoundEvent  — A single audible point on a tile. Created by noisy
                  tile interactions, wave propagation, or any future
                  sound-emitting action. Decays after N ticks.

    SoundWave   — An expanding hollow ring of sound that travels outward
                  from a source tile. Each tick it spawns new SoundEvents
                  on the border of the current ring, then advances. Walls
                  stop the ring from expanding through them. Models loud
                  one-time events (explosions, crashes).

    SoundSource — (Future) A persistent emitter that spawns a new
                  SoundEvent at a fixed tile every tick. Models continuous
                  sounds (fire, machinery). Placeholder stub included.

Sound propagation ring shape:
    The ring border at distance d is all tiles in the range=d rounded
    square that are NOT in the range=(d-1) rounded square. The rounded
    square clips the 4 outer corners and excludes the origin.

    Ring 1 (d=1):  4 cardinal neighbors
    Ring 2 (d=2):  border of range-2 shape minus ring-1 tiles
    Ring 3 (d=3):  border of range-3 shape minus ring-2 and ring-1 tiles

Walls:
    - Do NOT block SoundEvent audibility (hearing checks ignore walls)
    - DO stop SoundWave propagation — ring tiles on wall tiles are skipped,
      and walls do not spawn further children

Coordinate system:
    (row, col) — row 0 is top of map, col 0 is left edge.
"""

from app.models.grid import Grid
from app.systems.sound import get_sound_radius_tiles


class SoundEvent:
    """
    A single audible point on a grid tile.

    Created by noisy tile interactions, SoundWave propagation, or any
    future sound-emitting action. Persists for a fixed number of ticks
    before expiring.

    Attributes:
        position        (row, col) of the tile this event occupies.
        ticks_remaining Ticks before this event expires. Default 1.
        intensity       Reserved for future priority/volume use.
        expired         True when ticks_remaining reaches 0.
    """

    def __init__(
        self,
        position: tuple[int, int],
        ticks_remaining: int = 1,
        intensity: int = 1,
    ):
        self.position = position
        self.ticks_remaining = ticks_remaining
        self.intensity = intensity

    @property
    def expired(self) -> bool:
        """True if this event has fully decayed."""
        return self.ticks_remaining <= 0

    def tick(self) -> None:
        """Advance one game tick, decrementing the decay timer."""
        if not self.expired:
            self.ticks_remaining -= 1

    def __repr__(self) -> str:
        return (
            f"SoundEvent(pos={self.position}, "
            f"ticks={self.ticks_remaining}, "
            f"intensity={self.intensity})"
        )


class SoundWave:
    """
    An expanding hollow ring of sound travelling outward from a source.

    Each tick the wave advances one ring outward, spawning SoundEvent
    objects on the border tiles of the current ring. Wall tiles stop the
    wave from expanding through them — a ring tile on a wall is skipped
    and does not propagate further from that point.

    The wave expires when it has spawned all rings up to propagation_range.

    Attributes:
        origin              (row, col) where the wave originated.
        propagation_range   Total number of rings to expand.
        event_duration      Ticks each spawned SoundEvent will last.
        intensity           Passed through to spawned SoundEvents.
        current_ring        The ring distance being spawned this tick.
        expired             True when all rings have been spawned.

    Usage:
        wave = SoundWave(origin=(5, 5), propagation_range=3)
        new_events = wave.tick(grid)   # call each game tick
        if wave.expired:
            remove it from active waves
    """

    def __init__(
        self,
        origin: tuple[int, int],
        propagation_range: int = 1,
        event_duration: int = 1,
        intensity: int = 1,
    ):
        if propagation_range < 1:
            raise ValueError(
                f"propagation_range must be >= 1, got {propagation_range}"
            )
        self.origin = origin
        self.propagation_range = propagation_range
        self.event_duration = event_duration
        self.intensity = intensity
        self.current_ring = 1

    @property
    def expired(self) -> bool:
        """True when all rings have been spawned."""
        return self.current_ring > self.propagation_range

    def tick(self, grid: Grid) -> list[SoundEvent]:
        """
        Advance one game tick, spawning SoundEvents on the current ring border.

        Wall tiles are skipped — the wave does not pass through walls.
        After spawning, the wave advances to the next ring.

        Args:
            grid: The Grid, used for bounds checking and wall detection.

        Returns:
            List of newly spawned SoundEvent objects for this tick.
            Empty list if the wave has already expired.
        """
        if self.expired:
            return []

        border = self._get_ring_border(self.current_ring)
        events = []

        for tile in border:
            r, c = tile
            if not grid.in_bounds(r, c):
                continue
            if grid.blocks_sight(r, c):
                # Wall stops the wave from propagating through this tile
                continue
            events.append(SoundEvent(
                position=tile,
                ticks_remaining=self.event_duration,
                intensity=self.intensity,
            ))

        self.current_ring += 1
        return events

    def _get_ring_border(self, d: int) -> list[tuple[int, int]]:
        """
        Return the hollow border tiles at ring distance d from origin.

        The border is the set of tiles in the range=d rounded square
        that are NOT in the range=(d-1) rounded square.

        Args:
            d: Ring distance (1 = first ring outward from origin).

        Returns:
            List of (row, col) border tile positions.
        """
        outer = set(get_sound_radius_tiles(self.origin, d))
        if d == 1:
            # range=1 rounded square is already just the 4 cardinals —
            # there is no inner ring to subtract
            return list(outer)
        inner = set(get_sound_radius_tiles(self.origin, d - 1))
        return list(outer - inner)

    def __repr__(self) -> str:
        return (
            f"SoundWave(origin={self.origin}, "
            f"ring={self.current_ring}/{self.propagation_range}, "
            f"expired={self.expired})"
        )


class SoundSource:
    """
    A persistent sound emitter that spawns a new SoundEvent every tick.

    Models continuous ambient sounds (fire crackling, machinery humming).
    Unlike SoundWave, SoundSource never expires on its own — it must be
    explicitly removed from the active sources list.

    Attributes:
        position        (row, col) of the emitter tile.
        event_duration  Ticks each spawned SoundEvent will last.
        intensity       Passed through to spawned SoundEvents.

    Usage:
        source = SoundSource(position=(3, 3), event_duration=2)
        new_event = source.tick()   # call each game tick
    """

    def __init__(
        self,
        position: tuple[int, int],
        event_duration: int = 1,
        intensity: int = 1,
    ):
        self.position = position
        self.event_duration = event_duration
        self.intensity = intensity

    def tick(self) -> SoundEvent:
        """
        Spawn a new SoundEvent at this source's position.

        Returns:
            A fresh SoundEvent at this source's tile.
        """
        return SoundEvent(
            position=self.position,
            ticks_remaining=self.event_duration,
            intensity=self.intensity,
        )

    def __repr__(self) -> str:
        return (
            f"SoundSource(pos={self.position}, "
            f"duration={self.event_duration}, "
            f"intensity={self.intensity})"
        )
