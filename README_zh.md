# PackyAPI provider plugins for Hermes Agent

将 Hermes Agent 的推理请求路由到 [PackyAPI](https://www.packyapi.com) 的两个 model-provider 插件：

| 插件 | `api_mode` | base_url |
| --- | --- | --- |
| `packy-openai-responses` | `codex_responses` | `https://www.packyapi.com/v1` |
| `packy-anthropic-messages` | `anthropic_messages` | `https://www.packyapi.com` |

两个插件都通过环境变量 `PACKY_API_KEY` 使用同一个 API key 鉴权。

## 安装

把两个目录复制（或软链接）到 Hermes 的插件目录，作为 user plugin 被自动发现（last-writer-wins，无需修改仓库）：

```bash
mkdir -p "${HERMES_HOME:-$HOME/.hermes}/plugins/model-providers"
cp -r packy-openai-responses packy-anthropic-messages \
  "${HERMES_HOME:-$HOME/.hermes}/plugins/model-providers/"
```

## 配置

```bash
export PACKY_API_KEY=sk-...           # 你的 PackyAPI key（两个插件共用）
# 可选的端点覆盖：
# export PACKY_OPENAI_BASE_URL=https://www.packyapi.com/v1
# export PACKY_ANTHROPIC_BASE_URL=https://www.packyapi.com
```

## 使用

```bash
hermes doctor                         # 确认两个 provider 都已加载
hermes -z "hello" --provider packy-anthropic-messages -m claude-sonnet-4-6
hermes -z "hello" --provider packy-openai-responses   -m gpt-5.3-codex
```

`provider:model` 语法和别名同样可用，例如
`packy-claude:claude-opus-4-8` 或 `packy-openai:gpt-5.4`。

## 模型列表

各 `__init__.py` 里的 `fallback_models` 只在实时 `/models` 拉取失败时显示于
`/model` 选择器。列表取自 [PackyAPI pricing](https://www.packyapi.com/api/pricing)，
仅含 Claude 系列与 gpt 系列（不含思考等级变体、图像与内部工具模型）。

**packy-anthropic-messages：**
```
claude-opus-4-8, claude-opus-4-7, claude-opus-4-6, claude-opus-4-5-20251101,
claude-opus-4-1-20250805, claude-sonnet-4-6, claude-sonnet-4-5-20250929,
claude-haiku-4-5-20251001, claude-fable-5
```

**packy-openai-responses：**
```
gpt-5.5, gpt-5.4, gpt-5.4-pro, gpt-5.4-mini, gpt-5.3-codex, gpt-4.1
```

如你的套餐实际可用模型不同，请自行编辑。

## 说明

- `packy-anthropic-messages` 发送 `x-api-key` 头（Anthropic 风格）；
  `packy-openai-responses` 发送 `Authorization: Bearer`（OpenAI 风格）。
- 两个插件都设置了 CLI 身份的 `User-Agent`（各 `__init__.py` 中的 `_PACKY_*_UA`
  常量），以便请求通过 PackyAPI 的 Cloudflare，而不是被当作默认的
  `Python-urllib/x.y` 拦截返回 403。若 PackyAPI 期望其它客户端字符串，请修改该常量。
