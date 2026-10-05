// Baut den Ordner www/ für die App aus src/game.html:
//  - three.js kommt lokal aus node_modules (kein Internet nötig)
//  - Schriften kommen lokal aus @fontsource (falls installiert)
//  - vollständiges HTML-Dokument mit Handy-Viewport (kein Zoomen, Notch/Kamera-Loch beachtet)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const p = (...a) => path.join(root, ...a);
const www = p('www');
fs.rmSync(www, { recursive: true, force: true });
fs.mkdirSync(p('www', 'vendor'), { recursive: true });

let html = fs.readFileSync(p('src', 'game.html'), 'utf8');

// 1) three.js lokal
const threeSrc = p('node_modules', 'three', 'build', 'three.module.js');
if (!fs.existsSync(threeSrc)) { console.error('three.js fehlt – bitte zuerst "npm install" ausführen.'); process.exit(1); }
fs.copyFileSync(threeSrc, p('www', 'vendor', 'three.module.js'));
const cdn = /https:\/\/cdn\.jsdelivr\.net\/npm\/three@[\d.]+\/build\/three\.module\.js/g;
if (!cdn.test(html)) console.warn('Hinweis: three.js-Import nicht gefunden.');
html = html.replace(cdn, './vendor/three.module.js');

// 2) Schriften lokal
const fonts = [
  ['Nunito', 'nunito', [600, 700, 800, 900]],
  ['Young Serif', 'young-serif', [400]],
];
let css = '', okFonts = true;
fs.mkdirSync(p('www', 'fonts'), { recursive: true });
const RANGES = {
  'latin': 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD',
  'latin-ext': 'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF',
  'cyrillic': 'U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116',
  'cyrillic-ext': 'U+0460-052F,U+1C80-1C8A,U+20B4,U+2DE0-2DFF,U+A640-A69F,U+FE2E-FE2F',
};
for (const [family, pkg, weights] of fonts) for (const w of weights) for (const sub of Object.keys(RANGES)) {
  const f = `${pkg}-${sub}-${w}-normal.woff2`, src = p('node_modules', '@fontsource', pkg, 'files', f);
  if (!fs.existsSync(src)) { if (sub === 'latin') okFonts = false; continue; }
  fs.copyFileSync(src, p('www', 'fonts', f));
  css += `@font-face{font-family:'${family}';font-style:normal;font-weight:${w};font-display:swap;src:url(./${f}) format('woff2');unicode-range:${RANGES[sub]}}\n`;
}
if (okFonts) {
  fs.writeFileSync(p('www', 'fonts', 'fonts.css'), css);
  html = html.replace(/<link rel="preconnect"[^>]*>\s*/g, '').replace(/<link rel="stylesheet" href="https:\/\/fonts\.googleapis\.com[^>]*>/, '<link rel="stylesheet" href="fonts/fonts.css">');
} else console.warn('Hinweis: lokale Schriften nicht gefunden – es werden Google Fonts aus dem Internet geladen.');

// 3) Sichere Ränder (Notch, Gestenleiste) – Capacitor liefert --safe-area-inset-* als Variablen
html = html.replace(/env\(safe-area-inset-(top|right|bottom|left),\s*0px\)/g, 'var(--safe-area-inset-$1, env(safe-area-inset-$1, 0px))');

// 4) App-Dateien
for (const f of ['online-config.js', 'app-shell.js']) fs.copyFileSync(p('src', f), p('www', f));
const i = html.indexOf('<script type="module">');
if (i < 0) { console.error('Spielcode nicht gefunden'); process.exit(1); }
html = html.slice(0, i) + '<script src="online-config.js"></script>\n<script src="app-shell.js"></script>\n' + html.slice(i);

const head = `<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="theme-color" content="#2c3a22">
<meta name="format-detection" content="telephone=no">
`;
fs.writeFileSync(p('www', 'index.html'), head + html + '\n</html>\n');
console.log(`www/ fertig: index.html ${(Buffer.byteLength(html) / 1024).toFixed(0)} KB, three.js lokal, Schriften ${okFonts ? 'lokal' : 'online'}.`);
