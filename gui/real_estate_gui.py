import tkinter as tk
from tkinter import ttk

from controller import Controllers

from .entity_tab import EntityTab
from .properties_tab import PropertiesTab
from .reports_tab import ReportsTab
from .widgets import run_action


class RealEstateApp(tk.Tk):
    def __init__(self, controllers: Controllers) -> None:
        super().__init__()
        self.title("Real Estate Office")
        self.minsize(1250, 800)

        notebook = ttk.Notebook(self, padding=10)
        notebook.pack(fill="both", expand=True)
        self.tabs = [
            PropertiesTab(notebook, controllers.properties, self.refresh),
            *(
                EntityTab(notebook, controller, self.refresh)
                for controller in (
                    controllers.sales,
                    controllers.agents,
                    controllers.buyers,
                    controllers.sellers,
                )
            ),
            ReportsTab(notebook, controllers.reports),
        ]
        for tab in self.tabs:
            notebook.add(tab, text=tab.tab_name)
        self.refresh()

    def refresh(self) -> None:
        for tab in self.tabs:
            run_action(tab.refresh)
