from pathlib import Path
from .notes import Note
from .tasks import Task, TASK_STATUS
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
        files = (
            [Path(self.dir, note) for note in notes]
            if notes
            else list(self.dir.glob('*.md'))
        )
        self.notes = self.read_notes(files)
    
    def __repr__(self):
        return(f'<Notebook at {self.dir}>')

    def read_notes(self, files):
        return [(note.id, note) for note in (Note(f) for f in files)]

    def get_note_by_title(self, title):
        if not title:
            return None

        display_match = self._match_note(lambda note: title == getattr(note, "display_title", note.title))
        if display_match:
            return display_match

        normalized_query = self._normalize_display_title(title)
        if normalized_query is None:
            return None

        return self._match_note(lambda note: normalized_query == note.title)

    def _match_note(self, predicate):
        for _, note in self.notes:
            if predicate(note):
                return note
        return None

    @staticmethod
    def _normalize_display_title(title):
        trimmed = title.strip()
        if not trimmed:
            return None

        marker = " [#"
        if marker not in trimmed or not trimmed.endswith("]"):
            return trimmed

        base, _, tag_section = trimmed.partition(" [")
        tag_body = tag_section[:-1]
        tags = [fragment.strip() for fragment in tag_body.split(",") if fragment.strip()]

        if tags and all(tag.startswith("#") for tag in tags):
            return base

        return trimmed
    
    def get_tasks(self):
        command = ["rg", "--json", TASK_STATUS, self.dir]
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

        status_order = {
            '@focus': 0, 
            '@wip': 10, 
            '@project': 20,
            '@todo': 30, 
            '@next': 40, 
            '@review': 50, 
            '@waiting': 60, 
            '@later': 70, 
            '@someday': 80,
            '@done': 90,
            '@wontfix': 99
        }
        sorted_tasks = sorted(matches, key=lambda x: status_order.get(x['task'].task['status'], 6))
        with open('data.json', 'w') as fs:
            json.dump(sorted_tasks, fs, indent=2)
        tasks_fmt = [f"{task['task'].task['title']} [{task['task'].task['status']}]" for task in sorted_tasks if task['task'].task['open']]
        result = fzf_prompt(tasks_fmt, reversed_layout=True, print_query=True, match_exact=True)

        task_path = None

        query, task_title = unpack_fzf_prompt(result)

        for task in sorted_tasks:
            if task_title and (task['task'].task['title'] in task_title):
                task_path = f'{task["path"]}:{task["line"]}'
                break
        
        print(task_path)
