#!/usr/bin/env bash
set -euo pipefail

python3 codex_probe.py baseline \
  --current-codex \
  --profile codex-fast \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output baselines/current-codex-gpt-5.5-xhigh.json
