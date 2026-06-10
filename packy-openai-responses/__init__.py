"""PackyAPI — OpenAI Responses API provider profile.

Routes through PackyAPI's OpenAI-compatible Responses endpoint
(api_mode="codex_responses"), authenticating with a Bearer API key.
Same wire protocol as the bundled `xai` / `openai-codex` profiles, but
pointed at https://www.packyapi.com/v1 and using a plain API key instead
of external OAuth.
"""

from providers import register_provider
from providers.base import ProviderProfile

# PackyAPI sits behind Cloudflare, which 403s requests carrying urllib's
# default ``Python-urllib/x.y`` User-Agent. Advertise the Codex CLI identity
# (PackyAPI's expected upstream client) on every request. This propagates to:
#   - the inference client (agent_init.py falls back to profile.default_headers
#     for non-special-cased hosts like www.packyapi.com)
#   - the live /v1/models probe (ProviderProfile.fetch_models forwards
#     self.default_headers)
_PACKY_OPENAI_UA = "codex_cli_rs/0.45.0 (external, packy-hermes)"

packy_openai_responses = ProviderProfile(
    name="packy-openai-responses",
    aliases=("packy-openai", "packy-responses", "packy-codex"),
    api_mode="codex_responses",
    # API-key vars in priority order. A trailing *_BASE_URL entry lets the
    # user override the endpoint without editing this file.
    env_vars=("PACKY_API_KEY", "PACKY_OPENAI_BASE_URL"),
    base_url="https://www.packyapi.com/v1",
    auth_type="api_key",
    default_headers={"User-Agent": _PACKY_OPENAI_UA},
    display_name="Packy (OpenAI Responses)",
    description="PackyAPI — OpenAI Responses API relay",
    signup_url="https://www.packyapi.com",
    supports_vision=True,
    default_aux_model="gpt-5.4-mini",
    # Catalog from https://www.packyapi.com/api/pricing (gpt series, no
    # reasoning-level "thinking" variants). Shown in the /model picker when
    # the live /v1/models fetch fails.
    fallback_models=(
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-pro",
        "gpt-5.4-mini",
        "gpt-5.3-codex",
        "gpt-4.1",
    ),
)

register_provider(packy_openai_responses)


# ---------------------------------------------------------------------------
# Runtime fix: Hermes 1.x does not read profile.api_mode for third-party
# plugins.  _resolve_runtime_from_pool_entry (hermes_cli/runtime_provider.py)
# falls back to chat_completions unless the base URL ends with /anthropic
# or matches a hardcoded hostname.  Patch it so packy-* providers honour
# their declared api_mode.
# ---------------------------------------------------------------------------
def _install_packy_runtime_fix():
    """Idempotent monkey-patch: read profile.api_mode for packy-* providers.

    Both packy plugins call this at import time.  The first wins; the second
    is a no-op (sentinel ``_packy_api_mode_patched`` on the module).
    """
    try:
        import hermes_cli.runtime_provider as _rp
    except ImportError:
        return

    if getattr(_rp, "_packy_api_mode_patched", False):
        return
    _rp._packy_api_mode_patched = True

    _original_resolve = _rp._resolve_runtime_from_pool_entry

    def _patched_resolve(*, provider, **kwargs):
        result = _original_resolve(provider=provider, **kwargs)
        if provider and isinstance(provider, str) and provider.startswith("packy-"):
            try:
                from providers import get_provider_profile
                prof = get_provider_profile(provider)
            except Exception:
                prof = None
            if prof is not None and prof.api_mode:
                result["api_mode"] = prof.api_mode
                # Strip /v1 suffix for anthropic_messages providers so the
                # Anthropic SDK does not construct /v1/v1/messages.
                if prof.api_mode == "anthropic_messages":
                    import re
                    result["base_url"] = re.sub(r"/v1/?$", "", result.get("base_url", ""))
        return result

    _rp._resolve_runtime_from_pool_entry = _patched_resolve


_install_packy_runtime_fix()
