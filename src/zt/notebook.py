from pathlib import Path
from .notes import Note

class Notebook:
    def __init__(self, dir):
        if Path(dir).is_dir():
            self.dir = Path(dir)
            self.notes = self.read_notes()
        else:
            raise NotADirectoryError(f'{dir} is not a directory.')
    
    def __repr__(self):
        return(f'<Notebook at {self.dir}>')

    def read_notes(self):
        return {Note(f).id:Note(f) for f in self.dir.glob('*.md')}

    def get_note_by_title(self, title):
        for note in self.notes.values():
            if title == note.title:
                result = note
                break
        # result = [note for note in self.notes.values() if title == note.title][0]
        result = result if 'result' in locals() else None
        return result
