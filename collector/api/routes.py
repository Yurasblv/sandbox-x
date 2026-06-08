from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from collector.api.dependencies import get_collection_service
from collector.api.schemas import (
    AccountsResponse,
    PostsByIdsRequest,
    PostsResponse,
    PostsWithRepliesResponse,
    RepliesResponse,
)
from collector.services.collection import CollectionService

router = APIRouter(prefix="/api/v1", tags=["x"])


@router.get("/accounts/default", response_model=AccountsResponse)
async def get_default_accounts(
    service: Annotated[CollectionService, Depends(get_collection_service)],
) -> AccountsResponse:
    result = await service.default_accounts()
    return AccountsResponse(accounts=result.accounts, meta=result.metadata)


@router.get("/accounts", response_model=AccountsResponse)
async def get_accounts(
    usernames: Annotated[list[str], Query(min_length=1)],
    service: Annotated[CollectionService, Depends(get_collection_service)],
) -> AccountsResponse:
    result = await service.accounts(usernames)
    return AccountsResponse(accounts=result.accounts, meta=result.metadata)


@router.get("/accounts/search", response_model=AccountsResponse)
async def search_accounts(
    query: Annotated[str, Query(min_length=1)],
    service: Annotated[CollectionService, Depends(get_collection_service)],
    limit: Annotated[int, Query(ge=1)] = 20,
) -> AccountsResponse:
    result = await service.search_accounts(query, limit)
    return AccountsResponse(accounts=result.accounts, meta=result.metadata)


@router.get("/accounts/{username}/posts-with-replies", response_model=PostsWithRepliesResponse)
async def get_account_posts_with_replies(
    username: str,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    limit: Annotated[int, Query(ge=1)] = 20,
    replies_limit: Annotated[int, Query(ge=1)] = 20,
) -> PostsWithRepliesResponse:
    posts_result, replies_by_post = await service.account_posts_with_replies(
        username,
        limit,
        replies_limit,
    )
    return PostsWithRepliesResponse(
        posts=posts_result.posts,
        replies_by_post={
            post_id: reply_result.replies for post_id, reply_result in replies_by_post.items()
        },
        meta=posts_result.metadata,
        replies_meta={
            post_id: reply_result.metadata for post_id, reply_result in replies_by_post.items()
        },
    )


@router.post("/posts/by-ids", response_model=PostsResponse)
async def get_posts_by_ids(
    body: PostsByIdsRequest,
    service: Annotated[CollectionService, Depends(get_collection_service)],
) -> PostsResponse:
    result = await service.posts_by_ids(body.ids)
    return PostsResponse(posts=result.posts, meta=result.metadata)


@router.get("/posts/search", response_model=PostsResponse)
async def search_posts(
    query: Annotated[str, Query(min_length=1)],
    service: Annotated[CollectionService, Depends(get_collection_service)],
    query_type: Literal["Latest", "Top"] = "Latest",
    limit: Annotated[int, Query(ge=1)] = 20,
) -> PostsResponse:
    result = await service.search_posts(query, limit, query_type)
    return PostsResponse(posts=result.posts, meta=result.metadata)


@router.get("/posts/{post_id}/replies", response_model=RepliesResponse)
async def get_post_replies(
    post_id: str,
    service: Annotated[CollectionService, Depends(get_collection_service)],
    limit: Annotated[int, Query(ge=1)] = 20,
) -> RepliesResponse:
    result = await service.replies(post_id, limit)
    return RepliesResponse(replies=result.replies, meta=result.metadata)
