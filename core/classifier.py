
from core.platforms import Platform
from core.utils import ResultStatus


def classify_response(status: int, text: str, headers: dict,
                      location: str, platform: Platform) -> tuple[str, str]:
    text_lower = text.lower()
    headers_str = str(headers).lower()

    has_success = any(
        ind.lower() in text_lower or ind.lower() in headers_str
        for ind in platform.success_indicators
    )
    has_fail = any(
        ind.lower() in text_lower
        for ind in platform.fail_indicators
    )

    if 200 <= status < 300:
        if has_success and not has_fail:
            return ResultStatus.VALID, f"HTTP {status}"
        if has_fail:
            return ResultStatus.INVALID, f"HTTP {status} - fail indicator"
        return ResultStatus.INVALID, f"HTTP {status} - no success"

    if 300 <= status < 400:
        if not platform.redirect_valid:
            return ResultStatus.INVALID, f"Redirect {status} (not trusted)"
        if any(d in location.lower() for d in ["dashboard", "account", "home", "app"]):
            return ResultStatus.VALID, f"Redirect {status} -> {location[:60]}"
        return ResultStatus.VALID, f"Redirect {status}"

    if status in (401, 403):
        return ResultStatus.INVALID, f"HTTP {status}"
    if 400 <= status < 500:
        return ResultStatus.INVALID, f"HTTP {status}"

    if status >= 500:
        return ResultStatus.ERROR, f"HTTP {status}"

    return ResultStatus.INVALID, f"HTTP {status} (unhandled)"
