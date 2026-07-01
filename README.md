# WoT 0.8.10 Offline Hangar Server

Offline mod for World of Tanks 0.8.10 that bypasses the login server and loads the hangar (garage) directly.

## How it works

The mod consists of two Python scripts placed in `res_mods/0.8.10/scripts/client/`:

- **`game.py`** - Overrides the original `game.py` to schedule the offline hangar entry 5 seconds after the GUI starts.
- **`offline_hangar.py`** - Creates an Account entity locally (without a server), patches the connection manager to report "connected", replaces the personality GUI handler to skip server data sync, and triggers the hangar loading sequence.

## Installation

1. Download and extract the WoT 0.8.10 client.
2. Copy the contents of `res_mods/` from this repository into the client's `res_mods/` folder:

```
World_of_Tanks - 0.8.10/
  res_mods/
    0.8.10/
      scripts/
        client/
          game.pyc          <-- copy this
          offline_hangar.pyc <-- copy this
```

3. Launch `WorldOfTanks.exe` normally. After ~5 seconds, the login screen will be replaced by the hangar.

## Files

| File | Description |
|------|-------------|
| `res_mods/0.8.10/scripts/client/game.py` | Source code for the game.py override |
| `res_mods/0.8.10/scripts/client/game.pyc` | Compiled bytecode (Python 2.6) |
| `res_mods/0.8.10/scripts/client/offline_hangar.py` | Source code for the offline hangar module |
| `res_mods/0.8.10/scripts/client/offline_hangar.pyc` | Compiled bytecode (Python 2.6) |

**Note:** Only the `.pyc` files are needed for the game. The `.py` source files are included for reference.

## Technical Details

### Flow
1. `game.py` calls `gui_personality.start()` (normal GUI initialization)
2. After 5 seconds, `_enter_offline_hangar()` is called via `BigWorld.callback`
3. `offline_hangar.enter()` patches the connection manager, personality handler, and Account base proxy
4. A local Account entity is created with `BigWorld.createEntity()` with minimal properties
5. The entity is set as the player via `BigWorld.player()`
6. After 2 more seconds, `showGUI()` is called on the player entity
7. The patched personality handler skips server sync and directly initializes the hangar space

### Limitations
- No inventory data (no vehicles displayed)
- No shop/stats (credits, gold show as 0)
- No battle functionality
- VOIP is disabled
