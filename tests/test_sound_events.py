"""
test_sound_events.py — Unit tests for SoundEvent, SoundWave, and SoundSource.
"""

import pytest
from app.models.grid import Grid, TileType
from app.systems.sound_events import SoundEvent, SoundWave, SoundSource

G = TileType.GROUND
W = TileType.WALL
N = TileType.NOISY


def open_grid(rows=12, cols=12):
    return Grid(rows, cols)


# ---------------------------------------------------------------------------
# SoundEvent tests
# ---------------------------------------------------------------------------

class TestSoundEvent:
    def test_default_duration_is_one_tick(self):
        e = SoundEvent((5, 5))
        assert e.ticks_remaining == 1

    def test_not_expired_when_created(self):
        e = SoundEvent((5, 5))
        assert e.expired is False

    def test_expires_after_one_tick(self):
        e = SoundEvent((5, 5), ticks_remaining=1)
        e.tick()
        assert e.expired is True

    def test_multi_tick_duration(self):
        e = SoundEvent((5, 5), ticks_remaining=3)
        e.tick()
        assert e.ticks_remaining == 2
        assert e.expired is False
        e.tick()
        assert e.ticks_remaining == 1
        e.tick()
        assert e.expired is True

    def test_tick_does_not_go_below_zero(self):
        e = SoundEvent((5, 5), ticks_remaining=1)
        e.tick()
        e.tick()  # already expired
        assert e.ticks_remaining == 0

    def test_position_stored_correctly(self):
        e = SoundEvent((3, 7))
        assert e.position == (3, 7)

    def test_intensity_stored(self):
        e = SoundEvent((5, 5), intensity=3)
        assert e.intensity == 3

    def test_default_intensity_is_one(self):
        e = SoundEvent((5, 5))
        assert e.intensity == 1


# ---------------------------------------------------------------------------
# SoundWave ring border shape tests
# ---------------------------------------------------------------------------

class TestSoundWaveRingBorder:
    def test_ring1_is_four_cardinals(self):
        """Ring 1 from (5,5) should be the 4 cardinal neighbors."""
        wave = SoundWave(origin=(5, 5), propagation_range=3)
        border = set(wave._get_ring_border(1))
        assert border == {(4, 5), (6, 5), (5, 4), (5, 6)}

    def test_ring2_does_not_include_ring1_tiles(self):
        wave = SoundWave(origin=(5, 5), propagation_range=3)
        ring1 = set(wave._get_ring_border(1))
        ring2 = set(wave._get_ring_border(2))
        assert ring1.isdisjoint(ring2)

    def test_ring3_does_not_include_ring1_or_ring2(self):
        wave = SoundWave(origin=(5, 5), propagation_range=3)
        ring1 = set(wave._get_ring_border(1))
        ring2 = set(wave._get_ring_border(2))
        ring3 = set(wave._get_ring_border(3))
        assert ring3.isdisjoint(ring1)
        assert ring3.isdisjoint(ring2)

    def test_origin_never_in_any_ring(self):
        wave = SoundWave(origin=(5, 5), propagation_range=4)
        for d in range(1, 5):
            assert (5, 5) not in wave._get_ring_border(d)

    def test_rings_are_hollow(self):
        """Ring 2 border should not contain ring 1 interior tiles."""
        wave = SoundWave(origin=(5, 5), propagation_range=2)
        ring2 = set(wave._get_ring_border(2))
        # The 4 cardinals (ring 1) should not appear in ring 2
        assert (4, 5) not in ring2
        assert (6, 5) not in ring2
        assert (5, 4) not in ring2
        assert (5, 6) not in ring2

    def test_rings_expand_outward(self):
        wave = SoundWave(origin=(5, 5), propagation_range=4)
        sizes = [len(wave._get_ring_border(d)) for d in range(1, 5)]
        # Each ring should have more tiles than the previous
        for i in range(1, len(sizes)):
            assert sizes[i] > sizes[i - 1]


# ---------------------------------------------------------------------------
# SoundWave tick / propagation tests
# ---------------------------------------------------------------------------

