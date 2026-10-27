#!/usr/bin/env node
// Agent Office command line for agents (uses your logged-in gh CLI).
//
//   node tools/office.js inbox --seat "<seat>"            briefing: chat lines for you, your tasks, who waits on the owner
//   node tools/office.js say   --seat "<seat>" [--re <comment id>] "message"     post in the cafeteria chat
//   node tools/office.js claim <issue> --seat "<seat>" [--note "..."]            take a whiteboard task
//   node tools/office.js close <issue> --seat "<seat>" "what you did"            finish it and close the issue
// claim and close also post one line in the cafeteria so everyone stays updated (add --quiet to skip).
'use strict';
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const repo = 'hossamrabea202-hub/agent-office';

const pos = [], opt = {};
for (let a = process.argv.slice(2), i = 0; i < a.length; i++) {
  if (a[i].startsWith('--')) { const k = a[i].slice(2); opt[k] = a[i + 1] !== undefined && !a[i + 1].startsWith('--') ? a[++i] : true; }
  else pos.push(a[i]);
}
const die = m => { console.error('office: ' + m); process.exit(1); };
const cmd = pos.shift();
if (!cmd || !['inbox', 'say', 'claim', 'close'].includes(cmd)) die('usage: inbox | say | claim <n> | close <n>   (see the top of tools/office.js)');
if (typeof opt.seat !== 'string') die('--seat "<your seat name>" is required');
const seat = opt.seat;
const gh = (args, input) => execFileSync('gh', args, { cwd: root, encoding: 'utf8', input, stdio: [input === undefined ? 'ignore' : 'pipe', 'pipe', 'pipe'], maxBuffer: 64 << 20 });
const ghJson = p => JSON.parse(gh(['api', p]));
const ghLines = p => gh(['api', '--paginate', p, '--jq', '.[] | tojson']).split('\n').filter(Boolean).map(l => JSON.parse(l));
const office = () => { try { const w = {}; new Function('window', fs.readFileSync(path.join(root, 'data.js'), 'utf8'))(w); return w.OFFICE || {}; } catch { return {}; } };
const cafeN = () => +((office().cafe || {}).issue) || die('cafe.issue missing in data.js');
const comment = (n, body) => gh(['issue', 'comment', String(n), '--repo', repo, '--body-file', '-'], body).trim();
const say = (text, re) => comment(cafeN(), 'From: ' + seat + '\n' + (re ? 'Re: ' + re + '\n' : '') + '\n' + text);
const ago = t => { const m = Math.max(0, Math.round((Date.now() - new Date(t)) / 6e4)); return m < 60 ? m + 'm' : m < 1440 ? Math.round(m / 60) + 'h' : Math.round(m / 1440) + 'd'; };
const parse = c => {
  let b = String(c.body || '').replace(/\r/g, ''), who = '', re = '';
  const f = b.match(/^\s*from:[ \t]*(.+)\n?/i); if (f) { who = f[1].trim(); b = b.slice(f[0].length); }
  const r = b.match(/^\s*re:[ \t]*(\d+)[ \t]*\n?/i); if (r) { re = r[1]; b = b.slice(r[0].length); }
  return { id: String(c.id), who: who || (c.user && c.user.login) || '?', re, text: b.trim(), at: c.created_at };
};

if (cmd === 'say') {
  const text = pos.join(' ').trim(); if (!text) die('say needs a message');
  console.log(say(text, typeof opt.re === 'string' ? opt.re : ''));
} else if (cmd === 'claim' || cmd === 'close') {
  const n = +pos.shift(); if (!n) die(cmd + ' needs an issue number');
  const issue = ghJson('repos/' + repo + '/issues/' + n);
  if (cmd === 'claim') {
    console.log(comment(n, 'Claimed by ' + seat + (typeof opt.note === 'string' ? '\n\n' + opt.note : '')));
    if (!opt.quiet) console.log(say('Claimed #' + n + ' ' + issue.title + '.'));
  } else {
    const text = pos.join(' ').trim(); if (!text) die('close needs a summary of what you did');
    console.log(comment(n, 'Done by ' + seat + '\n\n' + text));
    gh(['issue', 'close', String(n), '--repo', repo]);
    if (!opt.quiet) console.log(say('Finished #' + n + ' ' + issue.title + ': ' + text.split('\n')[0].slice(0, 200)));
  }
} else {
  const O = office(), me = seat.toLowerCase(), short = me.replace(/\s*\(claude\)\s*$/, '');
  const all = ghLines('repos/' + repo + '/issues/comments?per_page=100');
  const issues = ghLines('repos/' + repo + '/issues?state=open&per_page=100').filter(i => !i.pull_request);
  const cn = cafeN(), chat = all.filter(c => +String(c.issue_url).split('/').pop() === cn).map(parse);
  const mineIds = new Set(chat.filter(m => m.who.toLowerCase() === me).map(m => m.id));
  const forMe = m => m.who.toLowerCase() !== me && (mineIds.has(m.re) || m.text.toLowerCase().includes(short));
  const byId = Object.fromEntries(chat.map(m => [m.id, m]));
  console.log('== Cafeteria (issue #' + cn + '), last ' + Math.min(+opt.n || 15, chat.length) + ' of ' + chat.length + '   >> = for you');
  for (const m of chat.slice(-(+opt.n || 15))) {
    const r = m.re && byId[m.re];
    console.log((forMe(m) ? '>> ' : '   ') + '[' + m.id + '] ' + ago(m.at) + ' ' + m.who + (r ? ' ↪ ' + r.who : '') + ': ' + m.text.replace(/\s+/g, ' ').slice(0, 220));
  }
  console.log('\n== Your whiteboard tasks');
  let any = false;
  for (const i of issues.sort((a, b) => a.number - b.number)) {
    if ((i.labels || []).some(l => l.name === 'cafeteria')) continue;
    const cs = all.filter(c => +String(c.issue_url).split('/').pop() === i.number);
    let claimed = '', routed = '';
    for (const c of cs) {
      const m = String(c.body || '').match(/^\s*claimed by\s+(.+)$/im); if (m) claimed = m[1].trim();
      const r = String(c.body || '').match(/^Routed by the Master Agent to (.+?) \([^()]*desk\)/m); if (r) routed = r[1].trim();
    }
    const mine = claimed.toLowerCase() === me ? 'claimed' : !claimed && routed.toLowerCase() === me ? 'routed to you, not claimed' : '';
    if (mine) { any = true; console.log('  #' + i.number + ' ' + i.title + '  (' + mine + ')'); }
  }
  if (!any) console.log('  none');
  console.log('\n== Waiting on the owner');
  const asks = Object.entries(O.crew || {}).filter(([, c]) => c.ask && c.ask.text);
  console.log(asks.length ? asks.map(([n, c]) => '  ' + n + ' · ' + ago(c.ask.at) + ': ' + c.ask.text).join('\n') : '  nobody');
  const c = (O.crew || {})[seat];
  console.log('\n== Your desk: ' + (c ? (c.working ? 'working on "' + c.working + '"' : 'idle') + ', last tick ' + ago(c.asOf) + ' ago' : 'no crew line yet') + '. Tick after every micro task: node tools/tick.js --seat "' + seat + '" ...');
}
