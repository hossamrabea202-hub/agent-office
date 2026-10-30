# manifest.json format

One manifest = one Blueprint graph (one live export). It is a JSON object.

| Key | Needed? | Meaning |
|---|---|---|
| `blueprint` | yes (recommended) | Blueprint name, e.g. `"BP_NoticeHUD"`. The tool checks it against the `ExportPath` in the live file, so you cannot merge into the wrong Blueprint. |
| `pastes` | no | List of paste files to add. Each item is a file name, or an object (see below). |
| `rewires` | no | List of link changes, done in order, after the pastes. |
| `_...` / `note` | no | Keys that start with `_`, and `note`, are ignored. Use them for comments. |

## `pastes` items

```json
"pastes": [
  "NoticeHUD_Infection_graph.txt",
  {"file": "Other_graph.txt", "offset": [2000, 0]}
]
```

- `file`: path **relative to the manifest file**. An absolute path also works.
- `offset`: `[dx, dy]` or `{"dx": .., "dy": ..}`, added to every `NodePosX` / `NodePosY` of the paste.
  When there is no offset, the paste goes **below** the live graph: its left edge lines up with the live graph's left edge,
  and its top is 600 units below the lowest live node.

What happens to each paste:

| Situation | Result |
|---|---|
| None of its nodes are in live | The nodes are added. A node whose name is already used gets a new name (`CX_5` -> `CX_5_m1`), and every link inside the paste is updated. The renames are printed. |
| All of its nodes are already in live | Nothing is added (it was merged before). Only the rewires run. |
| Some nodes are in live, some are not | Error. Clean up first. |

"Already in live" means: the same `NodeGuid`, **or** the node's `PinId`s are found on one live node of the same class.
`PinId`s are the main key. When you paste, the editor gives every node a **new** `NodeGuid` but keeps the `PinId`s
and names. The editor can also rebuild a hidden pin (for example `self`) with a new `PinId`, so most of the pins
matching is enough.

## `rewires` items

```json
{"from": "CX_208.then", "to": "InfIn.execute", "replace": true, "note": "was -> NoticeIn"}
```

| Key | Meaning |
|---|---|
| `from` | `Node.Pin`, normally an **output** pin (`then`, `ReturnValue`, `SizeX`...). |
| `to` | `Node.Pin`, normally an **input** pin (`execute`, `A`, `InInt`...). If you write it backwards, the tool swaps it and prints a note. |
| `replace` | `true`: first remove the old links of the "one link only" end (an exec **output**, or a data **input**). The link is removed on **both** nodes. `false` (default): if that end already has a link, stop with an error. |
| `unlink` | `true`: remove the link `from` - `to` instead of adding it. |
| `note` | Free text. |

Pin names:
- `Node` is the node `Name="..."` from the T3D, e.g. `CX_208` or `K2Node_IfThenElse_ZX12`. For a node from a paste,
  use the name **in the paste file**. If the tool renamed it, it finds the new name for you.
- `Pin` is the `PinName`, e.g. `then`, `else`, `then_0`, `execute`, `ReturnValue`, or a name with spaces like
  `AsPlayer Controller`. A 32-character `PinId` also works.
- If a node has two pins with the same name, add `@in` or `@out` (`Knot.InputPin@in`) or use the PinId.
- If a name is both a live node and a renamed paste node, write `live:CX_5.then` or `new:CX_5.then`.

Rules:
- An exec **output** holds 1 link. An exec **input** can hold many.
- A data **input** holds 1 link. A data **output** can hold many.
- If the link is already there, nothing happens ("already linked"). So running the same manifest twice is safe.

## Checks before writing

The tool writes nothing if any of these fail:
- every `LinkedTo` points to a node and pin that exist
- every link is stored on both ends
- the one-link rule above holds
- no two pins share a `PinId`, and no two nodes share a name
- no link joins two outputs or two inputs
- the change in `LinkedTo` entries = 2 x (net new links)

The live file and each paste file are checked first, on their own.

## Full example

```json
{
  "blueprint": "BP_NoticeHUD",
  "pastes": [
    {"file": "NoticeHUD_Infection_graph.txt"}
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
