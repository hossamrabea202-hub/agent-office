#!/usr/bin/env node
// Desk tick: update YOUR live numbers in data.js and push. Run it after EVERY micro task.
//
//   node tools/tick.js --seat "hossam gmail (Claude)" --tokens 123456 --working "Fixing the cafe bubbles"
//
// Numbers come from your get_usage tool (context.tokensUsed, plan windows).
//   --tokens N            context tokens used this session        --ctx N        context window (default 1000000)
//   --working "text"      what you are doing now (spins your ring) --idle         clear it
//   --done "text"         finished micro task, added to your last-10 list
//   --todo "text"         add to your still-to-do list            --todo-done "text"  remove it from the list
//   --plan Max --h5 PCT --h5reset ISO --wk PCT --wkreset ISO      plan meters (account-wide)
//   --ask "text"          you are blocked on the owner (paste, approval): rings a bell on your desk
//   --ask-clear           the owner did it, clear the bell
//   --since ISO           duty start (once per session)           --no-push      edit data.js only
//   --trailer "..."       extra commit trailer line (e.g. a Co-Authored-By line)
// Each agent has its own line in the crew block, so ticks from different agents merge cleanly.
'use strict';
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const root = path.join(__dirname, '..'), file = path.join(root, 'data.js');

const opt = {};
for (let a = process.argv.slice(2), i = 0; i < a.length; i++) {
  if (!a[i].startsWith('--')) continue;
  const k = a[i].slice(2), v = a[i + 1] !== undefined && !a[i + 1].startsWith('--') ? a[++i] : true;
  opt[k] = v;
}
const die = m => { console.error('tick: ' + m); process.exit(1); };
if (typeof opt.seat !== 'string') die('--seat "<your seat name>" is required');
const git = (...a) => execFileSync('git', a, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
const lit = v => typeof v === 'string' ? "'" + v.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\r?\n/g, '\\n') + "'"
  : Array.isArray(v) ? '[' + v.map(lit).join(',') + ']'
  : v && typeof v === 'object' ? '{' + Object.entries(v).map(([k, x]) => (/^[A-Za-z_$][\w$]*$/.test(k) ? k : lit(k)) + ':' + lit(x)).join(',') + '}'
  : JSON.stringify(v);
const num = (k, lo, hi) => { const n = Number(opt[k]); if (!Number.isFinite(n) || n < lo || n > hi) die('--' + k + ' must be a number'); return n; };
const iso = k => { const d = new Date(opt[k]); if (isNaN(d)) die('--' + k + ' must be a date like 2026-10-27T15:10:00Z'); return d.toISOString().replace(/\.\d{3}Z$/, 'Z'); };

function edit() {
  const src = fs.readFileSync(file, 'utf8'), w = {};
  new Function('window', src)(w);
  const crew = w.OFFICE.crew || {}, now = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
  const c = Object.assign({ working: '', tokens: 0, ctx: 1000000, since: now, done: [], todo: [] }, crew[opt.seat]);
  if (opt.tokens !== undefined) c.tokens = Math.round(num('tokens', 0, 1e9));
  if (opt.ctx !== undefined) c.ctx = Math.round(num('ctx', 1, 1e9));
  if (opt.since !== undefined) c.since = iso('since');
  if (typeof opt.working === 'string') c.working = opt.working;
  if (opt.idle) c.working = '';
  // RULE 6 (owner, 2026-10-27): every finished task registers how much of your token budget is left.
  if (typeof opt.done === 'string' && opt.tokens === undefined) die('--done needs --tokens (rule 6: register % tokens left after each task)');
  const leftPct = () => Math.max(0, 100 - Math.round(100 * c.tokens / c.ctx)), h5 = opt.h5 !== undefined ? ' · 5h plan ' + Math.max(0, 100 - num('h5', 0, 100)) + '% left' : '';
  if (typeof opt.done === 'string') { const d = opt.done + ' [' + leftPct() + '% tokens left' + h5 + ']'; c.done = [d, ...(c.done || []).filter(t => t !== d)].slice(0, 10); }
  if (typeof opt.todo === 'string' && !(c.todo || []).includes(opt.todo)) c.todo = [...(c.todo || []), opt.todo];
  if (typeof opt['todo-done'] === 'string') c.todo = (c.todo || []).filter(t => t !== opt['todo-done']);
  if (typeof opt.ask === 'string') c.ask = { text: opt.ask, at: now };
  if (opt['ask-clear']) delete c.ask;
  if (opt.h5 !== undefined || opt.wk !== undefined) {
    const old = c.usage || w.OFFICE.usage || { meters: [] }, m = k => (old.meters || []).find(x => x.k === k) || {};
    c.usage = { who: opt.seat, plan: typeof opt.plan === 'string' ? opt.plan : old.plan || '', asOf: now, meters: [
      { k: '5h', label: 'Session (5-hour)', pct: opt.h5 !== undefined ? num('h5', 0, 100) : m('5h').pct || 0, resetsAt: opt.h5reset ? iso('h5reset') : m('5h').resetsAt || '', color: '#59bda5' },
      { k: 'wk', label: 'Weekly (all models)', pct: opt.wk !== undefined ? num('wk', 0, 100) : m('wk').pct || 0, resetsAt: opt.wkreset ? iso('wkreset') : m('wk').resetsAt || '', color: '#d9af65' }] };
  }
  c.asOf = now;
  const eol = src.includes('\r\n') ? '\r\n' : '\n', lines = src.split(/\r?\n/), start = lines.findIndex(l => l.startsWith('crew:{'));
  if (start < 0 || lines[start] !== 'crew:{') die('data.js crew block not found (expected a line "crew:{")');
  const end = lines.findIndex((l, i) => i > start && l === '},');
  const line = lit(opt.seat) + ':' + lit(c) + ',', at = lines.findIndex((l, i) => i > start && i < end && l.startsWith(lit(opt.seat) + ':'));
  if (at >= 0) lines[at] = line; else lines.splice(end, 0, '// ---- ' + opt.seat, line);
  const out = lines.join(eol);
  new Function('window', out)({});  // still valid JavaScript
  fs.writeFileSync(file, out);
  return c;
}

try { git('pull', '--rebase', '--autostash', '-q'); } catch (e) { die('git pull failed, fix the repo first:\n' + e.stderr); }
const c = edit();
console.log('tick: ' + opt.seat + ' · ' + c.tokens + ' tok (' + Math.max(0, 100 - Math.round(100 * c.tokens / c.ctx)) + '% left) · ' + (c.working || 'idle'));
if (opt['no-push']) process.exit(0);
const msg = 'tick: ' + opt.seat + ' · ' + Math.round(c.tokens / 1000) + 'k tok · ' + (c.working || 'idle').slice(0, 60)
  + (typeof opt.trailer === 'string' ? '\n\n' + opt.trailer : '');
git('commit', '-q', '-m', msg, '--', 'data.js');
for (let i = 0; ; i++) {
  try { git('push', '-q', 'origin', 'HEAD'); console.log('tick: pushed'); break; }
  catch (e) {
    if (i >= 3) die('push failed:\n' + e.stderr);
    try { git('pull', '--rebase', '-q'); } catch (e2) { die('rebase failed (someone edited your line?):\n' + e2.stderr); }
  }
}
