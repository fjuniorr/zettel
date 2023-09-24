from pathlib import Path
from fzf import fzf_prompt
from datetime import datetime
import os

class Note():
    def __init__(self, path):
        try:
            with open(path, 'r') as f:
                content = f.read()
            self.content = content
        except UnicodeDecodeError as err:
            self.content = str(err)
        self.id = os.path.splitext(os.path.basename(path))[0]
        self.title = self.content.partition('\n')[0].replace('# ', '')

    def __repr__(self) -> str:
        return f'{self.id} {self.title}'

    def title(self):
        return self.title

    def id(self):
        return self.id

def get_files(path):
    files = path.glob('*.md')
    sorted_by_mtime_descending = sorted(files, key=lambda t: -os.stat(t).st_mtime)
    return sorted_by_mtime_descending

def get_notes(path):
    for file in get_files(path):
        yield Note(file)

def get_titles(path):
    for note in get_notes(path):
        yield note.title

def unpack_fzf_prompt(prompt):
    if not prompt:
        return (None, None)
    elif len(prompt.split('\n')) == 1:
        return (prompt, None)
    else:
        return prompt.split('\n')

def ss():
    home = Path('~')

    notebook = Path(home.expanduser(), 'Notebook/')

    result = fzf_prompt(get_titles(notebook),
            keybinds = f'f2:execute-silent(subl $(zt find --dir {notebook} {{}}))',
            reversed_layout=True,
            print_query=True,
            match_exact=True,
            preview_window_settings = 'down:60%',
            preview=f'zt find --dir {notebook} {{}} | xargs glow --style dark')

    note_id = None

    query, note_title = unpack_fzf_prompt(result)

    for note in get_notes(notebook):
        if note_title and (note_title == note.title):
            note_id = note.id
            break

    if not note_title and query:
        note_id = datetime.now().strftime('%Y%m%dT%H%M%S')
        path = Path(notebook, f'{note_id}.md')
        with open(path, 'x') as file:
            file.write(f'# {query.lower()}\n\n')

    if note_id:
        print(note_id)
