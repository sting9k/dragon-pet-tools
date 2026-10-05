// Renders Spine 4.1 models of the asset pack to pictures and pose data, in headless Chrome.
//   node spine/render.mjs --sheet out.png DIR [filter] [cell] [cols] [bare]   contact sheet of every model under DIR
//                                             (bare: transparent ground and no captions)
//   node spine/render.mjs --rig out.json MODEL [cell]                  the posed parts of one model, for rig_skin.py
//   node spine/render.mjs --strip out.png MODEL ANIM [frames] [cell] [fitA,fitB]   one animation as a strip of frames
//   node spine/render.mjs --bones out.json MODEL [ANIM] [at]           the skeleton's bones and slots in one pose
//   node spine/render.mjs --aim out.png MODEL ANIM at BONE deg0 deg1 [frames] [cell] [tipX,tipY]   one pose, a bone turned step by step
// DIR and MODEL are relative to the pack's spine folder; MODEL has no extension.
// Environment:
//   ASSETS_DIR     folder holding pack/spine (default: ../../assets from this tools folder)
//   SPINE_OVERLAY  folder whose files replace the pack's files of the same path, e.g. a pet with a redrawn skin
//   CHROME         path of the Chrome or Chromium binary, when it is not in a usual place
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';

const here = path.dirname(fileURLToPath(import.meta.url));
const tools = path.resolve(here, '..');
const SPINE = path.resolve(process.env.ASSETS_DIR ?? path.join(tools, '../../assets'), 'pack/spine');
const OVERLAY = process.env.SPINE_OVERLAY ? path.resolve(process.env.SPINE_OVERLAY) : null;
const RUNTIME = path.join(tools, 'node_modules/@esotericsoftware/spine-webgl/dist/iife/spine-webgl.js');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.atlas': 'text/plain', '.txt': 'text/plain', '.json': 'application/json' };
const BROWSERS = {
  darwin: ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium'],
  linux: ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'],
  win32: ['C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'],
};

const USAGE = fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').filter(l => l.startsWith('//')).map(l => l.slice(3)).join('\n');
const args = process.argv.slice(2);
if (!['--sheet', '--rig', '--strip', '--bones', '--aim'].includes(args[0])) { console.error(USAGE); process.exit(1); }
if (!fs.existsSync(SPINE)) { console.error(`no asset pack at ${SPINE}; set ASSETS_DIR`); process.exit(1); }
const chrome = process.env.CHROME ?? (BROWSERS[process.platform] ?? []).find(p => fs.existsSync(p));
if (!chrome) { console.error('Chrome not found; set CHROME to its binary'); process.exit(1); }

// a path asked for under /spine/ resolves inside the overlay or the pack, never outside them
function spineFile(rel) {
  for (const base of OVERLAY ? [OVERLAY, SPINE] : [SPINE]) {
    const file = path.resolve(base, rel);
    if (file.startsWith(base + path.sep) && fs.existsSync(file)) return file;
  }
  return null;
}

const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  const file = url === '/' ? path.join(here, 'render.html') : url === '/spine-webgl.js' ? RUNTIME : url.startsWith('/spine/') ? spineFile(url.slice(7)) : null;
  if (!file || !fs.existsSync(file)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': MIME[path.extname(file)] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise(r => server.listen(0, '127.0.0.1', r));

const browser = await puppeteer.launch({ executablePath: chrome, headless: true, args: ['--ignore-gpu-blocklist', '--enable-webgl', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage();
page.on('pageerror', e => console.error('[page]', e.message));
await page.goto(`http://127.0.0.1:${server.address().port}/`);
await page.evaluate(() => init());

const savePng = (file, dataUrl) => {
  fs.mkdirSync(path.dirname(path.resolve(file)), { recursive: true });
  fs.writeFileSync(file, Buffer.from(dataUrl.split(',')[1], 'base64'));
};
const saveJson = (file, data, indent) => fs.writeFileSync(file, JSON.stringify(data, null, indent));

// every .skel under `dir` that has an .atlas beside it is one model
function findModels(dir) {
  const out = [];
  const walk = d => {
    const ents = fs.readdirSync(d, { withFileTypes: true });
    for (const e of ents) if (e.isDirectory()) walk(path.join(d, e.name));
    for (const e of ents) {
      if (!e.name.endsWith('.skel')) continue;
      const base = path.relative(SPINE, path.join(d, e.name)).replace(/\.skel$/, '');
      if (fs.existsSync(path.join(SPINE, base + '.atlas'))) out.push({ id: path.basename(base), base });
    }
  };
  walk(path.join(SPINE, dir));
  return out;
}

const modes = {
  async '--sheet'(outFile, dir, filter = '-', cell = '150', cols = '8', bare = '') {
    let models = findModels(dir);
    if (filter !== '-') { const re = new RegExp(filter); models = models.filter(m => re.test(m.id)); }
    const r = await page.evaluate((m, c, k, b) => sheet(m, c, k, b), models, +cell, +cols, bare === 'bare');
    savePng(outFile, r.png);
    saveJson(outFile.replace(/\.png$/, '.json'), r.info);
    return `${models.length} models`;
  },
  async '--rig'(outFile, base, cell = '640') {
    saveJson(outFile, await page.evaluate((c, k) => rig(c, k), { base }, +cell));
  },
  async '--strip'(outFile, base, anim, frames = '8', cell = '320', fit = '') {
    savePng(outFile, await page.evaluate((c, a, n, k, f) => strip(c, a, n, k, f), { base }, anim, +frames, +cell, fit ? fit.split(',') : []));
  },
  async '--bones'(outFile, base, anim = 'idle', at = '0') {
    saveJson(outFile, await page.evaluate((c, a, t) => bones(c, a, t), { base }, anim, +at), 1);
  },
  async '--aim'(outFile, base, anim, at, bone, deg0, deg1, frames = '9', cell = '320', tip = '0,0') {
    const r = await page.evaluate((c, a, t, b, d0, d1, n, k, p) => aim(c, a, t, b, d0, d1, n, k, p), { base }, anim, +at, bone, +deg0, +deg1, +frames, +cell, tip.split(',').map(Number));
    savePng(outFile, r.png);
    saveJson(outFile.replace(/\.png$/, '.json'), { tips: r.tips, scale: r.scale, origin: r.origin });
  },
};

try {
  const note = await modes[args[0]](...args.slice(1));
  console.log(`${args[0].slice(2)}${note ? ': ' + note : ''} -> ${args[1]}`);
} catch (e) {
  console.error(e.code === 'ENOENT' ? `not found: ${e.path}` : e.message);
  process.exitCode = 1;
} finally {
  await browser.close();
  server.close();
}
