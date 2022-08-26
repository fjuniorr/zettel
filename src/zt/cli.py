import argparse
from .notebook import Notebook
from zt import notebook

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir')
    parser.add_argument('title')
    args = parser.parse_args(argv)
    
    notebook = Notebook(args.dir)
    note = notebook.get_note_by_title(args.title)

    if note is not None:
        print(note.path)

if __name__ == '__main__':
    main()