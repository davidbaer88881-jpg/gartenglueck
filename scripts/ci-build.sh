#!/usr/bin/env bash
# Kompletter Android-Bau für GitHub Actions. Alles landet in build.log (ohne Passwörter).
set -Eeuo pipefail
exec 3>&1                                   # Originalausgabe (für ::add-mask::, NICHT ins Log)
exec > >(tee -a build.log) 2>&1
step() { echo; echo "=== $* ==="; }
trap 'echo "FEHLER in Zeile $LINENO (Befehl: $BASH_COMMAND)"' ERR

step "1/8 Spiel zusammensetzen"
(cd src && sha256sum -c game.parts.sha256)
cat src/game.part*.b64 | base64 -d | xz -d > src/game.html
echo "$(cat src/game.sha256)  src/game.html" | sha256sum -c -

step "2/8 Android SDK"
export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
echo "ANDROID_HOME=${ANDROID_HOME:-?}  Java: $(java -version 2>&1 | head -1)  Node: $(node -v)"
SDKM=$(command -v sdkmanager || ls "$ANDROID_HOME"/cmdline-tools/*/bin/sdkmanager 2>/dev/null | sort -V | tail -1 || true)
echo "sdkmanager: ${SDKM:-nicht gefunden}"
ls "$ANDROID_HOME/platforms" "$ANDROID_HOME/build-tools" 2>&1 | tr '\n' ' ' || true; echo
if [ -n "${SDKM:-}" ]; then
  (yes 2>/dev/null | timeout 300 "$SDKM" --licenses >/dev/null 2>&1) || true
  timeout 600 "$SDKM" "platforms;android-36" "build-tools;36.0.0" "platform-tools" > sdk.log 2>&1 \
    || { echo "Hinweis: sdkmanager-Fehler:"; tail -8 sdk.log; }
fi
[ -d "$ANDROID_HOME/platforms/android-36" ] || { echo "Android-Plattform 36 fehlt"; exit 1; }
BT="$ANDROID_HOME/build-tools/36.0.0"
[ -x "$BT/apksigner" ] || BT=$(ls -d "$ANDROID_HOME"/build-tools/* | sort -V | tail -1)
echo "Build-Tools: $BT"

step "3/8 Icons und Store-Grafiken"
python3 -c "import PIL" 2>/dev/null \
  || python3 -m pip install --quiet --user --break-system-packages pillow \
  || { sudo apt-get update -qq && sudo apt-get install -y -qq python3-pil; }
python3 scripts/make-art.py .
ls assets store

step "4/8 npm install"
npm install --legacy-peer-deps --no-audit --no-fund
npx cap --version

step "5/8 www vorbereiten"
npm run build

step "6/8 Android-Projekt"
rm -rf android
npx cap add android
node scripts/patch-android.mjs
npx cap sync android
node scripts/patch-android.mjs
npx @capacitor/assets generate --android \
  --iconBackgroundColor "#7fae5a" --iconBackgroundColorDark "#4f7a39" \
  --splashBackgroundColor "#a7c197" --splashBackgroundColorDark "#2c3a22" 2>&1 | tail -15 \
  || echo "Hinweis: App-Icons konnten nicht erzeugt werden (Standard-Icon bleibt)."

step "7/8 Schlüssel"
if [ -n "${KEYSTORE_BASE64:-}" ] && [ -n "${KEYSTORE_PASSWORD:-}" ]; then
  echo "$KEYSTORE_BASE64" | base64 -d > upload.jks
  KS="$KEYSTORE_PASSWORD"; NEW_KEY=0
  echo "Vorhandener Upload-Schlüssel aus den Secrets wird benutzt."
else
  KS=$(openssl rand -base64 24 | tr -d '/+=' | cut -c1-24)
  echo "::add-mask::$KS" >&3
  keytool -genkeypair -keystore upload.jks -storetype PKCS12 -keyalg RSA -keysize 2048 -validity 10000 \
    -alias upload -storepass "$KS" -keypass "$KS" -dname "CN=Gartenglueck, O=Gartenglueck, C=DE" >/dev/null 2>&1
  NEW_KEY=1
  mkdir -p schluessel
  cp upload.jks schluessel/upload.jks
  base64 -w0 upload.jks > schluessel/KEYSTORE_BASE64.txt
  printf '%s' "$KS" > schluessel/KEYSTORE_PASSWORD.txt
  printf '%s\n' \
    "Das ist dein Upload-Schluessel fuer Gartenglueck. GUT AUFHEBEN (USB-Stick + Passwortmanager)!" \
    "Damit alle spaeteren Versionen mit demselben Schluessel unterschrieben werden:" \
    "GitHub -> Repository gartenglueck -> Settings -> Secrets and variables -> Actions -> New repository secret" \
    "  Name KEYSTORE_BASE64   -> Inhalt von KEYSTORE_BASE64.txt" \
    "  Name KEYSTORE_PASSWORD -> Inhalt von KEYSTORE_PASSWORD.txt" > schluessel/LIES-MICH.txt
  echo "Neuer Upload-Schlüssel erzeugt."
fi

step "8/8 Bauen und unterschreiben"
(cd android && chmod +x gradlew && ./gradlew --no-daemon --console=plain --warning-mode=none bundleRelease assembleRelease)
VER=$(node -p "require('./package.json').version")
mkdir -p out
cp android/app/build/outputs/bundle/release/app-release.aab "out/gartenglueck-$VER.aab"
jarsigner -sigalg SHA256withRSA -digestalg SHA-256 -keystore upload.jks -storepass "$KS" -keypass "$KS" \
  "out/gartenglueck-$VER.aab" upload >/dev/null
APK=$(ls android/app/build/outputs/apk/release/*.apk | head -1)
"$BT/zipalign" -f -p 4 "$APK" out/aligned.apk
"$BT/apksigner" sign --ks upload.jks --ks-pass "pass:$KS" --key-pass "pass:$KS" --ks-key-alias upload \
  --out "out/gartenglueck-$VER.apk" out/aligned.apk
rm -f out/aligned.apk out/*.idsig
"$BT/apksigner" verify "out/gartenglueck-$VER.apk" && echo "APK-Signatur OK"
cp store/play-icon-512.png store/feature-graphic-1024x500.png out/
ls -la out

TAG="v$VER-build${GITHUB_RUN_NUMBER:-0}"
NOTE="AAB fuer die Play Console, APK zum Testen auf dem Handy, Store-Grafiken."
[ "$NEW_KEY" = "1" ] && NOTE="$NOTE NEUER Upload-Schluessel: unter Actions -> dieser Lauf -> Artifacts herunterladen und sicher aufbewahren!"
gh release create "$TAG" out/* --title "Gartenglück $VER (Build ${GITHUB_RUN_NUMBER:-0})" --notes "$NOTE"
{ echo "NEW_KEY=$NEW_KEY"; echo "TAG=$TAG"; } >> "${GITHUB_ENV:-/dev/null}"
echo "FERTIG: $TAG"
