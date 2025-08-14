import os
import re
import sys

version = os.environ.get("NEW_VERSION")
if not version:
    sys.exit(1)

files_to_update = [
    {
        "file": "uv.lock",
        "pattern": re.compile(
            r'(?P<block>version\s*=\s*["\'])(?P<version>[^\s"\']+)(["\'][^\[]*?source\s*=\s*{[^}]*?editable)',
            re.DOTALL,
        ),
        "replacement": lambda m: f"{m.group('block')}{version}{m.group(3)}",
    },
    {
        "file": "pyproject.toml",
        "pattern": re.compile(
            r'(?P<block>\[project\]\s+name\s*=\s*["\'].*?["\']\s+version\s*=\s*["\'])(?P<version>[^\s"\']+)(["\'])',
            re.DOTALL,
        ),
        "replacement": lambda m: f"{m.group('block')}{version}{m.group(3)}",
    },
    {
        "file": "docs/source/conf.py",
        "pattern": re.compile(
            r'(?P<block>version\s*=\s*["\'])(?P<version>[^\s"\']+)(["\']\s+release\s*=\s*["\'])(?P<release>[^\s"\']+)(["\'])',
            re.DOTALL,
        ),
        "replacement": lambda m: f"{m.group('block')}{version}"
        f"{m.group(3)}{version}{m.group(5)}",
    },
]


for entry in files_to_update:
    filename = entry["file"]
    pattern = entry["pattern"]
    replacement_func = entry["replacement"]
    updated = False

    if not os.path.exists(filename):
        continue

    try:
        with open(filename, encoding="utf-8") as f:
            content = f.read()

        def replacement_with_log(m, replacement_func=replacement_func):
            old_line = m.group(0)
            new_line = replacement_func(m)
            if old_line.strip() != new_line.strip():
                global updated
                updated = True
            return new_line

        new_content, num_replacements = pattern.subn(replacement_with_log, content)

        if num_replacements > 0:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(new_content)
            if updated:
                pass
            else:
                pass
        else:
            pass
    except Exception:
        pass
