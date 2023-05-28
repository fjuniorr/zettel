import typer
from .notes import Note
from .tasks import Task
from rich.pretty import pprint
import re
import yaml
from rich import print
from rich.syntax import Syntax

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
    yaml_string = """
    title: Apresentar custo da divulgação fonte STN PdT (360 h / R$ 60 mil)
    status: x
    tags:
        nirvana: null
        activity: communication
        clock: 14:48
    """

    # Create a Syntax instance and pretty-print it
    syntax = Syntax(yaml_string, "yaml")
    note = Note(note)
    tasks = [Task(line).task for line in note.content.split('\n') if re.search(r'- \[.\] ', line)]
    if status == 'all':
        print(yaml.dump(tasks))
    else:
        print(yaml.dump([task for task in tasks if task['status'] == status]))
