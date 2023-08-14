import pytest
from zettel.notebook import Notebook
from zettel.tasks import Task

@pytest.fixture
def notebook():
    return Notebook('tests/notebook')

def test_tasks(notebook):
    expected = [
                {'title': 'Publicar dados abertos', 'status': 'done', 'tags': {'clock': '51:15', 'url': 'https://github.com/splor-mg/ppag2023-dadosmg/issues/14'}},
                {'title': 'Main task', 'status': 'next', 'tags': {'clock': '25:00'}}, 
                {'title': 'https://github.com/splor-mg/ppag2023-dadosmg/issues/14', 'status': 'someday', 'tags': {'clock': '51:15'}}, 
                {'title': 'Levantamento técnico inicial (diagramas c4)', 'status': 'done', 'tags': {'nirvana': True, 'clock': '02:08:49', 'activity': 'research'}}, 
                ]
    assert [task.task for task in notebook.get_tasks()] == expected

def test_task():
    task = Task('- [x] Levantamento técnico inicial (diagramas c4) @nirvana @clock(09:14, 01:59:35) @activity(research)')
    assert task.task['title'] == 'Levantamento técnico inicial (diagramas c4)'