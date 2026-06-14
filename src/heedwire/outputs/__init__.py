from __future__ import annotations

from typing import Type

from .base import Output
from .stdout import StdoutOutput
from .webhook import WebhookOutput

REGISTRY: dict[str, Type[Output]] = {WebhookOutput.id: WebhookOutput, StdoutOutput.id: StdoutOutput}
