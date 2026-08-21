import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from zettel.cli import app
from zettel.fzf import NOTES_DIR, Note, parse_fzf_output, ss
from zettel.notebook import Notebook


def write_note(tmp_path, name, content):
    note_path = tmp_path / name
    note_path.write_text(content)
    return note_path


def test_note_uses_frontmatter_title_and_tags(tmp_path):
    content = """---\ntitle: YAML Title\ntags:\n  - alpha\n  - beta\n---\n# heading\nbody\n"""
    note_path = write_note(tmp_path, "20240101T101010.md", content)

    note = Note(note_path)

    assert note.title == "YAML Title"
    assert note.tags == ["alpha", "beta"]
    assert note.display_title == "YAML Title [#alpha, #beta]"


def test_note_parses_string_tags_and_strips_hash(tmp_path):
    content = """---\ntitle: Another Title\ntags: alpha, beta , #gamma\n---\ncontent\n"""
    note_path = write_note(tmp_path, "20240102T101010.md", content)

    note = Note(note_path)

    assert note.tags == ["alpha", "beta", "gamma"]
    assert note.display_title == "Another Title [#alpha, #beta, #gamma]"


def test_note_falls_back_to_header_when_no_frontmatter(tmp_path):
    content = "# Header Title\nMore content\n"
    note_path = write_note(tmp_path, "20240103T101010.md", content)

    note = Note(note_path)

    assert note.title == "Header Title"
    assert note.display_title == "Header Title"


@pytest.mark.parametrize(
    "prompt,expected",
    [
        ("new note\n", ("new note", None)),
        ("  spaced query  \nExisting Title", ("spaced query", "Existing Title")),
        ("\n", (None, None)),
        ("", (None, None)),
    ],
)
def test_parse_fzf_output(prompt, expected):
    assert parse_fzf_output(prompt) == expected


def test_notebook_matches_display_title_and_plain_title(tmp_path):
    note_dir = tmp_path / "notebook"
    (note_dir / NOTES_DIR).mkdir(parents=True)
    content = """---\ntitle: Display Title\ntags:\n  - alpha\n---\nBody\n"""
    write_note(note_dir / NOTES_DIR, "20240104T101010.md", content)

    notebook = Notebook(note_dir)
    stored_note = next(iter(notebook.notes))[1]

    assert notebook.get_note_by_title(stored_note.display_title).id == stored_note.id
    assert notebook.get_note_by_title(stored_note.title).id == stored_note.id


def test_cli_copy_uses_wikilink(monkeypatch, tmp_path):
    note_dir = tmp_path / "notebook"
    (note_dir / NOTES_DIR).mkdir(parents=True)
    content = """---\ntitle: Copy Title\n---\nBody\n"""
    write_note(note_dir / NOTES_DIR, "20240105T101010.md", content)

    captured = {}

    def fake_copy(text):
        captured["text"] = text
        return True

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("zettel.cli.copy_to_clipboard", fake_copy)

    runner = CliRunner()
    result = runner.invoke(app, ["copy", "--dir", str(note_dir), "Copy Title"])

    assert result.exit_code == 0
    assert captured["text"] == "[[20240105T101010|Copy Title]]"


def test_cli_copy_uses_folder_path_for_index_notes(monkeypatch, tmp_path):
    note_dir = tmp_path / "notebook"
    folder = note_dir / NOTES_DIR / "20240106T101010"
    folder.mkdir(parents=True)
    content = """---\ntitle: Folder Note\n---\nBody\n"""
    write_note(folder, "index.md", content)

    captured = {}

    def fake_copy(text):
        captured["text"] = text
        return True

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("zettel.cli.copy_to_clipboard", fake_copy)

    runner = CliRunner()
    result = runner.invoke(app, ["copy", "--dir", str(note_dir), "Folder Note"])

    assert result.exit_code == 0
    assert captured["text"] == "[[20240106T101010/index|Folder Note]]"


def test_cli_copy_errors_when_note_missing(monkeypatch, tmp_path):
    note_dir = tmp_path / "notebook"
    (note_dir / NOTES_DIR).mkdir(parents=True)

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("zettel.cli.copy_to_clipboard", lambda text: True)

    runner = CliRunner()
    result = runner.invoke(app, ["copy", "--dir", str(note_dir), "Missing Title"])

    assert result.exit_code != 0
    assert "not found" in (result.stderr or "").lower()


