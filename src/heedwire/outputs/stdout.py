"""Stdout output (debug / --once / container log watchdog). Safe wire format only."""
from __future__ import annotations

import json

from ..models import Finding
from .base import Output


class StdoutOutput(Output):
    id = "stdout"

    def send(self, findings: list[Finding]) -> None:
        for f in findings:
            print(json.dumps(f.to_wire(), default=str))
        if not findings:
            print('{"count": 0}')
