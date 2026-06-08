from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProviderMetadata(BaseModel):
    provider_key: str
    request_path: str | None = None
    input_query: str | None = None
    input_ids: list[str] = Field(default_factory=list)
    next_cursor: str | None = None
    has_next_page: bool = False
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw: dict[str, Any] = Field(default_factory=dict)


class XAccount(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    username: str = Field(alias="userName")
    name: str | None = None
    url: str | None = None
    description: str | None = None
    location: str | None = None
    followers_count: int | None = Field(default=None, alias="followers")
    following_count: int | None = Field(default=None, alias="following")
    posts_count: int | None = Field(default=None, alias="statusesCount")
    profile_image_url: str | None = Field(default=None, alias="profilePicture")
    created_at: str | None = Field(default=None, alias="createdAt")
    is_verified: bool | None = Field(default=None, alias="isBlueVerified")
    raw: dict[str, Any] = Field(default_factory=dict)


class XPost(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    url: str | None = None
    text: str | None = None
    created_at: str | None = Field(default=None, alias="createdAt")
    language: str | None = Field(default=None, alias="lang")
    retweets: int | None = Field(default=None, alias="retweetCount")
    replies_count: int | None = Field(default=None, alias="replyCount")
    likes: int | None = Field(default=None, alias="likeCount")
    quotes: int | None = Field(default=None, alias="quoteCount")
    views: int | None = Field(default=None, alias="viewCount")
    is_reply: bool | None = Field(default=None, alias="isReply")
    in_reply_to_id: str | None = Field(default=None, alias="inReplyToId")
    conversation_id: str | None = Field(default=None, alias="conversationId")
    author: XAccount | None = None
    media: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class XReply(XPost):
    pass
