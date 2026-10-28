#!/usr/bin/env node
// Post a screenshot to the office SCREENSHOTS section (owner's rule, 2026-10-28) and push.
//   node tools/shot.js --seat "vice master (Claude)" --file C:/path/shot.png --caption "What it shows" [--card 79]
// The image is copied to shots/<date>-<slug>.<ext>; data.js gets a line in the shots:[ block (newest first, last 60 shown).
// Keep files small (a 1280-1600 px wide PNG/JPG is plenty).
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const root = path.resolve(__dirname, '..'), file = path.join(root, 'data.js');
const opt = {};
for (let a = process.argv.slice(2), i = 0; i < a.length; i++) {
  if (!a[i].startsWith('--')) continue;
  const k = a[i].slice(2), v = a[i + 1] !== undefined && !a[i + 1].startsWith('--') ? a[++i] : true;
  opt[k] = v;
}
const die = m => { console.error('shot: ' + m); process.exit(1); };
if (typeof opt.seat !== 'string') die('--seat "<your seat name>" is required');
if (typeof opt.file !== 'string' || !fs.existsSync(opt.file)) die('--file <existing image> is required');
if (typeof opt.caption !== 'string') die('--caption "<what it shows>" is required');
const ext = path.extname(opt.file).toLowerCase();
if (!['.png', '.jpg', '.jpeg', '.webp'].includes(ext)) die('image must be png, jpg or webp');
const git = (...a) => execFileSync('git', a, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
const lit = s => "'" + String(s).replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/\r?\n/g, ' ') + "'";

try { git('pull', '--rebase', '--autostash', '-q'); } catch (e) { die('git pull failed, fix the repo first:\n' + e.stderr); }
const now = new Date(), at = now.toISOString().replace(/\.\d{3}Z$/, 'Z');
const slug = opt.caption.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'shot';
const name = 'shots/' + at.replace(/[-:]/g, '').replace('T', '-').replace('Z', '') + '-' + slug + ext;
fs.mkdirSync(path.join(root, 'shots'), { recursive: true });
fs.copyFileSync(opt.file, path.join(root, name));

const src = fs.readFileSync(file, 'utf8'), eol = src.includes('\r\n') ? '\r\n' : '\n', lines = src.split(/\r?\n/);
const start = lines.findIndex(l => l === 'shots:[');
if (start < 0) die('data.js shots block not found (expected a line "shots:[")');
const card = opt.card !== undefined && opt.card !== true ? Number(String(opt.card).replace('#', '')) : 0;
lines.splice(start + 1, 0, '{f:' + lit(name) + ',t:' + lit(opt.caption) + ',who:' + lit(opt.seat) + ',at:' + lit(at) + (card ? ',card:' + card : '') + '},');
const out = lines.join(eol);
new Function('window', out)({});  // still valid JavaScript
fs.writeFileSync(file, out);
git('add', '--', name, 'data.js');
git('commit', '-q', '-m', 'shot: ' + opt.seat + ' · ' + opt.caption.slice(0, 70));
for (let i = 0; ; i++) {
  try { git('push', '-q', 'origin', 'HEAD'); console.log('shot: pushed ' + name); break; }
  catch (e) {
    if (i >= 3) die('push failed:\n' + e.stderr);
    try { git('pull', '--rebase', '-q'); } catch (e2) { die('rebase failed:\n' + e2.stderr); }
  }
}
