import typer
from .notes import Note
from .tasks import Task
from .notebook import Notebook
from rich.pretty import pprint
from pathlib import Path
from typing_extensions import Annotated

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
