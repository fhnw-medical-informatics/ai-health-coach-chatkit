# AI Health Coach

Demo of a multi-agent system powered by OpenAI ChatKit (based on the official [sample project](https://github.com/openai/openai-chatkit-advanced-samples)).

A supervisor agent triages health-related user queries to either a pharmacist or a psychologist agent.
The pharmacist agent manages a cabinet of medications which are displayed in the user interface.

This prototype shows how to use multi-agent systems for an orchestrated, intent-based user experience.

> **WARNING**: Designed for educational use only!

## Prerequisites
- Node.js 20+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or `pip`
- OpenAI API key exported as `OPENAI_API_KEY`

## Quick start (single install, one command to run both apps)

1) Set environment variables

```bash
export OPENAI_API_KEY="sk-proj-..."
```

2) Install dependencies (backend + frontend)

```bash
npm install
```

3) Start backend and frontend together

```bash
npm start
```

&copy; 2025 FHNW Medical Informatics – Rahel Lüthy