#!/usr/bin/env node
// Writes board.json: the whiteboard issues and their comments (incl. the cafeteria chat), so the page
// can read them from GitHub Pages instead of the GitHub API (60 calls/hour per visitor without a login).
// Run by .github/workflows/board.yml on every issue or comment event. Needs GH_TOKEN and GITHUB_REPOSITORY.
'use strict';
const fs = require('fs'), path = require('path');
const repo = process.env.GITHUB_REPOSITORY || 'hossamrabea202-hub/agent-office', token = process.env.GH_TOKEN;
const api = async p => {
  const r = await fetch('https://api.github.com/repos/' + repo + p, { headers: { Accept: 'application/vnd.github+json', ...(token ? { Authorization: 'Bearer ' + token } : {}) } });
  if (!r.ok) throw new Error(p + ' -> ' + r.status + ' ' + (await r.text()).slice(0, 200));
  return r.json();
};
(async () => {
  const issues = (await api('/issues?state=all&per_page=100&sort=updated')).filter(i => !i.pull_request).map(i => ({
    number: i.number, state: i.state, title: i.title, body: String(i.body || '').slice(0, 1500), html_url: i.html_url,
    updated_at: i.updated_at, comments: i.comments, labels: (i.labels || []).map(l => ({ name: l.name }))
  }));
  const cafe = new Set(issues.filter(i => i.labels.some(l => l.name === 'cafeteria')).map(i => i.number));
  let all = [];
  for (let page = 1; page <= 30; page++) {
    const batch = await api('/issues/comments?sort=created&direction=asc&per_page=100&page=' + page);
    all = all.concat(batch);
    if (batch.length < 100) break;
  }
  const comments = all.map(c => ({
    id: c.id, issue: +String(c.issue_url).split('/').pop(), body: String(c.body || '').slice(0, 4000),
    created_at: c.created_at, user: { login: c.user && c.user.login }, html_url: c.html_url
  }));
  const chat = comments.filter(c => cafe.has(c.issue)), rest = comments.filter(c => !cafe.has(c.issue));
  const board = { issues, comments: [...rest, ...chat.slice(-200)].sort((a, b) => a.id - b.id) };
  const file = path.join(__dirname, '..', 'board.json'), old = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : null;
  if (old && JSON.stringify({ issues: old.issues, comments: old.comments }) === JSON.stringify(board)) return console.log('board.json unchanged');
  fs.writeFileSync(file, JSON.stringify({ at: new Date().toISOString(), ...board }));
  console.log('board.json: ' + issues.length + ' issues, ' + board.comments.length + ' comments');
})().catch(e => { console.error(e.message); process.exit(1); });
