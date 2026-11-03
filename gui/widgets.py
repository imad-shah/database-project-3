import tkinter as tk
from collections.abc import Callable, Iterable, Mapping, Sequence
from io import BytesIO
from tkinter import font, messagebox, ttk

from PIL import Image, ImageTk

from controller import AppError, Field

Row = Sequence[str]
CELL_PADDING = 24


def run_action(action: Callable[[], object]) -> bool:
    try:
        action()
    except AppError as e:
        messagebox.showerror("Error", str(e))
        return False
    return True


class Form(ttk.LabelFrame):
    def __init__(self, parent: tk.Misc, title: str, fields: Sequence[Field]) -> None:
        super().__init__(parent, text=title, padding=10)
        self._fields = [field for field in fields if field.in_form]
        self._vars = {field.name: tk.StringVar() for field in self._fields}
        self._choosers: list[tuple[Field, ttk.Combobox]] = []
        for row, field in enumerate(self._fields):
            ttk.Label(self, text=field.label).grid(
                row=row, column=0, sticky="w", pady=2
            )
            self._build_input(field).grid(row=row, column=1, padx=(8, 0), pady=2)
        self.clear()

    def values(self) -> dict[str, str]:
        return {name: var.get() for name, var in self._vars.items()}

    def fill(self, values: Mapping[str, str]) -> None:
        for name, var in self._vars.items():
            var.set(values.get(name, ""))

    def clear(self) -> None:
        for field in self._fields:
            self._vars[field.name].set(field.default)

    def refresh(self) -> None:
        for field, chooser in self._choosers:
            chooser.configure(values=field.choices())

    def _build_input(self, field: Field) -> ttk.Widget:
        var = self._vars[field.name]
        if not field.has_choices:
            state = "normal" if field.editable else "readonly"
            return ttk.Entry(self, textvariable=var, width=30, state=state)
        chooser = ttk.Combobox(self, textvariable=var, width=28, state="readonly")
        self._choosers.append((field, chooser))
        return chooser


class Table(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        on_select: Callable[[Row], None],
        columns: Sequence[str] = (),
    ) -> None:
        super().__init__(parent)
        self._on_select = on_select
        self._rows: list[Row] = []
        self._columns: Sequence[str] = ()
        self._display_columns: Sequence[str] = ()
        self._cell_font = font.nametofont("TkDefaultFont")
        self._heading_font = font.nametofont("TkHeadingFont")
        self._tree = ttk.Treeview(self, show="headings", selectmode="browse", height=8)
        vertical = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self._tree.bind("<<TreeviewSelect>>", self._handle_select)
        self.set_columns(columns)

    def set_columns(self, columns: Sequence[str]) -> None:
        self._display_columns = ()
        self._tree.configure(displaycolumns=())
        self._columns = columns
        self._tree.configure(columns=tuple(columns))
        for column in columns:
            self._tree.heading(column, text=column)
            self._tree.column(column, anchor="w", stretch=False)
        self.set_display_columns(columns)

    def set_display_columns(self, columns: Sequence[str]) -> None:
        unknown = set(columns) - set(self._columns)
        if unknown:
            raise ValueError(f"Unknown table columns: {sorted(unknown)}")
        self._display_columns = columns
        self._tree.configure(displaycolumns=tuple(columns))

    def show(self, rows: Iterable[Row]) -> None:
        self._tree.delete(*self._tree.get_children())
        self._rows = list(rows)
        for index, row in enumerate(self._rows):
            self._tree.insert("", "end", iid=str(index), values=tuple(row))
        self._fit_columns()

    def select_first(self) -> None:
        if self._rows:
            self._tree.selection_set("0")

    def _fit_columns(self) -> None:
        for column in self._display_columns:
            index = self._columns.index(column)
            cells = [self._cell_font.measure(row[index]) for row in self._rows]
            width = max(self._heading_font.measure(column), *cells, 0)
            self._tree.column(column, width=width + CELL_PADDING)

    def _handle_select(self, _event: tk.Event) -> None:
        selection = self._tree.selection()
        if selection:
            self._on_select(self._rows[int(selection[0])])


class ImagePreview(ttk.Label):
    def __init__(self, parent: tk.Misc, size: tuple[int, int] = (340, 220)) -> None:
        super().__init__(parent, anchor="center", relief="groove", padding=4)
        self._size = size
        self._photo: ImageTk.PhotoImage | None = None
        self.show(None)

    def show(self, data: bytes | None) -> None:
        if data is None:
            self._photo = None
            self.configure(image="", text="No photo on file")
            return
        image = Image.open(BytesIO(data))
        image.thumbnail(self._size)
        self._photo = ImageTk.PhotoImage(image)
        self.configure(image=self._photo, text="")
