from typing import Any

from collector.models import ProviderMetadata, XAccount, XPost, XReply


def map_account(raw: dict[str, Any]) -> XAccount:
    mapped = {**raw, "raw": raw}
    if "userName" not in mapped:
        for key in ("username", "screen_name", "screenName", "user_name"):
            if username := mapped.get(key):
                mapped["userName"] = username
                break
    return XAccount.model_validate(mapped)


def map_post(raw: dict[str, Any]) -> XPost:
    mapped = {**raw, "raw": raw}
    if author := raw.get("author"):
        mapped["author"] = map_account(author)
    mapped["media"] = raw.get("media") or raw.get("extendedEntities", {}).get("media") or []
    return XPost.model_validate(mapped)


def map_reply(raw: dict[str, Any]) -> XReply:
    return XReply.model_validate(map_post(raw).model_dump())


def build_params(**params: Any) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}


def build_metadata(
    *,
    provider_key: str,
    request_path: str | None = None,
    input_query: str | None = None,
    input_ids: list[str] | None = None,
    next_cursor: str | None = None,
    has_next_page: bool = False,
    raw: dict[str, Any] | None = None,
) -> ProviderMetadata:
    return ProviderMetadata(
        provider_key=provider_key,
        request_path=request_path,
        input_query=input_query,
        input_ids=input_ids or [],
        next_cursor=next_cursor,
        has_next_page=has_next_page,
        raw=raw or {},
    )
