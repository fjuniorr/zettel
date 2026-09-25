from pathlib import Path
from fzf import fzf_prompt
import os
import re
import shlex
import subprocess

import frontmatter

NOTES_DIR = "notes"
PROPERTY_KEYS = ("org", "project")


class Note:
    def __init__(self, path):
        self.path = Path(path)

        try:
            with open(self.path, "r") as f:
                content = f.read()
            self.content = content
        except UnicodeDecodeError as err:
            self.content = str(err)
        self._frontmatter_post = self._parse_frontmatter(self.content)
        self.id = self._extract_id(self.path)
        self.title = self._extract_title() or self.id
        self.tags = self._extract_tags(self._frontmatter_post)
        self.status = self._extract_status(self._frontmatter_post)
        self.properties = self._extract_properties(self._frontmatter_post)
        self.display_title = self._format_display_title(
            self.title, self.tags, self.status, self.properties
        )

    def __repr__(self) -> str:
        return f"{self.id} {self.display_title}"

    def title(self):
        return self.title

    def id(self):
        return self.id

    def _extract_title(self):
        title_from_metadata = self._title_from_metadata(self._frontmatter_post)
        if title_from_metadata:
            return title_from_metadata

        header_source = (
            self._frontmatter_post.content
            if getattr(self._frontmatter_post, "content", None)
            else self.content
        )
        return self._title_from_first_header(header_source)

    @staticmethod
    def _extract_id(path):
        if path.name == "index.md":
            return path.parent.name
        return os.path.splitext(os.path.basename(path))[0]

    @staticmethod
    def _parse_frontmatter(content):
        try:
            return frontmatter.loads(content)
        except Exception:
            return None

    @staticmethod
    def _title_from_metadata(post):
        if not post:
            return None

        title = post.metadata.get("title") if isinstance(post.metadata, dict) else None
        if isinstance(title, str):
            stripped = title.strip()
            return stripped or None

        return None

    @staticmethod
    def _coerce_values(raw):
        """Normalize a frontmatter value into a deduplicated list of strings."""
        if raw is None:
            return []

        if isinstance(raw, str):
            raw_string = raw.strip()
            if not raw_string:
                return []
            if "," in raw_string:
                candidates = [part.strip() for part in raw_string.split(",")]
            else:
                candidates = [raw_string]
        elif isinstance(raw, (list, tuple, set)):
            candidates = list(raw)
        elif isinstance(raw, (int, float)) and not isinstance(raw, bool):
            candidates = [str(raw)]
        else:
            return []

        values = []
        seen = set()
        for candidate in candidates:
            if isinstance(candidate, str):
                stripped = candidate.strip()
            elif isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
                stripped = str(candidate)
            else:
                continue
            if stripped and stripped not in seen:
                values.append(stripped)
                seen.add(stripped)

        return values

    @staticmethod
    def _extract_tags(post):
        if post is None or not isinstance(post.metadata, dict):
            return []

        tags = []
        seen = set()
        for value in Note._coerce_values(post.metadata.get("tags")):
            normalized = value.lstrip("#")
            if normalized and normalized not in seen:
                tags.append(normalized)
                seen.add(normalized)

        return tags

    @staticmethod
    def _extract_properties(post):
        """Collect the configured frontmatter properties as (key, value) pairs."""
        if post is None or not isinstance(post.metadata, dict):
            return []

        properties = []
        for key in PROPERTY_KEYS:
            for value in Note._coerce_values(post.metadata.get(key)):
                properties.append((key, value))

        return properties

    @staticmethod
    def _extract_status(post):
        if post is None or not isinstance(post.metadata, dict):
            return None
        status = post.metadata.get("status")
        if isinstance(status, str) and status.strip():
            return status.strip()
        return None

    @staticmethod
    def _format_display_title(title, tags, status=None, properties=None):
        parts = [title]
        if tags:
            formatted_tags = ", ".join(f"#{tag}" for tag in tags)
            parts.append(f"[{formatted_tags}]")
        if status:
            parts.append(f"@{status}")
        for key, value in properties or []:
            parts.append(f"{key}/{value}")
        return " ".join(parts)

    @staticmethod
    def _title_from_first_header(content):
        first_line = content.partition("\n")[0]
        if not first_line:
            return None

        stripped = first_line.lstrip()
        if not stripped.startswith("#"):
            return None

        header_text = stripped.lstrip("#").strip()
        return header_text or None

    @staticmethod
    def strip_tags(text):
        if not text:
            return text
        # Strip bracketed tags: " [#tag1, #tag2]"
        result = re.sub(r'\s*\[#[^\]]*\]\s*$', '', text)
        # Strip bare tags from the end: " #tag1, #tag2"
        result = re.sub(r'(\s*,?\s*#[^\s,\[\]]+)+\s*$', '', result)
        return result


def iter_note_files(path):
    """Yield every note in the notebook: flat notes and folder notes."""
    subdir = Path(path) / NOTES_DIR
    if not subdir.is_dir():
        return
    yield from subdir.glob("*.md")
    yield from subdir.glob("*/index.md")


def get_files(path):
    files = list(iter_note_files(path))
    sorted_by_mtime_descending = sorted(files, key=lambda t: -os.stat(t).st_mtime)
    return sorted_by_mtime_descending


