#!/usr/bin/env node
// Agent Studio command line for agents (uses your logged-in gh CLI).
//
//   node tools/office.js inbox --seat "<seat>" [--all] [--n 15]   briefing: only what is NEW since your last inbox (cafeteria lines,
//        comments on your cards, requests), your tasks, who waits on the owner. --all = the last n cafeteria lines as before.
//   node tools/office.js say   --seat "<seat>" [--re <comment id>] [--card <issue>] "message"
//        post in the cafeteria chat; with --card the message goes on that card instead (card talk stays on the card)
//   node tools/office.js request --seat "<seat>" --kind export|paste|playtest|other --target "<asset / BP / level>"
//        [--file "<where the result should go>"] "title" ["details"]    ask the editor driver (Master / Vice) for something
//   node tools/office.js claim <issue> --seat "<seat>" [--note "..."]            take a whiteboard task
//   node tools/office.js close <issue> --seat "<seat>" "what you did"            finish it and close the issue
//   node tools/office.js handoff --seat "<seat>" --target "BP_X · EventGraph" --file "<path>" [--kind paste|python|asset|manual]
//        [--checks "what to verify after"] "title" ["details"]     hand Unreal editor work to the Master Agent
// Only the Master Agent drives the Unreal editor. Everyone else hands editor work over with "handoff"; it shows up in the
// READY TO PASTE room and the Master closes it once it is pasted and checked.
// Requests (exports, pastes, play-tests) are queued as issues labelled "request": they show in the READY TO PASTE room and at the
// top of the Master's and Vice's inbox. If no editor driver is online, the requester's desk bell rings so the owner sees it.
// claim, close, handoff and request also post one line in the cafeteria so everyone stays updated (add --quiet to skip).
'use strict';
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const root = path.join(__dirname, '..');
const repo = 'hossamrabea202-hub/agent-office';
const desks = require('./desks');

const pos = [], opt = {};
for (let a = process.argv.slice(2), i = 0; i < a.length; i++) {
  if (a[i].startsWith('--')) { const k = a[i].slice(2); opt[k] = a[i + 1] !== undefined && !a[i + 1].startsWith('--') ? a[++i] : true; }
  else pos.push(a[i]);
}
const die = m => { console.error('office: ' + m); process.exit(1); };
const cmd = pos.shift();
if (!cmd || !['inbox', 'say', 'claim', 'close', 'handoff', 'request'].includes(cmd)) die('usage: inbox | say | claim <n> | close <n> | handoff | request   (see the top of tools/office.js)');
if (typeof opt.seat !== 'string') die('--seat "<your seat name>" is required');
const seat = opt.seat;
const gh = (args, input) => execFileSync('gh', args, { cwd: root, encoding: 'utf8', input, stdio: [input === undefined ? 'ignore' : 'pipe', 'pipe', 'pipe'], maxBuffer: 64 << 20 });
const ghJson = p => JSON.parse(gh(['api', p]));
const ghLines = p => gh(['api', '--paginate', p, '--jq', '.[] | tojson']).split('\n').filter(Boolean).map(l => JSON.parse(l));
const office = () => { try { const w = {}; new Function('window', fs.readFileSync(path.join(root, 'data.js'), 'utf8'))(w); return w.OFFICE || {}; } catch { return {}; } };
// crew = data.js lines overlaid with the live desks (newer copy wins)
const crewLive = O => { const crew = Object.assign({}, O.crew || {}); try { for (const [s, d] of Object.entries(desks.list())) if (!crew[s] || new Date(d.asOf || 0) > new Date(crew[s].asOf || 0)) crew[s] = d; } catch {} return crew; };
const editors = O => [...new Set(Object.entries(O.preset || {}).filter(([d]) => d === '0' || d === '15').map(([, s]) => s))];
const fromOf = i => ((String(i.body || '').match(/^From:[ \t]*(.+)$/m) || [])[1] || '').trim();
const esc = t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
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

