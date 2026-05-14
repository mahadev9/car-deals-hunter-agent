# Car Deals Hunter Agent

An autonomous FastAPI service that receives Linq webhooks, queues incoming messages, and processes them in the background to evaluate car-deal leads.

![Car Deals Hunter Screenshot](./Car%20Deals%20Hunter.png)

https://github.com/mahadev9/car-deals-hunter-agent

## What It Does

The app runs a FastAPI service, verifies Linq webhook signatures, persists incoming events, and processes messages asynchronously with a SQLite-backed worker. The worker drains due jobs on a fixed polling interval after a short quiet window so the same chat can accumulate more context before the agent responds.

The agent collects follow-up parameters such as budget, vehicle preferences, and ZIP code, then uses its configured LLM and web search tooling to identify matching car deals and rank them against the user's criteria.

## Setup

Copy your environment file and fill in the required values. The required settings are the Linq API key, webhook signing secret, a supported `LLM_MODEL`, and the matching provider API key:

```env
APP_PATH=.
ENV=dev
APP_PORT=8000
MOUNT_FOLDER=./data
LLM_MODEL=anthropic:claude-haiku-4-5
DEFAULT_TEMPERATURE=0.7
LINQ_API_KEY=your_linq_api_key_here
LINQ_SIGNING_SECRET=your_webhook_signing_secret_here
ANTHROPIC_API_KEY=your_anthropic_key_here
MESSAGE_PROCESSING_DELAY_SECONDS=120
POLL_INTERVAL_SECONDS=10
EVENT_EXPIRATION_HOURS=12
```

`LLM_MODEL` uses the format `provider:model_name`. Supported providers are `lmstudio`, `openai`, `anthropic`, and `google_genai`. Set the corresponding API key:
- `OPENAI_API_KEY` for openai provider
- `ANTHROPIC_API_KEY` for anthropic provider (also enables web search tool)
- `GEMINI_API_KEY` for google_genai provider
- `LM_STUDIO_API_KEY` and `LM_STUDIO_BASE_URL` for lmstudio provider

For local development, `MOUNT_FOLDER` can point at `./data`. In Docker, the compose file mounts `./data` to `/mnt` and sets `MOUNT_FOLDER=/mnt`.

## Webhook

Linq should send events to `/api/linq/webhook`. The app expects the Linq webhook headers, verifies the signature, deduplicates events, and then hands them off for background processing.

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run Locally

```bash
python3 src/main.py
```

## Run With Docker

```bash
docker compose up --build
```

## Endpoints

- Health check: `/health`
- Linq webhook: `/api/linq/webhook`

## MCP Server

The application uses an MCP (Model Context Protocol) server running on `http://localhost:8010/mcp` to provide tool integrations:
- Web search capabilities (Anthropic)
- Custom tools for car deal hunting

The MCP server must be running for agent tool invocations to work properly.

## Notes

- The background worker checks for due jobs every `POLL_INTERVAL_SECONDS` seconds.
- New messages are held for `MESSAGE_PROCESSING_DELAY_SECONDS` before processing so follow-up messages can be batched into the same chat.
- The agent uses LangChain/LangGraph with SQLite-backed checkpointing for conversation state persistence.
- Webhook events are automatically cleaned up after `EVENT_EXPIRATION_HOURS` hours.
