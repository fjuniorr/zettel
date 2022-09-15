from zettel.notes import Note

def test_get_note_title():
    note = Note('tests/notebook/20220822T111909.md')
    assert note.title == 'python workouts - lerner2020 - ex 4.15'

def test_get_note_id():
    note = Note('tests/notebook/20220822T111909.md')
    assert note.id == '20220822T111909'

def test_unicode_decode_error():
    note = Note('tests/notebook/20220913T211650.md')
    assert "'utf-8' codec can't decode byte" in note.content

def test_note_repr():
    note = Note('tests/notebook/20220822T111909.md')
    assert repr(note) == '[20220822T111909] python workouts - lerner2020 - ex 4.15'
