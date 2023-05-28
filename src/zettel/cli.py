import typer
from .notes import Note
from .tasks import Task
from rich.pretty import pprint

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
def tasks(note: str,
          status: str = typer.Option(default="open", help="One of: all|open|closed", callback=validate_option)):
    """
    Download data packages (descriptor and resources data files) listed in package.sources and saves into datapackages/
    """
    note = Note(note)
    tasks = [Task(line).task for line in note.content.split('\n') if '@clock' in line]
    if status == 'all':
        pprint(tasks, expand_all=True)
    else:
        pprint([task for task in tasks if task['status'] == status], expand_all=True)
