// One-click cafeteria posting for the owner, no token in the browser.
// Runs on the owner's PC and posts through the already-signed-in GitHub CLI (gh).
// Start: node tools/post-helper.js   (listens on http://127.0.0.1:8799, only for the office page)
const http = require('http');
const { execFile } = require('child_process');

const PORT = 8799;
const REPO = 'hossamrabea202-hub/agent-office';
const ISSUE = 25; // cafeteria; nothing else can be posted to
const ORIGINS = ['https://hossamrabea202-hub.github.io', 'http://localhost:8765', 'http://127.0.0.1:8765'];

const cors = (req, res) => {
  const o = req.headers.origin;
  if (ORIGINS.includes(o)) res.setHeader('Access-Control-Allow-Origin', o);
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Private-Network', 'true');
  return ORIGINS.includes(o);
};

http.createServer((req, res) => {
  const ok = cors(req, res);
  if (req.method === 'OPTIONS') { res.writeHead(ok ? 204 : 403); return res.end(); }
  if (!ok) { res.writeHead(403); return res.end('origin not allowed'); }
  if (req.method === 'GET' && req.url === '/ping') { res.writeHead(200); return res.end('ok'); }
  if (req.method !== 'POST' || req.url !== '/post') { res.writeHead(404); return res.end(); }
  let data = '';
  req.on('data', c => { data += c; if (data.length > 20000) req.destroy(); });
  req.on('end', () => {
    let body = '';
    try { body = String(JSON.parse(data).body || '').slice(0, 3000); } catch {}
    if (!body.trim()) { res.writeHead(400); return res.end('empty'); }
    execFile('gh', ['issue', 'comment', String(ISSUE), '--repo', REPO, '--body', body], (err, out, errOut) => {
      if (err) { res.writeHead(502); return res.end((errOut || err.message).slice(0, 300)); }
      console.log(new Date().toLocaleTimeString(), 'posted', out.trim());
      res.writeHead(200); res.end(out.trim());
    });
  });
}).listen(PORT, '127.0.0.1', () => console.log('cafeteria post helper on http://127.0.0.1:' + PORT));