class TestSoundWaveTick:
    def test_not_expired_at_creation(self):
        wave = SoundWave(origin=(5, 5), propagation_range=2)
        assert wave.expired is False

    def test_expires_after_all_rings_spawned(self):
        wave = SoundWave(origin=(5, 5), propagation_range=2)
        grid = open_grid()
        wave.tick(grid)  # ring 1
        wave.tick(grid)  # ring 2
        assert wave.expired is True

    def test_tick_returns_sound_events(self):
        wave = SoundWave(origin=(5, 5), propagation_range=1)
        grid = open_grid()
        events = wave.tick(grid)
        assert len(events) > 0
        assert all(isinstance(e, SoundEvent) for e in events)

    def test_tick_returns_empty_when_expired(self):
        wave = SoundWave(origin=(5, 5), propagation_range=1)
        grid = open_grid()
        wave.tick(grid)
        assert wave.expired is True
        assert wave.tick(grid) == []

    def test_spawned_events_have_correct_duration(self):
        wave = SoundWave(origin=(5, 5), propagation_range=1, event_duration=3)
        grid = open_grid()
        events = wave.tick(grid)
        assert all(e.ticks_remaining == 3 for e in events)

    def test_spawned_events_positions_match_ring_border(self):
        wave = SoundWave(origin=(5, 5), propagation_range=1)
        grid = open_grid()
        events = wave.tick(grid)
        positions = {e.position for e in events}
        expected = {(4, 5), (6, 5), (5, 4), (5, 6)}
        assert positions == expected

    def test_propagation_range_invalid_raises(self):
        with pytest.raises(ValueError):
            SoundWave(origin=(5, 5), propagation_range=0)

    def test_wave_advances_ring_each_tick(self):
        wave = SoundWave(origin=(5, 5), propagation_range=3)
        grid = open_grid()
        assert wave.current_ring == 1
        wave.tick(grid)
        assert wave.current_ring == 2
        wave.tick(grid)
        assert wave.current_ring == 3

    def test_out_of_bounds_tiles_not_spawned(self):
        grid = Grid(5, 5)
        # Origin near edge — some ring tiles will be out of bounds
        wave = SoundWave(origin=(0, 0), propagation_range=2)
        events = wave.tick(grid)
        for e in events:
            r, c = e.position
            assert grid.in_bounds(r, c), \
                f"Out of bounds event spawned at {e.position}"


# ---------------------------------------------------------------------------
# SoundWave wall interaction tests
# ---------------------------------------------------------------------------

class TestSoundWaveWalls:
    def test_wall_tiles_not_spawned(self):
        """Wave should not spawn events on wall tiles."""
        layout = [
            [G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, W, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G],
            [G, G, G, G, G, G, G, G, G, G, G, G],
        ]
        grid = Grid.from_layout(layout)
        wave = SoundWave(origin=(5, 5), propagation_range=1)
        events = wave.tick(grid)
        positions = {e.position for e in events}
        # Wall at (4,4) is in ring 1 — should be skipped
        assert (4, 4) not in positions

    def test_non_wall_ring_tiles_still_spawned_near_wall(self):
        """A wall on one side should not suppress the rest of the ring."""
        layout = [[G] * 12 for _ in range(12)]
        layout[4][5] = W  # wall directly north of origin
        grid = Grid.from_layout(layout)
        wave = SoundWave(origin=(5, 5), propagation_range=1)
        events = wave.tick(grid)
        positions = {e.position for e in events}
        # South, east, west cardinals should still fire
        assert (6, 5) in positions
        assert (5, 6) in positions
        assert (5, 4) in positions
        # North is walled
        assert (4, 5) not in positions


# ---------------------------------------------------------------------------
# SoundSource tests
# ---------------------------------------------------------------------------

class TestSoundSource:
    def test_tick_returns_sound_event(self):
        source = SoundSource(position=(3, 3))
        event = source.tick()
        assert isinstance(event, SoundEvent)

    def test_event_position_matches_source(self):
        source = SoundSource(position=(3, 3))
        event = source.tick()
        assert event.position == (3, 3)

    def test_event_duration_passed_through(self):
        source = SoundSource(position=(3, 3), event_duration=4)
        event = source.tick()
        assert event.ticks_remaining == 4

    def test_emits_new_event_every_tick(self):
        source = SoundSource(position=(3, 3))
        e1 = source.tick()
        e2 = source.tick()
        assert e1 is not e2

    def test_source_never_expires(self):
        """SoundSource has no expiry — it runs until explicitly removed."""
        source = SoundSource(position=(3, 3))
        for _ in range(100):
            event = source.tick()
            assert isinstance(event, SoundEvent)
