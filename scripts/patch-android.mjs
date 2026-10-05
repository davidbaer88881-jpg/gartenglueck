// Passt das Android-Projekt nach "npx cap add android" / "npx cap sync" an:
//  - Ziel-API 36 (Pflicht im Play Store ab 31.08.2026), minSdk 24
//  - Versionsnummer aus package.json (version + androidVersionCode)
//  - Bildschirm-Ausrichtung (androidOrientation in package.json)
//  - Bildschirm bleibt beim Spielen an, Hardware-Beschleunigung an
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const A = (...a) => path.join(root, 'android', ...a);
const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
if (!fs.existsSync(A())) { console.error('Ordner android/ fehlt – zuerst "npx cap add android".'); process.exit(1); }
const edit = (file, fn) => { if (!fs.existsSync(file)) { console.warn('fehlt:', file); return; } const a = fs.readFileSync(file, 'utf8'), b = fn(a); if (a !== b) { fs.writeFileSync(file, b); console.log('angepasst:', path.relative(root, file)); } };

edit(A('variables.gradle'), s => s
  .replace(/minSdkVersion\s*=\s*\d+/, 'minSdkVersion = 24')
  .replace(/compileSdkVersion\s*=\s*\d+/, 'compileSdkVersion = 36')
  .replace(/targetSdkVersion\s*=\s*\d+/, 'targetSdkVersion = 36'));

edit(A('app', 'build.gradle'), s => s
  .replace(/versionCode\s+\d+/, `versionCode ${pkg.androidVersionCode || 1}`)
  .replace(/versionName\s+"[^"]*"/, `versionName "${pkg.version}"`));

const orient = pkg.androidOrientation || 'unspecified';
edit(A('app', 'src', 'main', 'AndroidManifest.xml'), s => {
  s = s.replace(/\s+android:screenOrientation="[^"]*"/g, '');
  s = s.replace(/<activity\b/, `<activity\n            android:screenOrientation="${orient}"`);
  if (!/android:hardwareAccelerated/.test(s)) s = s.replace(/<application\b/, '<application\n        android:hardwareAccelerated="true"');
  return s;
});

// Bildschirm beim Spielen nicht abschalten
const java = (() => { const base = A('app', 'src', 'main', 'java'); const out = []; const walk = d => { for (const f of fs.readdirSync(d)) { const q = path.join(d, f); if (fs.statSync(q).isDirectory()) walk(q); else if (f === 'MainActivity.java') out.push(q); } }; if (fs.existsSync(base)) walk(base); return out[0]; })();
if (java) edit(java, s => {
  if (s.includes('FLAG_KEEP_SCREEN_ON')) return s;
  s = s.replace(/import com\.getcapacitor\.BridgeActivity;/, 'import android.os.Bundle;\nimport android.view.WindowManager;\nimport com.getcapacitor.BridgeActivity;');
  return s.replace(/public class MainActivity extends BridgeActivity \{\s*\}/, `public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }
}`);
});
console.log(`Android-Projekt bereit: Version ${pkg.version} (${pkg.androidVersionCode || 1}), API 36, Ausrichtung ${orient}.`);
