import pytest
import datetime
from zettel.notebook import Notebook
from zettel.tasks import Task

@pytest.fixture
def notebook():
    return Notebook('tests/notebook')

def test_tasks(notebook):
    expected = [
                {'title': 'Publicar dados abertos','open': False, 'status': 'done', 'duration': '51.25 minutes' , 'tags': {'url': 'https://github.com/splor-mg/ppag2023-dadosmg/issues/14', 'clock': [{'start': None, 'end': None, 'duration': datetime.timedelta(seconds=3075)}]}},
                {'title': 'Main task','open': True, 'status': 'next', 'duration': '25 minutes' , 'tags': {'clock': [
                    {'start': None, 'end': None, 'duration': datetime.timedelta(seconds=1500)}
                ]}}, 
                {'title': 'https://github.com/splor-mg/ppag2023-dadosmg/issues/14','open': True, 'status': 'someday', 'duration': '51.25 minutes' , 'tags': {'clock': [
                    {'start': None, 'end': None, 'duration': datetime.timedelta(seconds=3075)}
                ]}}, 
                {'title': 'Levantamento técnico inicial (diagramas c4)','open': False, 'status': 'done', 'duration': '2 hours and 8.82 minutes' , 'tags': {'nirvana': True, 'clock': [
                             {'start': None, 'end': None, 'duration': datetime.timedelta(seconds=554)}, 
                             {'start': None, 'end': None, 'duration': datetime.timedelta(seconds=7175)}
                         ], 'activity': 'research'}}, 
                ]
    assert [task.task for task in notebook.get_tasks()] == expected

def test_task():
    task = Task('- [x] Levantamento técnico inicial @nirvana @clock(20230814T155459/09:14, 20230815T155503/01:59:35) @activity(research)')
    
    expected = {'title': 'Levantamento técnico inicial', 
                'open': False, 
                'status': 'done', 
                'duration': '2 hours and 8.82 minutes', 
                'tags': {'nirvana': True, 
                         'clock': [
                             {'start': datetime.datetime(2023, 8, 14, 15, 54, 59), 'end': datetime.datetime(2023, 8, 14, 16, 4, 13), 'duration': datetime.timedelta(seconds=554)}, 
                             {'start': datetime.datetime(2023, 8, 15, 15, 55, 3), 'end': datetime.datetime(2023, 8, 15, 17, 54, 38), 'duration': datetime.timedelta(seconds=7175)}
                         ], 
                         'activity': 'research'}}
    
    assert task.task == expected

def test_task_without_start_clock():
    task = Task('- [x] Levantamento técnico inicial @nirvana @clock(09:14, 20230815T155503/01:59:35) @activity(research)')
    
    expected = {'title': 'Levantamento técnico inicial', 
                'open': False, 
                'status': 'done', 
                'duration': '2 hours and 8.82 minutes', 
                'tags': {'nirvana': True, 
                         'clock': [
                             {'start': None, 'end': None, 'duration': datetime.timedelta(seconds=554)}, 
                             {'start': datetime.datetime(2023, 8, 15, 15, 55, 3), 'end': datetime.datetime(2023, 8, 15, 17, 54, 38), 'duration': datetime.timedelta(seconds=7175)}
                         ], 
                         'activity': 'research'}}
    
    assert task.task == expected

def test_task_without_clock():
    task = Task('- [ ] Levantamento técnico inicial @nirvana @activity(research)')
    
    expected = {'title': 'Levantamento técnico inicial', 
                'open': True, 
                'status': 'next', 
                'duration': None, 
                'tags': {'nirvana': True, 
                         'clock': None, 
                         'activity': 'research'}}
    
    assert task.task == expected