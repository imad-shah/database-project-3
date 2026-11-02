import tkinter as tk
from tkinter import ttk

from controller import IReportController, Report
from models import ReportResult

from .widgets import Form, ImagePreview, Row, Table, run_action


class ReportsTab(ttk.Frame):
    tab_name = "Reports"

    def __init__(self, parent: ttk.Notebook, controller: IReportController) -> None:
        super().__init__(parent, padding=10)
        self._controller = controller
        self._reports = {report.title: report for report in controller.reports}
        self._chosen = tk.StringVar(value=next(iter(self._reports)))
        self._form: Form | None = None
        self._result: ReportResult | None = None

        self._sidebar = ttk.Frame(self)
        self._sidebar.grid(row=0, column=0, rowspan=2, sticky="n", padx=(0, 10))
        chooser = ttk.Combobox(
            self._sidebar,
            textvariable=self._chosen,
            values=list(self._reports),
            state="readonly",
            width=38,
        )
        chooser.grid(row=0, column=0, sticky="ew")
        chooser.bind("<<ComboboxSelected>>", lambda _event: self._choose())
        ttk.Button(self._sidebar, text="Run Report", command=self._run).grid(
            row=2, column=0, sticky="ew", pady=10
        )
        self._preview = ImagePreview(self._sidebar)

        self._question = ttk.Label(self, wraplength=800, justify="left")
        self._question.grid(row=0, column=1, sticky="w", pady=(0, 8))
        self._table = Table(self, self._show_image)
        self._table.grid(row=1, column=1, sticky="nsew")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)
        self._choose()

    @property
    def _report(self) -> Report:
        return self._reports[self._chosen.get()]

    def refresh(self) -> None:
        self._form.refresh()

    def _choose(self) -> None:
        if self._form is not None:
            self._form.destroy()
        report = self._report
        self._form = Form(self._sidebar, "Options", report.params)
        if report.params:
            self._form.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self._form.refresh()
        self._form.fill({param.name: param.initial() for param in report.params})
        self._question.configure(text=report.question)
        self._table.set_columns(())
        self._table.show(())
        if report.image_column:
            self._preview.show(None)
            self._preview.grid(row=3, column=0, sticky="ew")
        else:
            self._preview.grid_remove()

    def _run(self) -> None:
        run_action(self._load)

    def _load(self) -> None:
        self._result = self._controller.run(self._report, self._form.values())
        self._table.set_columns(self._result.columns)
        self._table.show(self._result.rows)
        self._table.select_first()

    def _show_image(self, row: Row) -> None:
        column = self._report.image_column
        if column is None:
            return
        property_id = row[self._result.columns.index(column)]
        run_action(lambda: self._preview.show(self._controller.image(property_id)))
