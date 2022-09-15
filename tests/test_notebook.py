import pytest
from pathlib import Path
from zettel.notebook import Notebook
from zettel.notes import Note

@pytest.fixture
def notebook():
    return Notebook('tests/notebook')

def test_init(notebook):
    notebook.dir == Path('tests/notebook/')
    assert repr(notebook) == '<Notebook at tests/notebook>'

def test_not_directory_error():
    with pytest.raises(NotADirectoryError):
        notebook = Notebook('tests/notebook/notes')

def test_read_notes_full_dir(notebook):
    notes = list(notebook.notes)
    assert sorted([id for id, note in notes]) == ['20220822T111909', '20220822T155803', '20220822T163828', '20220913T211650']

def test_read_notes_specific_files():
    notebook = Notebook('tests/notebook', notes = ['20220822T111909.md', '20220822T163828.md'])
    notes = list(notebook.notes)
    assert sorted([id for id, note in notes]) == ['20220822T111909', '20220822T163828']

def test_get_note_by_title(notebook):
    note = notebook.get_note_by_title('python - mock multiple input calls')
    assert note.id == '20220822T155803'

def test_get_note_by_title_exists_false(notebook):
    note = notebook.get_note_by_title('this note do not exist')
    assert note is None

def test_notes(notebook):
    note = Note(sorted(Path('tests/notebook').glob('*.md'), key = lambda x: x.stat().st_mtime, reverse = True)[0])
    assert True