import pytest
from zt.cli import main

def test_cli_get_note_by_title(capsys):
    main(['--dir', 'tests/notebook/', 'python - mock multiple input calls'])
    stdout, stderr = capsys.readouterr()
    assert stdout == 'tests/notebook/20220822T155803.md\n'
    assert stderr == ''

def test_cli_get_note_by_title_exists_false(capsys):
    main(['--dir', 'tests/notebook/', 'this note do not exist'])
    stdout, stderr = capsys.readouterr()
    assert stdout == ''
    assert stderr == ''
