#!/usr/bin/python3
"""MyProjects — a small desktop project tracker.

Data lives in ~/.local/share/myprojects/projects.json
Each project has a set of subcategories; each subcategory has a checkbox
and a comment.
"""

import json
import os
import shutil
import uuid
import tkinter as tk
from tkinter import ttk
from datetime import datetime

APP_NAME = "MyProjects"
DATA_DIR = os.path.expanduser("~/.local/share/myprojects")
DATA_FILE = os.path.join(DATA_DIR, "projects.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# --- palette (dark, to match a Hyprland desktop) ---
BG        = "#1e1e2e"
SURFACE   = "#181825"
SURFACE2  = "#313244"
FG        = "#cdd6f4"
MUTED     = "#7f849c"
ACCENT    = "#89b4fa"
ACCENT_DK = "#11111b"
GREEN     = "#a6e3a1"
RED       = "#f38ba8"
BORDER    = "#45475a"

# Project subcategories (workflow stages, user-defined).
DEFAULT_SUBCATEGORIES = [
    "Registration", "Software", "Web", "Apple", "Test",
    "Maintenance", "Completion",
]


def today():
    return datetime.now().strftime("%Y-%m-%d")


def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def load_default_subcategories():
    names = load_settings().get("default_subcategories")
    if isinstance(names, list) and names:
        return [str(n) for n in names if str(n).strip()]
    return list(DEFAULT_SUBCATEGORIES)


def save_default_subcategories(names):
    settings = load_settings()
    settings["default_subcategories"] = names
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = SETTINGS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    os.replace(tmp, SETTINGS_FILE)


def make_default_subcategories():
    return [{"name": n, "checked": False, "comment": "",
             "subsubcategories": []}
            for n in load_default_subcategories()]


def load_projects():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        try:
            shutil.copy(DATA_FILE, DATA_FILE + ".corrupt")
        except OSError:
            pass
    return []


def save_projects(projects):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


class ProjectDialog(tk.Toplevel):
    """Modal add/edit dialog with a name and a note field."""

    def __init__(self, master, title, name="", note=""):
        super().__init__(master)
        self.result = None
        self.title(title)
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(master)

        outer = tk.Frame(self, bg=BG, padx=18, pady=18)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text=title, bg=BG, fg=FG,
                 font=("", 18, "bold")).pack(anchor="w")

        tk.Label(outer, text="Project name", bg=BG, fg=MUTED,
                 font=("", 18)).pack(anchor="w", pady=(14, 2))
        self.name_var = tk.StringVar(value=name)
        name_entry = tk.Entry(outer, textvariable=self.name_var, bg=SURFACE2,
                              fg=FG, insertbackground=FG, relief="flat",
                              highlightthickness=1, highlightbackground=BORDER,
                              highlightcolor=ACCENT, font=("", 18))
        name_entry.pack(fill="x", ipady=6)

        tk.Label(outer, text="Notes (optional)", bg=BG, fg=MUTED,
                 font=("", 18)).pack(anchor="w", pady=(12, 2))
        self.note_text = tk.Text(outer, height=5, bg=SURFACE2, fg=FG,
                                 insertbackground=FG, relief="flat",
                                 highlightthickness=1,
                                 highlightbackground=BORDER,
                                 highlightcolor=ACCENT, font=("", 18),
                                 wrap="word")
        self.note_text.insert("1.0", note)
        self.note_text.pack(fill="both", expand=True)

        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill="x", pady=(16, 0))
        tk.Button(btn_row, text="Cancel", command=self.destroy,
                  bg=SURFACE2, fg=FG, activebackground=SURFACE2,
                  activeforeground=FG, relief="flat", bd=0,
                  highlightthickness=0, font=("", 14), padx=16, pady=6,
                  cursor="hand2").pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="Save", command=self._save,
                  bg=ACCENT, fg=ACCENT_DK, activebackground=GREEN,
                  activeforeground=ACCENT_DK, relief="flat", bd=0,
                  highlightthickness=0, font=("", 14, "bold"),
                  padx=20, pady=6, cursor="hand2").pack(side="right")

        name_entry.focus_set()
        name_entry.select_range(0, "end")
        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._outside_funcid = master.bind("<Button-1>",
                                           self._on_outside_click, add="+")

    def _on_outside_click(self, event):
        self.destroy()

    def destroy(self):
        if getattr(self, "_outside_funcid", None):
            try:
                self.master.unbind("<Button-1>", self._outside_funcid)
            except tk.TclError:
                pass
            self._outside_funcid = None
        super().destroy()

    def _save(self):
        name = self.name_var.get().strip()
        if not name:
            self.bell()
            return
        self.result = (name, self.note_text.get("1.0", "end").strip())
        self.destroy()


