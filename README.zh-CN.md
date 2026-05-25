# Provider Probe

用于黑盒评估 OpenAI-compatible 中转站 / API 网关 / 模型代理的命令行工具。

它的目标不是证明上游账号到底是 Free、Plus 还是 Pro，而是用同一套复杂题和功能探针，对比一个可信 baseline，判断候选 provider 是否存在：

- 质量明显下降
- 输入 token 被隐藏包装放大
- 多路由 / 多适配器切换
- 疑似混用较弱模型
- `gpt-image-2`、snapshot model 等功能缺失
- 计费或 token 统计异常

## 基本流程

先用你信任的 provider 生成 baseline：

```bash
python3 provider_probe.py baseline \
  --current-codex \
  --model gpt-5.5 \
  --repeats 2 \
  --reasoning-effort xhigh \
  --image-probe \
  --output baselines/current-codex-gpt-5.5-xhigh.json
```

然后测试候选中转：

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

报告会输出这些分数：

```text
quality_score
wrapper_or_routing_suspicion
model_substitution_suspicion
billing_overhead_suspicion
feature_gap_suspicion
overall_risk
```

## 分数解释

- `quality_score`: 复杂客观题正确率。
- `wrapper_or_routing_suspicion`: 是否出现固定 input token 档位，比如有时多 `+335 tokens`。
- `model_substitution_suspicion`: 是否可能混入弱模型。主要看难题是否掉分，以及不同 token 档位是否正确率不同。
- `billing_overhead_suspicion`: token / 成本是否明显高于 baseline。
- `feature_gap_suspicion`: `gpt-image-2`、snapshot model、JSON schema 等功能是否缺失。
- `overall_risk`: 综合风险。

## 重要限制

- 这是黑盒启发式评估，不是密码学证明。
- 中转站可以伪造返回的 model 名。
- API 行为无法可靠证明上游是 ChatGPT Free / Plus / Pro / Team。
- `gpt-image-2` 能不能用，更多说明 API/project/group 权限，不直接说明 ChatGPT 订阅等级。
- token 数是 provider 返回的，可能包含隐藏 prompt、适配器包装或计费层开销。
