"""Source registry. v1 ships kev + rss; news/reddit/usn/nvd are fast-follows."""
from __future__ import annotations

from typing import Type

from .base import Source
from .kev import KevSource
from .rss import RssSource

REGISTRY: dict[str, Type[Source]] = {KevSource.id: KevSource, RssSource.id: RssSource}
