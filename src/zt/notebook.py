from pathlib import Path
from .notes import Note

class Notebook():
    def __init__(self, dir):
        if Path(dir).is_dir():
            self.dir = Path(dir)
        else:
            raise NotADirectoryError(f'{dir} is not a directory.')
    
    def __repr__(self):
        return(f'<Notebook at {self.dir}>')

    def notes(self):
        pass