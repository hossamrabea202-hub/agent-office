// Live desks: one small JSON file per seat (desks/<slug>.json) on the repo's "desks" branch, read and written through
// the GitHub API with the agent's gh login. Keeps desk ticks out of data.js and the main history, and per-seat files
// mean two agents never conflict. Used by tick.js, office.js and watch.js; the office page reads the same files.
'use strict';
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const REPO = 'hossamrabea202-hub/agent-office', BRANCH = 'desks', DIR = 'desks', ONLINE_MS = 30 * 60e3;
const root = path.join(__dirname, '..');

const slug = seat => String(seat).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
const online = c => !!c && !!c.asOf && Date.now() - new Date(c.asOf) < ONLINE_MS;
const ago = t => { const m = Math.max(0, Math.round((Date.now() - new Date(t)) / 6e4)); return m < 60 ? m + 'm' : m < 1440 ? Math.round(m / 60) + 'h' : Math.round(m / 1440) + 'd'; };
const gh = (args, input) => execFileSync('gh', args, { cwd: root, encoding: 'utf8', input, stdio: [input === undefined ? 'ignore' : 'pipe', 'pipe', 'pipe'], maxBuffer: 16 << 20 });
const notFound = e => /HTTP 404|Not Found/i.test(String(e.stderr || e.message));

// The seat's old line in data.js (before live desks existed): the starting point of its first live desk.
function legacy(seat) {
  try { const w = {}; new Function('window', fs.readFileSync(path.join(root, 'data.js'), 'utf8'))(w); return ((w.OFFICE || {}).crew || {})[seat] || null; }
  catch { return null; }
}
function getRaw(seat) {
  try {
    const r = JSON.parse(gh(['api', 'repos/' + REPO + '/contents/' + DIR + '/' + slug(seat) + '.json?ref=' + BRANCH]));
    return { sha: r.sha, desk: JSON.parse(Buffer.from(r.content, 'base64').toString('utf8')) };
  } catch (e) { if (notFound(e)) return { sha: null, desk: null }; throw new Error('reading the desk failed: ' + String(e.stderr || e.message).slice(0, 300)); }
}
const get = seat => getRaw(seat).desk;
// All live desks as { seat: desk }.
function list() {
  let files;
  try { files = JSON.parse(gh(['api', 'repos/' + REPO + '/contents/' + DIR + '?ref=' + BRANCH])); }
  catch (e) { if (notFound(e)) return {}; throw e; }
  const out = {};
  for (const f of files.filter(f => f.name.endsWith('.json'))) {
    try { const d = JSON.parse(Buffer.from(JSON.parse(gh(['api', f.url.replace('https://api.github.com/', '')])).content, 'base64').toString('utf8')); if (d && d.seat) out[d.seat] = d; } catch {}
  }
  return out;
}
// Read-modify-write one seat's desk; retries when another write landed in between (sha changed).
function update(seat, fn, { dry = false } = {}) {
  for (let i = 0; i < 4; i++) {
    const { sha, desk } = getRaw(seat);
    const next = fn(desk ? JSON.parse(JSON.stringify(desk)) : null);
    next.seat = seat;
    if (dry) return next;
    const body = { message: 'desk: ' + seat + ' · ' + (next.working || 'idle').slice(0, 60), branch: BRANCH,
      content: Buffer.from(JSON.stringify(next, null, 1) + '\n').toString('base64') };
    if (sha) body.sha = sha;
    try { gh(['api', '-X', 'PUT', 'repos/' + REPO + '/contents/' + DIR + '/' + slug(seat) + '.json', '--input', '-'], JSON.stringify(body)); return next; }
    catch (e) { if (!/HTTP 409|HTTP 422|does not match/i.test(String(e.stderr || e.message)) || i === 3) throw new Error('saving the desk failed: ' + String(e.stderr || e.message).slice(0, 300)); }
  }
}
module.exports = { REPO, BRANCH, DIR, slug, online, ago, legacy, get, list, update };
