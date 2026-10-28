# #68 Interaction prompts: fade-in + gentle blink

Seat: `hossam gmail laptop2 (Claude)` · card #68 · export request #101.
Status: **design ready, paste waits on the exports in `handoffs/exports/laptop2/prompt68/`** (no blind pastes).

## The look (vice master's Decision, kept)

| Phase | Time | Alpha |
|---|---|---|
| Fade-in | 0.25 s after the prompt becomes visible | 0 -> envelope (smoothstep) |
| Breathing | while visible | 0.75 .. 1.0, sine at 0.6 Hz (period ~1.67 s) |
| Fade-out | 0.25 s after it stops being visible | current -> 0 (smoothstep), then stop drawing |

Text colour and font stay as they are. Only alpha changes, applied to the text tint **and** to its shadow/plate, so nothing pops.

## Math (one function, shared by every prompt)

```
Env   = clamp(Env + (Visible ? +dt : -dt) / 0.25, 0, 1)        // per prompt, every frame
Ease  = Env * Env * (3 - 2 * Env)                               // smoothstep
Pulse = 0.875 + 0.125 * sin(2*pi * 0.6 * (Now - ShownAt))       // 0.75..1.0, starts at 0.875 rising
Alpha = Ease * Pulse
Draw only while Env > 0.
```

- `ShownAt` resets when `Visible` goes false -> true (rising edge), so every prompt starts its pulse at the same phase. No sync with other prompts is needed.
- `dt` = the HUD's world delta seconds (Get World Delta Seconds). It is frame-rate independent and works while paused only if the HUD ticks while paused (the HUDs already draw while paused).
- The fade-out needs the **last** text and position, so cache them while visible (`LastText`, `LastPos`) and draw the cache during the fade-out.

## Blueprint shape

One pure function in a shared place (`BP_NoticeHUD`, which already draws on top every frame, per the vice master's note on #68):

`PromptAlpha(Key: Name, Visible: bool) -> Alpha: float, Draw: bool`

- State per prompt in a `Map<Name, Vector>`: X = Env, Y = ShownAt, Z = last Visible (0/1). Keys: `Vesna`, `Command`, `Cannon`, `Gate`, `Pickup`.
- Each prompt's draw site: replace `Draw Text (Color)` with `Draw Text (Color * (1,1,1,Alpha))`, gated by `Draw`. The prompt's existing condition becomes the `Visible` input instead of a Branch that skips drawing.
- `BP_SkillTreeHUD` (Vesna, 44 MB graph): **don't re-paste the graph.** Pass its condition out through the existing MPC/flag pattern (#76 market guard) and let `BP_NoticeHUD` draw the Vesna prompt with the shared look. The other HUDs are small enough to change in place.

## Checks for the editor driver (after the paste)

1. Walk up to Vesna: `[E] Speak with Vesna` fades in over ~1/4 s, then breathes slowly. It never goes fully dark (min 0.75).
2. Walk away: it fades out over ~1/4 s, with no snap and no text left behind.
3. Same for `[E] Command`, the cannon mount, the gate lever and the pickups.
4. Pause / open a menu: no flicker, and the prompt stays where it is.
5. Two prompts in view at once: each fades on its own.
