# Agent Office: rules for agents

Read this before you work in the office. It applies on every machine.

**checkking starting fresh (new machine / new session)?** Read `handoffs/checkking-session/HANDOFF.md` first.

**Office page (live, for everyone):** https://hossamrabea202-hub.github.io/agent-office/ (the banner at the top links it; its text and link live in `banner` in `data.js`).

1. **Only the Master Agent touches the Unreal editor.** The Castle Defender project is open on the owner's PC with the latest work saved, and only the Master Agent (desk #0, now `hossam gmail (Claude)`) drives it. Everyone else works in the background and produces things the Master can apply: T3D graph pastes, editor Python scripts, assets to import, written steps. Don't paste, run editor scripts, save assets or start PIE yourself. Hand the work over instead:

   ```
   node tools/office.js handoff --seat "<seat>" --target "BP_X · EventGraph" --file "handoffs/<task>/<file>" --checks "<what to verify>" "<title>" "<details>"
   ```

   - Put your files in this repo under `handoffs/<task>/`, so the Master's PC can reach them.
   - It shows up in the READY TO PASTE room and in the cafeteria. The Master pastes, compiles, saves, checks and closes it, or answers in the cafeteria if something needs fixing.
   - Blueprints keep changing, so build graph pastes on a fresh export. **Ask for it with a request** (rule 4b): `node tools/office.js request --seat "<seat>" --kind export --target "BP_X" "title" "details"`. It lands in `handoffs/exports/`.
2. **`git pull` first.** Office content lives in `data.js`. Only touch `index.html` for layout or code. Desk ticks no longer touch `data.js` (rule 3).
3. **Tick your desk on events** (owner, 2026-10-28; replaces "after every micro task"): when you **start** a task, **finish** one, get **blocked**, and at least **every 25 minutes** while you work. Your desk shows your token count, plan meters, duty clock and what you're working on:

   ```
   node tools/tick.js --seat "<your seat name>" --start --tokens <context tokens used> --working "<first task>"      (once, at session start)
   node tools/tick.js --seat "<your seat name>" --tokens <context tokens used> --done "<finished>" --working "<next>"
   ```

   - Take the numbers from your `get_usage` tool: `--tokens` = context.tokensUsed. Plan meters: `--plan Max --h5 <5-hour %> --h5reset <ISO> --wk <weekly %> --wkreset <ISO>`. When you stop, use `--idle`.
   - Desks live in `desks/<seat>.json` on the repo's **`desks` branch**, written through the GitHub API: no `data.js` edit, no commit on main, no push collisions. The page and `office.js` read them (the page every 30 s).
   - **One session per seat.** The desk remembers which machine and session holds it. While it's live (ticked < 30 min ago), a tick from another machine or a new session is **refused**. Start every session with `--start`; if the tool says the seat is held and that old session is really gone, add `--take-over`. Never run two sessions as the same seat.
   - A desk with no tick for 30 minutes shows **offline · last seen …**.
   - **Blocked on the owner** (a Blueprint paste, an approval, a decision)? Add `--ask "<what you need>"`. A bell rings on your desk and in the header. Clear it with `--ask-clear` once it's done.
4. **Start every session with your briefing.** It shows only what's **new since your last inbox**: cafeteria lines (`>>` = for you), new comments on **your cards**, open requests, your tasks, and who is waiting on the owner. `--all` shows the last 15 cafeteria lines instead.

   ```
   node tools/office.js inbox --seat "<your seat name>"
   node tools/office.js say   --seat "<seat>" [--re <comment id>] "message"           team-wide news, blockers, @mentions
   node tools/office.js say   --seat "<seat>" --card <issue> "message"                talk about one card ON that card
   node tools/office.js claim <issue> --seat "<seat>"
   node tools/office.js close <issue> --seat "<seat>" "what you did"
   ```

   `claim` and `close` also post one line in the cafeteria.

   **4b. Need something from the editor (export, paste, play-test)? File a request**, don't just ask in the chat:

   ```
   node tools/office.js request --seat "<seat>" --kind export|paste|playtest|other --target "<asset / BP / level>" [--file "<where the result goes>"] "title" "details"
   ```

   It becomes an issue labelled `request`, shows in the READY TO PASTE room and at the top of the Master's and Vice's inbox (oldest first). If no editor driver is online, your desk bell rings so the owner sees it. **Editor drivers clear the request queue at the start of every editor session**; static-mesh exports go in one run with `tools/ue_export_meshes.py`. Work on another card while you wait.
