#!/usr/bin/env bash
# Schreibt BUILD-STATUS.md (Ergebnis, Schritte, Log-Ende ohne Passwörter) und committet sie.
{
  echo "# Letzter Bau: ${JOB_STATUS:-?}"
  echo
  echo "- Zeit: $(date -u '+%Y-%m-%d %H:%M UTC')"
  echo "- Lauf: $GITHUB_SERVER_URL/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID"
  if [ -n "${TAG:-}" ]; then echo "- Dateien: $GITHUB_SERVER_URL/$GITHUB_REPOSITORY/releases/tag/$TAG"; fi
  if [ "${NEW_KEY:-}" = "1" ]; then echo "- Neuer Upload-Schluessel erzeugt (Artifact im Lauf)"; fi
  echo
  echo '## Schritte'
  echo '```'
  echo "${SCHRITTE:-}" | grep -E '"(outcome|conclusion)"|^  "[a-z]+": \{' || true
  echo '```'
  echo
  echo '## Letzte Zeilen des Protokolls'
  echo '```'
  tail -n 150 build.log 2>/dev/null | grep -v -i -E "pass|add-mask" || true
  echo '```'
} > BUILD-STATUS.md
git config user.name "gartenglueck-bot"
git config user.email "actions@users.noreply.github.com"
git add BUILD-STATUS.md
git commit -m "Baustatus: ${JOB_STATUS:-?} (Lauf $GITHUB_RUN_NUMBER)" || true
git pull --rebase -q || true
git push || true
