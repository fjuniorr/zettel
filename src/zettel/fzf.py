from pathlib import Path
from fzf import fzf_prompt
from datetime import datetime
import os
import subprocess
from urllib.parse import quote

import frontmatter

COPY_KEYS = {"ctrl-c"}
ACCEPTED_KEYS = COPY_KEYS | {"enter"}


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
        self.id = os.path.splitext(os.path.basename(self.path))[0]
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
    files = path.glob("*.md")
    sorted_by_mtime_descending = sorted(files, key=lambda t: -os.stat(t).st_mtime)
    return sorted_by_mtime_descending


def get_notes(path):
    for file in get_files(path):
        yield Note(file)


def get_titles(path):
    for note in get_notes(path):
        yield note.display_title


def unpack_fzf_prompt(prompt):
    if not prompt:
        return (None, None, None)

    lines = prompt.split("\n")
    key = None

    for index, line in enumerate(list(lines[:2])):
        if line in ACCEPTED_KEYS:
            key = line
            lines.pop(index)
            break

    query = lines[0] if lines else None
    note_title = lines[1] if len(lines) > 1 and lines[1] else None

    return (key, query, note_title)


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

    while True:
        result = fzf_prompt(
            get_titles(notebook),
            keybinds=f"f2:execute-silent(subl $(zt find --dir {notebook} {{}}))",
            reversed_layout=True,
            print_query=True,
            match_exact=True,
            preview_window_settings="down:60%",
            preview=f"zt find --dir {notebook} {{}} | xargs glow --style dark",
            expect_keys="enter,ctrl-c",
            header="Enter opens in Obsidian; F2 opens in Sublime Text, ctrl+c copy note wikilink",
        )

        key_pressed, query, note_title = unpack_fzf_prompt(result)
        note_id = None
        copy_requested = key_pressed in COPY_KEYS

        for note in get_notes(notebook):
            if note_title and (note_title == note.display_title):
                note_id = note.id
                break

        if not note_title and query:
            note_id = datetime.now().strftime("%Y%m%dT%H%M%S")
            content = f"# {query.lower()}\n\n"
            encoded_content = quote(content, safe="")
            params = [
                ("vault", "510b22d0827fd8cf"),
                ("filename", note_id),
                ("openmode", "tab"),
                ("data", encoded_content),
            ]
        elif note_id:
            params = [
                ("vault", "510b22d0827fd8cf"),
                ("filename", note_id),
                ("openmode", "tab"),
            ]
        else:
            params = []

        if copy_requested and note_id:
            if copy_to_clipboard(f"[[{note_id}|{note.title}]]"):
                print(f"Copied {note_id} to clipboard")
            else:
                print(f"Note ID: {note_id} (clipboard copy failed)")
            continue

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
