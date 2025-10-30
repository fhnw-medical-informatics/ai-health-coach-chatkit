# AI Health Coach Backend

A Python backend that exposes a multi-agent system powered by OpenAI ChatKit, as well as a REST API for medication management.

## Features

- **ChatKit endpoint** at `POST /chatkit` that streams multi-agent responses for the UI shell.
- **In-memory medication store** in `app/medications.py` shared by the pharmacist agent and REST API.
- **REST endpoints** for the frontend medication cabinet and health check:
  - `GET /medications` – list saved medications
  - `DELETE /medications/{medication_name}` – remove a single medication
  - `DELETE /medications` – clear the cabinet
  - `GET /health` – basic service ping

## Quick start

See [README.md](../README.md) at the top directory for instructions on how to run both the backend and frontend together.