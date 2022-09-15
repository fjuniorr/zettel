import argparse
from .notebook import Notebook
from zettel import notebook
import sys

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir')
    parser.add_argument('title')
    args = parser.parse_args(argv)
    
    if sys.stdin.isatty():
        notebook = Notebook(args.dir)
    else:
        files = sys.stdin.read().splitlines()
        notebook = Notebook(args.dir, notes = files)
    
    note = notebook.get_note_by_title(args.title)

    if note is not None:
        print(note.path)

if __name__ == '__main__':
    main()