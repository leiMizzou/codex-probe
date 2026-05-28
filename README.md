<div align="center">

# 🔍 Codex Probe

**OpenAI-compatible 中转站 / API 网关黑盒纯净度审计 CLI**
**Black-box purity audit for OpenAI-compatible model providers & gateways**

<kbd>🐍 Python 3.10+</kbd> &nbsp;<kbd>📜 MIT</kbd> &nbsp;<kbd>🧪 Alpha</kbd> &nbsp;<kbd>🔓 Zero dependencies</kbd> &nbsp;<kbd>⚠️ Unofficial</kbd>

<sub>

[🇨🇳 简体中文](#-简体中文) &nbsp;·&nbsp; [🇬🇧 English](#-english) &nbsp;·&nbsp; [✨ 推荐中转 Recommended](#-推荐中转-recommended-providers) &nbsp;·&nbsp; [📋 题库 Suite](model_substitution_hard_suite.md) &nbsp;·&nbsp; [📖 完整中文文档](README.zh-CN.md)

</sub>

</div>

---

> 用你信任的 Codex provider 作为 baseline，对第三方中转跑同一套复杂题、功能探针和速度指标，输出 token / 质量 / 功能 / 速度差异和综合风险评分。
>
> Build a trusted baseline from a provider you already trust, then audit any candidate endpoint against it with the same hard suite, feature probes, and timing measurements.

---

## ✨ 推荐中转 Recommended providers

**已通过 hard-v1 黑盒测试** · Passed the hard-v1 black-box audit

| Provider | Endpoint | 测试配置 / Tested with | Quality | Overall risk | 状态 / Status |
|---|---|---|---|---|---|
| **agnx** | `https://www.agnx.run/v1` | `gpt-5.5` · `xhigh` · hard-v1 | **100 / 100** ✅ | 45.75 / 100 🟡 | 已挂，待恢复；购买入口已移除<br>Down, pending recovery; purchase link removed |

**入选条件 / Inclusion criteria**

- `quality_score = 100 / 100`（hard-v1 全通过）
- `model_substitution_suspicion = 0 / 100`（无弱模型替换信号）
- `speed_suspicion = 0 / 100`（速度近 baseline）
- `overall_risk < 50`（综合风险中等偏下）

> 通过黑盒测试 ≠ 全功能等价 provider。每一项推荐都附了"适合 / 不适合"清单，使用前请先看下方对应案例分析里的 token、功能和速度细节。
>
> Passing the black-box audit does **not** mean a candidate is feature-equivalent to the baseline. Each entry has a per-case "best for / avoid" list — read the matching case study below before relying on it.
>
> 状态为"已挂"的服务暂不提供购买入口，恢复并复测前不建议新购或依赖。Providers marked "down" intentionally have no purchase link and should not be newly purchased or relied on until recovery is verified.

#### 各候选的适用面 / Suitability cheat sheet

| Provider | ✅ 适合 / Best for | ❌ 不适合 / Avoid |
|---|---|---|
| **agnx** | 已挂，待恢复；恢复并复测前暂不建议新购或依赖<br>Down, pending recovery; not recommended for new purchase or dependency until verified again | 恢复前的所有生产、长期依赖和新购场景<br>All production, long-lived dependency, and new-purchase use before recovery |

> 详细评分、token 档位、速度比、功能探针结果见下方各语言区"案例：agnx 对比内置基线 / Case study: agnx vs the built-in baseline"小节。
>
> Detailed scores, token tiers, speed ratios, and feature probe results: see the "Case study" subsection inside each language section below.

#### 📨 提名新候选 / Nominate a candidate

> 欢迎大家用 `codex-probe` 自测，或者把想审计的中转 endpoint [开 issue](https://github.com/leiMizzou/codex-probe/issues/new) 提名给我。**通过上面入选条件的候选**会被加进推荐表，并按 **周 / 月** 周期跑复测，结果直接更新到本表 —— 不通过的也会在 issue 里给出失败原因。
>
> Run `codex-probe` yourself, or [open an issue](https://github.com/leiMizzou/codex-probe/issues/new) nominating a relay endpoint you'd like audited. **Candidates that clear the inclusion criteria** above get added to this table and re-tested on a **weekly / monthly** cadence; failures get a public reason in the issue thread.

---

## 🇨🇳 简体中文

### 它能做什么

Codex Probe 是一个 **纯 Python、零依赖** 的命令行工具，用于黑盒判断一个 OpenAI 兼容 endpoint 是否"纯净"。

| ✅ 它能告诉你 | ❌ 它不能告诉你 |
|---|---|
| 模型质量是否接近 baseline | 上游账号是 Free / Plus / Pro / Team |
| input token 是否被隐藏 wrapper 放大 | 中转方内部真实路由细节 |
| 是否存在多路由 / 多适配器切换 | 中转方主观声称的"原生" / "官转" |
| 是否疑似混入较弱模型 | 加密学层面的"证明" |
| `gpt-image-2` / snapshot / JSON schema 等能力是否缺失 | |
| token 使用量、估算成本是否异常 | |
| median / p90 latency、输出 token/s 是否明显劣化 | |

> ⚠️ 本项目是非官方工具，不隶属于 OpenAI。输出的是黑盒证据和风险评分，不是定罪结论。

### 安装 & 快速开始

需要 Python 3.10+（若要用 `--current-codex` 从 `~/.codex/config.toml` 读 baseline，建议 3.11+）。

```bash
# 直接运行
python3 codex_probe.py --help

# 或安装为本地 CLI（推荐）
python3 -m pip install -e .
codex-probe --help
```

### 三种使用姿势

<table>
<tr>
<th width="33%">1️⃣ 用内置 baseline</th>
<th width="33%">2️⃣ 自建可信 baseline</th>
<th width="33%">3️⃣ Audit 候选中转</th>
</tr>
<tr>
<td valign="top">最快上手，无需可信 provider，直接对比仓库内置参考样本。</td>
<td valign="top">更贴近你自己的 Codex 配置，可标注 <code>--profile codex-fast</code>。</td>
<td valign="top">跑题、对比、出 token / 质量 / 功能 / 速度 / 综合风险评分。</td>
</tr>
</table>

<details open>
<summary><b>方式 1：使用内置参考 baseline（最快）</b></summary>

```bash
python3 codex_probe.py list-baselines

export PROVIDER_BASE_URL="https://candidate.example.com/v1"
export PROVIDER_API_KEY="your-api-key"

python3 codex_probe.py audit \
  --baseline-id official-sub2api-20x-fast-16c16g-gpt-5.5-xhigh \
  --base-url "$PROVIDER_BASE_URL" \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-vs-official-sub2api-gpt-5.5-xhigh.json
```

</details>

<details>
<summary><b>方式 2：从当前 Codex 配置生成可信 baseline</b></summary>

```bash
python3 codex_probe.py baseline \
  --current-codex \
  --profile codex-fast \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output baselines/current-codex-gpt-5.5-xhigh.json
```

> `--image-probe` 会调用 `gpt-image-2`，可能消耗图片额度。

也可以显式指定可信 endpoint：

```bash
export PROVIDER_BASE_URL="https://trusted.example.com/v1"
export PROVIDER_API_KEY="your-api-key"

python3 codex_probe.py baseline \
  --base-url "$PROVIDER_BASE_URL" \
  --api-key "$PROVIDER_API_KEY" \
  --label trusted \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --output baselines/trusted-gpt-5.5-xhigh.json
```

</details>

<details>
<summary><b>方式 3：使用自己的 baseline 审计候选</b></summary>

```bash
export PROVIDER_BASE_URL="https://candidate.example.com/v1"
export PROVIDER_API_KEY="your-api-key"

python3 codex_probe.py audit \
  --baseline baselines/current-codex-gpt-5.5-xhigh.json \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-gpt-5.5-xhigh-audit.json
```

> 报告会自动脱敏，不保存 API key。

</details>

### 📦 内置参考基线

仓库内置一份可直接比较的脱敏参考样本：

```text
id: official-sub2api-20x-fast-16c16g-gpt-5.5-xhigh
```

| 项 | 值 |
|---|---|
| 生成时间 | 2026-05-25 13:54:32 UTC |
| Provider | 自建 `sub2api` relay |
| Base URL | `https://20x-fast-2.111138.xyz/v1` |
| 服务器 | 16C16G VPS |
| 模型 / 推理强度 | `gpt-5.5` / `xhigh` |
| 题库 | `hard-v1`，16 case × 2 repeats，`temperature=0` |
| 通过率 | **32 / 32** |
| Token (in / out / total) | 2770 / 4052 / 6822 |
| Latency (median / p90) | 5.9155 s / 8.9552 s |
| 功能探针 | ✅ `gpt-image-2`（b64_json）· ✅ snapshot `gpt-5.5-2026-04-23` · `/models` 9 个 ID |

> 这不是 OpenAI 官方成绩，也不能证明候选服务的上游账号类型。它是一份固定脱敏的黑盒锚点，用来对比 token、功能、速度和输出质量。

### 📋 案例：agnx 对比内置基线

用内置基线测试当前 Codex 配置里的 `https://www.agnx.run/v1`（`gpt-5.5` + `xhigh`）。本节数字来自 2026-05-25 15:48:14 UTC 的重测报告。

> **结论**：文本质量满分、延迟接近基线，作为日常 `gpt-5.5 xhigh` 文本调用可用；但它不是全功能等价 provider。候选服务有明显 input token / 成本开销，且本轮探针确认 `gpt-image-2` 与 `gpt-5.5-2026-04-23` snapshot 不可用或失败。
>
> **当前状态**：已挂，待恢复；购买入口已移除。下面保留的是 2026-05-25 15:48:14 UTC 的历史测试结果，恢复后需要重新复测。

#### 关键指标

| 维度 | Baseline | Candidate | Ratio | |
|---|---|---|---|---|
| Pass rate | 1.00 | 1.00 | Δ = 0.0 | ✅ |
| Input tokens | 1× | **4.0058×** | — | 🔴 偏高 |
| Output tokens | 1× | 0.9817× | — | ✅ |
| Total tokens | 1× | 2.2096× | — | 🟡 |
| Estimated cost | 1× | 1.291× | — | 🟡 |
| Median latency | 1× | 0.9683× | — | ✅ |
| p90 latency | 1× | 1.0582× | — | ✅ |
| Output tokens/s | 1× | 0.7709× | — | ✅ |

#### 风险评分

| Score | Value | 解读 |
|---|---|---|
| `quality_score` | **100 / 100** | 无弱模型替换信号 |
| `wrapper_or_routing_suspicion` | 70 / 100 | 🟡 存在固定 input token 档位 |
| `model_substitution_suspicion` | 0 / 100 | ✅ |
| `billing_overhead_suspicion` | 100 / 100 | 🔴 token / 成本用量明显高 |
| `feature_gap_suspicion` | 55 / 100 | 🟡 缺 `gpt-image-2` 和 snapshot |
| `speed_suspicion` | 0 / 100 | ✅ |
| `overall_risk` | **45.75 / 100** | high |
| `profile_comparison` | `unlikely_match` (49.0) | — |
| `assessment` | `passes_text_quality_but_provider_differs` | 文本质量通过，但 provider 行为差异明显 |

> **解读**：两边质量都满分，没有弱模型替换信号；但候选服务 input token 明显更高，形成 `+335` 左右的固定档位 —— 这是隐藏 wrapper / 适配器 / 路由差异的典型指纹。候选 `/models` 列出 17 个 ID，并包含若干 `gpt-5.*` / Codex 名称，但本轮只验证了 `gpt-5.5` 文本；`gpt-image-2` 返回 403，snapshot `gpt-5.5-2026-04-23` 返回 503。
>
> **关于"贵不贵"的客观补充**：input ratio 看起来涨到 **4.01×**，但 `Estimated cost ratio` 仅 **1.29×**。原因是 input 单价只有 output 的 1/6（gpt-5.5：$5 vs $30 per 1M），并且 `+335` 这种**稳定档位极有可能命中 prompt cache**（OpenAI cache 命中部分约按 10% input 单价计费）。所以 wrapper 的存在是真的，**但实际 ¥ 开销远小于 input token 倍数所暗示的水平**。下面"评分维度"小节有更详细的解释。

#### 假设 wrapper 命中 prompt cache 时的成本（情景分析）

audit 报告里新增了 `candidate_to_baseline_cost_under_cache_scenarios` 字段，按不同 cache 命中率给出 cost ratio 区间。agnx 这次审计的多余 8326 个 input token 在不同假设下的实际成本：

| 假设 wrapper 命中率 | 候选实际成本 | cost ratio vs baseline |
|---|---|---|
| 0% (即 raw `Estimated cost ratio`) | $0.17482 | **1.291×** |
| 50% | $0.15609 | **1.153×** |
| 90% | $0.14110 | **1.042×** |
| 100% | $0.13735 | **1.014×** |

> 这是一个"如果上游真的对固定前缀做了 prompt cache"的敏感度区间，不是观察结论。OpenAI 官方对命中部分的标准折扣是按 input 单价的 10% 计费（即节省 90%）。如果该候选服务的上游也按此政策走，**当 wrapper 命中率达到 90% 时，实际 ¥ 开销和 baseline 几乎相同**。

### 🎯 评分维度

| 维度 | 含义 |
|---|---|
| `quality_score` | 复杂客观题正确率 |
| `wrapper_or_routing_suspicion` | 是否出现固定 input token 档位，常见于隐藏 wrapper 或不同适配器 |
| `model_substitution_suspicion` | 是否疑似混入弱模型 —— 重点看难题掉分和不同 token 档位的正确率差异 |
| `billing_overhead_suspicion` | token / 成本是否明显高于 baseline |
| `feature_gap_suspicion` | `gpt-image-2`、snapshot model、JSON schema 等能力是否缺失 |
| `speed_suspicion` | median / p90 latency、输出 token/s 是否明显差于 baseline |
| `profile_comparison` | baseline 用 `--profile codex-fast` 标注时，输出候选是否匹配该 baseline |
| `overall_risk` | 综合风险评分 |

> 💡 **怎么客观看待 input token 放大 / 计费风险**
>
> `wrapper_or_routing_suspicion` 和 `billing_overhead_suspicion` 都会因为候选 input token 偏高而升分。但 input token 放大**对最终钱袋负担的影响往往远小于 token 倍数所暗示的**，主要有两个原因：
>
> 1. **input 单价远低于 output 单价**。以 `gpt-5.5` 为例：input $5 / 1M、output $30 / 1M，比例约 **1 : 6**。只要 output token 接近 baseline，总成本不会被 input 放大成比例拉高。
> 2. **稳定的 wrapper 前缀大概率命中 prompt cache**。如果中转方注入的是每次请求都相同的固定内容（典型征兆就是 `+335` 这种稳定档位），按 OpenAI Prompt Caching，命中部分约按 **10% 原 input 单价**计费，再次摊薄成本。
>
> 想看真实钱袋负担请直接读报告里的 `candidate_to_baseline_estimated_cost_ratio`（README 案例对比表里也列出了 "Estimated cost"）—— 这两个 suspicion 分数检出的是 **wrapper / 路由层的存在**，回答的是"是否有差异"，**不直接等价于"贵了多少倍"**。建议对照三个数一起看：input ratio + cost ratio + 是否存在稳定档位。
>
> 报告里还有一个 `candidate_to_baseline_cost_under_cache_scenarios` 字段，按 0% / 50% / 90% / 100% wrapper 命中率给出 cost ratio 区间。如果 wrapper 是稳定固定前缀（最常见情况），90% 命中假设下的数字通常和 baseline 相差无几 —— 上面 agnx 案例的表里能直接看到。

### 🚀 Codex Fast 模式判断

黑盒请求无法证明候选 provider 内部用了 Codex Fast 模式，但可以判断它是否"像你的 Codex Fast baseline"。

<details>
<summary><b>展开示例</b></summary>

生成 baseline 时加上 profile：

```bash
python3 codex_probe.py baseline \
  --current-codex \
  --profile codex-fast \
  --model gpt-5.5 \
  --repeats 3 \
  --reasoning-effort xhigh \
  --output baselines/current-codex-fast-gpt-5.5-xhigh.json
```

之后 audit 会输出：

```text
Profile match: verdict=matches_baseline_profile, confidence=...
```

如果想区分 Fast 和更慢/更深的模式，分别生成两个 baseline（`--profile codex-fast` 和 `--profile codex-deep`），同一个候选中转分别 audit 两次，看更接近哪一个。

</details>

#### Token 档位的读法

候选 provider 出现类似：

```text
+0 input tokens
+335 input tokens
```

→ 很可能存在隐藏包装或不同路由。
- **两个档位都通过复杂题** → 更像 wrapper / routing 成本问题
- **某个档位明显更容易错** → 更像混入弱模型

### ⚠️ 重要限制

- 这是黑盒启发式评估，**不是密码学证明**
- 中转站可以伪造返回的 model 名
- API 行为无法可靠证明上游是 ChatGPT Free / Plus / Pro / Team
- `gpt-image-2` 能不能用，更多说明 API/project/group 权限，不直接说明 ChatGPT 订阅等级
- token 数是 provider 返回的，可能包含隐藏 prompt、适配器包装或计费层开销

### 🛠 进阶配置

| Flag | 作用 |
|---|---|
| `--prices-file path.json` | 加载自定义价格表（`{"gpt-foo": {"input": 5.0, "output": 30.0}}`，USD per 1M tokens）。会 merge 进内置价格表，让未在源码中预置的模型也能算成本。 |
| `--no-retry` | 关闭默认 HTTP 重试。默认只对幂等 `GET` / `HEAD` / `OPTIONS` 的 5xx 或网络异常做最多 2 次指数退避；付费 `POST` 探针默认单次发送。 |
| `PROVIDER_BASE_URL` / `PROVIDER_API_KEY` 环境变量 | 推荐用法。`--api-key` 会落入 shell history。 |

### 🧪 跑测试

```bash
python3 -m unittest discover -s tests
```

测试覆盖评分函数、聚类、validator、价格表加载、HTTP 重试策略（无真实网络）。零依赖，纯 stdlib。

> 完整中文说明见 **[README.zh-CN.md](README.zh-CN.md)**，题库说明见 **[model_substitution_hard_suite.md](model_substitution_hard_suite.md)**。

---

## 🇬🇧 English

### What it does

Codex Probe is a **pure-Python, zero-dependency** CLI that compares any OpenAI-compatible endpoint against a trusted baseline (commonly your own trusted Codex provider).

| ✅ It can tell you | ❌ It cannot tell you |
|---|---|
| Whether the model behaves close to baseline on hard deterministic tasks | The upstream ChatGPT account type (Free / Plus / Pro / Team) |
| Whether the provider injects hidden prompt/wrapper tokens | The provider's internal real routing |
| Whether there's evidence of mixed routing or adapter switching | Marketing claims of "official" / "native" |
| Whether expected features are missing (`gpt-image-2`, snapshot IDs, JSON schema) | Anything at a cryptographic level of proof |
| Reported token usage and estimated cost diffs | |
| Latency, p90, output tokens/s diffs | |

> ⚠️ Unofficial tool, not affiliated with OpenAI. Reports are observable evidence + heuristic risk scores, not legal conclusions.

### What it tests

The built-in `hard-v1` suite has 16 deterministic prompts covering:

<table>
<tr>
<td valign="top" width="50%">

- 🐍 Python execution reasoning
- 📜 JavaScript execution reasoning
- 🗓 Critical path scheduling
- 🛣 Weighted graph shortest path
- 🎯 Decoy retrieval
- 📊 SQL-style aggregation
- 🎲 Conditional probability
- 🔣 Mini DSL interpretation

</td>
<td valign="top" width="50%">

- 📆 Calendar arithmetic
- 🛡 Instruction-injection resistance
- 🧬 Strict JSON output
- 🐛 Bug localization
- 🚫 Impossible-constraint detection
- 🗂 Nested JSON extraction
- 🔢 Base conversion
- 🔁 Stable repetition formatting

</td>
</tr>
</table>

See [model_substitution_hard_suite.md](model_substitution_hard_suite.md) for the full prompt suite.

### Install

Requires Python 3.10+. Python 3.11+ recommended for `--current-codex` baseline generation from `~/.codex/config.toml`.

```bash
# Run directly
python3 codex_probe.py --help

# Or install as a local CLI
python3 -m pip install -e .
codex-probe --help
```

> The legacy `provider-probe` command is still installed as a compatibility alias.

### Three ways to use it

<details open>
<summary><b>1. Use the built-in reference baseline (fastest)</b></summary>

```bash
python3 codex_probe.py list-baselines

export PROVIDER_BASE_URL="https://candidate.example.com/v1"
export PROVIDER_API_KEY="sk-..."

python3 codex_probe.py audit \
  --baseline-id official-sub2api-20x-fast-16c16g-gpt-5.5-xhigh \
  --base-url "$PROVIDER_BASE_URL" \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-vs-official-sub2api-gpt-5.5-xhigh.json
```

</details>

<details>
<summary><b>2. Build your own trusted baseline</b></summary>

If you trust your locally-configured Codex provider:

```bash
python3 codex_probe.py baseline \
  --current-codex \
  --profile codex-fast \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output baselines/current-codex-gpt-5.5-xhigh.json
```

> `--image-probe` calls `gpt-image-2` and may consume image credits.

Or with explicit endpoint credentials:

```bash
export PROVIDER_BASE_URL="https://trusted.example.com/v1"
export PROVIDER_API_KEY="sk-..."

python3 codex_probe.py baseline \
  --base-url "$PROVIDER_BASE_URL" \
  --api-key "$PROVIDER_API_KEY" \
  --label trusted \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --output baselines/trusted-gpt-5.5-xhigh.json
```

</details>

<details>
<summary><b>3. Audit a candidate against your own baseline</b></summary>

```bash
export PROVIDER_BASE_URL="https://candidate.example.com/v1"
export PROVIDER_API_KEY="sk-..."

python3 codex_probe.py audit \
  --baseline baselines/current-codex-gpt-5.5-xhigh.json \
  --label candidate \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output reports/candidate-gpt-5.5-xhigh-audit.json
```

> Saved reports are redacted; API keys are not written to output.

</details>

### 📦 Built-in reference baseline

Packaged in the repo:

```text
id: official-sub2api-20x-fast-16c16g-gpt-5.5-xhigh
```

| Field | Value |
|---|---|
| Generated | 2026-05-25 13:54:32 UTC |
| Provider | self-hosted `sub2api` relay |
| Base URL | `https://20x-fast-2.111138.xyz/v1` |
| Server | 16C16G VPS |
| Model / Effort | `gpt-5.5` / `xhigh` |
| Suite | `hard-v1`, 16 cases × 2 repeats, `temperature=0` |
| Pass rate | **32 / 32** |
| Tokens (in / out / total) | 2770 / 4052 / 6822 |
| Latency (median / p90) | 5.9155 s / 8.9552 s |
| Features | ✅ `gpt-image-2` (b64_json) · ✅ snapshot `gpt-5.5-2026-04-23` · 9 model IDs in `/models` |

> Not an OpenAI benchmark. Does not prove any candidate's upstream account type. It is a fixed, redacted black-box reference anchor.

### 📋 Case study: agnx vs the built-in baseline

The current Codex-configured `https://www.agnx.run/v1` audited with `gpt-5.5` + `xhigh`. Numbers below come from the 2026-05-25 15:48:14 UTC rerun.

> **Summary**: passed all text-quality cases, with latency close to the baseline; usable for daily `gpt-5.5 xhigh` text workloads. It is not a full feature-equivalent provider: the rerun shows material input-token / estimated-cost overhead, and `gpt-image-2` plus the `gpt-5.5-2026-04-23` snapshot were unavailable or failed.
>
> **Current status**: down, pending recovery; purchase link removed. The numbers below are the historical 2026-05-25 15:48:14 UTC audit and should be rerun after recovery.

#### Key ratios

| Metric | Baseline | Candidate | Ratio | |
|---|---|---|---|---|
| Pass rate | 1.00 | 1.00 | Δ = 0.0 | ✅ |
| Input tokens | 1× | **4.0058×** | — | 🔴 |
| Output tokens | 1× | 0.9817× | — | ✅ |
| Total tokens | 1× | 2.2096× | — | 🟡 |
| Estimated cost | 1× | 1.291× | — | 🟡 |
| Median latency | 1× | 0.9683× | — | ✅ |
| p90 latency | 1× | 1.0582× | — | ✅ |
| Output tokens/s | 1× | 0.7709× | — | ✅ |

#### Risk scores

| Score | Value | Reading |
|---|---|---|
| `quality_score` | **100 / 100** | No weak-model signal |
| `wrapper_or_routing_suspicion` | 70 / 100 | 🟡 Fixed input-token tier present |
| `model_substitution_suspicion` | 0 / 100 | ✅ |
| `billing_overhead_suspicion` | 100 / 100 | 🔴 Token / estimated-cost usage materially higher |
| `feature_gap_suspicion` | 55 / 100 | 🟡 Missing `gpt-image-2` and snapshot |
| `speed_suspicion` | 0 / 100 | ✅ |
| `overall_risk` | **45.75 / 100** | high |
| `profile_comparison` | `unlikely_match` (49.0) | — |
| `assessment` | `passes_text_quality_but_provider_differs` | Text quality passed, provider behavior differs |

> **Reading**: both passed all cases, so no weak-model substitution signal. The candidate used much more input token budget and formed a stable `+335` tier, a typical fingerprint of hidden wrappers / adapters / routing differences. Candidate `/models` listed 17 IDs and included several `gpt-5.*` / Codex names, but this audit only validated `gpt-5.5` text; `gpt-image-2` returned 403 and snapshot `gpt-5.5-2026-04-23` returned 503.
>
> **Cost-impact caveat**: input ratio looks like **4.01×**, but `Estimated cost ratio` is only **1.29×**. Two reasons: input is 1/6 the price of output for `gpt-5.5` ($5 vs $30 per 1M tokens), and a stable `+335` tier is a **prime prompt-cache candidate** (OpenAI charges cached prefixes at ~10% of the input rate). So the wrapper layer is real, **but the actual dollar overhead is much smaller than the input-token multiple suggests**. See the "Score reference" subsection below for the full reasoning.

#### Cost sensitivity if the wrapper hits prompt cache

Audit reports now include `candidate_to_baseline_cost_under_cache_scenarios`, a what-if range over cache hit rates. For agnx's 8,326 extra input tokens:

| Wrapper cache hit rate | Candidate cost | Cost ratio vs baseline |
|---|---|---|
| 0% (raw `Estimated cost ratio`) | $0.17482 | **1.291×** |
| 50% | $0.15609 | **1.153×** |
| 90% | $0.14110 | **1.042×** |
| 100% | $0.13735 | **1.014×** |

> This is a sensitivity range, not an observation. The OpenAI default is to price cached prefixes at 10% of the input rate (a 90% discount). If this candidate's upstream follows the same policy, **at 90% wrapper cache hit, the real dollar cost is effectively identical to the baseline**.

### 🎯 Score reference

| Score | Meaning |
|---|---|
| `quality_score` | Correctness on the hard deterministic suite |
| `wrapper_or_routing_suspicion` | Fixed input-token overhead tiers — hidden wrappers or different adapters |
| `model_substitution_suspicion` | Weaker / mixed model routing — look for quality drops or one tier failing more often |
| `billing_overhead_suspicion` | Materially higher input / total token budget |
| `feature_gap_suspicion` | Missing / different features vs baseline |
| `speed_suspicion` | Materially slower by median / p90 latency or output tokens/s |
| `profile_comparison` | When baseline has `--profile`, reports whether candidate matches that profile |
| `overall_risk` | Weighted summary |

> 💡 **Reading input-token inflation in context**
>
> Both `wrapper_or_routing_suspicion` and `billing_overhead_suspicion` flag input-token growth. But the impact on actual **dollar cost** is usually much smaller than the raw token multiple suggests, for two reasons:
>
> 1. **Input is much cheaper than output**. For `gpt-5.5`: input $5 / 1M, output $30 / 1M — a **~1 : 6 ratio**. As long as output stays near the baseline, total cost won't scale with input inflation.
> 2. **A stable wrapper prefix is a prime prompt-cache candidate**. If the relay injects identical fixed content on every call (the giveaway: a stable `+335` tier), OpenAI Prompt Caching charges cached prefixes at **~10% of the input rate**, further damping the cost impact.
>
> For the real wallet impact, read `candidate_to_baseline_estimated_cost_ratio` in the report (and the "Estimated cost" row in this README's case tables). These two suspicion scores detect the **existence of a wrapper / routing layer** — they answer "is there a difference," not "how much more expensive." Read the three numbers together: input ratio + cost ratio + whether a stable tier exists.
>
> Reports also include `candidate_to_baseline_cost_under_cache_scenarios`, a what-if range over 0% / 50% / 90% / 100% wrapper cache hit rates. When the wrapper is a stable fixed prefix (the common case), the 90% hit assumption typically lands near the baseline — see the agnx case study above for a concrete example.

### 🚀 Reading speed results

Every chat completion records total request latency. Reports summarize median / p90 latency, median output tokens/s, and candidate / baseline ratios.

> Latency is noisy — treat speed as supporting evidence. A relay much slower than the baseline may be overloaded, routed through an extra wrapper, or using a different upstream. A faster relay is not automatically suspicious; quality, feature, and token evidence still matters.

### 🎚 Codex Fast profile matching

Codex Probe cannot prove the provider's real upstream mode from black-box responses, but it can test whether the candidate behaves like a trusted Codex Fast baseline.

<details>
<summary><b>Example</b></summary>

```bash
python3 codex_probe.py baseline \
  --current-codex \
  --profile codex-fast \
  --model gpt-5.5 \
  --repeats 3 \
  --reasoning-effort xhigh \
  --output baselines/current-codex-fast-gpt-5.5-xhigh.json
```

Audit reports then include `profile_comparison` with `verdict`, `confidence`, and evidence. To distinguish Fast from a deeper / slower mode, build separate baselines for each mode and compare the same candidate against both.

</details>

### 📊 Reading token clusters

A clean provider should usually have input token counts close to the baseline for the same prompt.

If the candidate forms stable clusters like:

```text
+0 input tokens
+335 input tokens
```

that is strong evidence of hidden wrapper / routing differences:

- **Both clusters pass the hard suite** → more likely adapter / wrapper overhead
- **One cluster fails more often** → mixed or weaker upstream routing becomes more suspicious

### ⚠️ Limitations

- Black-box heuristic audit — **not cryptographic proof**
- Providers can spoof returned model names
- API behavior cannot reliably identify ChatGPT Free / Plus / Pro / Team account type
- `gpt-image-2` success / failure reflects API / project / group permission, not necessarily ChatGPT subscription
- Token counts are provider-reported and may include hidden prompt, adapter, or billing-layer overhead

### 🛠 Advanced configuration

| Flag | Purpose |
|---|---|
| `--prices-file path.json` | Load a custom price table (`{"gpt-foo": {"input": 5.0, "output": 30.0}}`, USD per 1M tokens). Merges into the built-in table so models not pre-listed in the source can also get cost estimates. |
| `--no-retry` | Disable the default HTTP retry. By default, only idempotent `GET` / `HEAD` / `OPTIONS` requests retry 5xx / transport errors up to 2 times with exponential backoff; paid `POST` probes are single-shot. |
| `PROVIDER_BASE_URL` / `PROVIDER_API_KEY` env vars | Recommended. `--api-key` on the command line may end up in shell history. |

### 🧪 Running tests

```bash
python3 -m unittest discover -s tests
```

Covers scoring functions, clustering, validators, price-file loading, and the HTTP retry policy (no real network calls). Zero deps, stdlib only.

### 🧹 Repository hygiene

Generated baselines, audit reports, local images, and Python caches are ignored by default. Do not commit real API keys or private provider reports unless reviewed and redacted.

---

<div align="center">
<sub>

Made for honest provider comparison · MIT License · [Report an issue](https://github.com/leiMizzou/codex-probe/issues)

</sub>
</div>
