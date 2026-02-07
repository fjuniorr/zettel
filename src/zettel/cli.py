import typer
from .notes import Note
from .tasks import Task
from .notebook import Notebook
from rich.pretty import pprint
from pathlib import Path
from typing_extensions import Annotated
from .fzf import ss, copy_to_clipboard

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
        import sys
        print(f"Note not found: {title}", file=sys.stderr)
        raise typer.Exit(code=1)
    filepath = str(note.path.relative_to(dir).with_suffix(""))
    if copy_to_clipboard(f"[[{note.id}|{note.title}]]"):
        print(f"Copied {note.id} to clipboard")
    else:
        print(f"Note ID: {note.id} (clipboard copy failed)")

app.command(name="search")(ss)
