# #302 Multi-User editing: one live Castle Defender session across several PCs

By `adjustedfilm (Claude)`, 2026-10-31.
- **Owner:** *"multi share the same project across multi laptops and edit in real time like a farm"*, then *"you take
  over and do it"*.
- **Uses Unreal's built-in Multi-User Editing** (the Concert plugin): every seat works in the same level at the same
  time, and the changes show up on the others within a second.

## 0. Who can be a seat

Run `check_pc.ps1` on each machine (it only reads) and paste the output on card #302:

```
powershell -ExecutionPolicy Bypass -File check_pc.ps1
```

| Machine | Result |
|---|---|
| i5 laptop (5CD3147LBC, adjustedfilm) | **not a seat**: MX570 2 GB VRAM, 16 GB RAM, 58 GB free. It stays an agent machine. |
| Master PC | the server and the main seat (it already has the project) |
| others | run the check |

A seat needs a GPU with **6 GB+ VRAM** (8+ recommended), **32 GB RAM** recommended, and about **200 GB free**.

## 1. The same engine everywhere: UE 5.3.2

1. On the Master PC, look at **Help → About Unreal Editor**. Every seat installs that exact version.
2. **To install 5.3:** Epic Games Launcher → Unreal Engine → Library → **+** beside ENGINE VERSIONS → click the version
   number on the new slot → **5.3.2** → Install.
3. **Never open this project in 5.8:** it converts the project, with no way back, and the 5.3 hand-offs stop matching.

## 2. The same project everywhere

- **Joining is refused if the files differ,** so every seat needs an identical copy before a session.
- **Simple (now):** copy the whole project folder from the Master PC (USB drive or LAN share), without `Saved/`,
  `Intermediate/` and `DerivedDataCache/`. Copy it again after each persisted session.
- **Proper (soon):** a **private Perforce (Helix Core) server** on the Master PC, free for up to 5 users. Everyone syncs
  the same revision, and licensed Fab/Megascans/CGTrader assets never touch the public GitHub repo.
- **Before copying licensed assets to another PC,** check that the licences cover your team's machines. Fab's standard
  licence is per seat for teams.

## 3. Turn on the plugin (once, on the Master PC; the copies carry it)

1. Edit → Plugins → search **Multi-User Editing** → enable it, then restart.
2. Recommended: Project Settings → **World Partition / One File Per Actor**, so seats editing one level touch different
   files.

## 4. Run a session

| Step | Where | What |
|---|---|---|
| 1 | Master PC | `start_server.bat`, and keep the window open |
| 2 | Master PC | open the editor → toolbar **Multi-User** button → **Create session** `CastleDefender` |
| 3 | each seat | `join_session.bat "D:\...\CastleDefender.uproject" <SeatName>` |
| 4 | end of the day | Master: Multi-User Browser → **Persist** the session changes → Save All. Then refresh the copies (step 2) |

- **Outside the house:** install **Tailscale** (free, private VPN) on every machine and sign in with one account.
  Multi-User discovery only works on a LAN, so pass the IPs (`tailscale ip -4`):
  - server: `start_server.bat 100.x.y.z` (the server's own IP);
  - seats: `join_session.bat "<uproject>" <Seat> <myIP> 100.x.y.z`.
- **Firewall:** allow `UnrealMultiUserServer` / `UnrealEditor` on private networks when Windows asks (UDP 9030).

## 5. What changes in the office

- **Rule 1 (only the Master edits) changes only when you say which machines are seats.** Then each seat pastes its own
  agent's hand-offs into the live session, and the Master persists at the end of the day.
- The 60-hand-off queue then clears in parallel instead of behind one desk.
- **Locks:** a Blueprint or material someone is editing is locked for the others until they save. Big shared Blueprints
  (BP_ThirdPersonCharacter, BPC_MotionFX) still go one at a time; that's what the applyall merges are for.

## 6. "Farm" (later, optional)

- **Lighting bakes:** Unreal Swarm splits the work across machines.
- **Shaders:** compiling across machines needs Incredibuild (has a free tier) or Horde. The built-in UBA comes in 5.4+.
- **Trailer and cinematic renders:** Movie Render Queue, plus Deadline for several PCs.
