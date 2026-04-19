#!/usr/bin/env node
// Verify that a job posting URL is a real, currently-open job.
//
// Emits a single JSON object on stdout. Exit code: 0=live, 1=dead, 2=unverified.
// Rules live here (not in Python) so there is one source of truth.
//
// Usage:
//   node verify_url.js --url <url> --title "<title>" --company "<company>" [--timeout-ms 20000] [--host-risk high|normal]
//
// Dependencies: playwright-core (bundled with @playwright/mcp, which the plugin
// installs during setup). This script tries several common locations to locate
// playwright-core so it works whether MCP is installed globally, per-user, or
// via npx cache.
//
// Forked from Pradeep's personal job-search automation.

// playwright-core is installed locally in adapters/node_modules/ via the
// install scripts (install_deps.sh on macOS/Linux; install_deps.ps1 on
// Windows). This keeps resolution reliable across platforms and across
// Homebrew / nvm / system Node installs.

let chromium;
try {
  ({ chromium } = require('playwright-core'));
} catch (err) {
  const hint = process.platform === 'win32'
    ? 'Run: powershell -ExecutionPolicy Bypass -File scripts\\install_deps.ps1'
    : 'Run: bash scripts/install_deps.sh';
  process.stdout.write(JSON.stringify({
    status: 'unverified',
    reason: `playwright_not_found: ${err.message}. ${hint}`,
    evidence: {},
  }) + '\n');
  process.exit(2);
}

function parseArgs(argv) {
  const out = { timeoutMs: 20000, hostRisk: 'normal' };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--url') out.url = argv[++i];
    else if (a === '--title') out.title = argv[++i];
    else if (a === '--company') out.company = argv[++i];
    else if (a === '--timeout-ms') out.timeoutMs = parseInt(argv[++i], 10);
    else if (a === '--host-risk') out.hostRisk = argv[++i];
  }
  return out;
}

const CLOSURE_PHRASES = [
  'no longer active',
  'no longer available',
  'position was filled',
  'position has been filled',
  'ad has expired',
  'vacancy has expired',
  'this vacancy has now expired',
  "page you are looking for doesn't exist",
  'page you are looking for does not exist',
  'job you are looking for',
  'we couldn\u2019t find',
  "we couldn't find",
  'page not found',
  'job not found',
  'inaktiv',
  'stillingen er ikke lenger',
  'annonsen er utl\u00f8pt',
  'job is no longer available',
  'this posting is closed',
  'this job has expired',
  'opportunity is no longer accepting applications',
  'role is no longer open',
];

// Phrases that only count if the page is also missing the job title/company.
const AMBIGUOUS_PHRASES = [
  '404 error',
  '\u2013 404',
  '- 404',
];

const ROOT_PATH_PATTERNS = [
  /\/careers\/?$/i,
  /\/jobs\/?$/i,
  /\/search\/?$/i,
  /\/careers\/jobs\/?$/i,
];

