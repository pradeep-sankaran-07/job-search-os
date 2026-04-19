#!/usr/bin/env bash
# Install Job Search OS dependencies. Safe to re-run.
#
# Installs:
#   - Python packages: python-jobspy, openpyxl, python-docx, pandas, pyyaml
#   - Playwright MCP (Node.js) + Chromium browser
#   - Registers the Playwright MCP server with Claude Code (if not already)
#
# Does NOT install:
#   - Claude Desktop (user installs from claude.ai/download)
#   - claude-in-chrome browser extension (user installs from Chrome Web Store)

set -u  # Fail on unset vars but keep going on command errors — best-effort.

echo "▸ Job Search OS — dependency install"
echo

# --- Detect Python ---
PYTHON=""
for candidate in python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 \
                 /opt/homebrew/Caskroom/miniconda/base/bin/python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON="$candidate"
    break
  fi
done

if [ -z "$PYTHON" ]; then
  echo "✗ No python3 found. Install Python 3.10+ from https://www.python.org/downloads/"
  echo "  (or on macOS: brew install python)"
  exit 1
fi

echo "• Python: $PYTHON ($("$PYTHON" --version))"

# --- Python packages ---
# Handle PEP 668 "externally-managed-environment" on modern Homebrew/Debian Python:
# try plain install first, fall back to --user, then to --break-system-packages.
echo "• Installing Python packages..."
PIP_PKGS=(python-jobspy openpyxl python-docx pandas pyyaml)

if "$PYTHON" -m pip install --upgrade --quiet "${PIP_PKGS[@]}" 2>/tmp/jsos_pip.err; then
  echo "  ✅ python packages installed"
elif "$PYTHON" -m pip install --upgrade --quiet --user "${PIP_PKGS[@]}" 2>/tmp/jsos_pip.err; then
  echo "  ✅ python packages installed (--user)"
elif "$PYTHON" -m pip install --upgrade --quiet --break-system-packages "${PIP_PKGS[@]}" 2>/tmp/jsos_pip.err; then
  echo "  ✅ python packages installed (--break-system-packages)"
else
  echo "  ⚠️  pip install failed:"
  cat /tmp/jsos_pip.err
  echo "  → Consider creating a venv: python3 -m venv ~/.venvs/job-search-os && source ~/.venvs/job-search-os/bin/activate, then re-run this script."
fi

# --- Node + Playwright MCP ---
if ! command -v node >/dev/null 2>&1; then
  echo "• Node.js not found. Install from https://nodejs.org/ or: brew install node"
  echo "  (Playwright MCP + live-URL verifier need Node.)"
  echo "  Skipping MCP setup for now."
else
  echo "• Node: $(node --version)"
  if ! npm list -g --depth=0 2>/dev/null | grep -q '@playwright/mcp'; then
    echo "• Installing @playwright/mcp globally..."
    npm install -g @playwright/mcp@latest \
      && echo "  ✅ @playwright/mcp installed" \
      || echo "  ⚠️  npm install failed — you may need sudo or a node-version manager"
  else
    echo "  ✅ @playwright/mcp already installed"
  fi

  echo "• Installing Playwright Chromium browser (if missing)..."
  npx --yes playwright install chromium \
    && echo "  ✅ Chromium ready" \
    || echo "  ⚠️  Playwright chromium install failed"
fi

# --- Register Playwright MCP with Claude Code ---
if command -v claude >/dev/null 2>&1; then
  if ! claude mcp list 2>/dev/null | grep -q 'playwright'; then
    echo "• Registering Playwright MCP with Claude Code..."
    claude mcp add playwright -- npx @playwright/mcp@latest \
      && echo "  ✅ MCP server registered" \
      || echo "  ⚠️  Register failed — try manually: claude mcp add playwright -- npx @playwright/mcp@latest"
  else
    echo "  ✅ Playwright MCP already registered"
  fi
else
  echo "• 'claude' CLI not on PATH — skipping MCP registration."
  echo "  If /mcp in Claude Code doesn't show 'playwright', run manually:"
  echo "    claude mcp add playwright -- npx @playwright/mcp@latest"
fi


# --- Install playwright-core in adapters/ for verify_url.js ---
PLUGIN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$PLUGIN_DIR/adapters/package.json" ]; then
  echo "• Installing playwright-core for URL verifier..."
  (cd "$PLUGIN_DIR/adapters" && npm install --silent) \
    && echo "  ✅ playwright-core installed in adapters/" \
    || echo "  ⚠️  adapter-local npm install failed — verify_url.js may not work"
fi

# --- Final verification ---
echo
echo "• Verifying installs..."
"$PYTHON" -c "import jobspy, openpyxl, docx, pandas, yaml" 2>/tmp/jsos_verify.err
if [ $? -eq 0 ]; then
  echo "  ✅ all python packages importable"
else
  echo "  ✗ python verification failed:"
  cat /tmp/jsos_verify.err
  echo "  → Some features will not work. Retry the install or report the error."
fi

echo
echo "▸ Done. Run /job-search-status to verify everything is ready."
