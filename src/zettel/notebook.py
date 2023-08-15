from pathlib import Path
from .notes import Note
from .tasks import Task
from .utils import unpack_fzf_prompt
import subprocess
import json
from fzf import fzf_prompt
from pathlib import Path

class Notebook:
    def __init__(self, dir, notes=None):
        if not Path(dir).is_dir():
            raise NotADirectoryError(f'{dir} is not a directory.') 
        self.dir = Path(dir)
        if notes:
            self.notes = self.read_notes([Path(self.dir, note) for note in notes])
        else:
            self.notes = self.read_notes(self.dir.glob('*.md'))
    
    def __repr__(self):
        return(f'<Notebook at {self.dir}>')

    def read_notes(self, files):
        for note in (Note(f) for f in files):
            yield note.id, note

    def get_note_by_title(self, title):
        for note_id, note in self.notes:
            if title == note.title:
                result = note
                break
        # result = [note for note in self.notes.values() if title == note.title][0]
        result = result if 'result' in locals() else None
        return result
    
    def get_tasks(self):
        command = ["rg", "--json", "@todo", self.dir]
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True)

        matches = []
        for line in result.stdout.splitlines():
            data = json.loads(line)
            if data["type"] == "match":
                match_data = {
                    "path": Path(data["data"]["path"]["text"]).stem,
                    "line": data["data"]["line_number"],
                    "task": Task(data["data"]["lines"]["text"])
                }
                matches.append(match_data)

        
        status_order = {'focus': 0, 'in progress': 1, 'next': 2, 'someday': 3, 'done': 4}
        sorted_tasks = sorted(matches, key=lambda x: status_order.get(x['task'].task['status'], 5))
        
        tasks_fmt = [f"{task['task'].task['title']} [#{task['task'].task['status']}]" for task in sorted_tasks if task['task'].task['open']]
        result = fzf_prompt(tasks_fmt, reversed_layout=True, print_query=True, match_exact=True)

        task_path = None

        query, task_title = unpack_fzf_prompt(result)

        for task in sorted_tasks:
            if task_title and (task['task'].task['title'] in task_title):
                task_path = f'{task["path"]}:{task["line"]}'
                break
        
        print(task_path)