function normalise(s) {
  return (s || '')
    .toLowerCase()
    .replace(/[\u2013\u2014]/g, '-')
    .replace(/[^a-z0-9\s\-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function firstSignificantTitleWords(title, n = 3) {
  const stop = new Set(['of', 'the', 'and', 'for', 'a', 'an', 'to', 'in', 'at', 'on', '-']);
  const words = normalise(title).split(' ').filter((w) => w && !stop.has(w));
  return words.slice(0, n);
}

function hostFamily(url) {
  try {
    const h = new URL(url).host.toLowerCase();
    if (h.endsWith('.myworkdayjobs.com')) return 'myworkdayjobs.com';
    if (h === 'jobs.lever.co' || h.endsWith('.lever.co')) return 'lever.co';
    if (h.endsWith('.greenhouse.io') || h === 'boards.greenhouse.io') return 'greenhouse.io';
    if (h.endsWith('.ashbyhq.com') || h === 'jobs.ashbyhq.com') return 'ashbyhq.com';
    if (h.endsWith('.bamboohr.com')) return 'bamboohr.com';
    if (h.endsWith('.smartrecruiters.com')) return 'smartrecruiters.com';
    if (h.startsWith('jobs.') && !h.includes('linkedin') && !h.includes('indeed')) return 'teamtailor';
    return h;
  } catch (_) {
    return null;
  }
}

function looksLikeRootRedirect(originalUrl, finalUrl) {
  try {
    const o = new URL(originalUrl);
    const f = new URL(finalUrl);
    if (o.pathname === f.pathname) return false;
    const fPath = f.pathname.replace(/\/+$/, '');
    for (const p of ROOT_PATH_PATTERNS) {
      if (p.test(fPath)) return true;
    }
    const oTail = o.pathname.split('/').filter(Boolean).pop() || '';
    if (oTail && !f.pathname.toLowerCase().includes(oTail.toLowerCase())) {
      if (f.pathname.length < o.pathname.length * 0.6) return true;
    }
    return false;
  } catch (_) {
    return false;
  }
}

function companyRoot(company) {
  return normalise(company).split(' ')[0] || '';
}

async function verify(opts) {
  const { url, title, company, timeoutMs, hostRisk } = opts;
  const evidence = { originalUrl: url, finalUrl: null, title: null, bodySample: null, hostFamily: hostFamily(url) };

  let browser;
  try {
    try {
      browser = await chromium.launch({ headless: true });
    } catch (launchErr) {
      // Playwright-core is present but the Chromium binary wasn't installed
      // (npx playwright install chromium didn't run or failed). Give a clear
      // actionable hint so Claude Code can surface the right fix.
      const launchHint = process.platform === 'win32'
        ? "Run: npx playwright install chromium (from the plugin's adapters folder), or re-run install_deps.ps1"
        : "Run: npx playwright install chromium (from the plugin's adapters folder), or re-run install_deps.sh";
      const msg = String(launchErr && launchErr.message || launchErr);
      if (/Executable doesn'?t exist|browsers\s+not\s+installed|BROWSERS_PATH/i.test(msg)) {
        return { status: 'unverified', reason: `chromium_not_installed: ${msg}. ${launchHint}`, evidence };
      }
      throw launchErr;
    }
    const ctx = await browser.newContext({
      userAgent:
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    });
    const page = await ctx.newPage();

    let resp;
    try {
      resp = await page.goto(url, { timeout: timeoutMs, waitUntil: 'domcontentloaded' });
    } catch (err) {
      return { status: 'unverified', reason: `navigation_failed: ${err.message}`, evidence };
    }

    const httpStatus = resp ? resp.status() : null;
    evidence.httpStatus = httpStatus;

    if (httpStatus && httpStatus >= 400) {
      return { status: 'dead', reason: `http_${httpStatus}`, evidence };
    }

    await page.waitForTimeout(3000);
    try {
      await page.waitForLoadState('networkidle', { timeout: 4000 });
    } catch (_) {}

    const details = await page.evaluate(() => ({
      finalUrl: location.href,
      title: document.title,
      bodyText: (document.body && document.body.innerText) || '',
    }));

    evidence.finalUrl = details.finalUrl;
    evidence.title = details.title;
    evidence.bodySample = details.bodyText.slice(0, 400);

    const bodyLower = details.bodyText.toLowerCase();
    const titleLower = (details.title || '').toLowerCase();

    for (const phrase of CLOSURE_PHRASES) {
      if (bodyLower.includes(phrase) || titleLower.includes(phrase)) {
        return { status: 'dead', reason: `closure_phrase:${phrase}`, evidence };
      }
    }

    if (looksLikeRootRedirect(url, details.finalUrl)) {
      return { status: 'dead', reason: 'redirected_to_root', evidence };
    }

    const titleWords = firstSignificantTitleWords(title || '', 3);
    const normBody = normalise(details.bodyText + ' ' + details.title);
    const titleHit = titleWords.length > 0 && titleWords.every((w) => normBody.includes(w));
    const companyHit = !!companyRoot(company) && normBody.includes(companyRoot(company));

    if (!titleHit || !companyHit) {
      for (const phrase of AMBIGUOUS_PHRASES) {
        if (bodyLower.includes(phrase) || titleLower.includes(phrase)) {
          return { status: 'dead', reason: `ambiguous_404_no_positive:${phrase}`, evidence };
        }
      }
      const missing = [];
      if (!titleHit) missing.push('title');
      if (!companyHit) missing.push('company');
      return { status: 'dead', reason: `missing_positive_signal:${missing.join(',')}`, evidence };
    }

    if (hostRisk === 'high' && details.bodyText.length < 600) {
      return { status: 'unverified', reason: 'high_risk_host_thin_body', evidence };
    }

    return { status: 'live', reason: 'ok', evidence };
  } catch (err) {
    return { status: 'unverified', reason: `exception: ${err.message}`, evidence };
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

(async () => {
  const args = parseArgs(process.argv);
  if (!args.url || !args.title || !args.company) {
    console.error('usage: verify_url.js --url <url> --title <t> --company <c>');
    process.exit(3);
  }
  const result = await verify(args);
  process.stdout.write(JSON.stringify(result) + '\n');
  const code = result.status === 'live' ? 0 : result.status === 'dead' ? 1 : 2;
  process.exit(code);
})();
