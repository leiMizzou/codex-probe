# Provider Probe

## 中文说明

Provider Probe 是一个用于黑盒评估 OpenAI-compatible 中转站、API 网关、模型代理的命令行工具。

它会先用你信任的 provider 建立一个 baseline，然后用同一套复杂题和功能探针去测试候选 provider，大致判断：

- 模型质量是否接近 baseline
- 是否有隐藏 prompt / wrapper 导致 input token 被放大
- 是否存在多路由、多适配器切换
- 是否疑似混入较弱模型
- `gpt-image-2`、snapshot model、JSON schema 等能力是否缺失
- token 使用量和估算成本是否异常

它不能证明上游账号到底是 ChatGPT Free、Plus、Pro 还是 Team。API 行为和 ChatGPT 订阅不是同一个权限面；本工具输出的是黑盒证据和风险评分。

### 快速开始

直接运行：

```bash
python3 provider_probe.py --help
```

也可以安装成本地 CLI：

```bash
python3 -m pip install -e .
provider-probe --help
```

### 1. 生成可信 Baseline

如果你信任当前 Codex 配置的 provider：

```bash
python3 provider_probe.py baseline \
  --current-codex \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output baselines/current-codex-gpt-5.5-xhigh.json
```

`--image-probe` 会调用 `gpt-image-2`，如果图片能力已开启，可能消耗图片额度。

也可以显式指定可信 endpoint：

```bash
export PROVIDER_BASE_URL="https://trusted.example.com/v1"
export PROVIDER_API_KEY="your-api-key"

python3 provider_probe.py baseline \
  --base-url "$PROVIDER_BASE_URL" \
  --api-key "$PROVIDER_API_KEY" \
  --label trusted \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --output baselines/trusted-gpt-5.5-xhigh.json
```

### 2. 测试候选中转

```bash
export PROVIDER_BASE_URL="https://candidate.example.com/v1"
export PROVIDER_API_KEY="your-api-key"

python3 provider_probe.py audit \
  --baseline baselines/current-codex-gpt-5.5-xhigh.json \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-gpt-5.5-xhigh-audit.json
```

报告会自动脱敏，不会保存 API key。

### 分数含义

- `quality_score`: 复杂客观题正确率。
- `wrapper_or_routing_suspicion`: 是否出现固定 input token 档位，常见于隐藏 wrapper 或不同适配器。
- `model_substitution_suspicion`: 是否疑似混入弱模型，重点看难题掉分和不同 token 档位的正确率差异。
- `billing_overhead_suspicion`: token / 成本是否明显高于 baseline。
- `feature_gap_suspicion`: `gpt-image-2`、snapshot model、JSON schema 等能力是否缺失。
- `overall_risk`: 综合风险评分。

如果候选 provider 出现类似：

```text
+0 input tokens
+335 input tokens
```

说明它很可能存在隐藏包装或不同路由。如果两个档位都能通过复杂题，更像 wrapper / routing 成本问题；如果某个档位明显更容易错，更像混入弱模型。

完整中文说明见 [README.zh-CN.md](README.zh-CN.md)，题库说明见 [model_substitution_hard_suite.md](model_substitution_hard_suite.md)。

---

## English

Black-box audit tooling for OpenAI-compatible model providers and API gateways.

Provider Probe helps you compare a candidate API endpoint against a trusted baseline and answer practical questions:

- Is the claimed model behaving close to the baseline on hard deterministic tasks?
- Does the provider inject hidden prompt/wrapper tokens?
- Is there evidence of mixed routing or weaker model substitution?
- Are expected capabilities missing, such as `gpt-image-2` or snapshot model IDs?
- How different are reported token usage and estimated cost?

It is designed for testing third-party "OpenAI-compatible" gateways, proxy providers, and model resellers. It does **not** prove the upstream account type, and it cannot definitively prove Free / Plus / Pro / Team usage. It reports observable evidence and risk scores.

## What It Tests

The built-in hard suite includes deterministic prompts for:

- Python and JavaScript execution reasoning
- Critical path scheduling
- Weighted graph shortest path with tie-breaking
- Decoy retrieval
- SQL-style aggregation
- Conditional probability
- Mini DSL interpretation
- Calendar arithmetic
- Instruction-injection resistance
- Strict JSON output
- Bug localization
- Impossible-constraint detection
- Nested JSON extraction
- Base conversion
- Stable repetition formatting

See [model_substitution_hard_suite.md](model_substitution_hard_suite.md) for the full prompt suite.

## Install

Requires Python 3.10+. Python 3.11+ is recommended if you want `--current-codex` baseline generation from `~/.codex/config.toml`.

Run directly:

```bash
python3 provider_probe.py --help
```

Or install as a local CLI:

```bash
python3 -m pip install -e .
provider-probe --help
```

## 1. Build A Trusted Baseline

If you use Codex locally and trust its configured provider:

```bash
python3 provider_probe.py baseline \
  --current-codex \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output baselines/current-codex-gpt-5.5-xhigh.json
```

`--image-probe` calls `gpt-image-2` and may consume image credits if enabled.

You can also build a baseline from explicit endpoint credentials:

```bash
export PROVIDER_BASE_URL="https://trusted.example.com/v1"
export PROVIDER_API_KEY="sk-..."

python3 provider_probe.py baseline \
  --base-url "$PROVIDER_BASE_URL" \
  --api-key "$PROVIDER_API_KEY" \
  --label trusted \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --output baselines/trusted-gpt-5.5-xhigh.json
```

## 2. Audit A Candidate Provider

```bash
export PROVIDER_BASE_URL="https://candidate.example.com/v1"
export PROVIDER_API_KEY="sk-..."

python3 provider_probe.py audit \
  --baseline baselines/current-codex-gpt-5.5-xhigh.json \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-gpt-5.5-xhigh-audit.json
```

The saved report is redacted. API keys are not written to output files.

## Scores

Reports include:

- `quality_score`: correctness on the hard deterministic suite.
- `wrapper_or_routing_suspicion`: fixed input-token overhead tiers, likely hidden wrappers or different adapters.
- `model_substitution_suspicion`: risk of weaker/mixed model routing based on quality drops or one token tier failing more often.
- `billing_overhead_suspicion`: candidate uses much more input/total token budget than baseline.
- `feature_gap_suspicion`: missing or different features compared with baseline.
- `overall_risk`: weighted summary of routing, substitution, billing, and feature issues.

Example:

```text
quality_score: 100/100
wrapper_or_routing_suspicion: 70/100
model_substitution_suspicion: 0/100
billing_overhead_suspicion: 100/100
feature_gap_suspicion: 55/100
overall_risk: 54.25/100
```

## Reading Token Clusters

A clean provider should usually have input token counts close to the baseline for the same prompt.

If the candidate forms stable clusters like:

```text
+0 input tokens
+335 input tokens
```

that is strong evidence of hidden wrapper/routing differences. If both clusters pass the hard suite, this points more toward adapter/wrapper overhead than weaker model substitution. If one cluster fails more often, mixed or weaker upstream routing becomes more suspicious.

## Limitations

- This is a black-box heuristic audit, not cryptographic proof.
- Providers can spoof returned model names.
- API behavior cannot reliably identify ChatGPT Free / Plus / Pro / Team account type.
- Image generation success or failure reflects API/project/group permission, not necessarily ChatGPT subscription.
- Token counts are provider-reported and may include hidden prompt, adapter, or billing-layer overhead.

## Repository Hygiene

Generated baselines, audit reports, local images, and Python caches are ignored by default. Do not commit real API keys or private provider reports unless you have reviewed and redacted them.
