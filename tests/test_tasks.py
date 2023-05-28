import pytest
from zettel.notebook import Notebook
from zettel.tasks import Task
from pathlib import Path

@pytest.fixture
def notebook():
    return Notebook('tests/notebook')

def test_tasks(notebook):
    expected = [
                {'id': 'daily-20230528', 'title': 'https://github.com/splor-mg/ppag2023-dadosmg/issues/14', 'status': 'Todo', 'created_at': '20230528', 'tags': {'clock': '51:15'}}, 
                {'id': 'daily-20230528', 'title': 'Levantamento técnico inicial (diagramas c4)', 'status': 'Done ', 'created_at': '20230528', 'tags': {'nirvana': True, 'clock': '02:08:49', 'activity': 'research'}}, 
                ]
    assert [task.task for task in notebook.get_tasks()] == expected

def test_task():
    task = Task('daily-20230528.md', '- [x] Levantamento técnico inicial (diagramas c4) @nirvana @clock(09:14, 01:59:35) @activity(research)')
    assert task.task['title'] == 'Levantamento técnico inicial (diagramas c4)'