from collections.abc import Callable
from tkinter import messagebox, ttk

from controller import IEntityController

from .widgets import Form, Row, Table, run_action


class EntityTab(ttk.Frame):
    def __init__(
        self,
        parent: ttk.Notebook,
        controller: IEntityController,
        on_change: Callable[[], None],
    ) -> None:
        super().__init__(parent, padding=10)
        self.controller = controller
        self.spec = controller.spec
        self.tab_name = self.spec.plural
        self._on_change = on_change

        self.sidebar = ttk.Frame(self)
        self.sidebar.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.form = Form(self.sidebar, self.spec.title, self.spec.fields)
        self.form.grid(row=0, column=0, sticky="ew")
        self._build_buttons().grid(row=1, column=0, sticky="ew", pady=10)

        self.table = Table(
            self, self._select, [field.label for field in self.spec.fields]
        )
        self.table.grid(row=0, column=1, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def refresh(self) -> None:
        self.table.show(self.controller.rows())
        self.form.refresh()

    def selected_id(self) -> str:
        return self.form.values()[self.spec.key.name]

    def clear(self) -> None:
        self.form.clear()

    def _select(self, row: Row) -> None:
        names = (field.name for field in self.spec.fields)
        self.form.fill(dict(zip(names, row)))
        self.form.lock_fixed(True)

    def _build_buttons(self) -> ttk.Frame:
        buttons = ttk.Frame(self.sidebar)
        actions = [
            ("Save", self._save),
            ("Delete", self._delete),
            ("Clear", self.clear),
        ]
        for column, (text, command) in enumerate(actions):
            ttk.Button(buttons, text=text, command=command).grid(
                row=0, column=column, padx=2
            )
        return buttons

    def _save(self) -> None:
        if run_action(lambda: self.controller.save(self.form.values())):
            self.finish(f"{self.spec.title} saved.")

    def _delete(self) -> None:
        record_id = self.selected_id()
        prompt = (
            f"Delete {self.spec.title.lower()} {record_id}?{self.spec.delete_warning}"
        )
        if not messagebox.askyesno("Confirm Delete", prompt):
            return
        if run_action(lambda: self.controller.delete(record_id)):
            self.finish(f"{self.spec.title} deleted.")

    def finish(self, message: str) -> None:
        self.clear()
        self._on_change()
        messagebox.showinfo("Success", message)
