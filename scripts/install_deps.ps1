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

# --- Python packages (with PEP 668 fallbacks) ---
$pkgs = @("python-jobspy", "openpyxl", "python-docx", "pandas", "pyyaml")
Write-Host "- Installing Python packages..."

$installed = $false
# Try plain install first
& $Python -m pip install --upgrade --quiet @pkgs 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK python packages installed"
    $installed = $true
}
# Fall back to --user
if (-not $installed) {
    & $Python -m pip install --upgrade --quiet --user @pkgs 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK python packages installed (--user)"
        $installed = $true
    }
}
# Last resort: --break-system-packages
if (-not $installed) {
    & $Python -m pip install --upgrade --quiet --break-system-packages @pkgs 2>$null
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
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "- Node.js not found. Install from https://nodejs.org/ (LTS) or: winget install OpenJS.NodeJS"
    Write-Host "  Skipping MCP setup for now."
} else {
    $nodeVersion = node --version
    Write-Host "- Node: $nodeVersion"

    $mcpInstalled = $false
    try {
        $npmList = npm list -g --depth=0 2>$null | Out-String
        if ($npmList -match '@playwright/mcp') { $mcpInstalled = $true }
    } catch {}

    if (-not $mcpInstalled) {
        Write-Host "- Installing @playwright/mcp globally..."
        npm install -g @playwright/mcp@latest
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK @playwright/mcp installed"
        } else {
            Write-Host "  ! npm install failed - you may need a Node-version manager or to run as admin"
        }
    } else {
        Write-Host "  OK @playwright/mcp already installed"
    }

    Write-Host "- Installing Playwright Chromium browser (if missing)..."
    npx --yes playwright install chromium
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK Chromium ready"
    } else {
        Write-Host "  ! Playwright chromium install failed"
    }
}

# --- Register Playwright MCP with Claude Code ---
if (Get-Command claude -ErrorAction SilentlyContinue) {
    $mcpList = claude mcp list 2>$null | Out-String
    if ($mcpList -notmatch 'playwright') {
        Write-Host "- Registering Playwright MCP with Claude Code..."
        claude mcp add playwright -- npx @playwright/mcp@latest
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  OK MCP server registered"
        } else {
            Write-Host "  ! Register failed - try manually: claude mcp add playwright -- npx @playwright/mcp@latest"
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
& $Python -c $verifyScript 2>$errFile
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK all python packages importable"
} else {
    Write-Host "  X python verification failed:"
    if (Test-Path $errFile) { Get-Content $errFile }
    Write-Host "  -> Some features will not work. Retry the install or report the error."
}

Write-Host ""
Write-Host "- Done. Run /job-search-status in Claude Code to verify everything is ready."
