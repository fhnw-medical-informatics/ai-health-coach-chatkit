# AI Health Coach Backend

> For the steps to run both frontend and backend apps in this repo, please refer to the README.md at the top directory instead.

This FastAPI service provides a comprehensive health coaching backend with medication management, health tracking, and personalized wellness guidance. The service integrates with ChatKit to provide an intelligent conversational interface for health coaching.

## Features

- **ChatKit endpoint** at `POST /chatkit` that streams responses using the ChatKit protocol when the optional ChatKit Python package is installed.
- **Medication management tool** that records and tracks user medications with confirmation widgets.
- **Health coaching system prompt** extracted into `app/constants.py` for easy customization.
- **Medication store** backed by in-memory storage in `app/medications.py`.
- **REST helpers**
  - `GET  /medications` – list saved medications (used by the frontend medication cabinet)
  - `POST /medications/{medication_id}/save` – mark a medication as saved
  - `POST /medications/{medication_id}/discard` – discard a pending medication
  - `GET  /health` – surface a basic health indicator

## Getting started

To enable the realtime assistant you need to install both the ChatKit Python package and the OpenAI SDK, then provide an `OPENAI_API_KEY` environment variable.

```bash
uv sync
export OPENAI_API_KEY=sk-proj-...
uv run uvicorn app.main:app --reload
```
