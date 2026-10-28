#!/usr/bin/env node
// Desk tick: update YOUR live desk. Tick on events: when you start a task, finish one, get blocked, and at least every
// 25 minutes while you work (a desk with no tick for 30 minutes shows offline).
//
//   node tools/tick.js --seat "hossam gmail (Claude)" --start --tokens 123456 --working "Fixing the cafe bubbles"   (session start)
//   node tools/tick.js --seat "hossam gmail (Claude)" --tokens 130000 --done "Cafe bubbles fixed" --working "Next card"
//
// Numbers come from your get_usage tool (context.tokensUsed, plan windows).
//   --tokens N            context tokens used this session        --ctx N        context window (default 1000000)
//   --working "text"      what you are doing now (spins your ring) --idle         clear it
//   --done "text"         finished task, added to your last-10 list (needs --tokens: rule 6)
//   --todo "text"         add to your still-to-do list            --todo-done "text"  remove it from the list
//   --plan Max --h5 PCT --h5reset ISO --wk PCT --wkreset ISO      plan meters (account-wide)
//   --ask "text"          you are blocked on the owner (paste, approval): rings a bell on your desk
//   --ask-clear           the owner did it, clear the bell
//   --start / --since ISO a new session takes the seat (duty clock starts now / at ISO)
//   --take-over           take the seat although another session still holds it (only if that session is really gone)
//   --dry-run             show the new desk, write nothing
//
// Where it goes: desks/<seat>.json on the repo's "desks" branch, written through the GitHub API (your gh login), so
// ticks never touch data.js or the main history and two agents never conflict. The office page and office.js read it.
// Seat lock: the desk remembers which machine + session holds it. While that desk is live (ticked < 30 min ago), a tick
// from another machine or another session is refused, so two sessions can't both be "you".
'use strict';
const fs = require('fs'), os = require('os'), path = require('path'), crypto = require('crypto');
const desks = require('./desks');

const opt = {};
for (let a = process.argv.slice(2), i = 0; i < a.length; i++) {
  if (!a[i].startsWith('--')) continue;
  const k = a[i].slice(2), v = a[i + 1] !== undefined && !a[i + 1].startsWith('--') ? a[++i] : true;
  opt[k] = v;
}
const die = m => { console.error('tick: ' + m); process.exit(1); };
if (typeof opt.seat !== 'string') die('--seat "<your seat name>" is required');
const seat = opt.seat, now = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
const num = (k, lo, hi) => { const n = Number(opt[k]); if (!Number.isFinite(n) || n < lo || n > hi) die('--' + k + ' must be a number'); return n; };
const iso = k => { const d = new Date(opt[k]); if (isNaN(d)) die('--' + k + ' must be a date like 2026-10-27T15:10:00Z'); return d.toISOString().replace(/\.\d{3}Z$/, 'Z'); };

// ---- this machine's session for the seat (local, git-ignored) ----
const sessFile = path.join(__dirname, '.session-' + desks.slug(seat) + '.json');
let sess = null;
try { sess = JSON.parse(fs.readFileSync(sessFile, 'utf8')); } catch {}
const starting = !!(opt.start || opt.since !== undefined || !sess);
if (starting) sess = { id: crypto.randomBytes(6).toString('hex'), host: os.hostname(), started: now };

function apply(c) {
  c = Object.assign({ working: '', tokens: 0, ctx: 1000000, since: now, done: [], todo: [] }, c || {});
  // seat lock
  const held = c.session, live = desks.online(c);
  if (held && held.id !== sess.id && live && !opt['take-over'])
    die('seat "' + seat + '" is held by another session (' + held.host + ', session ' + held.id + ', last tick ' + desks.ago(c.asOf) + ' ago).\n'
      + '      Two sessions must not share a desk. If that session is really gone, run again with --take-over.');
  if (held && held.id !== sess.id) console.log('tick: taking the seat over from ' + held.host + ' (' + (live ? 'live, --take-over' : 'offline since ' + desks.ago(c.asOf)) + ')');
  if (starting || (held && held.id !== sess.id)) c.since = opt.since !== undefined ? iso('since') : now;
  c.session = { id: sess.id, host: sess.host };
  if (opt.tokens !== undefined) c.tokens = Math.round(num('tokens', 0, 1e9));
  if (opt.ctx !== undefined) c.ctx = Math.round(num('ctx', 1, 1e9));
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
    const old = c.usage || { meters: [] }, m = k => (old.meters || []).find(x => x.k === k) || {};
    c.usage = { who: seat, plan: typeof opt.plan === 'string' ? opt.plan : old.plan || '', asOf: now, meters: [
      { k: '5h', label: 'Session (5-hour)', pct: opt.h5 !== undefined ? num('h5', 0, 100) : m('5h').pct || 0, resetsAt: opt.h5reset ? iso('h5reset') : m('5h').resetsAt || '', color: '#59bda5' },
      { k: 'wk', label: 'Weekly (all models)', pct: opt.wk !== undefined ? num('wk', 0, 100) : m('wk').pct || 0, resetsAt: opt.wkreset ? iso('wkreset') : m('wk').resetsAt || '', color: '#d9af65' }] };
  }
  c.asOf = now;
  return c;
}

let c;
try {
  c = desks.update(seat, cur => apply(cur || desks.legacy(seat)), opt['dry-run'] ? { dry: true } : {});
} catch (e) { die(e.message); }
if (!opt['dry-run']) try { fs.writeFileSync(sessFile, JSON.stringify(sess)); } catch {}
console.log('tick: ' + seat + ' · ' + c.tokens + ' tok (' + Math.max(0, 100 - Math.round(100 * c.tokens / c.ctx)) + '% left) · ' + (c.working || 'idle')
  + (opt['dry-run'] ? ' (dry run, nothing written)' : ' · saved'));
if (opt['dry-run']) console.log(JSON.stringify(c, null, 1));
