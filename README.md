# Car Deals Hunter Agent

An autonomous agent that hunts for the best car deals online and notifies users via Linq.

https://github.com/mahadev9/car-deals-hunter-agent

## What It Does

The app runs a FastAPI service, listens for Linq webhook events, and processes incoming messages in the background. It is designed to watch for new leads, evaluate them, and keep the workflow automated end to end.

To avoid per-message processing, the webhook handler persists each incoming event to the database and a scheduled worker drains the backlog every 3 minutes in batches. For each event, the agent collects follow-up parameters such as budget, vehicle preferences, and ZIP code, then uses web search tooling to identify matching car deals and rank them against the user's criteria.

## Setup

Copy your environment file and fill in the required values. The most important settings are your Linq API key, webhook signing secret, and Anthropic API key:

```env
LINQ_API_KEY=your_linq_api_key_here
LINQ_SIGNING_SECRET=your_webhook_signing_secret_here
LLM_MODEL=anthropic:claude-haiku-4-5
ANTHROPIC_API_KEY=your_anthropic_key_here
ENV=prod
APP_PORT=8000
MOUNT_PATH=./data
```

## Webhook

Linq should send events to `/api/linq/webhook`. The app uses this endpoint to receive and verify webhook requests before handing them off for processing.

## Install dependencies:

```bash
pip install -r requirements.txt
```

## Run Locally

```bash
python3 src/main.py
```

## Endpoints

- Health check: `/health`
- Linq webhook: `/api/linq/webhook`
