# PackyAPI provider plugins for Hermes Agent

Two model-provider plugins that route Hermes through [PackyAPI](https://www.packyapi.com):

| Plugin | `api_mode` | base_url |
| --- | --- | --- |
| `packy-openai-responses` | `codex_responses` | `https://www.packyapi.com/v1` |
| `packy-anthropic-messages` | `anthropic_messages` | `https://www.packyapi.com` |

Both authenticate with a single API key via the `PACKY_API_KEY` env var.

Astraflow by UCloud is also available as OpenAI-compatible providers:

| Provider | `api_mode` | base_url |
| --- | --- | --- |
| `astraflow` | `chat_completions` | `https://api-us-ca.umodelverse.ai/v1` |
| `astraflow-cn` | `chat_completions` | `https://api.modelverse.cn/v1` |

## Install

Copy (or symlink) both directories into your Hermes plugin dir so they are
discovered as user plugins (last-writer-wins, no repo edits needed):

```bash
mkdir -p "${HERMES_HOME:-$HOME/.hermes}/plugins/model-providers"
cp -r packy-openai-responses packy-anthropic-messages \
  "${HERMES_HOME:-$HOME/.hermes}/plugins/model-providers/"
```

## Configure

```bash
export PACKY_API_KEY=sk-...           # your PackyAPI key (used by both plugins)
# optional endpoint overrides:
# export PACKY_OPENAI_BASE_URL=https://www.packyapi.com/v1
# export PACKY_ANTHROPIC_BASE_URL=https://www.packyapi.com

export ASTRAFLOW_API_KEY=sk-...       # Astraflow global endpoint
# or: export ASTRAFLOW_CN_API_KEY=sk-...  # Astraflow China endpoint
```

## Use

```bash
hermes doctor                         # confirm both providers load
hermes -z "hello" --provider packy-anthropic-messages -m claude-sonnet-4-6
hermes -z "hello" --provider packy-openai-responses   -m gpt-5.3-codex
hermes -z "hello" --provider astraflow -m gpt-4o-mini
```

`provider:model` syntax and aliases also work, e.g.
`packy-claude:claude-opus-4-8` or `packy-openai:gpt-5.4`.

## Model list

`fallback_models` in each `__init__.py` are only shown in the `/model` picker
when the live `/models` fetch fails. The lists come from
[PackyAPI pricing](https://www.packyapi.com/api/pricing) and include only the
Claude series and gpt series (no reasoning-level "thinking" variants, no image
or internal-tool models).

**packy-anthropic-messages:**
```
claude-opus-4-8, claude-opus-4-7, claude-opus-4-6, claude-opus-4-5-20251101,
claude-opus-4-1-20250805, claude-sonnet-4-6, claude-sonnet-4-5-20250929,
claude-haiku-4-5-20251001, claude-fable-5
```

**packy-openai-responses:**
```
gpt-5.5, gpt-5.4, gpt-5.4-pro, gpt-5.4-mini, gpt-5.3-codex, gpt-4.1
```

Edit them to match the models your PackyAPI plan actually serves.

## Notes

- `packy-anthropic-messages` sends the `x-api-key` header (Anthropic style);
  `packy-openai-responses` sends `Authorization: Bearer` (OpenAI style).
- Both set a CLI-identity `User-Agent` (`_PACKY_*_UA` constant in each
  `__init__.py`) so requests pass PackyAPI's Cloudflare layer instead of being
  403'd as the default `Python-urllib/x.y` agent. Edit the constant if PackyAPI
  expects a different client string.
