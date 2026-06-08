# X Collector Service

FastAPI microservice for Stage 2 X collection. It uses the configured X API provider now and keeps provider-specific code behind an interface so Apify, official X, or another provider can be added later without changing API/business logic.

## Endpoints

- `GET /api/v1/accounts/default` - fetch configured demo accounts.
- `GET /api/v1/accounts/search?query=elon&limit=20` - search accounts by query.
- `GET /api/v1/accounts/{username}/posts-with-replies?limit=20&replies_limit=20` - fetch account posts and replies for each post.
- `POST /api/v1/posts/by-ids` - fetch posts by a list of post IDs.
- `GET /api/v1/posts/search?query=from:elonmusk&query_type=Latest&limit=20` - search posts.
- `GET /api/v1/posts/{post_id}/replies?limit=20` - fetch replies for a post.

## Run Locally

```bash
cp .env.example .env
uv sync
uv run uvicorn collector.main:app --reload
```

Set `X__API_KEY` in `.env`. The referral link from the task is used when creating the API account: `https://twitterapi.io/?ref=NateHerkelman`.

## Notes

The X API provider uses `X-API-Key` authentication. Its paginated endpoints return `has_next_page` and `next_cursor`; this service follows those cursors until `limit` is reached. The provider documentation currently warns that `advanced_search` pagination is problematic and recommends time-windowed queries via `since_time` and `until_time`; the service supports cursor pagination defensively, but callers should prefer bounded search queries for predictable runs.

## Architecture

```text
api/          FastAPI routers and request/response schemas
services/     Business collection orchestration
providers/    Provider interface and X API provider adapter
core/         App/X settings, logging, errors
```

To add a provider:

1. Implement `XProvider` in `collector/providers/base.py`.
2. Add the implementation to `providers/factory.py`.
3. Keep provider-only fields in `raw` while returning normalized DTOs.

## Quality Gates

```bash
uv run ruff check .
uv run pytest
```
