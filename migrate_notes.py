#!/usr/bin/env python3
"""
Migrate old-style notes to flat YAML frontmatter notes.

Handles:
- Flat notes: 20260317T135504.md with markdown header → YAML frontmatter
- Folder notes: 20260317T135541/index.md → flat 20260317T135541.md with YAML frontmatter
  - Deletes index.md always
  - Deletes folder only if empty after removing index.md

Notes that already have YAML frontmatter are skipped.

Usage:
    python migrate_notes.py ~/Notebook
    python migrate_notes.py ~/Notebook --dry-run
"""
import re
import sys
import shutil
from pathlib import Path

import yaml

TIMESTAMP_RE = re.compile(r"^\d{8}T\d{6}$")


def yaml_quote(value):
    """Add double quotes around a YAML value only when needed."""
    try:
        parsed = yaml.safe_load(f"v: {value}")
        if isinstance(parsed, dict) and parsed.get("v") == value:
            return value
    except yaml.YAMLError:
        pass
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def parse_header(content):
    """Extract title and tags from the first markdown header line."""
    first_line, _, rest = content.partition("\n")
    stripped = first_line.strip()
    if not stripped.startswith("# "):
        return None, [], content

    header_text = stripped[2:]
    # Extract the tag portion: everything from the first #tag onward
    tag_match = re.search(r"\[?#\S", header_text)
    if tag_match:
        tag_str = header_text[tag_match.start():]
        title = header_text[:tag_match.start()].strip()
        # Remove brackets, split on commas, extract tag names
        tag_str = tag_str.strip("[]")
        tags = [t.strip().lstrip("#") for t in tag_str.split(",") if t.strip()]
    else:
        title = header_text.strip()
        tags = []

    return title, tags, rest


def build_yaml_content(title, tags, body):
    """Build note content with YAML frontmatter."""
    lines = ["---", f"title: {yaml_quote(title)}"]
    if tags:
        lines.append("tags:")
        for tag in tags:
            lines.append(f"  - {tag}")
    lines.append("---")
    lines.append(body)
    return "\n".join(lines)


def has_frontmatter(content):
    return content.startswith("---\n") or content.startswith("---\r\n")


def migrate_note(path, content, dry_run=False):
    """Migrate a single note's content. Returns new content or None if skipped."""
    if has_frontmatter(content):
        print(f"  SKIP (already has frontmatter): {path}")
        return None

    title, tags, body = parse_header(content)
    if title is None:
        print(f"  SKIP (no markdown header): {path}")
        return None

    new_content = build_yaml_content(title, tags, body)
    if not dry_run:
        path.write_text(new_content)
    print(f"  CONVERT: {path} → title={title!r}, tags={tags}")
    return new_content


def process_flat_note(path, dry_run=False):
    """Process a flat timestamp note like 20260317T135504.md."""
    try:
        content = path.read_text()
    except UnicodeDecodeError:
        print(f"  SKIP (encoding error): {path}")
        return
    migrate_note(path, content, dry_run)


def process_folder_note(folder, dry_run=False):
    """Process a folder note like 20260317T135541/index.md."""
    index_path = folder / "index.md"
    if not index_path.exists():
        return

    other_files = [f for f in folder.iterdir() if f.name != "index.md"]
    flat_path = folder.parent / f"{folder.name}.md"

    content = index_path.read_text()
    new_content = migrate_note(flat_path, content, dry_run)

    if new_content is None and not has_frontmatter(content):
        return

    # Write flat file (for frontmatter-skipped notes, copy as-is)
    if new_content is None:
        if not dry_run:
            shutil.copy2(index_path, flat_path)
        print(f"  COPY: {index_path} → {flat_path}")

    # Delete index.md
    if not dry_run:
        index_path.unlink()
    print(f"  DELETE: {index_path}")

    # Delete folder if empty
    if other_files:
        print(f"  KEEP folder (has extra files): {folder}")
    else:
        if not dry_run:
            folder.rmdir()
        print(f"  DELETE folder: {folder}")


def migrate(notebook_path, dry_run=False):
    notebook = Path(notebook_path)
    if not notebook.is_dir():
        print(f"Error: {notebook} is not a directory", file=sys.stderr)
        sys.exit(1)

    mode = "DRY RUN" if dry_run else "MIGRATING"
    print(f"{mode}: {notebook}\n")

    # Flat timestamp notes
    for path in sorted(notebook.glob("*.md")):
        stem = path.stem
        if TIMESTAMP_RE.match(stem):
            process_flat_note(path, dry_run)

    # Folder timestamp notes
    for folder in sorted(notebook.iterdir()):
        if folder.is_dir() and TIMESTAMP_RE.match(folder.name):
            index = folder / "index.md"
            if index.exists():
                process_folder_note(folder, dry_run)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate notes to YAML frontmatter format")
    parser.add_argument("notebook", help="Path to the Notebook folder")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    args = parser.parse_args()

    migrate(args.notebook, dry_run=args.dry_run)
