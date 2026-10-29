#!/usr/bin/env python3
"""Shallow public audit of iceccarelli/ecowoods-app and ecowoods-test.

Does not clone. The app repo reports ~1 GB; cloning it into this bundle would
blow the 25 MB handoff cap and might pull backend/ecowoods.db. That file is
flagged, not downloaded.

Usage:
  python scripts/backend_repo_audit.py
  python scripts/backend_repo_audit.py --dry-run
  python scripts/backend_repo_audit.py --repo iceccarelli/ecowoods-app
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eco_common import REPORTS, arg_value, dry_run_requested, fetch, utc_now, write_json  # noqa: E402


def gh_json(url: str):
    res = fetch(url, limit=1_500_000, timeout=40)
    if res["status"] != 200:
        return {"_error": res["error"] or res["status"], "_status": res["status"]}
    try:
        return json.loads(res["body"].decode())
    except Exception as exc:  # noqa: BLE001
        return {"_error": str(exc), "_status": res["status"]}


def names(listing) -> list[str]:
    if not isinstance(listing, list):
        return []
    return [x.get("name", "") for x in listing]


def main(argv: list[str]) -> int:
    repo = arg_value(argv, "--repo", "iceccarelli/ecowoods-app")
    test_repo = arg_value(argv, "--test-repo", "iceccarelli/ecowoods-test")
    if dry_run_requested(argv):
        print(json.dumps({"dry_run": True, "would_fetch": [repo, test_repo]}))
        return 0
    meta = gh_json(f"https://api.github.com/repos/{repo}")
    root = gh_json(f"https://api.github.com/repos/{repo}/contents/")
    backend = gh_json(f"https://api.github.com/repos/{repo}/contents/backend")
    apps = gh_json(f"https://api.github.com/repos/{repo}/contents/apps")
    scripts = gh_json(f"https://api.github.com/repos/{repo}/contents/scripts")
    commits = gh_json(f"https://api.github.com/repos/{repo}/commits?per_page=5")
    test_meta = gh_json(f"https://api.github.com/repos/{test_repo}")
    test_root = gh_json(f"https://api.github.com/repos/{test_repo}/contents/")
    script_names = names(scripts)
    verify = [n for n in script_names if n.startswith("verify-") or n.startswith("audit-")]
    backend_names = names(backend)
    app_names = names(apps)
    recent = []
    if isinstance(commits, list):
        for c in commits:
            recent.append({
                "sha": (c.get("sha") or "")[:12],
                "date": ((c.get("commit") or {}).get("author") or {}).get("date"),
                "message": ((c.get("commit") or {}).get("message") or "").split("\n", 1)[0][:180],
            })
    report = {
        "audited_at": utc_now(),
        "clone_performed": False,
        "reason_not_cloned": "Repo size is about 1 GB and backend/ecowoods.db must not be copied into this handoff.",
        "repo": {
            "full_name": repo,
            "private": meta.get("private") if isinstance(meta, dict) else None,
            "description": meta.get("description") if isinstance(meta, dict) else None,
            "language": meta.get("language") if isinstance(meta, dict) else None,
            "default_branch": meta.get("default_branch") if isinstance(meta, dict) else None,
            "pushed_at": meta.get("pushed_at") if isinstance(meta, dict) else None,
            "size_kb": meta.get("size") if isinstance(meta, dict) else None,
            "stars": meta.get("stargazers_count") if isinstance(meta, dict) else None,
            "open_issues": meta.get("open_issues") if isinstance(meta, dict) else None,
            "license": ((meta.get("license") or {}) if isinstance(meta, dict) else {}).get("spdx_id"),
            "topics": meta.get("topics") if isinstance(meta, dict) else None,
            "homepage": meta.get("homepage") if isinstance(meta, dict) else None,
        },
        "top_level": names(root),
        "apps": app_names,
        "backend_files": backend_names,
        "committed_sqlite": "ecowoods.db" in backend_names,
        "has_fastapi_layout": "app" in backend_names and "requirements.txt" in backend_names,
        "has_alembic": "alembic.ini" in backend_names,
        "has_backend_tests": "tests" in backend_names,
        "has_dockerfile": "Dockerfile" in backend_names,
        "has_docker_compose": "docker-compose.yml" in names(root),
        "has_mobile": "mobile" in app_names,
        "has_admin": "admin" in app_names,
        "has_web": "web" in app_names,
        "internal_verify_or_audit_scripts": len(verify),
        "verify_script_sample": verify[:25],
        "recent_commits": recent,
        "job_lifecycle_note": "End-to-end estimate→measure→schedule→photos→invoice was NOT executed. No credentials, and this stack will not create production leads.",
        "test_repo": {
            "full_name": test_repo,
            "private": test_meta.get("private") if isinstance(test_meta, dict) else None,
            "size_kb": test_meta.get("size") if isinstance(test_meta, dict) else None,
            "pushed_at": test_meta.get("pushed_at") if isinstance(test_meta, dict) else None,
            "description": test_meta.get("description") if isinstance(test_meta, dict) else None,
            "files": names(test_root),
            "populated_by_this_stack": False,
            "blocker": "No GitHub token in the audit environment. Seed content is in test-repo-seed/. Run scripts/seed_test_repo.sh after gh auth login.",
        },
        "security_flags": [],
    }
    if report["committed_sqlite"]:
        report["security_flags"].append({
            "id": "committed-sqlite",
            "severity": "P0",
            "detail": "backend/ecowoods.db is in the public tree. Confirm it is a fixture with zero customer rows. If it has leads, phones, or addresses: remove it from git, purge history, rotate any secrets that lived beside it, and notify affected people if the data was personal.",
        })
    if (report["repo"].get("size_kb") or 0) > 500_000:
        report["security_flags"].append({
            "id": "repo-size",
            "severity": "P1",
            "detail": f"GitHub reports size_kb={report['repo'].get('size_kb')} (~1 GB class). CI clones, agent clones, and forks will be slow or fail. Find the blob (likely media or the sqlite file) and move it to object storage or Git LFS with a budget.",
        })
    write_json(REPORTS / "backend_repo.json", report)
    print(json.dumps({
        "pushed_at": report["repo"]["pushed_at"],
        "apps": app_names,
        "committed_sqlite": report["committed_sqlite"],
        "verify_scripts": report["internal_verify_or_audit_scripts"],
        "test_repo_files": report["test_repo"]["files"],
        "flags": [f["id"] for f in report["security_flags"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
