from models import Listing
from repository import IListingRepository

from .entity_controller import EntityController
from .errors import friendly_errors
from .fields import Option
from .interfaces import IListingController


class ListingController(EntityController[Listing], IListingController):
    _repo: IListingRepository

    def available_options(self) -> list[Option]:
        with friendly_errors():
            return self._to_options(self._repo.find_available())
