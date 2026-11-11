from collections.abc import Callable
from tkinter import filedialog, messagebox, ttk

from controller import IPropertyController

from .entity_tab import EntityTab
from .widgets import ImagePreview, Row, run_action

IMAGE_TYPES = (("Images", "*.png *.jpg *.jpeg *.gif"), ("All files", "*"))
SUMMARY_COLUMNS = (
    "Property ID",
    "Status",
    "Street",
    "City",
    "State",
    "ZIP Code",
    "Bedrooms",
    "Bathrooms",
    "Square Feet",
    "Photo",
)


class PropertiesTab(EntityTab):
    controller: IPropertyController

    def __init__(
        self,
        parent: ttk.Notebook,
        controller: IPropertyController,
        on_change: Callable[[], None],
    ) -> None:
        super().__init__(parent, controller, on_change)
        self.table.set_display_columns(SUMMARY_COLUMNS)
        self._preview = ImagePreview(self.sidebar)
        self._preview.grid(row=2, column=0, sticky="ew")
        self._build_photo_buttons().grid(row=3, column=0, sticky="ew", pady=(8, 0))

    def clear(self) -> None:
        super().clear()
        self._preview.show(None)

    def _select(self, row: Row) -> None:
        super()._select(row)
        self._show_photo()

    def _show_photo(self) -> None:
        run_action(
            lambda: self._preview.show(self.controller.image(self.selected_id()))
        )

    def _photo_changed(self, message: str) -> None:
        self._on_change()
        self._show_photo()
        messagebox.showinfo("Success", message)

    def _build_photo_buttons(self) -> ttk.Frame:
        buttons = ttk.Frame(self.sidebar)
        actions = [("Attach Photo", self._attach), ("Remove Photo", self._remove)]
        for column, (text, command) in enumerate(actions):
            ttk.Button(buttons, text=text, command=command).grid(
                row=0, column=column, padx=2
            )
        return buttons

    def _attach(self) -> None:
        path = filedialog.askopenfilename(title="Choose a photo", filetypes=IMAGE_TYPES)
        if not path:
            return
        record_id = self.selected_id()
        if run_action(lambda: self.controller.attach_image(record_id, path)):
            self._photo_changed("Photo saved.")

    def _remove(self) -> None:
        record_id = self.selected_id()
        if run_action(lambda: self.controller.remove_image(record_id)):
            self._photo_changed("Photo removed.")
