from pathlib import Path

class Note():
    def __init__(self, path):
        try:
            with open(path, 'r') as f:
                content = f.read()
            self.content = content
        except UnicodeDecodeError as err:
            self.content = str(err)
        self.path = Path(path)
        self.id = self.path.stem
        self.title = self.content.partition('\n')[0].replace('# ', '')

    def __repr__(self) -> str:
        return f'{self.id} {self.title}'

    def title(self):
        return self.title

    def id(self):
        return self.id
