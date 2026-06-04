# ROADMAP — last-known-position

A state machine visualizer disguised as a stealth/patrol game.
Built on a graph paper grid with coin-token characters and a live debug panel.

---

## Project Philosophy

The backend is the star. The NPC's state machine, pathfinding, line-of-sight, and
sound propagation all live in Python and know nothing about the browser. The frontend
is a transparent window into that logic — a clear plastic Gameboy. Pull the frontend
out, the backend still runs.

---

## Phase 1 — Core Backend Systems

**Branch:** `phase/core-backend`

**Goal:** A fully functional, fully tested Python backend with no frontend dependency.
All core systems implemented and verifiable from a script or test runner.

**Deliverables:**

- `Grid` model: tile types (Ground, NoisyGround, Wall), coordinate system
- `Pathfinding`: A* implementation, wall-aware, returns tile path or None
- `LineOfSight`: tile-based ray cast, blocked by Wall tiles
- `SoundPropagation`: radius check from source tile, walls do not block
- `StateMachine`: NPC states (Patrol, Alerted, Chasing, Lost, Return), full
  transition table, timer logic
- `NPCController`: wires state machine to grid, LOS, sound, and pathfinding
- `PlayerModel`: position, movement, noisy-tile detection
- Unit tests for all systems
- `README.md` updated to reflect Phase 1 status

**State Transition Table:**

```
patrol   -> (hear something)            -> alerted
patrol   -> (see player)                -> chasing

alerted  -> (reach target, no player)   -> lost
alerted  -> (hear something new)        -> alerted (update target)
alerted  -> (see player)                -> chasing

chasing  -> (reach target, no player)   -> lost
chasing  -> (player moves, in sight)    -> chasing (update target)
chasing  -> (reach player)              -> game over
chasing  -> (hear something)            -> chasing (ignore, sight takes priority)

lost     -> (timer expires)             -> return
lost     -> (hear something)            -> alerted
lost     -> (see player)                -> chasing

return   -> (reaches patrol path)       -> patrol
return   -> (hear something)            -> alerted
return   -> (see player)                -> chasing
```

---

## Phase 2 — WebSocket Server + Minimal Frontend

**Branch:** `phase/websocket-server`

**Goal:** The backend game loop runs over Flask-SocketIO. A bare-bones canvas
frontend renders the grid and tokens. Player input works. NPC moves and transitions
states visibly. No debug panel yet — just the world functioning end-to-end.

**Deliverables:**

- Flask-SocketIO server with game loop tick (server-side timer)
- WebSocket events: `player_move`, `world_state`, `state_transition`, `game_over`
- HTML5 Canvas frontend: grid tiles, player token, NPC token
- Player movement via arrow keys or click-to-move
- NPC moves each tick, transitions states in response to player
- Codespaces port-forwarding config (CORS/transport origin fix)
- `README.md` updated to reflect Phase 2 status

---

## Phase 3 — Debug Panel

**Branch:** `phase/debug-panel`

**Goal:** The right panel comes to life. This is the "clear plastic" moment —
the player can watch the state machine respond in real time, read the event log,
and tune the NPC's behavior via settings.

**Deliverables:**

- **State Diagram:** visual graph of all 5 states, active state highlighted,
  transitions animate on change
- **Event Log:** scrolling history of state transitions and perception events
  ("Heard something at (3,4)", "Lost sight of player", "Returning to patrol")
- **Visual Toggles (checkboxes):**
  - Show/hide NPC awareness radius (sight + sound circles)
  - Show/hide NPC current route (line toward active target)
  - Show/hide points of interest (markers on alert/noise tiles)
- **Variable Editors:**
  - Sight radius (tiles)
  - Sound radius (tiles)
  - Alert/lost timer duration (seconds)
- `README.md` updated to reflect Phase 3 status

---

## Phase 4 — Polish & Presentation

**Branch:** `phase/polish`

**Goal:** The project looks and feels like a portfolio piece. Aesthetic is
consistent, the README tells the full story, and the app is easy to run.

**Deliverables:**

- Graph paper background texture (CSS grid or canvas)
- Token styling (colored material-design circles with initials/icons)
- Sight cone overlay shading
- Sound radius pulse animation on noisy tile trigger
- Preset maps (at least 2: open map, walled corridor map)
- Optional: simple map layout config file so new maps are easy to add
- Final `README.md` with screenshots, architecture overview, and run instructions
- `ROADMAP.md` updated to mark all phases complete

---

## Backlog / Future Ideas

These are intentionally out of scope for the current build but worth preserving:

- Multiple NPC agents with independent state machines
- NPC-to-NPC communication ("I heard something, go check it")
- Mobile game expansion (separate project)
- Map editor UI
- Exportable state machine configs

---

## Branch Strategy

```
main          ← stable, tagged at end of each phase
develop       ← integration branch
phase/<name>  ← feature work, merges into develop, then main
```
