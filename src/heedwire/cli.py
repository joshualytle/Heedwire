"""CLI: run (loop) | once (single run) | serve (API) | resolve (debug)."""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .config import load_config


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="heedwire")
    p.add_argument("--version", action="version", version=f"heedwire {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("run", "once", "serve", "resolve"):
        sp = sub.add_parser(name)
        sp.add_argument("--config", "-c", default="config.yaml")
        if name == "once":
            sp.add_argument("--no-deliver", action="store_true")

    args = p.parse_args(argv)
    cfg = load_config(args.config)

    if args.cmd == "run":
        from .scheduler import loop
        loop(cfg)
        return 0
    if args.cmd == "once":
        from .engine import run_once
        r = run_once(cfg, deliver=not args.no_deliver)
        print(f"fetched={r.fetched} new={r.new_items} findings={len(r.findings)} "
              f"errors={len(r.errors)}", file=sys.stderr)
        for e in r.errors:
            print(f"  ! {e}", file=sys.stderr)
        return 1 if r.errors and r.fetched == 0 else 0
    if args.cmd == "serve":
        import uvicorn
        from .api import create_app
        uvicorn.run(create_app(cfg), host=cfg.api_host, port=cfg.api_port)
        return 0
    if args.cmd == "resolve":
        from .taxonomy import load_taxonomy, resolve
        rw = resolve(cfg.watch, load_taxonomy(cfg.taxonomy_path))
        print(json.dumps({"vendor_products": sorted(rw.vendor_products),
                          "vendors": sorted(rw.vendors), "packages": sorted(rw.packages),
                          "aliases": rw.aliases, "advisory_feeds": sorted(rw.advisory_feeds)},
                         indent=2))
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