class SubcategoryWindow(tk.Toplevel):
    """Modal window for one subcategory: sub-subcategories + a comment field."""

    def __init__(self, master, subcategory):
        super().__init__(master)
        self.sub = subcategory
        self.title(subcategory.get("name", "Subcategory"))
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(master)

        outer = tk.Frame(self, bg=BG, padx=18, pady=18)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text=subcategory.get("name", ""), bg=BG, fg=FG,
                 font=("", 18, "bold")).pack(anchor="w")

        tk.Label(outer, text="Tasks", bg=BG, fg=MUTED,
                 font=("", 18)).pack(anchor="w", pady=(14, 2))
        ss_frame = tk.Frame(outer, bg=SURFACE2)
        ss_frame.pack(fill="both", expand=True)
        self.subsub = tk.Listbox(ss_frame, height=6, bg=SURFACE2, fg=FG,
                                 relief="flat", highlightthickness=0,
                                 font=("", 18), activestyle="none",
                                 selectbackground=SURFACE,
                                 selectforeground=FG)
        ss_scroll = ttk.Scrollbar(ss_frame, orient="vertical",
                                  command=self.subsub.yview)
        self.subsub.configure(yscrollcommand=ss_scroll.set)
        self.subsub.pack(side="left", fill="both", expand=True)
        ss_scroll.pack(side="right", fill="y")
        self._subsub_items = []
        for ss in subcategory.get("subsubcategories", []):
            name = ss.get("name") if isinstance(ss, dict) else ss
            checked = ss.get("checked", False) if isinstance(ss, dict) \
                else False
            self.subsub.insert("end", ("☑" if checked else "☐") + "  " + name)
            self._subsub_items.append(
                ss if isinstance(ss, dict) else {"name": name,
                                                 "checked": checked})
        self.subsub.bind("<Button-1>", self._toggle_subsub)

        add_row = tk.Frame(outer, bg=BG)
        add_row.pack(fill="x", pady=(6, 0))
        self.subsub_entry = tk.Entry(add_row, bg=SURFACE2, fg=FG,
                                     insertbackground=FG, relief="flat",
                                     highlightthickness=1,
                                     highlightbackground=BORDER,
                                     highlightcolor=ACCENT, font=("", 18))
        self.subsub_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.subsub_entry.bind("<Return>", self._add_subsub)
        tk.Button(add_row, text="+ Add", command=self._add_subsub,
                  bg=ACCENT, fg=ACCENT_DK, activebackground=GREEN,
                  activeforeground=ACCENT_DK, relief="flat", bd=0,
                  highlightthickness=0, font=("", 14, "bold"),
                  padx=12, pady=4, cursor="hand2").pack(side="left",
                                                        padx=(8, 0))
        tk.Button(add_row, text="Remove", command=self._remove_subsub,
                  bg=SURFACE2, fg=RED, activebackground=SURFACE2,
                  activeforeground=RED, relief="flat", bd=0,
                  highlightthickness=0, font=("", 14),
                  padx=12, pady=4, cursor="hand2").pack(side="left",
                                                        padx=(8, 0))

        tk.Label(outer, text="Comment", bg=BG, fg=MUTED,
                 font=("", 18)).pack(anchor="w", pady=(12, 2))
        self.comment = tk.Text(outer, height=5, bg=SURFACE2, fg=FG,
                               insertbackground=FG, relief="flat",
                               highlightthickness=1, highlightbackground=BORDER,
                               highlightcolor=ACCENT, font=("", 18),
                               wrap="word")
        self.comment.insert("1.0", subcategory.get("comment", ""))
        self.comment.pack(fill="both", expand=True)

        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill="x", pady=(14, 0))
        tk.Button(btn_row, text="Cancel", command=self.destroy,
                  bg=SURFACE2, fg=FG, activebackground=SURFACE2,
                  activeforeground=FG, relief="flat", bd=0,
                  highlightthickness=0, font=("", 14), padx=16, pady=6,
                  cursor="hand2").pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="Save", command=self._save,
                  bg=ACCENT, fg=ACCENT_DK, activebackground=GREEN,
                  activeforeground=ACCENT_DK, relief="flat", bd=0,
                  highlightthickness=0, font=("", 14, "bold"),
                  padx=20, pady=6, cursor="hand2").pack(side="right")

        self.comment.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self._save)
        self._outside_funcid = master.bind("<Button-1>",
                                           self._on_outside_click, add="+")

    def _on_outside_click(self, event):
        self._save()

    def destroy(self):
        if getattr(self, "_outside_funcid", None):
            try:
                self.master.unbind("<Button-1>", self._outside_funcid)
            except tk.TclError:
                pass
            self._outside_funcid = None
        super().destroy()

    def _toggle_subsub(self, event):
        idx = self.subsub.nearest(event.y)
        if idx < 0 or idx >= len(self._subsub_items):
            return
        ss = self._subsub_items[idx]
        ss["checked"] = not ss.get("checked", False)
        self.subsub.delete(idx)
        self.subsub.insert(idx, ("☑" if ss["checked"] else "☐") + "  " +
                           ss["name"])
        self.subsub.selection_clear(0, "end")
        self.subsub.selection_set(idx)

    def _add_subsub(self, event=None):
        name = self.subsub_entry.get().strip()
        if not name:
            self.bell()
            return
        new = {"name": name, "checked": False}
        self.sub["subsubcategories"].append(new)
        self._subsub_items.append(new)
        self.subsub.insert("end", "☐  " + name)
        self.subsub_entry.delete(0, "end")

    def _remove_subsub(self):
        sel = self.subsub.curselection()
        if not sel:
            self.bell()
            return
        idx = sel[0]
        self._subsub_items.pop(idx)
        self.sub["subsubcategories"].pop(idx)
        self.subsub.delete(idx)

    def _save(self):
        self.sub["comment"] = self.comment.get("1.0", "end").strip()
        self.destroy()


