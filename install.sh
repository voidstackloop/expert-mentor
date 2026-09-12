#!/usr/bin/env bash
# One-command setup for expert-mentor.
#
#   ./install.sh
#
# Installs:
#   - the `mentor` command into ~/.local/bin
#   - the skill into ~/.claude/skills and ~/.config/opencode/skills
#   - ~/.local/bin on PATH (appended to your shell rc, idempotent)
#
# Override locations with env vars: BIN_DIR, CLAUDE_SKILLS, OPENCODE_SKILLS, PYTHON
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PYTHON=${PYTHON:-python3}
BIN_DIR=${BIN_DIR:-$HOME/.local/bin}
CLAUDE_SKILLS=${CLAUDE_SKILLS:-$HOME/.claude/skills}
OPENCODE_SKILLS=${OPENCODE_SKILLS:-$HOME/.config/opencode/skills}
MARKER="# >>> expert-mentor setup >>>"

say() { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }

say "expert-mentor installer"
say "  source: $ROOT"
say ""

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "error: python3 is required but was not found on PATH" >&2
    exit 1
fi

# 1. Launcher on PATH
mkdir -p "$BIN_DIR"
chmod +x "$ROOT/bin/mentor" "$ROOT/scripts/expert_mentor.py" "$ROOT/scripts/selftest.py"
ln -sf "$ROOT/bin/mentor" "$BIN_DIR/mentor"
say "[1/4] installed launcher: $BIN_DIR/mentor"

# 2. Skill symlinks (opencode auto-loads ~/.claude/skills too)
link_skill() {
    local target="$1"
    mkdir -p "$(dirname "$target")"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        warn "$target exists and is not a symlink; leaving it alone"
    else
        ln -sfn "$ROOT" "$target"
        say "      linked skill: $target"
    fi
}
say "[2/4] linking skill"
link_skill "$CLAUDE_SKILLS/expert-mentor"
link_skill "$OPENCODE_SKILLS/expert-mentor"

# 3. Ensure ~/.local/bin is on PATH
case ":$PATH:" in
    *":$BIN_DIR:"*) PATH_OK=1 ;;
    *) PATH_OK=0 ;;
esac
if [ "$PATH_OK" -eq 0 ]; then
    RC=""
    for candidate in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        [ -e "$candidate" ] && RC="$candidate" && break
    done
    RC=${RC:-$HOME/.bashrc}
    if [ -f "$RC" ] && grep -qF "$MARKER" "$RC"; then
        say "[3/4] PATH: already configured in $RC"
    else
        {
            printf '\n%s\n' "$MARKER"
            printf 'export PATH="%s:$PATH"\n' "$BIN_DIR"
            printf '%s\n' "# <<< expert-mentor setup <<<"
        } >> "$RC"
        say "[3/4] PATH: added $BIN_DIR to $RC"
    fi
else
    say "[3/4] PATH: $BIN_DIR already on PATH"
fi

# 4. Health check
say "[4/4] running doctor"
say ""
# shellcheck disable=SC2086
"$PYTHON" "$ROOT/scripts/expert_mentor.py" doctor || true

say ""
say "Setup complete."
say ""
if [ "$PATH_OK" -eq 0 ]; then
    say "For this shell, run:   export PATH=\"$BIN_DIR:\$PATH\""
    say "or open a new terminal."
    say ""
fi
say "Try it:"
say "  mentor --field 'quantum computing' --level beginner"
say "  mentor save rustbuddy --field 'Rust' --level intermediate"
say "  mentor ollama rusttutor --field 'Rust' --compact"
say "  mentor doctor"
say ""
say "Prefer an isolated install? 'pipx install .' also provides the 'mentor' command."
