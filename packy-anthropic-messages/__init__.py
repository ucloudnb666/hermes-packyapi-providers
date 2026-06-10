"""PackyAPI — Anthropic Messages API provider profile.

Routes through PackyAPI's Anthropic-compatible endpoint
(api_mode="anthropic_messages"). base_url is the host root; the Messages
adapter appends /v1/messages itself, mirroring the bundled `anthropic`
profile. Auth uses the x-api-key header (not Bearer), so fetch_models is
overridden to match.
"""

import json
import logging
import urllib.request

from providers import register_provider
from providers.base import ProviderProfile

logger = logging.getLogger(__name__)

# PackyAPI sits behind Cloudflare, which 403s the default ``Python-urllib/x.y``
# User-Agent that urllib sends on the /v1/models probe below. Advertise the
# Claude Code CLI identity (PackyAPI's expected upstream client) instead.
# NOTE: the actual /v1/messages inference path is built by
# agent/anthropic_adapter.py, which uses the Anthropic SDK's own (non-urllib)
# User-Agent and does NOT read profile.default_headers — so this UA governs the
# plugin's own catalog request, where the 403 risk actually lives.
_PACKY_ANTHROPIC_UA = "claude-cli/1.0.0 (external, packy-hermes)"


class PackyAnthropicProfile(ProviderProfile):
    """PackyAPI Anthropic relay — uses x-api-key header, not Bearer."""

    def fetch_models(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        """Fetch the catalog with Anthropic-style headers."""
        if not api_key:
            return None
        url = (self.base_url or "https://www.packyapi.com").rstrip("/") + "/v1/models"
        try:
            req = urllib.request.Request(url)
            req.add_header("x-api-key", api_key)
            req.add_header("anthropic-version", "2023-06-01")
            req.add_header("Accept", "application/json")
            req.add_header("User-Agent", _PACKY_ANTHROPIC_UA)
            for k, v in self.default_headers.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
            return [
                m["id"]
                for m in data.get("data", [])
                if isinstance(m, dict) and "id" in m
            ]
        except Exception as exc:
            logger.debug("fetch_models(packy-anthropic-messages): %s", exc)
            return None


packy_anthropic_messages = PackyAnthropicProfile(
    name="packy-anthropic-messages",
    aliases=("packy-anthropic", "packy-claude"),
    api_mode="anthropic_messages",
    # API-key vars in priority order. A trailing *_BASE_URL entry lets the
    # user override the endpoint without editing this file.
    env_vars=("PACKY_API_KEY", "PACKY_ANTHROPIC_BASE_URL"),
    # Host root only — the Messages adapter appends /v1/messages.
    base_url="https://www.packyapi.com",
    auth_type="api_key",
    default_headers={"User-Agent": _PACKY_ANTHROPIC_UA},
    display_name="Packy (Anthropic Messages)",
    description="PackyAPI — Anthropic Messages API relay",
    signup_url="https://www.packyapi.com",
    supports_vision=True,
    default_aux_model="claude-haiku-4-5-20251001",
    # Catalog from https://www.packyapi.com/api/pricing (Claude series).
    # Shown in the /model picker when the live fetch fails.
    fallback_models=(
        "claude-opus-4-8",
        "claude-opus-4-7",
        "claude-opus-4-6",
        "claude-opus-4-5-20251101",
        "claude-opus-4-1-20250805",
        "claude-sonnet-4-6",
        "claude-sonnet-4-5-20250929",
        "claude-haiku-4-5-20251001",
        "claude-fable-5",
    ),
)

register_provider(packy_anthropic_messages)


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