def get_notes(path):
    for file in get_files(path):
        yield Note(file)


def _colorize_display(display_title, tags, status, properties=None):
    result = display_title
    if tags:
        formatted_tags = ", ".join(f"#{tag}" for tag in tags)
        result = result.replace(f"[{formatted_tags}]", f"\033[35m[{formatted_tags}]\033[0m")
    if status:
        result = result.replace(f"@{status}", f"\033[36m@{status}\033[0m")
    for key, value in properties or []:
        formatted_property = f"{key}/{value}"
        result = result.replace(
            formatted_property, f"\033[33m{formatted_property}\033[0m", 1
        )
    return result


def get_titles(path):
    for note in get_notes(path):
        yield _colorize_display(
            note.display_title, note.tags, note.status, note.properties
        )


def collect_projects(path):
    """Map each project value to its note count and the unique orgs it appears with."""
    projects = {}
    for note in get_notes(path):
        orgs = [value for key, value in note.properties if key == "org"]
        for key, value in note.properties:
            if key != "project":
                continue
            entry = projects.setdefault(value, {"count": 0, "orgs": set()})
            entry["count"] += 1
            entry["orgs"].update(orgs)
    return projects


def collect_tags(path):
    """Map each tag to the number of notes carrying it."""
    tags = {}
    for note in get_notes(path):
        for tag in note.tags:
            tags[tag] = tags.get(tag, 0) + 1
    return tags


def project_lines(path):
    """Tab-separated picker lines: name, note count, unique orgs."""
    projects = collect_projects(path)
    for name in sorted(projects, key=lambda n: (-projects[n]["count"], n.lower())):
        entry = projects[name]
        line = f"{name}\t({entry['count']})"
        if entry["orgs"]:
            orgs = ", ".join(sorted(entry["orgs"], key=str.lower))
            line += f"\t[{orgs}]"
        yield line


def tag_lines(path):
    """Tab-separated picker lines: name, note count."""
    tags = collect_tags(path)
    for name in sorted(tags, key=lambda n: (-tags[n], n.lower())):
        yield f"{name}\t({tags[name]})"


def _escape_query_term(value):
    return value.replace("\\", "\\\\").replace(" ", "\\ ")


def project_filter_query(name):
    return f"project/{_escape_query_term(name)}"


def tag_filter_query(name):
    return f"#{_escape_query_term(name)}"


def pick_first_field(lines, prompt):
    """Run a nested fzf over lines; return the first tab field of the selection."""
    joined = "\n".join(lines)
    if not joined:
        return None
    try:
        result = subprocess.run(
            ["fzf", "--reverse", "--exact", f"--prompt={prompt}"],
            input=joined,
            stdout=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    selection = result.stdout.rstrip("\n")
    if not selection:
        return None
    return selection.split("\t")[0]


def parse_fzf_output(prompt):
    if not prompt:
        return (None, None)

    lines = prompt.split("\n")
    query = lines[0].strip() if lines and lines[0].strip() else None
    note_title = lines[1] if len(lines) > 1 and lines[1] else None

    return (query, note_title)


def copy_to_clipboard(text):
    try:
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard"], input=text.encode(), check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def ss():
    if "ZETTEL_DIR" in os.environ:
        notebook = Path(os.environ["ZETTEL_DIR"]).expanduser()
    elif (Path.cwd() / NOTES_DIR).is_dir():
        notebook = Path.cwd()
    else:
        notebook = Path("~/Notebook").expanduser()
    notebook_arg = shlex.quote(str(notebook))
    pick_file = '"${TMPDIR:-/tmp}/zt-pick-query"'
    apply_pick = (
        f"transform-query([ -s {pick_file} ] && cat {pick_file} || echo {{q}})"
    )

    try:
        fzf_prompt(
            get_titles(notebook),
            reversed_layout=True,
            print_query=True,
            match_exact=True,
            ansi=True,
            escape_output=False,
            preview_window_settings="down:60%",
            preview=f"zt find --dir {notebook_arg} {{}} | xargs glow --style dark",
            keybinds=",".join([
                f"enter:execute-silent(zt open --dir {notebook_arg} --query {{q}} {{}})+reload(zt list --dir {notebook_arg})+clear-query",
                f"ctrl-x:execute-silent(zt copy --dir {notebook_arg} {{}})",
                f"ctrl-s:execute-silent(zt share --dir {notebook_arg} {{}})+reload(zt list --dir {notebook_arg})",
                f'f2:execute-silent(f=$(zt find --dir {notebook_arg} {{}}); if [ "$(basename "$f")" = "index.md" ]; then code "$(dirname "$f")"; else code "$f"; fi)',
                "ctrl-z:clear-query",
                f"ctrl-r:reload(zt list --dir {notebook_arg})",
                f"ctrl-p:execute(zt pick-project --dir {notebook_arg} > {pick_file})+{apply_pick}",
                f"ctrl-t:execute(zt pick-tag --dir {notebook_arg} > {pick_file})+{apply_pick}",
            ]),
            header="(enter: Obsidian; f2: VSCode, ctrl+x: wikilink, ctrl+s: gist, ctrl+r: reload, ctrl+p: project, ctrl+t: tag)",
        )
    except KeyboardInterrupt:
        return None
