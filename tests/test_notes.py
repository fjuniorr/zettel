from zt.notes import Note

def test_get_note_title():
    note = Note('tests/notebook/20220822T111909.md')
    assert note.title == 'python workouts - lerner2020 - ex 4.15'

def test_get_note_id():
    note = Note('tests/notebook/20220822T111909.md')
    assert note.id == '20220822T111909'
