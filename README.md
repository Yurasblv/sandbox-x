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
- `GET /api/v1/accounts/{username}/posts?provider_key=x_io&limit=20&include_replies=true`
  - `provider_key=x_io`
  - `username=elonmusk`
  - `limit=20`
  - `include_replies=true` includes reply-posts authored by the account in `posts`
  - optional date filters: `since=2026-06-01&until_date=2026-06-09`
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
- `accounts/{username}/posts`: `username=elonmusk&limit=20&include_replies=true`
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
  - params: `provider_key=x_io`, `limit=20`, `include_replies=true`
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

Useful `.env` settings:

```env
X__PROVIDER=x_io
X__BASE_URL=https://api.twitterapi.io
X__API_KEY=...

COLLECTOR__REQUEST_BATCH_SIZE=10
COLLECTOR__RATE_LIMIT_REQUESTS=1
COLLECTOR__RATE_LIMIT_PERIOD_SECONDS=5
COLLECTOR__POSTS_LIMIT=20
COLLECTOR__MAX_POSTS_LIMIT=200
```

## Notes

The X API provider uses `X-API-Key` authentication. Its paginated endpoints return `has_next_page` and `next_cursor`; this service follows those cursors until `limit` is reached, but stops pagination on an empty page to avoid burning provider quota.

`include_replies=true` on `accounts/{username}/posts` means "include reply-posts authored by this account in `posts`". It does not fetch replies to each post. To fetch replies to a specific post, use `GET /api/v1/posts/{post_id}/replies`.

Free-tier X API rate limits can be strict. The default collector limiter is `1` request per `5` seconds per Python worker process.

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
