#!/usr/bin/env python3
"""Compatibility entrypoint for the Codex Probe CLI."""

from provider_probe import main


if __name__ == "__main__":
    raise SystemExit(main())