const master = () => Object.entries((office().preset || {})).find(([d]) => d === '0')?.[1] || 'the Master Agent';
if (cmd === 'say') {
  const text = pos.join(' ').trim(); if (!text) die('say needs a message');
  if (opt.card) console.log(comment(+opt.card || die('--card needs an issue number'), 'From: ' + seat + '\n\n' + text));
  else console.log(say(text, typeof opt.re === 'string' ? opt.re : ''));
} else if (cmd === 'request') {
  const title = (pos.shift() || '').trim(); if (!title) die('request needs a title');
  if (typeof opt.target !== 'string') die('--target "<asset / Blueprint / level>" is required');
  const kind = typeof opt.kind === 'string' ? opt.kind : 'export';
  const body = 'From: ' + seat + '\nTarget: ' + opt.target + '\nKind: ' + kind + '\nFile: ' + (typeof opt.file === 'string' ? opt.file : '-')
    + '\n\n' + (pos.join(' ').trim() || '(no details)')
    + '\n\n---\nRequest for the editor driver (Master or Vice). Do it, reply here with where the result is, and close the issue.'
    + (kind === 'export' ? '\nStatic meshes: tools/ue_export_meshes.py exports a list of assets to FBX in one go.' : '');
  try { gh(['label', 'create', 'request', '--repo', repo, '--color', 'd9af65', '--description', 'Request for the Unreal editor driver']); } catch {}
  const url = gh(['issue', 'create', '--repo', repo, '--label', 'request', '--title', title, '--body-file', '-'], body).trim();
  console.log(url);
  const O = office(), crew = crewLive(O), on = editors(O).filter(e => desks.online(crew[e]));
  if (!on.length) {
    try {
      desks.update(seat, c => Object.assign(c || desks.legacy(seat) || {}, { ask: { text: 'No editor driver online: ' + title + ' (' + url + ')', at: new Date().toISOString().replace(/\.\d{3}Z$/, 'Z') } }));
      console.log('office: no editor driver online, your desk bell rings for the owner');
    } catch {}
  }
  if (!opt.quiet) console.log(say('Request for ' + (on.length ? on.join(' / ') : 'the editor driver (none online, bell rung)') + ': ' + title + ' (' + kind + ', ' + opt.target + ') ' + url));
} else if (cmd === 'handoff') {
  const title = (pos.shift() || '').trim(); if (!title) die('handoff needs a title');
  if (typeof opt.target !== 'string') die('--target "<Blueprint / asset / level the Master works in>" is required');
  const kind = typeof opt.kind === 'string' ? opt.kind : 'paste';
  if (kind === 'paste' && typeof opt.file !== 'string') die('--file "<path to the paste text>" is required for a paste');
  const body = 'From: ' + seat + '\nTarget: ' + opt.target + '\nKind: ' + kind + '\nFile: ' + (typeof opt.file === 'string' ? opt.file : '-')
    + '\nChecks: ' + (typeof opt.checks === 'string' ? opt.checks : '-') + '\n\n' + (pos.join(' ').trim() || '(no details)')
    + '\n\n---\nHand-off for the Master Agent (the only seat that drives the Unreal editor). The Master closes this once it is pasted and checked.';
  const url = gh(['issue', 'create', '--repo', repo, '--label', 'handoff', '--title', title, '--body-file', '-'], body).trim();
  console.log(url);
  if (!opt.quiet) console.log(say('Hand-off for ' + master() + ': ' + title + ' (' + opt.target + ') ' + url));
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
  const stFile = path.join(__dirname, '.inbox-' + desks.slug(seat) + '.json');
  let st = { last: 0 }; try { st = JSON.parse(fs.readFileSync(stFile, 'utf8')); } catch {}
  const isNew = m => +m.id > +st.last, showAll = opt.all || !st.last;
  const lines = showAll ? chat.slice(-(+opt.n || 15)) : chat.filter(m => isNew(m) && m.who.toLowerCase() !== me);
  console.log('== Cafeteria (issue #' + cn + '): ' + (showAll ? 'last ' + lines.length + ' of ' + chat.length : lines.length + ' new since your last inbox (--all for the last 15)') + '   >> = for you');
  for (const m of lines) {
    const r = m.re && byId[m.re];
    console.log((forMe(m) ? '>> ' : '   ') + '[' + m.id + '] ' + ago(m.at) + ' ' + m.who + (r ? ' ↪ ' + r.who : '') + ': ' + m.text.replace(/\s+/g, ' ').slice(0, 220));
  }
  if (!showAll && !lines.length) console.log('   nothing new');
  console.log('');
  // comments on your cards (claimed by you, or hand-offs / requests you filed) since your last inbox
  const claimRe = new RegExp('^\\s*claimed by\\s+' + esc(seat) + '\\s*$', 'im');
  const issueOf = c => +String(c.issue_url).split('/').pop();
  const myCards = new Set(issues.filter(i => fromOf(i).toLowerCase() === me || all.some(c => issueOf(c) === i.number && claimRe.test(String(c.body || '')))).map(i => i.number));
  const cardNew = all.filter(c => myCards.has(issueOf(c)) && +c.id > +(st.last || 0) && parse(c).who.toLowerCase() !== me && !/^\s*claimed by/i.test(String(c.body || '')));
  console.log('== New on your cards');
  console.log(st.last && cardNew.length ? cardNew.map(c => { const m = parse(c); return '>> #' + issueOf(c) + ' [' + m.id + '] ' + ago(m.at) + ' ' + m.who + ': ' + m.text.replace(/\s+/g, ' ').slice(0, 220); }).join('\n') : '  none');
  console.log('');
  // requests for the editor driver (oldest first)
  const reqs = issues.filter(i => (i.labels || []).some(l => l.name === 'request')).sort((a, b) => a.number - b.number);
  const isEditor = editors(O).map(e => e.toLowerCase()).includes(me);
  const myReqs = isEditor ? reqs : reqs.filter(i => fromOf(i).toLowerCase() === me);
  const tgt = i => ((String(i.body || '').match(/^Target:[ \t]*(.+)$/m) || [])[1] || '').trim();
  console.log(isEditor ? '== Requests waiting for you in the editor (oldest first)' : '== Your open requests to the editor driver');
  console.log(myReqs.length ? myReqs.map(i => '  #' + i.number + ' ' + i.title + '  · ' + tgt(i) + (isEditor ? '  · from ' + fromOf(i) : '') + '  · ' + ago(i.created_at) + ' ago').join('\n') : '  none');
  console.log('');
  const hand =issues.filter(i => (i.labels || []).some(l => l.name === 'handoff')).sort((a, b) => a.number - b.number);
  const isMaster = master().toLowerCase() === me, from = i => ((String(i.body || '').match(/^From:[ \t]*(.+)$/m) || [])[1] || '').trim();
  const target = i => ((String(i.body || '').match(/^Target:[ \t]*(.+)$/m) || [])[1] || '').trim();
  const mineH = isMaster ? hand : hand.filter(i => from(i).toLowerCase() === me);
  console.log(isMaster ? '== Hand-offs waiting for you in the editor' : '== Your hand-offs waiting for the Master (' + master() + ')');
  console.log(mineH.length ? mineH.map(i => '  #' + i.number + ' ' + i.title + '  · ' + target(i) + (isMaster ? '  · from ' + from(i) : '') + '  · ' + ago(i.created_at) + ' ago').join('\n') : '  none');
  if (isMaster) {
    const ready = (O.pasteJobs || []).filter(j => j.s === 'ready');
    console.log('== Ready in the paste queue (data.js pasteJobs)');
    console.log(ready.length ? ready.map(j => '  ' + j.t + '  · ' + j.bp + '  · ' + j.file).join('\n') : '  none');
  }
  console.log('\n== Your whiteboard tasks');
  let any = false;
  for (const i of issues.sort((a, b) => a.number - b.number)) {
    if ((i.labels || []).some(l => l.name === 'cafeteria' || l.name === 'handoff' || l.name === 'request')) continue;
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
  const crew = crewLive(O), asks = Object.entries(crew).filter(([, c]) => c.ask && c.ask.text);
  console.log(asks.length ? asks.map(([n, c]) => '  ' + n + ' · ' + ago(c.ask.at) + ': ' + c.ask.text).join('\n') : '  nobody');
  const c = crew[seat], held = c && c.session;
  console.log('\n== Your desk: ' + (c ? (c.working ? 'working on "' + c.working + '"' : 'idle') + ', last tick ' + ago(c.asOf) + ' ago' + (held ? ' · held by ' + held.host + (desks.online(c) ? ' (live)' : ' (offline)') : '') : 'no desk yet')
    + '. Tick on events (start, done, blocked; at least every 25 min): node tools/tick.js --seat "' + seat + '" ...');
  if (!opt['no-mark']) { const top = all.length ? Math.max(...all.map(x => +x.id)) : 0; try { fs.writeFileSync(stFile, JSON.stringify({ last: top, at: new Date().toISOString() })); } catch {} }
}
