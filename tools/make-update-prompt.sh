#!/usr/bin/env bash
# make-update-prompt.sh — build a self-contained "paste into Claude" prompt that updates an
# already-installed trellis-ae plugin OUT OF BAND (no GitHub, no reinstall).
#
# The recipient pastes the generated file's contents into Claude Code on their machine; Claude finds
# their installed trellis-ae plugin and overwrites exactly the files you bundled, at the right paths.
#
# Usage (run from anywhere in the repo):
#   tools/make-update-prompt.sh plugins/trellis-ae/agents/ob-messaging.md plugins/trellis-ae/agents/ob-external-research.md
#   tools/make-update-prompt.sh --since <git-ref>     # bundle every plugin file changed since <ref>, e.g. a prior release commit/tag
#
# Output: update-prompt.md at the repo root. Send its full contents to recipients.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_PREFIX="plugins/trellis-ae/"
OUT="$REPO/update-prompt.md"

# ---- collect the files to bundle (repo-relative paths under the plugin) ----
files=()
if [ "${1:-}" = "--since" ]; then
  ref="${2:-}"
  [ -n "$ref" ] || { echo "usage: $0 --since <git-ref>"; exit 1; }
  while IFS= read -r f; do [ -n "$f" ] && files+=("$f"); done \
    < <(git -C "$REPO" diff --name-only "$ref" -- "$PLUGIN_PREFIX")
else
  [ "$#" -gt 0 ] || { echo "usage: $0 <plugin-file> [<plugin-file> ...]   |   $0 --since <git-ref>"; exit 1; }
  for f in "$@"; do
    f="${f#"$REPO"/}"                 # accept absolute paths too
    files+=("$f")
  done
fi
[ "${#files[@]}" -gt 0 ] || { echo "No plugin files to bundle."; exit 1; }
for f in "${files[@]}"; do
  case "$f" in "$PLUGIN_PREFIX"*) ;; *) echo "Skip (not under $PLUGIN_PREFIX): $f"; exit 1;; esac
  [ -f "$REPO/$f" ] || { echo "Missing file: $f"; exit 1; }
done

# ---- header / instructions ----
cat > "$OUT" <<'HEADER'
# Update my trellis-ae plugin (out of band — no GitHub)

Paste this entire message into Claude Code on the machine where the `trellis-ae` plugin is installed.

**Claude — do exactly this:**
1. Find the installed `trellis-ae` plugin root. It's normally under `~/.claude/plugins/cache/trellis-ae/`
   and the path contains a version number, so glob/find for `.claude-plugin/plugin.json` inside any
   `trellis-ae` plugin folder. If more than one version is installed, update EVERY copy you find.
2. For each file block below, overwrite the file at the listed **plugin-relative path** (e.g.
   `agents/ob-messaging.md`, `skills/cold-outbound/SKILL.md`, `config/ab-tests.md`) with the exact text
   between its BEGIN/END markers — do NOT include the marker lines. Create the file if it doesn't exist.
3. Change nothing else. Then list the path(s) you updated and print the first line of each new file to confirm.

Note: this manually overrides the installed plugin files; a later marketplace/GitHub update of the plugin
would replace them again.

Files in this update:
HEADER
for f in "${files[@]}"; do echo "- ${f#"$PLUGIN_PREFIX"}" >> "$OUT"; done
echo "" >> "$OUT"

# ---- one block per file ----
for f in "${files[@]}"; do
  rel="${f#"$PLUGIN_PREFIX"}"
  printf '================ BEGIN %s ================\n' "$rel" >> "$OUT"
  cat "$REPO/$f" >> "$OUT"
  printf '\n================ END %s ================\n\n' "$rel" >> "$OUT"
done

echo "Wrote $OUT — $(wc -l < "$OUT" | tr -d ' ') lines, ${#files[@]} file(s):"
for f in "${files[@]}"; do echo "  - ${f#"$PLUGIN_PREFIX"}"; done
echo "Send the full contents of update-prompt.md to recipients; they paste it into Claude Code."
