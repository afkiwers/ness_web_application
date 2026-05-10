import os
import platform
from functools import lru_cache

import django


def _clean_env(name):
    return (os.environ.get(name) or "").strip()


@lru_cache(maxsize=1)
def get_build_metadata():
    tag         = _clean_env("NESS_GIT_TAG")
    branch      = _clean_env("NESS_GIT_BRANCH")
    commit_hash = _clean_env("NESS_GIT_COMMIT")
    commit_date = _clean_env("NESS_GIT_COMMIT_DATE")

    short_hash = commit_hash[:7] if commit_hash else ""

    if tag:
        version_label = tag
        channel = "release"
    else:
        branch_label = branch or "unknown"
        hash_label   = short_hash or "unknown"
        version_label = f"DEV ({branch_label} @ {hash_label})"
        channel = "development"

    return {
        "tag":           tag,
        "branch":        branch or "unknown",
        "commit_hash":   commit_hash,
        "short_hash":    short_hash or "unknown",
        "commit_date":   commit_date or "unknown",
        "version_label": version_label,
        "channel":       channel,
        "status_badge":  "RELEASE" if channel == "release" else "DEVELOPMENT VERSION",
    }


def get_version_info():
    build = get_build_metadata()

    rows = [
        {
            "label":         "Ness Web Version",
            "display_value": build["version_label"],
            "copy_value":    build["version_label"],
            "accent":        True,
        },
        {
            "label":         "Python Version",
            "display_value": platform.python_version(),
            "copy_value":    platform.python_version(),
        },
        {
            "label":         "Django Version",
            "display_value": django.get_version(),
            "copy_value":    django.get_version(),
        },
        {
            "label":         "Commit Hash",
            "display_value": build["short_hash"],
            "copy_value":    build["commit_hash"] or "unknown",
        },
        {
            "label":         "Commit Date",
            "display_value": build["commit_date"],
            "copy_value":    build["commit_date"],
        },
        {
            "label":         "Commit Branch",
            "display_value": build["branch"],
            "copy_value":    build["branch"],
        },
    ]

    summary_lines = [f"{r['label']}: {r['copy_value']}" for r in rows]

    return {
        "title":        "About Ness Web",
        "status_badge": build["status_badge"],
        "version_rows": rows,
        "copy_text":    "\n".join(summary_lines),
    }
