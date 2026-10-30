# MyProjects

A small desktop project tracker built with Python + Tkinter.

## What it does

- Add projects (name + optional note), each with a start date.
- Mark a project done — a completion date is recorded automatically.
- Each project has a set of subcategories (workflow stages) with checkboxes.
- Click a subcategory to open a window with a "Tasks" list (add/remove your own
  tasks) and a comment field.
- Filter by Active / Done / All and search by name or note.
- Data is saved automatically to `~/.local/share/myprojects/projects.json`.

## Run it

```bash
python3 myprojects.py
```

Requires Python 3 and Tkinter (on Arch: `sudo pacman -S tk`).

## Install as a desktop app (Linux)

1. Put `myprojects.py` somewhere stable, e.g. `~/.local/bin/myprojects`.
2. Copy `myprojects.desktop` to `~/.local/share/applications/` and make sure
   the `Exec=` line points at your copy.
3. (Optional) Generate an app icon with `python3 make_icon.py` — it writes PNGs
   to `~/.local/share/icons/hicolor/`.
