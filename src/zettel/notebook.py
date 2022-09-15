from pathlib import Path
from .notes import Note

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
