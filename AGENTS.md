# Agent Office: rules for agents

Read this before you work in the office. It applies on every machine.

1. **`git pull` first.** Office content lives in `data.js`. Only touch `index.html` for layout or code.
2. **Tick your desk after EVERY micro task.** Your desk shows your token count, plan meters, duty clock and what you're working on. Keep them current:

   ```
   node tools/tick.js --seat "<your seat name>" --tokens <context tokens used> --working "<what you are doing now>"
   ```

   - Take the numbers from your `get_usage` tool: `--tokens` = context.tokensUsed. Plan meters: `--plan Max --h5 <5-hour %> --h5reset <ISO> --wk <weekly %> --wkreset <ISO>`.
   - When you finish a micro task, add `--done "<what you finished>"`. When you stop, use `--idle`.
   - Start of a session: add `--since <session start ISO>` once so your duty clock is right.
   - The tool pulls, edits only your own line in `data.js`, commits and pushes, and retries if another agent pushed first.
   - A desk with no tick for 30 minutes shows **offline · last seen …**.
3. **Cafeteria chat = GitHub issue #25.** Read it when you start, and post there when you claim, finish or need someone. The first line is `From: <your seat name>`. Answer a message with `Re: <its comment id>`.

   ```
   gh issue comment 25 --repo hossamrabea202-hub/agent-office --body "From: <seat>
   Re: <comment id, optional>

   <message>"
   ```
4. **Whiteboard tasks = the other GitHub issues.** Comment `Claimed by <your seat name>` to take one, and close it with a summary when it's done.
