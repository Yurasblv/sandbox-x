from fastapi.testclient import TestClient

from collector.api.dependencies import get_collection_service
from collector.api.schemas import AccountsResponse, PostsResponse, PostsWithRepliesResponse, RepliesResponse
from collector.main import app
from collector.models import ErrorDTO, ProviderMetadata, XAccount, XPost, XReply


class FakeCollectionService:
    async def get_account(self, usernames: list[str]) -> AccountsResponse:
        return AccountsResponse(
            accounts=[_account(username) for username in usernames],
            meta=_meta("/twitter/user/info", input_ids=usernames),
            errors=[ErrorDTO(source="bad_user", error="failed", status_code=500)],
        )

    async def search_accounts(self, query: str, limit: int) -> AccountsResponse:
        return AccountsResponse(
            accounts=[_account(f"{query}_{index}") for index in range(limit)],
            meta=_meta("/twitter/user/search", input_query=query),
        )

    async def get_account_posts(
        self,
        username: str,
        posts_limit: int,
        replies_limit: int,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostsWithRepliesResponse:
        posts = [_post(f"{username}-{index}", username) for index in range(posts_limit)]
        return PostsWithRepliesResponse(
            posts=posts,
            replies_by_post={
                post.id: [_reply(f"{post.id}-reply-{index}") for index in range(replies_limit)]
                for post in posts
            },
            meta=_meta("/twitter/user/last_tweets", input_ids=[username]),
            replies_meta={
                post.id: _meta("/twitter/tweet/replies", input_ids=[post.id]) for post in posts
            },
        )

    async def posts_by_ids(self, ids: list[str]) -> PostsResponse:
        return PostsResponse(
            posts=[_post(post_id, "author") for post_id in ids],
            meta=_meta("/twitter/tweets", input_ids=ids),
        )

    async def search_posts(
        self,
        query: str,
        limit: int,
        query_type: str,
        since: str | None = None,
        until_date: str | None = None,
    ) -> PostsResponse:
        return PostsResponse(
            posts=[_post(f"{query_type}-{index}", "search_author") for index in range(limit)],
            meta=_meta("/twitter/tweet/advanced_search", input_query=query),
        )

    async def replies(self, post_id: str, limit: int) -> RepliesResponse:
        return RepliesResponse(
            replies=[_reply(f"{post_id}-reply-{index}") for index in range(limit)],
            meta=_meta("/twitter/tweet/replies", input_ids=[post_id]),
        )


def override_collection_service() -> FakeCollectionService:
    return FakeCollectionService()


def test_get_accounts_requires_usernames() -> None:
    client = _client()

    response = client.get("/api/v1/accounts")

    assert response.status_code == 422


def test_health() -> None:
    client = _client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_cors_preflight() -> None:
    client = _client()

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_get_accounts_by_usernames() -> None:
    client = _client()

    response = client.get("/api/v1/accounts", params={"usernames": ["elonmusk", "openai"]})

    assert response.status_code == 200
    body = response.json()
    assert [account["userName"] for account in body["accounts"]] == ["elonmusk", "openai"]
    assert body["meta"]["input_ids"] == ["elonmusk", "openai"]


def test_search_accounts() -> None:
    client = _client()

    response = client.get("/api/v1/accounts/search", params={"query": "ai", "limit": 2})

    assert response.status_code == 200
    body = response.json()
    assert len(body["accounts"]) == 2
    assert body["meta"]["input_query"] == "ai"


def test_get_account_posts_with_replies() -> None:
    client = _client()

    response = client.get(
        "/api/v1/accounts/elonmusk/posts",
        params={"posts_limit": 2, "replies_limit": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["posts"]) == 2
    assert sorted(body["replies_by_post"]) == ["elonmusk-0", "elonmusk-1"]
    assert len(body["replies_by_post"]["elonmusk-0"]) == 1


def test_get_posts_by_ids() -> None:
    client = _client()

    response = client.post("/api/v1/posts/by-ids", json={"ids": ["1", "2"]})

    assert response.status_code == 200
    body = response.json()
    assert [post["id"] for post in body["posts"]] == ["1", "2"]
    assert body["meta"]["input_ids"] == ["1", "2"]


def test_search_posts() -> None:
    client = _client()

    response = client.get(
        "/api/v1/posts/search",
        params={"query": "from:openai", "query_type": "Top", "limit": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert [post["id"] for post in body["posts"]] == ["Top-0", "Top-1"]
    assert body["meta"]["input_query"] == "from:openai"


def test_get_post_replies() -> None:
    client = _client()

    response = client.get("/api/v1/posts/123/replies", params={"limit": 2})

    assert response.status_code == 200
    body = response.json()
    assert [reply["id"] for reply in body["replies"]] == ["123-reply-0", "123-reply-1"]
    assert body["meta"]["input_ids"] == ["123"]


def test_provider_key_is_enumerated_in_openapi() -> None:
    schema = app.openapi()

    provider_param = next(
        param
        for path, methods in schema["paths"].items()
        if path == "/api/v1/accounts/search"
        for param in methods["get"]["parameters"]
        if param["name"] == "provider_key"
    )
    provider_ref = provider_param["schema"]["anyOf"][0]["$ref"].split("/")[-1]

    assert schema["components"]["schemas"][provider_ref]["enum"] == ["x_io"]


def _client() -> TestClient:
    app.dependency_overrides[get_collection_service] = override_collection_service
    return TestClient(app)


def _account(username: str) -> XAccount:
    return XAccount(id=f"{username}-id", username=username, name=username.title())


def _post(post_id: str, username: str) -> XPost:
    return XPost(
        id=post_id,
        text=f"Post {post_id}",
        author=_account(username),
        replies_count=1,
    )


def _reply(reply_id: str) -> XReply:
    return XReply(id=reply_id, text=f"Reply {reply_id}", author=_account("reply_author"))


def _meta(
    path: str,
    *,
    input_query: str | None = None,
    input_ids: list[str] | None = None,
) -> ProviderMetadata:
    return ProviderMetadata(
        provider_key="test_provider",
        request_path=path,
        input_query=input_query,
        input_ids=input_ids or [],
    )
