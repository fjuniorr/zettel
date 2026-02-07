import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import typer
from typing_extensions import Annotated

from .fzf import ss, copy_to_clipboard
from .notebook import Notebook
from .notes import Note
from .tasks import Task

app = typer.Typer()

def validate_option(value: str):
    allowed_values = {"all", "open", "closed"}
    if value not in allowed_values:
        raise typer.BadParameter(f"Invalid option. Allowed options are {', '.join(allowed_values)}")
    return value

@app.callback()
def callback():
    """
    Plaintext personal information management.
    """

@app.command()
def tasks(dir: Annotated[Path, typer.Argument(help='Notebook folder')] = Path('.'), status: str = typer.Option(default="open", help="One of: all|open|closed", callback=validate_option)):
    """
    Find all actions itens (todos) in folder
    """
    notebook = Notebook(dir)
    notebook.get_tasks()

@app.command()
def find(title: Annotated[str, typer.Argument],
         dir: Annotated[Path, typer.Option(help='Notebook folder')] = Path('.')
         ):
    notebook = Notebook(dir)
    note = notebook.get_note_by_title(title)
    if note is not None:
        print(note.path)

@app.command()
def copy(title: Annotated[str, typer.Argument],
         dir: Annotated[Path, typer.Option(help='Notebook folder')] = Path('.')
         ):
    """
    Copy a wikilink for a note to the clipboard.
    """
    notebook = Notebook(dir)
    note = notebook.get_note_by_title(title)
    if note is None:
        print(f"Note not found: {title}", file=sys.stderr)
        raise typer.Exit(code=1)
    if copy_to_clipboard(f"[[{note.id}|{note.title}]]"):
        print(f"Copied {note.id} to clipboard")
    else:
        print(f"Note ID: {note.id} (clipboard copy failed)")

VAULT_ID = "510b22d0827fd8cf"

def _build_obsidian_url(params):
    encoded_parts = []
    for key, value in params:
        encoded_key = quote(str(key), safe="")
        if key == "data":
            encoded_value = value
        else:
            encoded_value = quote(str(value), safe="")
        encoded_parts.append(f"{encoded_key}={encoded_value}")
    return f"obsidian://adv-uri?{'&'.join(encoded_parts)}"

@app.command(name="open")
def open_note(title: Annotated[Optional[str], typer.Argument()] = None,
              query: Annotated[Optional[str], typer.Option()] = None,
              dir: Annotated[Path, typer.Option(help='Notebook folder')] = Path('.')
              ):
    """
    Open a note in Obsidian, or create a new one from a query.
    """
    title = title.strip() if title else None
    query = query.strip() if query else None

    if title:
        notebook = Notebook(dir)
        note = notebook.get_note_by_title(title)
        if note is None:
            return
        filepath = str(note.path.relative_to(dir).with_suffix(""))
        params = [
            ("vault", VAULT_ID),
            ("filename", filepath),
            ("viewmode", "source"),
            ("openmode", "tab"),
        ]
    elif query:
        note_id = datetime.now().strftime("%Y%m%dT%H%M%S")
        filepath = f"{note_id}/index"
        content = f"# {query.lower()}\n\n"
        encoded_content = quote(content, safe="")
        params = [
            ("vault", VAULT_ID),
            ("filename", filepath),
            ("openmode", "tab"),
            ("viewmode", "source"),
            ("data", encoded_content),
        ]
    else:
        return

    subprocess.run(["open", _build_obsidian_url(params)])

app.command(name="search")(ss)
