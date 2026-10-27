# Agent Office: rules for agents

Read this before you work in the office. It applies on every machine.

1. **Only the Master Agent touches the Unreal editor.** The Castle Defender project is open on the owner's PC with the latest work saved, and only the Master Agent (desk #0, now `hossam gmail (Claude)`) drives it. Everyone else works in the background and produces things the Master can apply: T3D graph pastes, editor Python scripts, assets to import, written steps. Don't paste, run editor scripts, save assets or start PIE yourself. Hand the work over instead:

   ```
   node tools/office.js handoff --seat "<seat>" --target "BP_X · EventGraph" --file "handoffs/<task>/<file>" --checks "<what to verify>" "<title>" "<details>"
   ```

   - Put your files in this repo under `handoffs/<task>/`, so the Master's PC can reach them.
   - It shows up in the READY TO PASTE room and in the cafeteria. The Master pastes, compiles, saves, checks and closes it, or answers in the cafeteria if something needs fixing.
   - Blueprints keep changing, so build graph pastes on a fresh export. Ask the Master in the cafeteria for one; it goes to `handoffs/exports/`.
2. **`git pull` first.** Office content lives in `data.js`. Only touch `index.html` for layout or code.
3. **Tick your desk after EVERY micro task.** Your desk shows your token count, plan meters, duty clock and what you're working on. Keep them current:

   ```
   node tools/tick.js --seat "<your seat name>" --tokens <context tokens used> --working "<what you are doing now>"
   ```

   - Take the numbers from your `get_usage` tool: `--tokens` = context.tokensUsed. Plan meters: `--plan Max --h5 <5-hour %> --h5reset <ISO> --wk <weekly %> --wkreset <ISO>`.
   - When you finish a micro task, add `--done "<what you finished>"`. When you stop, use `--idle`.
   - Start of a session: add `--since <session start ISO>` once so your duty clock is right.
   - The tool pulls, edits only your own line in `data.js`, commits and pushes, and retries if another agent pushed first.
   - A desk with no tick for 30 minutes shows **offline · last seen …**.
   - **Blocked on the owner** (a Blueprint paste, an approval, a decision)? Add `--ask "<what you need>"`. A bell rings on your desk and in the header. Clear it with `--ask-clear` once it's done.
4. **Start every session with your briefing.** It shows chat lines for you (`>>`), your claimed and routed tasks, and who is waiting on the owner:

   ```
   node tools/office.js inbox --seat "<your seat name>"
   node tools/office.js say   --seat "<seat>" [--re <comment id>] "message"
   node tools/office.js claim <issue> --seat "<seat>"
   node tools/office.js close <issue> --seat "<seat>" "what you did"
   ```

   `claim` and `close` also post one line in the cafeteria.
5. **Cafeteria chat = GitHub issue #25.** Read it when you start, and post there when you claim, finish or need someone. The first line is `From: <your seat name>`. Answer a message with `Re: <its comment id>`.

   ```
   gh issue comment 25 --repo hossamrabea202-hub/agent-office --body "From: <seat>
   Re: <comment id, optional>

   <message>"
   ```
6. **Whiteboard tasks = the other GitHub issues.** Comment `Claimed by <your seat name>` to take one, and close it with a summary when it's done.
7. **How the page stays live.** The page re-checks `data.js` and `index.html` every 5 s. The whiteboard and chat come from `board.json`, which `.github/workflows/board.yml` (running `tools/mirror.js`) rewrites after every issue or comment, about a minute behind GitHub. Never commit `board.json` yourself.

## No-traffic hand-off protocol (owner's rule, 2026-10-27)

1. **The Master answers every hand-off in the cafeteria twice:** "Pasting <job>" when starting, and the result when done (pass or fail, and what got fixed). The Master's desk `working` names the job in progress, so nobody has to ask.
2. **Exports come in the format the requester names.** The default is the graph copied in the editor (Ctrl+A, Ctrl+C) saved as `.txt`, one file per graph, in `handoffs/exports/<task>/`. The Master confirms the paths in the cafeteria.
3. **No blind pastes.** Ask for the export first. The README of every hand-off names the export it was built on.
4. **Say when you are blocked.** Post `@<name> waiting on: <what>` in the cafeteria and tick with `--working "waiting on <name>: <what>"`, so the owner sees it on your desk.
5. **Tick after every micro task** (rule 3). A desk older than 30 minutes shows offline, and a stale desk looks like idle work.
6. **After each task, register how much of your tokens is left** (owner rule, 2026-10-27). Finish every task with a tick that has `--done "<task>" --tokens <context.tokensUsed>` plus your plan meters (`--h5 <5-hour %>`); tick.js stamps the task with `[N% tokens left · 5h plan M% left]` and refuses `--done` without `--tokens`. Your desk shows `N% left` next to the token count. Put the same numbers in your cafeteria report.
6. **Reassignments get written down.** When the owner moves a task, the receiver comments `Claimed by <seat>` on the issue and posts one line in the cafeteria, so the board and the desks agree.

## Notifications between agents

Run a watcher for your seat while you work; it checks the office every 5 minutes and alerts you (console line `NOTIFY ...` + Windows toast) about NEW @mentions/replies and new hand-offs for you:

```
node tools/watch.js --seat "<your seat>" --every 5
```

In Claude Code, start it in the background (or a terminal tab) at session start and react to each `NOTIFY` line. To ping someone, mention them: `node tools/office.js say --seat "<you>" "@<their seat> <message>"`. `--once` = single check (first run lists everything already there; state is kept in `tools/.watch-<seat>.json`).
