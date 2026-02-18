"""Pydantic Logfire setup for tau2.

Configure with LOGFIRE_TOKEN from https://logfire-us.pydantic.dev or run: logfire auth

Debug: set LOGFIRE_DEBUG=1 to print init/flush/instrumentation status to stderr.
"""

import os
import sys
import warnings

from tau2.config import LOGFIRE_SCRUBBING, USE_LOGFIRE

# Suppress Pydantic serialization warnings when Logfire serializes litellm response
# objects (Message/Choices) that have a different schema than expected
warnings.filterwarnings(
    "ignore",
    message=".*Pydantic serializer.*",
    category=UserWarning,
    module="pydantic.main",
)

_logfire_configured = False

# Logfire reads LOGFIRE_TOKEN from the environment only; push from config if set
try:
    from tau2 import config as _tau2_config
    if getattr(_tau2_config, "LOGFIRE_TOKEN", None) and not os.environ.get("LOGFIRE_TOKEN"):
        os.environ["LOGFIRE_TOKEN"] = str(_tau2_config.LOGFIRE_TOKEN)
except Exception:
    pass
_LOGFIRE_DEBUG = os.environ.get("LOGFIRE_DEBUG", "").strip() in ("1", "true", "yes")


def _debug(msg: str) -> None:
    if _LOGFIRE_DEBUG:
        print(f"[Logfire] {msg}", file=sys.stderr, flush=True)


def init_logfire() -> bool:
    """Configure Logfire if enabled. Safe to call multiple times.

    Enabled when USE_LOGFIRE is True or LOGFIRE_TOKEN is set.
    Returns True if Logfire was configured, False otherwise.
    """
    global _logfire_configured
    if _logfire_configured:
        _debug("init_logfire: already configured, skipping")
        return True
    enabled = USE_LOGFIRE or os.environ.get("LOGFIRE_TOKEN")
    _debug(f"init_logfire: USE_LOGFIRE={USE_LOGFIRE}, LOGFIRE_TOKEN set={bool(os.environ.get('LOGFIRE_TOKEN'))}, enabled={enabled}")
    if not enabled:
        _debug("init_logfire: disabled, not configuring")
        return False
    try:
        import logfire

        _debug("init_logfire: calling logfire.configure() ...")
        logfire.configure(scrubbing=LOGFIRE_SCRUBBING)
        _debug("init_logfire: configure() ok")
        try:
            logfire.instrument_litellm()
            _debug("init_logfire: instrument_litellm() ok")
        except Exception as e:
            _debug(f"init_logfire: instrument_litellm() failed: {e!r}")
        _logfire_configured = True
        _debug("init_logfire: done, Logfire configured")
        return True
    except Exception as e:
        _debug(f"init_logfire: failed: {e!r}")
        return False


def is_logfire_enabled() -> bool:
    """Return whether Logfire is configured and active."""
    return _logfire_configured


def flush_logfire(timeout_millis: int = 10_000) -> None:
    """Flush pending Logfire spans so they are sent before process exit.

    Call this after runs (e.g. after run_domain returns) so traces and LLM spans
    are exported; otherwise the process may exit before the batch exporter sends them.
    No-op if Logfire is not configured.
    """
    _debug(f"flush_logfire: called, _logfire_configured={_logfire_configured}")
    if not _logfire_configured:
        _debug("flush_logfire: not configured, no-op")
        return
    try:
        import logfire

        _debug(f"flush_logfire: calling logfire.force_flush(timeout_millis={timeout_millis}) ...")
        ok = logfire.force_flush(timeout_millis=timeout_millis)
        _debug(f"flush_logfire: force_flush returned {ok!r}")
    except Exception as e:
        _debug(f"flush_logfire: failed: {e!r}")


def add_loguru_handler(log_level: str = "DEBUG"):
    """Add Logfire as a loguru sink so existing loguru logs are sent to Logfire.

    Call after loguru is configured (e.g. in run_domain). No-op if Logfire not configured.
    """
    _debug(f"add_loguru_handler: called, _logfire_configured={_logfire_configured}")
    if not _logfire_configured:
        return
    try:
        import logfire
        from loguru import logger

        logger.add(logfire.loguru_handler(), level=log_level)
        _debug("add_loguru_handler: loguru handler added")
    except Exception as e:
        _debug(f"add_loguru_handler: failed: {e!r}")