def test_ss_handles_keyboard_interrupt(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "Notebook").mkdir()

    def fake_fzf_prompt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("zettel.fzf.fzf_prompt", fake_fzf_prompt)

    # Should return without raising
    assert ss() is None


class FakeRun:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _make_notebook(tmp_path):
    notes = tmp_path / NOTES_DIR
    notes.mkdir(parents=True)
    return tmp_path, notes


def test_cli_share_creates_private_gist_by_default(monkeypatch, tmp_path):
    note_dir, actions = _make_notebook(tmp_path)
    content = """---\ntitle: Share Me\ntags:\n  - alpha\n---\nBody\n"""
    note_path = write_note(actions, "20240201T101010.md", content)

    calls = []

    def fake_run(cmd, capture_output=False, text=False):
        calls.append(cmd)
        return FakeRun(stdout="https://gist.github.com/user/abc123\n")

    monkeypatch.setattr("zettel.cli.subprocess.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(app, ["share", "--dir", str(note_dir), "Share Me"])

    assert result.exit_code == 0, result.output
    assert calls == [["gh", "gist", "create", str(note_path)]]
    assert "https://gist.github.com/user/abc123" in result.stdout

    import frontmatter as fm

    post = fm.load(str(note_path))
    assert post.metadata["gist"] == "https://gist.github.com/user/abc123"
    assert "gist" in post.metadata["tags"]
    assert list(post.metadata.keys())[-1] == "gist"

    raw = note_path.read_text()
    # gist should be the final key line before the closing "---"
    metadata_block = raw.split("---", 2)[1]
    last_key_line = [
        line for line in metadata_block.strip().splitlines() if re.match(r"^\S", line)
    ][-1]
    assert last_key_line.startswith("gist:")


def test_cli_share_public_flag_adds_public(monkeypatch, tmp_path):
    note_dir, actions = _make_notebook(tmp_path)
    content = """---\ntitle: Public Note\n---\nBody\n"""
    note_path = write_note(actions, "20240202T101010.md", content)

    calls = []

    def fake_run(cmd, capture_output=False, text=False):
        calls.append(cmd)
        return FakeRun(stdout="https://gist.github.com/user/pub999\n")

    monkeypatch.setattr("zettel.cli.subprocess.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(
        app, ["share", "--dir", str(note_dir), "--public", "Public Note"]
    )

    assert result.exit_code == 0, result.output
    assert calls == [["gh", "gist", "create", str(note_path), "--public"]]


def test_cli_share_updates_existing_gist(monkeypatch, tmp_path):
    note_dir, actions = _make_notebook(tmp_path)
    content = (
        "---\n"
        "title: Already Shared\n"
        "gist: https://gist.github.com/user/deadbeef\n"
        "---\n"
        "Body\n"
    )
    note_path = write_note(actions, "20240203T101010.md", content)

    calls = []

    def fake_run(cmd, capture_output=False, text=False):
        calls.append(cmd)
        return FakeRun(stdout="")

    monkeypatch.setattr("zettel.cli.subprocess.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(app, ["share", "--dir", str(note_dir), "20240203T101010"])

    assert result.exit_code == 0, result.output
    assert calls == [["gh", "gist", "edit", "deadbeef", str(note_path)]]
    assert "Updated gist" in result.stdout


def test_cli_share_errors_when_note_missing(monkeypatch, tmp_path):
    note_dir, _ = _make_notebook(tmp_path)

    def fail_run(*args, **kwargs):
        raise AssertionError("gh should not be invoked when the note is missing")

    monkeypatch.setattr("zettel.cli.subprocess.run", fail_run)

    runner = CliRunner()
    result = runner.invoke(app, ["share", "--dir", str(note_dir), "Nope"])

    assert result.exit_code != 0
    assert "not found" in (result.stderr or "").lower()


def test_cli_share_propagates_gh_failure(monkeypatch, tmp_path):
    note_dir, actions = _make_notebook(tmp_path)
    content = """---\ntitle: Fails\n---\nBody\n"""
    write_note(actions, "20240204T101010.md", content)

    def fake_run(cmd, capture_output=False, text=False):
        return FakeRun(stderr="gh: not authenticated\n", returncode=1)

    monkeypatch.setattr("zettel.cli.subprocess.run", fake_run)

    runner = CliRunner()
    result = runner.invoke(app, ["share", "--dir", str(note_dir), "Fails"])

    assert result.exit_code != 0
    assert "not authenticated" in (result.stderr or "").lower()
