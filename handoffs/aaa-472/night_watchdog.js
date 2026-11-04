// Alien's overnight order (2026-11-03): "wake up other agents and make sure each one works nonstop". Token-free watchdog:
// every 30 min, read the fast chat; an agent with no real line (auto temp lines and stale auto-ticks don't count) for 60+ min
// gets one nudge, at most once an hour. Runs 8 h, then exits. Usage: node night_watchdog.js [hours=8]
const http = require('http');
const HOST = '100.87.149.123', PORT = 8765;
const AGENTS = ['i9', 'TGA_PC', 'TGA1', 'TGA'];
const req = (method, path, body) => new Promise((res, rej) => {
  const r = http.request({ host: HOST, port: PORT, path, method, timeout: 20000, headers: body ? { 'Content-Length': Buffer.byteLength(body), 'Content-Type': 'text/plain' } : {} }, m => { let d = ''; m.on('data', c => d += c); m.on('end', () => res(d)); });
  r.on('error', rej); r.on('timeout', () => r.destroy(new Error('timeout'))); if (body) r.write(body); r.end();
});
const lastNudge = {}; const start = Date.now(); const HOURS = +process.argv[2] || 8;
let after = 0; const lastSeen = {};
async function tick() {
  try {
    const txt = await req('GET', '/read?after=' + after);
    for (const line of txt.split('\n')) {
      const m = line.match(/^(\d+)\|[\d:]+\|﻿?From: ([A-Za-z0-9_]+)[ :]/); if (!m) { const n = line.match(/^(\d+)\|/); if (n) after = Math.max(after, +n[1]); continue; }
      after = Math.max(after, +m[1]);
      if (/i9 temp|tick - i9 status/.test(line)) continue;
      lastSeen[m[2]] = Date.now();
    }
    for (const a of AGENTS) {
      const seen = lastSeen[a] || start, nudged = lastNudge[a] || 0;
      if (Date.now() - seen > 60 * 60e3 && Date.now() - nudged > 60 * 60e3) {
        lastNudge[a] = Date.now();
        const said = await req('POST', '/say', 'From: i5: @' + a + ' watchdog: no report from you for 60+ min. Alien\'s overnight order (1273): non-stop, work your queue, decide yourself, take the next open card (#461 harmony, #472, the whiteboard). Post one line when you resume, or a hand-off note if you are out of tokens.');
        console.log(new Date().toISOString(), 'nudged', a, 'server:', said.slice(0, 20));   // log what the server answered: v1 logged success while every POST was dropped
      }
    }
  } catch (e) { console.log(new Date().toISOString(), 'chat error', e.message); }
  if (Date.now() - start > HOURS * 3600e3) { console.log('watchdog done', JSON.stringify(lastSeen)); process.exit(0); }
}
tick(); setInterval(tick, 30 * 60e3);
