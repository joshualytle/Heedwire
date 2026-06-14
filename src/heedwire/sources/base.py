"""Source contract. A Source fetches the BROAD/recent feed and normalizes to Item.
It must never query upstream by the user's watchlist (privacy boundary)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ..models import Item


class Source(ABC):
    id = "base"

    def __init__(self, **options: Any) -> None:
        self.options = options

    @abstractmethod
    def fetch(self, since: datetime) -> list[Item]:
        raise NotImplementedError
