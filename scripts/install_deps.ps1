# Install Job Search OS dependencies on Windows (PowerShell).
# Mirrors scripts/install_deps.sh for macOS/Linux.
# Safe to re-run.
#
# Installs:
#   - Python packages: python-jobspy, openpyxl, python-docx, pandas, pyyaml
#   - Playwright MCP (Node.js) + Chromium browser
#   - Registers the Playwright MCP server with Claude Code (if not already)
#   - Installs playwright-core locally in adapters/ for verify_url.js
#
# Does NOT install:
#   - Claude Code (user installs via: npm install -g @anthropic-ai/claude-code)
#   - The claude-in-chrome browser extension (user installs from Chrome Web Store)

$ErrorActionPreference = "Continue"  # keep going on errors; best-effort

Write-Host ""
Write-Host "- Job Search OS - dependency install (Windows)"
Write-Host ""

# --- Detect Python ---
$Python = $null
foreach ($candidate in @("python3", "python", "py")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $Python = $candidate
        break
    }
}

if (-not $Python) {
    Write-Host "X No python found. Install Python 3.10+ from https://www.python.org/downloads/"
    Write-Host "  (or: winget install Python.Python.3.12)"
    exit 1
}

$pyVersion = & $Python --version
Write-Host "- Python: $Python ($pyVersion)"

# Persist the resolved Python binary name so skills can read it (no re-detection).
$userDir = if ($env:JSOS_USER_DIR) { $env:JSOS_USER_DIR } else { Join-Path $env:USERPROFILE "Documents\job-search" }
try {
    if (-not (Test-Path $userDir)) { New-Item -ItemType Directory -Force -Path $userDir | Out-Null }
    Set-Content -Path (Join-Path $userDir ".python-bin") -Value $Python -NoNewline -ErrorAction SilentlyContinue
    Write-Host "  -> recorded in $userDir\.python-bin"
} catch {}

# Build the right pip invocation. The `py` launcher needs `-3` to force Python 3.
$pyArgs = @()
if ($Python -eq "py") { $pyArgs = @("-3") }

# --- Python packages (with PEP 668 fallbacks) ---
$pkgs = @("python-jobspy", "openpyxl", "python-docx", "pandas", "pyyaml")
Write-Host "- Installing Python packages..."

$installed = $false
# Try plain install first
& $Python @pyArgs -m pip install --upgrade --quiet @pkgs 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK python packages installed"
    $installed = $true
}
# Fall back to --user
if (-not $installed) {
    & $Python @pyArgs -m pip install --upgrade --quiet --user @pkgs 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK python packages installed (--user)"
        $installed = $true
    }
}
# Last resort: --break-system-packages
if (-not $installed) {
    & $Python @pyArgs -m pip install --upgrade --quiet --break-system-packages @pkgs 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK python packages installed (--break-system-packages)"
        $installed = $true
    }
}
if (-not $installed) {
    Write-Host "  ! pip install failed. Consider creating a venv:"
    Write-Host "    $Python -m venv `$env:USERPROFILE\.venvs\job-search-os"
    Write-Host "    `$env:USERPROFILE\.venvs\job-search-os\Scripts\Activate.ps1"
    Write-Host "    then re-run this script."
}

# --- Node + Playwright MCP ---
# Resolve node/npm/npx via Get-Command so we use .cmd shim paths explicitly.
# When the script is invoked via `powershell -File ...` from another process,
# PATHEXT resolution can fail for .cmd wrappers — calling them by full path works.
$node = (Get-Command node -ErrorAction SilentlyContinue).Source
$npm  = (Get-Command npm  -ErrorAction SilentlyContinue).Source
$npx  = (Get-Command npx  -ErrorAction SilentlyContinue).Source

if (-not $node) {
    Write-Host "- Node.js not found. Install from https://nodejs.org/ (LTS) or: winget install OpenJS.NodeJS"
    Write-Host "  Skipping MCP setup for now."
} else {
    $nodeVersion = & $node --version
    Write-Host "- Node: $nodeVersion"

    # Global install location check — on Windows, npm install -g defaults to
    # Program Files which needs admin. Warn the user before attempting.
    if ($npm) {
        $npmPrefix = & $npm config get prefix 2>$null
        if ($npmPrefix -like "*Program Files*") {
            Write-Host "  ! npm global prefix is under Program Files; 'npm install -g' needs admin."
            Write-Host "    Either re-run this installer from an elevated PowerShell, or run:"
            Write-Host '      npm config set prefix "$env:APPDATA\npm"'
            Write-Host "    and try again."
        }
    }

    $mcpInstalled = $false
    try {
        if ($npm) {
            $npmList = & $npm list -g --depth=0 2>$null | Out-String
            if ($npmList -match '@playwright/mcp') { $mcpInstalled = $true }
        }
    } catch {}

    if (-not $mcpInstalled -and $npm) {
        Write-Host "- Installing @playwright/mcp globally..."
        & $npm install -g "@playwright/mcp@latest"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK @playwright/mcp installed"
        } else {
            Write-Host "  ! npm install failed - you may need a Node-version manager or to run as admin"
        }
    } else {
        Write-Host "  OK @playwright/mcp already installed"
    }

    if ($npx) {
        Write-Host "- Installing Playwright Chromium browser (if missing)..."
        & $npx --yes playwright install chromium
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK Chromium ready"
        } else {
            Write-Host "  ! Playwright chromium install failed"
        }
    }
}

# --- Register Playwright MCP with Claude Code ---
$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if ($claude) {
    $mcpList = & $claude mcp list 2>$null | Out-String
    if ($mcpList -notmatch 'playwright') {
        Write-Host "- Registering Playwright MCP with Claude Code..."
        # Quote the '--' so PowerShell doesn't swallow it as an arg separator.
        & $claude mcp add playwright '--' npx '@playwright/mcp@latest'
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK MCP server registered"
        } else {
            Write-Host "  ! Register failed - try manually from an interactive shell:"
            Write-Host '    claude mcp add playwright -- npx @playwright/mcp@latest'
        }
    } else {
        Write-Host "  OK Playwright MCP already registered"
    }
} else {
    Write-Host "- 'claude' CLI not on PATH - skipping MCP registration."
    Write-Host "  If /mcp in Claude Code doesn't show 'playwright', run manually:"
    Write-Host "    claude mcp add playwright -- npx @playwright/mcp@latest"
}

# --- Install playwright-core in adapters/ for verify_url.js ---
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pluginDir = Resolve-Path (Join-Path $scriptDir "..")
$adaptersDir = Join-Path $pluginDir "adapters"
if (Test-Path (Join-Path $adaptersDir "package.json")) {
    Write-Host "- Installing playwright-core for URL verifier..."
    Push-Location $adaptersDir
    npm install --silent
    $npmOk = $LASTEXITCODE -eq 0
    Pop-Location
    if ($npmOk) {
        Write-Host "  OK playwright-core installed in adapters/"
    } else {
        Write-Host "  ! adapter-local npm install failed - verify_url.js may not work"
    }
}

# --- Final verification ---
Write-Host ""
Write-Host "- Verifying installs..."
$verifyScript = "import jobspy, openpyxl, docx, pandas, yaml"
$errFile = Join-Path $env:TEMP "jsos_verify.err"
& $Python @pyArgs -c $verifyScript 2>$errFile
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK all python packages importable"
} else {
    Write-Host "  X python verification failed:"
    if (Test-Path $errFile) { Get-Content $errFile }
    Write-Host "  -> Some features will not work. Retry the install or report the error."
}

Write-Host ""
Write-Host "- Done. Run /job-search-status in Claude Code to verify everything is ready."
