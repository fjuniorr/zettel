from pathlib import Path
from fzf import fzf_prompt
from datetime import datetime
import os
import subprocess
from urllib.parse import quote

import frontmatter

EXPECT_KEYS = {"enter", "ctrl-x"}


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
        self.display_title = self._format_display_title(self.title, self.tags)

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
    def _extract_tags(post):
        if post is None or not isinstance(post.metadata, dict):
            return []

        raw_tags = post.metadata.get("tags")
        if not raw_tags:
            return []

        if isinstance(raw_tags, str):
            raw_string = raw_tags.strip()
            if not raw_string:
                return []
            if "," in raw_string:
                candidates = [part.strip() for part in raw_string.split(",")]
            else:
                candidates = [raw_string]
        elif isinstance(raw_tags, (list, tuple, set)):
            candidates = list(raw_tags)
        else:
            return []

        tags = []
        for tag in candidates:
            if isinstance(tag, str):
                stripped = tag.strip()
                if stripped:
                    normalized = stripped.lstrip("#")
                    if normalized:
                        tags.append(normalized)

        deduped = []
        seen = set()
        for tag in tags:
            if tag not in seen:
                deduped.append(tag)
                seen.add(tag)

        return deduped

    @staticmethod
    def _format_display_title(title, tags):
        if tags:
            formatted_tags = ", ".join(f"#{tag}" for tag in tags)
            return f"{title} [{formatted_tags}]"

        return title

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


def get_files(path):
    files = list(path.glob("*.md")) + list(path.glob("*/index.md"))
    sorted_by_mtime_descending = sorted(files, key=lambda t: -os.stat(t).st_mtime)
    return sorted_by_mtime_descending


def get_notes(path):
    for file in get_files(path):
        yield Note(file)


def get_titles(path):
    for note in get_notes(path):
        yield note.display_title


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
    home = Path("~")
    notebook = Path(home.expanduser(), "Notebook/")

    try:
        while True:
            result = fzf_prompt(
                get_titles(notebook),
                reversed_layout=True,
                print_query=True,
                match_exact=True,
                preview_window_settings="down:60%",
                preview=f"zt find --dir {notebook} {{}} | xargs glow --style dark",
                expect_keys="enter,ctrl-x",
                keybinds=",".join([
                    f"f2:execute-silent(open -a iTerm $(dirname $(zt find --dir {notebook} {{}})))",
                    f"ctrl-s:execute-silent(subl $(zt find --dir {notebook} {{}}))",
                ]),
                header="(enter: Obsidian; f2: iTerm, ctrl+s: Sublime Text, ctrl+x: wikilink)",
            )

            if not result:
                break

            lines = result.split("\n")
            key_pressed = None
            for i, line in enumerate(lines[:2]):
                if line in EXPECT_KEYS:
                    key_pressed = line
                    lines.pop(i)
                    break

            query, note_title = parse_fzf_output("\n".join(lines))
            matched_note = None

            for note in get_notes(notebook):
                if note_title and (note_title == note.display_title):
                    matched_note = note
                    break

            if key_pressed == "ctrl-x" and matched_note:
                filepath = str(matched_note.path.relative_to(notebook).with_suffix(""))
                if copy_to_clipboard(f"[[{filepath}|{matched_note.title}]]"):
                    print(f"Copied {filepath} to clipboard")
                else:
                    print(f"Note ID: {filepath} (clipboard copy failed)")
                continue

            if not note_title and query:
                note_id = datetime.now().strftime("%Y%m%dT%H%M%S")
                filepath = f"{note_id}/index"
                content = f"# {query.lower()}\n\n"
                encoded_content = quote(content, safe="")
                params = [
                    ("vault", "510b22d0827fd8cf"),
                    ("filename", filepath),
                    ("openmode", "tab"),
                    ("viewmode", "source"),
                    ("data", encoded_content),
                ]
            elif matched_note:
                filepath = str(matched_note.path.relative_to(notebook).with_suffix(""))
                params = [
                    ("vault", "510b22d0827fd8cf"),
                    ("filename", filepath),
                    ("viewmode", "source"),
                    ("openmode", "tab"),
                ]
            else:
                params = []

            if params:
                encoded_parts = []
                for key, value in params:
                    encoded_key = quote(str(key), safe="")
                    if key == "data":
                        encoded_value = value
                    else:
                        encoded_value = quote(str(value), safe="")
                    encoded_parts.append(f"{encoded_key}={encoded_value}")
                obsidian_url = f"obsidian://adv-uri?{'&'.join(encoded_parts)}"
                subprocess.run(["open", obsidian_url])
    except KeyboardInterrupt:
        return None
