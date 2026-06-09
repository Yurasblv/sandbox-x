from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from collector.api.dependencies import get_collection_service
from collector.api.schemas import (
    AccountsResponse,
    PostsByIdsRequest,
    PostsResponse,
    RepliesResponse,
)
from collector.core.config import settings
from collector.services.collection import CollectionService

router = APIRouter(prefix="/api/v1", tags=["x"])


@router.get("/accounts", response_model=AccountsResponse)
async def get_accounts(
    usernames: Annotated[list[str], Query(min_length=1)],
    service: Annotated[CollectionService, Depends(get_collection_service)],
) -> AccountsResponse:
    return await service.get_account(usernames)


@router.get("/accounts/search", response_model=AccountsResponse)
async def search_accounts(
    query: Annotated[str, Query(min_length=1)],
    service: Annotated[CollectionService, Depends(get_collection_service)],
    limit: Annotated[int, Query(ge=1)] = 1,
) -> AccountsResponse:
    return await service.search_accounts(query, limit)


@router.get("/accounts/{username}/posts", response_model=PostsResponse)
async def get_account_posts(
    username: str,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    limit: Annotated[int, Query(ge=1)] = settings.collector.posts_limit,
    include_replies: bool = False,
    since: Annotated[str | None, Query()] = None,
    until_date: Annotated[str | None, Query()] = None,
) -> PostsResponse:
    return await service.get_account_posts(
        username,
        limit,
        include_replies,
        since,
        until_date,
    )


@router.post("/posts/by-ids", response_model=PostsResponse)
async def get_posts_by_ids(
    body: PostsByIdsRequest,
    service: Annotated[CollectionService, Depends(get_collection_service)],
) -> PostsResponse:
    return await service.posts_by_ids(body.ids)


@router.get("/posts/search", response_model=PostsResponse)
async def search_posts(
    query: Annotated[str, Query(min_length=1)],
    service: Annotated[CollectionService, Depends(get_collection_service)],
    query_type: Literal["Latest", "Top"] = "Latest",
    limit: Annotated[int, Query(ge=1)] = 1,
    since: Annotated[str | None, Query()] = None,
    until_date: Annotated[str | None, Query()] = None,
) -> PostsResponse:
    return await service.search_posts(query, limit, query_type, since, until_date)


@router.get("/posts/{post_id}/replies", response_model=RepliesResponse)
async def get_post_replies(
    post_id: str,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    limit: Annotated[int, Query(ge=1)] = 1,
) -> RepliesResponse:
    return await service.replies(post_id, limit)