class ManageSubcategoriesWindow(tk.Toplevel):
    """Edit one project's subcategory list: add, remove, and reorder."""

    def __init__(self, master, names, project_name=""):
        super().__init__(master)
        self.result = None  # list of names, or None on cancel
        self.title("Manage Subcategories")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(master)

        outer = tk.Frame(self, bg=BG, padx=18, pady=18)
        outer.pack(fill="both", expand=True)

        heading = "Subcategories" + (" \u2014 " + project_name if project_name else "")
        tk.Label(outer, text=heading, bg=BG, fg=FG,
                 font=("", 18, "bold")).pack(anchor="w")
        tk.Label(outer, text="These stages belong to this project only, in order.",
                 bg=BG, fg=MUTED, font=("", 13)).pack(anchor="w", pady=(2, 10))

        mid = tk.Frame(outer, bg=BG)
        mid.pack(fill="both", expand=True)

        lb_frame = tk.Frame(mid, bg=SURFACE2)
        lb_frame.pack(side="left", fill="both", expand=True)
        self.listbox = tk.Listbox(lb_frame, height=10, width=30, bg=SURFACE2,
                                  fg=FG, relief="flat", highlightthickness=0,
                                  font=("", 18), activestyle="none",
                                  selectbackground=SURFACE,
                                  selectforeground=FG)
        lb_scroll = ttk.Scrollbar(lb_frame, orient="vertical",
                                  command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=lb_scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        lb_scroll.pack(side="right", fill="y")
        for n in names:
            self.listbox.insert("end", n)

        side = tk.Frame(mid, bg=BG)
        side.pack(side="left", fill="y", padx=(10, 0))
        self._side_btn(side, "Move Up", self._move_up).pack(fill="x", pady=(0, 6))
        self._side_btn(side, "Move Down", self._move_down).pack(fill="x", pady=(0, 6))
        self._side_btn(side, "Remove", self._remove, danger=True).pack(fill="x")

        add_row = tk.Frame(outer, bg=BG)
        add_row.pack(fill="x", pady=(10, 0))
        self.add_entry = tk.Entry(add_row, bg=SURFACE2, fg=FG,
                                  insertbackground=FG, relief="flat",
                                  highlightthickness=1,
                                  highlightbackground=BORDER,
                                  highlightcolor=ACCENT, font=("", 18))
        self.add_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.add_entry.bind("<Return>", self._add)
        tk.Button(add_row, text="+ Add", command=self._add,
                  bg=ACCENT, fg=ACCENT_DK, activebackground=GREEN,
                  activeforeground=ACCENT_DK, relief="flat", bd=0,
                  highlightthickness=0, font=("", 14, "bold"),
                  padx=12, pady=4, cursor="hand2").pack(side="left", padx=(8, 0))

        tk.Label(outer, text="Removing a stage deletes its tasks and notes "
                             "in this project.",
                 bg=BG, fg=MUTED, font=("", 13), justify="left").pack(
            anchor="w", pady=(12, 0))

        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill="x", pady=(14, 0))
        tk.Button(btn_row, text="Cancel", command=self.destroy,
                  bg=SURFACE2, fg=FG, activebackground=SURFACE2,
                  activeforeground=FG, relief="flat", bd=0,
                  highlightthickness=0, font=("", 14), padx=16, pady=6,
                  cursor="hand2").pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="Save", command=self._save,
                  bg=ACCENT, fg=ACCENT_DK, activebackground=GREEN,
                  activeforeground=ACCENT_DK, relief="flat", bd=0,
                  highlightthickness=0, font=("", 14, "bold"),
                  padx=20, pady=6, cursor="hand2").pack(side="right")

        self.add_entry.focus_set()
        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._outside_funcid = master.bind("<Button-1>",
                                           self._on_outside_click, add="+")

    def _side_btn(self, parent, text, command, danger=False):
        fg = RED if danger else FG
        return tk.Button(parent, text=text, command=command, bg=SURFACE2,
                         fg=fg, activebackground=SURFACE2, activeforeground=fg,
                         relief="flat", bd=0, highlightthickness=0,
                         font=("", 14), padx=14, pady=4, cursor="hand2")

    def _on_outside_click(self, event):
        self.destroy()

    def destroy(self):
        if getattr(self, "_outside_funcid", None):
            try:
                self.master.unbind("<Button-1>", self._outside_funcid)
            except tk.TclError:
                pass
            self._outside_funcid = None
        super().destroy()

    def _names(self):
        return list(self.listbox.get(0, "end"))

    def _selected_index(self):
        sel = self.listbox.curselection()
        return sel[0] if sel else None

    def _add(self, event=None):
        name = self.add_entry.get().strip()
        if not name or name in self._names():
            self.bell()
            return
        self.listbox.insert("end", name)
        self.add_entry.delete(0, "end")
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set("end")
        self.listbox.see("end")

    def _remove(self):
        idx = self._selected_index()
        if idx is None:
            self.bell()
            return
        self.listbox.delete(idx)
        if self.listbox.size():
            self.listbox.selection_set(min(idx, self.listbox.size() - 1))

    def _move_up(self):
        idx = self._selected_index()
        if idx is None or idx == 0:
            return
        name = self.listbox.get(idx)
        self.listbox.delete(idx)
        self.listbox.insert(idx - 1, name)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(idx - 1)
        self.listbox.see(idx - 1)

    def _move_down(self):
        idx = self._selected_index()
        if idx is None or idx >= self.listbox.size() - 1:
            return
        name = self.listbox.get(idx)
        self.listbox.delete(idx)
        self.listbox.insert(idx + 1, name)
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(idx + 1)
        self.listbox.see(idx + 1)

    def _save(self):
        names = self._names()
        if not names:
            self.bell()
            return
        self.result = names
        self.destroy()


