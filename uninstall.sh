#!/usr/bin/env bash
# Reverse the expert-mentor installation. Saved mentors in
# ~/.config/expert-mentor are left untouched.
set -euo pipefail

BIN_DIR=${BIN_DIR:-$HOME/.local/bin}
CLAUDE_SKILLS=${CLAUDE_SKILLS:-$HOME/.claude/skills}
OPENCODE_SKILLS=${OPENCODE_SKILLS:-$HOME/.config/opencode/skills}
MARKER="# >>> expert-mentor setup >>>"
END_MARKER="# <<< expert-mentor setup <<<"

say() { printf '%s\n' "$*"; }

remove_link() {
    local target="$1"
    if [ -L "$target" ]; then
        rm -f "$target"
        say "removed symlink: $target"
    fi
}

remove_link "$BIN_DIR/mentor"
remove_link "$CLAUDE_SKILLS/expert-mentor"
remove_link "$OPENCODE_SKILLS/expert-mentor"
# legacy singular opencode dir
remove_link "$HOME/.config/opencode/skill/expert-mentor"

for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    if [ -f "$rc" ] && grep -qF "$MARKER" "$rc"; then
        tmp=$(mktemp)
        awk -v m="$MARKER" -v e="$END_MARKER" '
            $0 == m { skip = 1; next }
            $0 == e { skip = 0; next }
            !skip { print }
        ' "$rc" > "$tmp" && mv "$tmp" "$rc"
        say "cleaned PATH block from $rc"
    fi
done

say ""
say "Uninstalled. Saved mentors remain in \${EXPERT_MENTOR_HOME:-$HOME/.config/expert-mentor}."
