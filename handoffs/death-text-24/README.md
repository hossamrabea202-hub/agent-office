# #24 Upon death: the death screen says what killed you

By `adjustedfilm (Claude)`, 2026-10-31. Owner, 2026-10-27: *"text if died by tanticle attack you fallen, if died by
zombie : you been bitten or something like that"*. This card waited 4 days; sorry.

| Killed by | Death title |
|---|---|
| a zombie, Flesh Brute, half-horse zombie, wasp or risen soldier | **YOU WERE BITTEN** |
| a tentacle, the realm, anything else | **YOU HAVE FALLEN** |

**Hero:** every hit remembers its cause in `DeathText`. **HUD:** both death titles draw it: the "YOU HAVE FALLEN" screen,
which stays centred, and the older "YOU DIED" one.

## Pre-checks (done, on the Master's 10-30b exports)

| Check | Result |
|---|---|
| `fix_impure` on both pastes | no changes |
| HUD `merge --dry-run` (BP_ZombieHUD) | **Validation OK**, +11 links |
| hero `merge --dry-run` (BP_ThirdPersonCharacter) | **Validation OK**, +23 links. The 10-30b hero export is partial (20 links to nodes it doesn't contain), so I stripped those in a temp copy for the dry-run. Run it on your fresh export. |

## Steps (Master)

1. BP_ThirdPersonCharacter: paste the line of `DeathText_BPVar.txt` (default "YOU HAVE FALLEN"), then Compile.
2. Hero EventGraph: `applyall merge --live <fresh hero export> --manifest handoffs/death-text-24/manifest_hero_deathcause.json`,
   then Ctrl+A, Delete, paste the merged file, compile and save.
3. BP_ZombieHUD EventGraph: the same with `manifest_hud_deathtext.json`, then compile and save.

## Tests

1. Let a zombie kill you: **YOU WERE BITTEN**.
2. Let a tentacle strike kill you: **YOU HAVE FALLEN**.
3. The title is centred as before.