class MyProjectsApp:
    def __init__(self, root):
        self.root = root
        self.projects = load_projects()
        self.filter_var = tk.StringVar(value="active")
        self.search_var = tk.StringVar()
        self.search_ph = "Search"
        self._sub_vars = []

        # upgrade any project that predates subcategories / sub-subcategories
        changed = False
        for p in self.projects:
            if "subcategories" not in p:
                p["subcategories"] = make_default_subcategories()
                changed = True
            for sub in p.get("subcategories", []):
                if "subsubcategories" not in sub:
                    sub["subsubcategories"] = []
                    changed = True
        if changed:
            save_projects(self.projects)

        root.title(APP_NAME)
        root.configure(bg=BG)
        root.geometry("1080x640")
        root.minsize(720, 460)

        self._build_style()
        self._build_ui()
        self.refresh()

        self.search_var.trace_add("write", lambda *a: self.refresh())
        self.filter_var.trace_add("write", lambda *a: self.refresh())

    # ---- styling ----
    def _build_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Vertical.TScrollbar", background=SURFACE2,
                        troughcolor=BG, borderwidth=0, arrowsize=12)
        style.configure("Toolbutton", background=SURFACE2, foreground=MUTED,
                        padding=(12, 6), font=("", 13))
        style.map("Toolbutton",
                  background=[("selected", ACCENT), ("active", SURFACE2)],
                  foreground=[("selected", ACCENT_DK)])
        style.configure("TCheckbutton", background=BG, foreground=FG,
                        font=("", 10))
        style.map("TCheckbutton",
                  background=[("active", BG)],
                  foreground=[("active", FG)],
                  indicatorcolor=[("selected", ACCENT),
                                  ("!selected", SURFACE2)])

    # ---- UI ----
    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=20, pady=(18, 6))
        tk.Label(header, text=APP_NAME, bg=BG, fg=FG,
                 font=("", 26, "bold")).pack(side="left")
        self.count_label = tk.Label(header, text="", bg=BG, fg=MUTED,
                                    font=("", 13))
        self.count_label.pack(side="right", pady=(8, 0))

        # filter + search
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x", padx=20, pady=(0, 10))
        self.search_entry = tk.Entry(bar, textvariable=self.search_var,
                                     bg=SURFACE2, fg=FG, insertbackground=FG,
                                     relief="flat", highlightthickness=1,
                                     highlightbackground=BORDER,
                                     highlightcolor=ACCENT, font=("", 13),
                                     width=18)
        self.search_entry.pack(side="left", ipady=5)
        self._set_placeholder(self.search_entry, self.search_ph)
        self.search_entry.bind("<FocusIn>", self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)

        for text, val in (("Done", "done"), ("All", "all"),
                          ("Active", "active")):
            ttk.Radiobutton(bar, text=text, value=val,
                            variable=self.filter_var,
                            style="Toolbutton").pack(side="right",
                                                     padx=(4, 0))

        # scrollable project list
        list_area = tk.Frame(self.root, bg=BG)
        list_area.pack(fill="both", expand=True, padx=20)
        self.main_canvas = tk.Canvas(list_area, bg=BG, highlightthickness=0)
        vscroll = ttk.Scrollbar(list_area, orient="vertical",
                                command=self.main_canvas.yview)
        hscroll = ttk.Scrollbar(list_area, orient="horizontal",
                                command=self.main_canvas.xview)
        self.main_canvas.configure(yscrollcommand=vscroll.set,
                                   xscrollcommand=hscroll.set)
        self.projects_frame = tk.Frame(self.main_canvas, bg=BG)
        self.projects_frame.bind("<Configure>", lambda e:
                                 self.main_canvas.configure(
                                     scrollregion=self.main_canvas.bbox("all")))

        def _sync_width(event):
            self.main_canvas.itemconfigure(
                self._main_window,
                width=max(event.width, self.projects_frame.winfo_reqwidth()))

        self._main_window = self.main_canvas.create_window(
            (0, 0), window=self.projects_frame, anchor="nw")
        self.main_canvas.bind("<Configure>", _sync_width)
        self.main_canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")
        hscroll.pack(side="bottom", fill="x")
        for w in (self.main_canvas, self.projects_frame):
            self._bind_wheel(w)

        # bottom: new project
        btns = tk.Frame(self.root, bg=BG)
        btns.pack(fill="x", padx=20, pady=12)
        tk.Button(btns, text="+  New Project", command=self._add,
                  bg=ACCENT, fg=ACCENT_DK, activebackground=GREEN,
                  activeforeground=ACCENT_DK, relief="flat", bd=0,
                  highlightthickness=0, font=("", 13, "bold"),
                  padx=16, pady=8, cursor="hand2").pack(side="left")

    def _bind_wheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if getattr(event, "num", 0) == 4:
            self.main_canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", 0) == 5:
            self.main_canvas.yview_scroll(1, "units")
        elif getattr(event, "delta", 0):
            self.main_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _place_below(self, win, anchor):
        """Position a popup window just below the given widget (clamped)."""
        win.update_idletasks()
        w = win.winfo_width()
        h = win.winfo_height()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height() + 6
        if x + w > sw:
            x = max(0, sw - w - 12)
        if y + h > sh:
            y = max(0, sh - h - 12)
        win.geometry(f"+{x}+{y}")

    # ---- placeholder handling ----
    def _set_placeholder(self, entry, text):
        entry._ph = text
        entry._has_ph = True
        entry.delete(0, "end")
        entry.insert(0, text)
        entry.configure(fg=MUTED)

    def _clear_placeholder(self, event):
        e = event.widget
        if getattr(e, "_has_ph", False):
            e.delete(0, "end")
            e._has_ph = False
            e.configure(fg=FG)

    def _restore_placeholder(self, event):
        e = event.widget
        if not e.get() and hasattr(e, "_ph"):
            e._has_ph = True
            e.insert(0, e._ph)
            e.configure(fg=MUTED)

    # ---- rendering ----
    def _visible_projects(self):
        status_filter = self.filter_var.get()
        query = self.search_var.get().strip().lower()
        if query == self.search_ph.lower():
            query = ""
        active, done = [], []
        for p in self.projects:
            if status_filter == "active" and p.get("status") == "done":
                continue
            if status_filter == "done" and p.get("status") != "done":
                continue
            if query and query not in p.get("name", "").lower() and \
               query not in p.get("note", "").lower():
                continue
            (done if p.get("status") == "done" else active).append(p)
        active.sort(key=lambda p: p.get("created", ""), reverse=True)
        done.sort(key=lambda p: p.get("completed", p.get("created", "")),
                  reverse=True)
        return active + done

    def refresh(self):
        active_n = sum(1 for p in self.projects if p.get("status") != "done")
        self.count_label.configure(
            text=f"{active_n} active · {len(self.projects)} total")
        self._render_projects()

    def _render_projects(self):
        for w in self.projects_frame.winfo_children():
            w.destroy()
        self._sub_vars = []
        visible = self._visible_projects()
        if not visible:
            tk.Label(self.projects_frame,
                     text='No projects here. Click "+ New Project" to add one.',
                     bg=BG, fg=MUTED, font=("", 14), wraplength=500,
                     justify="left").pack(anchor="w", padx=4, pady=18)
            return
        col_names = self._subcategory_columns(visible)
        if getattr(self, "_spacer_col", None) is not None:
            self.projects_frame.grid_columnconfigure(self._spacer_col, weight=0)
        self._spacer_col = 2 + len(col_names)
        self.projects_frame.grid_columnconfigure(self._spacer_col, weight=1)
        for i, p in enumerate(visible):
            self._render_project_row(p, i, col_names)

    def _subcategory_columns(self, visible):
        """Ordered union of subcategory names across visible projects.

        Default stages lead (in their saved order), then any extra names a
        project carries, first-seen. New defaults therefore become new
        columns automatically and stay aligned for every project.
        """
        order = []
        seen = set()
        for name in load_default_subcategories():
            if name not in seen:
                seen.add(name)
                order.append(name)
        for p in visible:
            for s in p.get("subcategories", []):
                n = s.get("name")
                if n and n not in seen:
                    seen.add(n)
                    order.append(n)
        return order

    def _render_project_row(self, p, i, col_names):
        is_done = p.get("status") == "done"
        r = i * 3 + 1
        subs_by_name = {s.get("name"): s for s in p.get("subcategories", [])}

        tk.Frame(self.projects_frame, bg=BORDER, height=1).grid(
            row=r - 1, column=0, columnspan=4 + len(col_names),
            sticky="ew", pady=(0, 8))

        name = ("✓ " if is_done else "") + p.get("name", "Untitled")
        name_btn = tk.Button(self.projects_frame, text=name, anchor="w",
                             bg=BG, fg=(MUTED if is_done else FG),
                             activebackground=SURFACE2, activeforeground=FG,
                             relief="flat", bd=0, highlightthickness=0,
                             font=("", 15, "bold"), cursor="hand2")
        name_btn.grid(row=r, column=0, sticky="nw", padx=(4, 8), pady=(10, 0))
        name_btn.configure(command=lambda pp=p, w=name_btn:
                           self._edit_project(pp, w))

        dates = p.get("created", "")
        if is_done and p.get("completed"):
            dates += "\n→ " + p["completed"]
        tk.Label(self.projects_frame, text=dates, bg=BG, fg=MUTED,
                 font=("", 12), justify="left").grid(row=r, column=1,
                 sticky="nw", padx=(0, 8), pady=(17, 0))

        for j, cname in enumerate(col_names):
            sub = subs_by_name.get(cname)
            if sub is None:
                tk.Label(self.projects_frame, text="", bg=BG).grid(
                    row=r, column=2 + j, sticky="nw", padx=(0, 8),
                    pady=(10, 0))
                continue
            cell = tk.Frame(self.projects_frame, bg=BG)
            cell.grid(row=r, column=2 + j, sticky="nw", padx=(0, 8),
                      pady=(10, 0))
            var = tk.BooleanVar(value=bool(sub.get("checked")))
            self._sub_vars.append(var)
            cb = ttk.Checkbutton(cell, variable=var,
                                 command=lambda s=sub, v=var:
                                 self._toggle_subcategory(s, v))
            cb.pack(side="left")
            btn = tk.Button(cell, text=cname, anchor="w",
                            bg=BG, fg=FG, activebackground=SURFACE2,
                            activeforeground=FG, relief="flat", bd=0,
                            highlightthickness=0, font=("", 14),
                            cursor="hand2")
            btn.pack(side="left")
            btn.configure(command=lambda s=sub, w=name_btn:
                          self._open_subcategory(s, w))
            for w in (cell, cb, btn):
                self._bind_wheel(w)

        mgr = self._small_button(self.projects_frame, "Manage Subcategories",
                                 None)
        mgr.grid(row=r, column=3 + len(col_names), sticky="ne",
                 padx=(8, 4), pady=(10, 0))
        mgr.configure(command=lambda pp=p, w=mgr:
                      self._manage_project_subcategories(pp, w))

        acts = tk.Frame(self.projects_frame, bg=BG)
        acts.grid(row=r + 1, column=0, columnspan=2 + len(col_names),
                  sticky="w", padx=(4, 0), pady=(0, 10))
        edit_btn = self._small_button(acts, "Edit", None)
        edit_btn.pack(side="left", padx=(0, 6))
        edit_btn.configure(command=lambda pp=p, w=edit_btn:
                           self._edit_project(pp, w))
        self._small_button(acts, "Active" if is_done else "Done",
                           lambda pp=p: self._toggle_project(pp)).pack(
            side="left", padx=(0, 6))
        del_btn = self._small_button(acts, "Delete", None, danger=True)
        del_btn.pack(side="left")
        del_btn.configure(command=lambda pp=p, w=del_btn:
                          self._delete_project(pp, w))

    def _small_button(self, parent, text, command, danger=False):
        fg = RED if danger else MUTED
        return tk.Button(parent, text=text, command=command, bg=SURFACE,
                         fg=fg, activebackground=SURFACE2, activeforeground=fg,
                         relief="flat", bd=0, highlightthickness=0,
                         font=("", 14), padx=8, pady=2, cursor="hand2")

    # ---- subcategory actions ----
    def _toggle_subcategory(self, sub, var):
        sub["checked"] = bool(var.get())
        save_projects(self.projects)

    def _open_subcategory(self, sub, anchor=None):
        win = SubcategoryWindow(self.root, sub)
        if anchor is not None:
            self._place_below(win, anchor)
        self.root.wait_window(win)
        save_projects(self.projects)

    # ---- project actions ----
    def _add(self):
        dlg = ProjectDialog(self.root, "New Project")
        self.root.wait_window(dlg)
        if dlg.result:
            name, note = dlg.result
            self.projects.append({"id": uuid.uuid4().hex, "name": name,
                                  "note": note, "status": "active",
                                  "created": today(),
                                  "subcategories": make_default_subcategories()})
            save_projects(self.projects)
            self.refresh()

    def _manage_project_subcategories(self, p, anchor=None):
        names = [s.get("name") for s in p.get("subcategories", [])]
        win = ManageSubcategoriesWindow(self.root, names,
                                        project_name=p.get("name", ""))
        if anchor is not None:
            self._place_below(win, anchor)
        self.root.wait_window(win)
        if not win.result:
            return
        self._reconcile_subcategories(p, win.result)
        save_projects(self.projects)
        self.refresh()

    def _reconcile_subcategories(self, p, new_names):
        subs = p.get("subcategories", [])
        by_name = {s.get("name"): s for s in subs}
        new_subs = []
        for name in new_names:
            if name in by_name:
                new_subs.append(by_name[name])
            else:
                new_subs.append({"name": name, "checked": False,
                                 "comment": "", "subsubcategories": []})
        p["subcategories"] = new_subs

    def _edit_project(self, p, anchor=None):
        dlg = ProjectDialog(self.root, "Edit Project", name=p.get("name", ""),
                            note=p.get("note", ""))
        if anchor is not None:
            self._place_below(dlg, anchor)
        self.root.wait_window(dlg)
        if dlg.result:
            p["name"], p["note"] = dlg.result
            save_projects(self.projects)
            self.refresh()

    def _toggle_project(self, p):
        if p.get("status") == "done":
            p["status"] = "active"
            p.pop("completed", None)
        else:
            p["status"] = "done"
            p["completed"] = today()
        save_projects(self.projects)
        self.refresh()

    def _delete_project(self, p, anchor=None):
        if not self._confirm(f'Delete "{p.get("name")}"?\n'
                             "This can't be undone.", anchor=anchor):
            return
        self.projects = [x for x in self.projects if x["id"] != p["id"]]
        save_projects(self.projects)
        self.refresh()

    def _confirm(self, message, anchor=None):
        result = {"ok": False}
        dlg = tk.Toplevel(self.root)
        dlg.title("Confirm")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.transient(self.root)
        frame = tk.Frame(dlg, bg=BG, padx=22, pady=18)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text=message, bg=BG, fg=FG, justify="left",
                 font=("", 18)).pack(anchor="w")
        row = tk.Frame(frame, bg=BG)
        row.pack(fill="x", pady=(16, 0))

        def ok():
            result["ok"] = True
            dlg.destroy()

        tk.Button(row, text="Cancel", command=dlg.destroy, bg=SURFACE2, fg=FG,
                  activebackground=SURFACE2, activeforeground=FG,
                  relief="flat", bd=0, font=("", 14), padx=16, pady=6,
                  cursor="hand2").pack(side="right", padx=(8, 0))
        tk.Button(row, text="Delete", command=ok, bg=RED, fg=ACCENT_DK,
                  activebackground=RED, activeforeground=ACCENT_DK,
                  relief="flat", bd=0, font=("", 14, "bold"), padx=16,
                  pady=6, cursor="hand2").pack(side="right")
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

        def _cleanup():
            try:
                self.root.unbind("<Button-1>", _funcid)
            except tk.TclError:
                pass

        def _on_outside(event):
            _cleanup()
            dlg.destroy()

        _funcid = self.root.bind("<Button-1>", _on_outside, add="+")

        if anchor is not None:
            self._place_below(dlg, anchor)
        self.root.wait_window(dlg)
        _cleanup()
        return result["ok"]


def main():
    root = tk.Tk(className=APP_NAME)
    MyProjectsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
