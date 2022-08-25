import pytest
from pathlib import Path
from zt.notebook import Notebook
from zt.notes import Note

@pytest.fixture
def notebook():
    return Notebook('tests/notebook')

def test_init(notebook):
    notebook.dir == Path('tests/notebook/')

def test_not_directory_error():
    with pytest.raises(NotADirectoryError):
        notebook = Notebook('tests/notebook/notes')

def test_get_note_by_title(notebook):
    note = notebook.get_note_by_title('python - mock multiple input calls')
    assert note.id == '20220822T155803'

def test_notes(notebook):
    note = Note(sorted(Path('tests/notebook').glob('*.md'), key = lambda x: x.stat().st_mtime, reverse = True)[0])
    assert True