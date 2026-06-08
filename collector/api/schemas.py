from typing import Any, Literal

from pydantic import BaseModel, Field

from collector.models import ProviderMetadata, XAccount, XPost, XReply


class AccountsResponse(BaseModel):
    accounts: list[XAccount]
    meta: ProviderMetadata


class PostsResponse(BaseModel):
    posts: list[XPost]
    meta: ProviderMetadata


class RepliesResponse(BaseModel):
    replies: list[XReply]
    meta: ProviderMetadata


class PostsByIdsRequest(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=100)


class PostsWithRepliesResponse(BaseModel):
    posts: list[XPost]
    replies_by_post: dict[str, list[XReply]]
    meta: ProviderMetadata
    replies_meta: dict[str, ProviderMetadata]


class SearchPostsQuery(BaseModel):
    query_type: Literal["Latest", "Top"] = "Latest"


class ErrorResponse(BaseModel):
    error: dict[str, Any]
