from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import Finding


class Output(ABC):
    id = "base"

    def __init__(self, **options: Any) -> None:
        self.options = options

    @abstractmethod
    def send(self, findings: list[Finding]) -> None:
        raise NotImplementedError
