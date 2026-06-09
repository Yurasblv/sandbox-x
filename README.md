# X Collector Service

FastAPI microservice for Stage 2 X collection. It uses the configured X API provider now and keeps provider-specific code behind an interface so Apify, official X, or another provider can be added later without changing API/business logic.

## Endpoints

- `GET /health`
  - no query
- `GET /api/v1/accounts?provider_key=x_io&usernames=elonmusk&usernames=openai`
  - `provider_key=x_io`
  - `usernames=elonmusk&usernames=openai`
- `GET /api/v1/accounts/search?provider_key=x_io&query=elon&limit=2`
  - `provider_key=x_io`
  - `query=elon&limit=2`
- `GET /api/v1/accounts/{username}/posts?provider_key=x_io&posts_limit=2&replies_limit=1`
  - `provider_key=x_io`
  - `username=elonmusk`
  - `posts_limit=2&replies_limit=1`
- `POST /api/v1/posts/by-ids?provider_key=x_io`
  - `provider_key=x_io`
  - body: `{"ids":["1","2"]}`
- `GET /api/v1/posts/search?provider_key=x_io&query=from:elonmusk&query_type=Latest&limit=2`
  - `provider_key=x_io`
  - `query=from:elonmusk&query_type=Latest&limit=2`
- `GET /api/v1/posts/{post_id}/replies?provider_key=x_io&limit=2`
  - `provider_key=x_io`
  - `post_id=123`
  - `limit=2`

## Swagger

Open `http://localhost:8000/docs` and use:

- `provider_key`: `x_io`
- `accounts`: `usernames=elonmusk&usernames=openai`
- `accounts/search`: `query=elon&limit=2`
- `accounts/{username}/posts`: `username=elonmusk&posts_limit=2&replies_limit=1`
- `posts/by-ids`: body `{"ids":["1","2"]}`
- `posts/search`: `query=from:elonmusk&query_type=Latest&limit=2`
- `posts/{post_id}/replies`: `post_id=123&limit=2`

## Postman

Base URL: `http://localhost:8000`

- `GET /api/v1/accounts`
  - params: `provider_key=x_io`, `usernames=elonmusk`, `usernames=openai`
- `GET /api/v1/accounts/search`
  - params: `provider_key=x_io`, `query=elon`, `limit=2`
- `GET /api/v1/accounts/{username}/posts`
  - params: `provider_key=x_io`, `posts_limit=2`, `replies_limit=1`
- `POST /api/v1/posts/by-ids`
  - params: `provider_key=x_io`
  - body: `{"ids":["1","2"]}`
- `GET /api/v1/posts/search`
  - params: `provider_key=x_io`, `query=from:elonmusk`, `query_type=Latest`, `limit=2`
- `GET /api/v1/posts/{post_id}/replies`
  - params: `provider_key=x_io`, `limit=2`

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
