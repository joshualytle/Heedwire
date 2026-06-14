"""Simple internal scheduler for the long-running `run` mode: loop with jitter."""
from __future__ import annotations

import random
import time

from .config import Config
from .engine import run_once


def loop(cfg: Config) -> None:
    while True:
        result = run_once(cfg, deliver=True)
        print(f"[heedwire] fetched={result.fetched} new={result.new_items} "
              f"findings={len(result.findings)} errors={len(result.errors)}", flush=True)
        for e in result.errors:
            print(f"[heedwire]   ! {e}", flush=True)
        sleep_s = max(60, cfg.interval_minutes * 60) + random.randint(0, 60)
        time.sleep(sleep_s)
