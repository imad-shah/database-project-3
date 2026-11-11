from io import BytesIO
from pathlib import Path

from PIL import Image

from models import Property
from repository import IPropertyRepository

from .entity_controller import EntityController
from .errors import AppError, friendly_errors
from .fields import Option
from .interfaces import IPropertyController


def _read_image(path: str) -> bytes:
    try:
        data = Path(path).read_bytes()
        with Image.open(BytesIO(data)) as image:
            image.verify()
    except (OSError, SyntaxError):
        raise AppError("That file isn't a readable image.") from None
    return data


class PropertyController(EntityController[Property], IPropertyController):
    _repo: IPropertyRepository

    def unlisted_options(self) -> list[Option]:
        with friendly_errors():
            return self._to_options(self._repo.find_unlisted())

    def image(self, property_id: str) -> bytes | None:
        key = self._parse_key(property_id)
        with friendly_errors():
            return self._repo.get_image(key)

    def attach_image(self, property_id: str, path: str) -> None:
        key = self._parse_key(property_id)
        image = _read_image(path)
        with friendly_errors():
            self._repo.set_image(key, image)

    def remove_image(self, property_id: str) -> None:
        key = self._parse_key(property_id)
        with friendly_errors():
            self._repo.set_image(key, None)