5. **Cafeteria chat = GitHub issue #25: team-wide only.** Post there when you claim, finish, hand off, get blocked or need someone (`@<seat>`). Discussion about one card goes **on that card** (`say --card <n>`), not in the cafeteria. The first line is `From: <your seat name>`. Answer a message with `Re: <its comment id>`.

   ```
   gh issue comment 25 --repo hossamrabea202-hub/agent-office --body "From: <seat>
   Re: <comment id, optional>

   <message>"
   ```
6. **Whiteboard tasks = the other GitHub issues.** Comment `Claimed by <your seat name>` to take one, and close it with a summary when it's done.
7. **How the page stays live.** The page re-checks `data.js` and `index.html` every 5 s. The whiteboard and chat come from `board.json`, which `.github/workflows/board.yml` (running `tools/mirror.js`) rewrites after every issue or comment, about a minute behind GitHub. Never commit `board.json` yourself. Desks come from the `desks` branch (raw files, re-read every 30 s).

## Non-stop rule: decide yourself (owner's rule, 2026-10-28)

The owner wants agents working until their tokens run out, not stopping after a few minutes to ask.

1. **Work the whiteboard queue in order**: quick fixes, then medium cards, then large ones. When a card is done (built, tested, saved), close it with a summary, tick your desk and take the next card. No asking in between.
2. **Unclear point? Decide.** Pick the sensible default, write `Decision: ...` on the card, keep going. The owner reviews results, not questions.
3. **Only these stop work:** spending money, deleting the owner's data, overwriting the owner's save game, or a hard blocker only the owner can clear. Then tick `--ask "..."` (desk bell) and switch to another card while you wait.
4. **New owner comments go onto the whiteboard first** as cards, then into the queue.
5. **Before your tokens or plan run out**, leave a handoff note on the card you're in the middle of, so the next agent continues without asking.
6. **Report on events, not on a clock** (owner, 2026-10-28; replaces the 10-minute report). The page shows every desk live, so: post in the cafeteria when you **finish** a card or hand-off (what, where, % tokens left), when you are **blocked**, and when you **hand off**. Keep the watcher running (below) and read your inbox when it notifies you or when you start a new card. No "still working" reports.
7. **Send screenshots to the SCREENSHOTS section** (owner, 2026-10-28) when a card is finished or a visible result is ready to judge (not every step): `node tools/shot.js --seat "<your seat>" --file <image> --caption "<what it shows>" --card <issue number>`. Keep images around 1280-1600 px wide.

## No-traffic hand-off protocol (owner's rule, 2026-10-27)

1. **The Master answers every hand-off in the cafeteria twice:** "Pasting <job>" when starting, and the result when done (pass or fail, and what got fixed). The Master's desk `working` names the job in progress, so nobody has to ask.
2. **Exports come in the format the requester names.** The default is the graph copied in the editor (Ctrl+A, Ctrl+C) saved as `.txt`, one file per graph, in `handoffs/exports/<task>/`. The Master confirms the paths in the cafeteria.
3. **No blind pastes.** Ask for the export first. The README of every hand-off names the export it was built on.
4. **Say when you are blocked.** File a request (rule 4b) or post `@<name> waiting on: <what>` in the cafeteria, and tick with `--working "waiting on <name>: <what>"`, so the owner sees it on your desk. Then take another card.
5. **Tick on events** (rule 3): start, done, blocked, and at least every 25 minutes. A desk older than 30 minutes shows offline, and a stale desk looks like idle work.
6. **After each task, register how much of your tokens is left** (owner rule, 2026-10-27). Finish every task with a tick that has `--done "<task>" --tokens <context.tokensUsed>` plus your plan meters (`--h5 <5-hour %>`); tick.js stamps the task with `[N% tokens left · 5h plan M% left]` and refuses `--done` without `--tokens`. Your desk shows `N% left` next to the token count. Put the same numbers in your cafeteria report.
6. **Reassignments get written down.** When the owner moves a task, the receiver comments `Claimed by <seat>` on the issue and posts one line in the cafeteria, so the board and the desks agree.

## Notifications between agents

Run a watcher for your seat while you work; it checks the office every 5 minutes and alerts you (console line `NOTIFY ...` + Windows toast) about NEW @mentions/replies, new comments on your cards, new hand-offs for you, and (Master / Vice) new requests. It doesn't mark anything read, so your inbox still shows them as new:

```
node tools/watch.js --seat "<your seat>" --every 5
```

In Claude Code, start it in the background (or a terminal tab) at session start and react to each `NOTIFY` line. To ping someone, mention them: `node tools/office.js say --seat "<you>" "@<their seat> <message>"`. `--once` = single check (first run lists everything already there; state is kept in `tools/.watch-<seat>.json`).
