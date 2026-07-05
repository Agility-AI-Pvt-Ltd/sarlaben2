Cow X
=====

FastAPI backend for tracking farmers, cattle health, chat history, AI memory, voice call logs, and audio WebSocket sessions.

Project Layout
--------------

- `app/main.py`: FastAPI application and route wiring.
- `app/api/v1`: REST and WebSocket API routes.
- `app/models`: SQLAlchemy Postgres models for farmers, cattle, sessions, messages, memories, and call logs.
- `app/schemas`: Pydantic request/response schemas.
- `app/repositories`: Database access layer.
- `app/services`: Business logic layer.
- `app/ai`: LLM, memory extraction, STT, TTS, and voice pipeline interfaces.
- `app/websocket`: WebSocket connection management and audio event handling.
- `app/database`: Async SQLAlchemy session and Alembic migrations.
- `app/workers`: Background worker entrypoints.

Core Endpoints
--------------

- `POST /api/v1/auth/otp/send`
- `POST /api/v1/auth/otp/verify`
- `POST /api/v1/cattle`
- `GET /api/v1/cattle?farmer_id=<human_id>`
- `POST /api/v1/cattle/{cattle_id}/memories`
- `POST /api/v1/sessions`
- `POST /api/v1/message/cattle/{cattle_id}/human/{human_id}`
- `POST /api/v1/message/ai/human/{human_id}/cattle/{cattle_id}`
- `POST /api/v1/calls`
- `WS /api/v1/ws/cattle/{cattle_id}/human/{human_id}`
- `WS /api/v1/ws/ai/cattle/{cattle_id}/human/{human_id}`

Add Cattle from Chat
--------------------

Call `POST /api/v1/cattle` after asking the farmer for the cattle name and
optional cattle ID:

```json
{
  "farmer_id": "00000000-0000-0000-0000-000000000000",
  "name": "Lakshmi",
  "cattle_id": "TN-1042"
}
```

If the farmer does not provide `cattle_id`, omit it (or send an empty string).
The API generates a unique ID such as `COW-3F0A...`. The existing
`cattle_tag` request field remains supported for compatibility.

Run Locally
-----------

```bash
uv sync
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`, then start the API:

```bash
python app.py
```

The server defaults to `http://0.0.0.0:8000`. Override it with `HOST`
or `PORT` environment variables when needed. For a loopback-only local
server, run `HOST=127.0.0.1 python app.py`.

For phone verification, also set `TWILIO_ACCOUNT_SID`,
`TWILIO_AUTH_TOKEN`, and `TWILIO_VERIFY_SERVICE_SID`. Phone numbers must
use E.164 format, such as `+919876543210`.

To generate an AI reply, first store the farmer's message, then call
`POST /api/v1/message/ai/human/{human_id}/cattle/{cattle_id}` with the
`session_id` returned by the human-message endpoint:

```json
{
  "session_id": "00000000-0000-0000-0000-000000000000",
  "context": "Optional current observations that are not already in chat"
}
```

The audio WebSocket assumes voice activity detection happens on the client. The client should send VAD lifecycle events as JSON and speech audio chunks as binary frames.

Deploy on Render
----------------

This repo is configured for Render with Python `3.11.15`:

- `.python-version` contains `3.11.15`.
- `pyproject.toml` requires `==3.11.15`.
- `render.yaml` sets `PYTHON_VERSION=3.11.15`.

Use the included Render Blueprint (`render.yaml`) or create a Python Web
Service manually with:

```bash
uv sync --frozen --no-dev
```

as the build command, and:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

as the start command.

The Blueprint also provisions a Render Postgres database, injects
`DATABASE_URL`, runs `uv run alembic upgrade head` before deploy, and uses
`/health` for health checks. Set the prompted secret values in the Render
dashboard, especially `OPENAI_API_KEY` and any Sarvam/Twilio values you need.
