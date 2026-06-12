"""Astraflow (global) — OpenAI Responses API provider profile.

Routes through Astraflow's OpenAI-compatible endpoint (global region)
at https://api-us-ca.umodelverse.ai/v1, authenticating with a Bearer API key.
Same wire protocol as the bundled OpenAI profiles.
"""

from providers import register_provider
from providers.base import ProviderProfile

astraflow_responses = ProviderProfile(
    name="packy-astraflow-responses",
    aliases=("astraflow", "astraflow-global"),
    api_mode="codex_responses",
    env_vars=("ASTRAFLOW_API_KEY", "ASTRAFLOW_BASE_URL"),
    base_url="https://api-us-ca.umodelverse.ai/v1",
    auth_type="api_key",
    display_name="Astraflow (Global)",
    description="Astraflow by UCloud — OpenAI-compatible platform supporting 200+ models (global endpoint)",
    signup_url="https://astraflow.ucloud-global.com",
    supports_vision=True,
    default_aux_model="gpt-4o-mini",
    fallback_models=(
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
    ),
)

register_provider(astraflow_responses)


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