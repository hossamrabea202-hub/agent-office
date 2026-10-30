# applyall.py

Puts Blueprint paste files into a live Blueprint graph, makes the rewires, checks everything, and writes **one**
merged file. You paste that file back into the editor in one go.

Why: UE 5.3 Python cannot edit Blueprint graphs. Copy and paste (T3D text) can.

Needs Python 3.8+ only. No installs, no internet.

## Workflow (5 steps)

1. **Export:** open the Blueprint's EventGraph, press Ctrl+A, then Ctrl+C, and save the clipboard as `live.t3d`.
2. **Merge:** `python3 applyall.py merge --live live.t3d --manifest manifest.json --out merged.t3d`
3. **Clipboard:** copy all the text of `merged.t3d` to the clipboard (only if step 2 said `Validation: OK`).
4. **Paste:** in the same EventGraph, press Ctrl+A, then Delete, then Ctrl+V.
5. **Compile** and save. Then export again and run `check` if you want to be sure.

If step 2 prints `ERROR`, nothing was written. Read the message, fix the manifest, and run it again.
You can run a manifest twice: pastes that are already in are not added again, and links that are already there are
skipped.

## Commands

```
python3 applyall.py merge --live LIVE.t3d --manifest MANIFEST.json --out MERGED.t3d [--dry-run]
python3 applyall.py check FILE.t3d [Node ...]
python3 applyall.py manifest-from-readme README.md [--out draft.json]
```

- **merge**: adds the paste files, makes the rewires, checks, and writes. `--dry-run` checks only.
- **check**: shows every link of the nodes you name (debug view) and checks the whole file:
  ```
  $ python3 applyall.py check nh3.t3d InfIn
  InfIn  [K2Node_ExecutionSequence]  pos (-3760, -1632)
      execute                (exec in) <- CX_208.then, CX_138.else
      then_0                 (exec out) -> nAs2.execute
  nh3.t3d: 514 nodes, 2331 pins, 1616 LinkedTo entries (808 links)
  Validation: OK
  ```
- **manifest-from-readme**: reads a hand-off README and makes a **draft** manifest. It reads lines like
  `X.pin -> Y.pin` and tables with `From` / `To` columns. If the README names more than one paste file, you get one
  draft per paste. Words like "replaces" or "used to" set `replace: true`. **It is only a draft.** Check the names,
  the `replace` flags and the blueprint name before you use it.

## Manifest (short)

Full details are in `manifest_schema.md`. Example (`examples/infection73_noticehud.json`):

```json
{
  "blueprint": "BP_NoticeHUD",
  "pastes": [
    {"file": "NoticeHUD_Infection_graph.txt", "offset": [0, 3000]}
  ],
  "rewires": [
    {"from": "CX_208.then",   "to": "InfIn.execute",    "replace": true},
    {"from": "CX_138.else",   "to": "InfIn.execute",    "replace": true},
    {"from": "InfOut.then_0", "to": "NoticeIn.execute"},
    {"from": "CX_1.SizeX",    "to": "InfSizeX.InInt"},
    {"from": "CX_1.SizeY",    "to": "InfSizeY.InInt"}
  ]
}
```

- `file` paths are relative to the manifest.
- `offset` is optional. Without it, the paste goes below the live graph.
- `replace: true` removes the old link first, on both nodes. You need it when an exec **output** or a data **input**
  is already linked, because those pins hold only 1 link.

## What the tool does NOT do (you still need the editor)

- **New variables, components, functions, macros, event dispatchers, custom event inputs.** A paste only holds
  nodes. Create these first, with the `create_*.py` editor scripts or by hand. Otherwise the pasted nodes come in
  red or empty.
- **Compiling.** The tool checks links, not types. A link from `int` to `string` passes the check but fails the
  compile.
- **Pin layouts.** If a node's pins in the paste don't match the engine (a wrong function signature, or a
  `self` pin that is missing), the editor fixes or drops them on paste. Use right-click -> Refresh Node, then
  compile.
- **Other graphs.** One manifest = one graph (usually EventGraph). Function graphs are exported and merged one at a
  time.
- **Note on NodeGuids** (not a limit): the editor gives every node a new NodeGuid on paste. That's fine, because the
  tool matches nodes by PinId. An `offset` is used only when a paste is really added.

## Tests

```
cd applyall
python3 -m unittest -v
```

24 tests with small made-up graphs. One test uses the real `nh2.t3d` / `nh3.t3d` exports when they exist (and is
skipped when they don't).

## Rule for AGENTS.md

> Every Blueprint hand-off ships a `manifest.json` (format: `tools/applyall/manifest_schema.md`) next to its paste
> files, one per target graph, and `applyall.py merge --dry-run` against the latest export must print
> `Validation: OK`.
