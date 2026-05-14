import asyncio
import logging
import time
from datetime import datetime

from config import settings
from logger_analytics import log_event_analytics
from services.llm_agent import invoke_agent
from services.message_processing_queue import (
    claim_pending_job,
    complete_pending_job,
    get_pending_job,
    list_due_pending_jobs,
)

logger = logging.getLogger("car-deals-hunter")


async def _process_pending_job(chat_id: str, generation: int) -> None:
    logger.info(f"Processing pending job for chat {chat_id} generation {generation}")

    if not claim_pending_job(chat_id=chat_id, generation=generation):
        logger.info(
            f"Failed to claim pending job for chat {chat_id} generation {generation} - it may have been claimed by another worker or completed"
        )
        return

    pending_job = get_pending_job(chat_id)
    if pending_job is None:
        logger.info(
            f"Pending job for chat {chat_id} disappeared after claiming - skipping"
        )
        return

    if pending_job.process_at > datetime.now():
        logger.warning(
            f"Pending job for chat {chat_id} generation {generation} is not due yet (process_at={pending_job.process_at}) - skipping"
        )
        return

    start_time = time.time()
    success = False

    try:
        success = await invoke_agent(
            f"New message received in chat '{chat_id}' from {pending_job.sender}: {pending_job.user_message}"
        )

        duration_ms = int((time.time() - start_time) * 1000)

        if success:
            log_event_analytics(
                event_type="agent.invocation",
                event_id=pending_job.event_id,
                metadata={
                    "chat_id": chat_id,
                    "sender": pending_job.sender,
                    "message_id": pending_job.message_id,
                    "duration_ms": duration_ms,
                    "generation": generation,
                    "status": "success",
                },
            )

            completed = complete_pending_job(chat_id, generation)
            if not completed:
                logger.info(
                    f"Skipped completing stale pending job for chat {chat_id} generation {generation}"
                )
        else:
            log_event_analytics(
                event_type="agent.invocation",
                event_id=pending_job.event_id,
                metadata={
                    "chat_id": chat_id,
                    "sender": pending_job.sender,
                    "message_id": pending_job.message_id,
                    "duration_ms": duration_ms,
                    "generation": generation,
                    "status": "failed",
                },
            )
            completed = complete_pending_job(chat_id, generation)
            if completed:
                logger.error(
                    f"Marked failed job as complete after agent invocation failure: chat {chat_id} generation {generation}"
                )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            f"Unexpected error while processing pending job for chat {chat_id} generation {generation}: {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        log_event_analytics(
            event_type="agent.invocation",
            event_id=pending_job.event_id,
            metadata={
                "chat_id": chat_id,
                "sender": pending_job.sender,
                "message_id": pending_job.message_id,
                "duration_ms": duration_ms,
                "generation": generation,
                "status": "error",
                "error_type": type(e).__name__,
            },
        )
        completed = complete_pending_job(chat_id, generation)
        if completed:
            logger.info(
                f"Marked failed job as complete to avoid retrying: chat {chat_id} generation {generation}"
            )


async def run_message_processing_worker(stop_event: asyncio.Event) -> None:
    logger.info("Starting SQLite-backed message processing worker")

    while not stop_event.is_set():
        now = datetime.now()
        due_jobs = list_due_pending_jobs(now)

        for job in due_jobs:
            if stop_event.is_set():
                break
            await _process_pending_job(job.chat_id, job.generation)

        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=settings.POLL_INTERVAL_SECONDS
            )
        except asyncio.TimeoutError:
            pass


async def start_message_processing_worker() -> tuple[asyncio.Task[None], asyncio.Event]:
    stop_event = asyncio.Event()
    task = asyncio.create_task(run_message_processing_worker(stop_event))
    return task, stop_event


async def stop_message_processing_worker(
    task: asyncio.Task[None], stop_event: asyncio.Event | None = None
) -> None:
    if stop_event is not None:
        stop_event.set()
    await task
