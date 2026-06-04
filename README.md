# last-known-position

> *"Target acquired. Target lost. Searching last known position."*

A state machine visualizer disguised as a stealth/patrol game.

---

## What Is This?

**last-known-position** is a portfolio project built to make finite state machines
(FSMs) visible, interactive, and intuitive — without reading a textbook.

Most explanations of state machines are static: a diagram on a slide, a block of
pseudocode, a YouTube video playing out a pre-scripted sequence. This is different.
You control a player token on a graph paper grid. An NPC guard follows a patrol
route. The moment you step on the wrong tile, or wander into the guard's line of
sight, his internal state machine reacts — and you can watch it happen in real time
on the debug panel to the right.

The goal is the same as a **clear plastic Gameboy**: you can see the circuit boards
through the shell. You don't need to build the machine to understand how it works —
you just need a window into it.

---

## The Concept

The NPC guard has five internal states:

| State       | Behavior                                      |
|-------------|-----------------------------------------------|
| **Patrol**  | Follows a pre-scripted route of waypoints     |
| **Alerted** | Heard a sound — moving toward the source tile |
| **Chasing** | Spotted the player — actively pursuing.       |
| **Lost**    | Reached target, player not found — searching  |
| **Return**  | Gave up — heading back to patrol route        |

These states are wired to real perception systems:

- **Sight** is directional and blocked by walls. Step in front of the guard and
  within his sight radius — he sees you.
- **Sound** radiates in all directions and passes through walls. Step on a noisy
  tile near the guard — he hears you.
- **Memory** persists. If the guard was chasing you and you duck behind a wall,
  he doesn't freeze — he moves to your last known position, then enters a lost
  state before eventually giving up.

---

## The Debug Panel

The right panel is the point of the project. While you play, it shows:

- **Live state diagram** — the active state is highlighted, transitions animate
  as they fire
- **Event log** — a scrolling history of what the NPC perceived and decided
  ("Heard noise at (3,4)", "Player spotted", "Lost sight — searching")
- **Visual toggles** — show or hide the NPC's sight radius, sound radius, active
  route, and points of interest on the grid
- **Variable editors** — tune the NPC's sight range, sound range, and alert timer
  in real time to see how they affect behavior

---

## Tech Stack

- **Backend:** Python, Flask-SocketIO
- **Frontend:** HTML5 Canvas, vanilla JavaScript
- **Communication:** WebSockets (server owns the game loop and state, client renders)

The backend state machine, pathfinding (A*), line-of-sight, and sound propagation
are all pure Python with no frontend dependency. The frontend is a rendering layer —
swap it out, the logic still runs.

---

## Running the Project

*Setup and run instructions will be added at the end of Phase 2.*

---

## Project Status

| Phase | Description                         | Status         |
|-------|-------------------------------------|----------------|
| 1     | Core backend systems                | 🔲 Not started |
| 2     | WebSocket server + minimal frontend | 🔲 Not started |
| 3     | Debug panel                         | 🔲 Not started |
| 4     | Polish & presentation               | 🔲 Not started |

See [ROADMAP.md](./ROADMAP.md) for full phase details.

---

## Part of a Series

This project is part of a series of portfolio pieces that use nerdy source material
to demystify classic computer science concepts. See also:

- [poke-rsa](https://github.com/your-username/poke-rsa) — RSA encryption explained
  through Pokémon and prime numbers
