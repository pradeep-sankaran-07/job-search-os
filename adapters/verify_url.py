"""Shared URL verifier for the Job Search OS tracker pipeline.

Delegates to verify_url.js (a Node/Playwright script) which owns the
actual rule logic. This Python module is a thin shim so update-tracker
code and other Python callers don't have to wire subprocess themselves.

Fail-closed: any non-'live' result must NOT be written to the tracker.

Exit codes from the Node CLI: 0=live, 1=dead, 2=unverified, 3=bad args.

Forked from Pradeep's personal job-search automation.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
NODE_SCRIPT = HERE / "verify_url.js"
# Learnings file lives in the user's job-search folder, not the plugin dir.
# Resolved at call time from the userDataPath setting.


@dataclass
class VerificationResult:
    status: str  # "live" | "dead" | "unverified"
    reason: str
    evidence: dict
    url: str
    title: str
    company: str

    @property
    def is_live(self) -> bool:
        return self.status == "live"

    def summary_line(self) -> str:
        return f"[{self.status}] {self.company} — {self.title}: {self.reason} ({self.url})"


def _host_risk(url: str, learnings_file: Optional[Path] = None) -> str:
    """Return 'high' for host families that have produced false positives before."""
    if learnings_file is None or not learnings_file.exists():
        return "normal"

    try:
        learnings = json.loads(learnings_file.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return "normal"

    high_risk = set(learnings.get("high_risk_host_families", []))
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return "normal"
    host = host.lower()

    if host.endswith(".myworkdayjobs.com") and "myworkdayjobs.com" in high_risk:
        return "high"
    if (host == "jobs.lever.co" or host.endswith(".lever.co")) and "lever.co" in high_risk:
        return "high"
    if host.startswith("jobs.") and "teamtailor" in high_risk:
        return "high"
    if host.endswith(".greenhouse.io") and "greenhouse.io" in high_risk:
        return "high"
    if host.endswith(".ashbyhq.com") and "ashbyhq.com" in high_risk:
        return "high"
    if host.endswith(".bamboohr.com") and "bamboohr.com" in high_risk:
        return "high"
    if host.endswith(".smartrecruiters.com") and "smartrecruiters.com" in high_risk:
        return "high"
    return "normal"


def verify_job_url(
    url: str,
    title: str,
    company: str,
    timeout_ms: int = 20000,
    learnings_file: Optional[Path] = None,
) -> VerificationResult:
    """Run the Node verifier and return a structured result.

    Never raises. On any tool-side failure returns status='unverified'.

    Args:
        url: The job posting URL to verify.
        title: The job title (used for positive-signal matching).
        company: The company name (used for positive-signal matching).
        timeout_ms: Max navigation time in milliseconds.
        learnings_file: Optional path to false_positive_learnings.json in the
            user's job-search folder, for host-risk escalation.
    """
    if not url or not url.startswith("http"):
        return VerificationResult(
            status="unverified",
            reason="non_http_url",
            evidence={"originalUrl": url},
            url=url,
            title=title,
            company=company,
        )

    cmd = [
        "node",
        str(NODE_SCRIPT),
        "--url", url,
        "--title", title,
        "--company", company,
        "--timeout-ms", str(timeout_ms),
        "--host-risk", _host_risk(url, learnings_file),
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=(timeout_ms / 1000) + 20,
        )
    except subprocess.TimeoutExpired:
        return VerificationResult(
            status="unverified",
            reason="subprocess_timeout",
            evidence={"originalUrl": url},
            url=url, title=title, company=company,
        )
    except FileNotFoundError:
        return VerificationResult(
            status="unverified",
            reason="node_not_found",
            evidence={"originalUrl": url},
            url=url, title=title, company=company,
        )

    stdout = proc.stdout.strip()
    if not stdout:
        return VerificationResult(
            status="unverified",
            reason=f"empty_stdout (rc={proc.returncode}, stderr={proc.stderr[:200]})",
            evidence={"originalUrl": url},
            url=url, title=title, company=company,
        )

    try:
        payload = json.loads(stdout.splitlines()[-1])
    except json.JSONDecodeError as exc:
        return VerificationResult(
            status="unverified",
            reason=f"json_decode_failed: {exc}",
            evidence={"originalUrl": url, "raw_stdout": stdout[:400]},
            url=url, title=title, company=company,
        )

    return VerificationResult(
        status=payload.get("status", "unverified"),
        reason=payload.get("reason", "no_reason"),
        evidence=payload.get("evidence", {}),
        url=url, title=title, company=company,
    )


def main(argv: Optional[list[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Verify a job posting URL is real and open.")
    parser.add_argument("url")
    parser.add_argument("--title", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--timeout-ms", type=int, default=20000)
    parser.add_argument("--learnings-file", default=None,
                        help="Path to false_positive_learnings.json in the user's job-search folder.")
    args = parser.parse_args(argv)

    learnings_file = Path(args.learnings_file) if args.learnings_file else None
    result = verify_job_url(args.url, args.title, args.company, args.timeout_ms, learnings_file)
    print(json.dumps({
        "status": result.status,
        "reason": result.reason,
        "url": result.url,
        "title": result.title,
        "company": result.company,
        "evidence": result.evidence,
    }, indent=2))
    return {"live": 0, "dead": 1, "unverified": 2}.get(result.status, 2)


if __name__ == "__main__":
    sys.exit(main())
