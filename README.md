# zettel - Notetaking with Zettelkasten

A CLI program for notetaking following the [Zettelkasten Method](https://zettelkasten.de/).

## Install

```bash
pipx install .
```

## Search

Run `zt search` from a directory containing `notes/` to search that notebook. If
`ZETTEL_DIR` is set, it takes precedence. Otherwise, search falls back to
`~/Notebook` when the current directory has no `notes/` directory.

Search includes Markdown files directly in `notes/` and folders containing
`index.md` or `README.md`. If a folder contains both, `index.md` is used.
