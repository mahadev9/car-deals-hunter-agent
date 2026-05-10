import logging
import time

from logger_analytics import log_event_analytics
from models.event_status import EventStatus
from models.webhook_event_model import WebhookEvent
from services.llm_agent import invoke_agent

logger = logging.getLogger(__name__)


async def handle_message_received(event_payload: WebhookEvent) -> None:
    """
    Handle incoming message.

    Args:
        event_data: Message event data
    """
    start_time = time.time()

    event_data = event_payload.data
    sender = event_data.get("sender_handle", {}).get("handle", "Unknown")
    chat_id = event_data.get("chat", {}).get("id", "Unknown")
    message_id = event_data.get("id")
    is_group_chat = event_data.get("chat", {}).get("is_group", False)

    logger.info(f"Message received from a sender in chat {chat_id}")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={
            "sender": sender,
            "chat_id": chat_id,
            "is_group_chat": is_group_chat,
            "message_id": message_id,
            "duration_ms": duration_ms,
        },
    )

    start_time = time.time()

    user_message = "\n".join([part["value"] for part in event_data.get("parts", [])])
    await invoke_agent(
        f"New message received in chat '{chat_id}' from {sender}: {user_message}"
    )

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type="agent.invocation",
        event_id=event_payload.event_id,
        metadata={
            "chat_id": chat_id,
            "sender": sender,
            "message_id": message_id,
            "duration_ms": duration_ms,
        },
    )


async def handle_message_sent(event_payload: WebhookEvent) -> None:
    """
    Handle outgoing message confirmation.

    Args:
        event_data: Message event data
    """
    start_time = time.time()

    event_data = event_payload.data
    chat_id = event_data.get("chat", {}).get("id", "Unknown")
    message_id = event_data.get("id")
    sender = event_data.get("sender_handle", {}).get("handle", "Unknown")
    is_group_chat = event_data.get("chat", {}).get("is_group", False)

    logger.info(f"Message sent to a recipient in chat {chat_id}")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={
            "chat_id": chat_id,
            "duration_ms": duration_ms,
            "sender": sender,
            "is_group_chat": is_group_chat,
            "message_id": message_id,
        },
    )


async def handle_message_delivered(event_payload: WebhookEvent) -> None:
    """Handle message delivery confirmation.

    Args:
        event_data: Message event data
    """
    start_time = time.time()

    event_data = event_payload.data
    chat_id = event_data.get("chat", {}).get("id", "Unknown")
    sender = event_data.get("sender_handle", {}).get("handle", "Unknown")
    is_group_chat = event_data.get("chat", {}).get("is_group", False)
    message_id = event_data.get("id")
    logger.info(f"Message {message_id} delivered in chat {chat_id}")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={
            "chat_id": chat_id,
            "duration_ms": duration_ms,
            "sender": sender,
            "is_group_chat": is_group_chat,
            "message_id": message_id,
        },
    )


async def handle_message_read(event_payload: WebhookEvent) -> None:
    """
    Handle message read receipt.

    Args:
        event_data: Message event data
    """
    start_time = time.time()

    event_data = event_payload.data
    chat_id = event_data.get("chat", {}).get("id", "Unknown")
    message_id = event_data.get("id")
    sender = event_data.get("sender_handle", {}).get("handle", "Unknown")
    is_group_chat = event_data.get("chat", {}).get("is_group", False)
    logger.info(f"Message {message_id} read in chat {chat_id}")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={
            "chat_id": chat_id,
            "duration_ms": duration_ms,
            "sender": sender,
            "is_group_chat": is_group_chat,
            "message_id": message_id,
        },
    )


async def handle_message_failed(event_payload: WebhookEvent) -> None:
    """
    Handle message delivery failure.

    Args:
        event_data: Message failure data
    """
    start_time = time.time()

    event_data = event_payload.data
    chat_id = event_data.get("chat_id")
    message_id = event_data.get("message_id")
    code = event_data.get("code")
    reason = event_data.get("reason")

    logger.error(f"Message {message_id} failed in chat {chat_id}: ({code}) {reason}")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={
            "error_code": code,
            "duration_ms": duration_ms,
            "message_id": message_id,
            "chat_id": chat_id,
        },
        status=EventStatus.FAILED.value,
        error=f"{code}: {reason}",
    )


async def handle_reaction_added(event_payload: WebhookEvent) -> None:
    """
    Handle reaction added to message.

    Args:
        event_data: Reaction event data
    """
    start_time = time.time()

    event_data = event_payload.data
    chat_id = event_data.get("chat_id")
    message_id = event_data.get("message_id")
    reaction_type = event_data.get("reaction_type")
    receipent = event_data.get("from_handle", {}).get("handle", "Unknown")

    logger.info(
        f"Reaction {reaction_type} added to message {message_id} in chat {chat_id}"
    )

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={
            "recipient": receipent,
            "chat_id": chat_id,
            "message_id": message_id,
            "duration_ms": duration_ms,
        },
    )


async def handle_reaction_removed(event_payload: WebhookEvent) -> None:
    """
    Handle reaction removed from message.

    Args:
        event_data: Reaction event data
    """
    start_time = time.time()

    event_data = event_payload.data
    chat_id = event_data.get("chat_id")
    message_id = event_data.get("message_id")
    reaction_type = event_data.get("reaction_type")
    from_handle = event_data.get("from_handle", {}).get("handle", "Unknown")

    logger.info(
        f"Reaction {reaction_type} removed from message {message_id} in chat {chat_id}"
    )

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={
            "recipient": from_handle,
            "chat_id": chat_id,
            "message_id": message_id,
            "duration_ms": duration_ms,
        },
    )


async def handle_chat_created(event_payload: WebhookEvent) -> None:
    """
    Handle new chat creation.

    Args:
        event_data: Chat event data
    """
    start_time = time.time()
    event_data = event_payload.data
    chat_id = event_data.get("id")
    display_name = event_data.get("display_name")
    is_group = event_data.get("is_group")
    handles = ", ".join(
        p.get("handle", "Unknown") for p in event_data.get("handles", [])
    )

    logger.info(f"Chat created: {display_name} (group: {is_group}, id: {chat_id})")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={
            "is_group": is_group,
            "duration_ms": duration_ms,
            "chat_id": chat_id,
            "is_group_chat": is_group,
            "display_name": display_name,
            "handles": handles,
        },
    )


async def handle_chat_typing_started(event_payload: WebhookEvent) -> None:
    """
    Handle typing indicator started.

    Args:
        event_data: Typing indicator event data
    """
    start_time = time.time()
    event_data = event_payload.data
    chat_id = event_data.get("chat_id")
    logger.info(f"User started typing in chat {chat_id}")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={"chat_id": chat_id, "duration_ms": duration_ms},
    )


async def handle_chat_typing_stopped(event_payload: WebhookEvent) -> None:
    """
    Handle typing indicator stopped.

    Args:
        event_data: Typing indicator event data
    """
    start_time = time.time()
    event_data = event_payload.data
    chat_id = event_data.get("chat_id")
    logger.info(f"User stopped typing in chat {chat_id}")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={"chat_id": chat_id, "duration_ms": duration_ms},
    )


async def handle_participant_added(event_payload: WebhookEvent) -> None:
    """
    Handle participant added to group chat.

    Args:
        event_data: Participant event data
    """
    start_time = time.time()
    event_data = event_payload.data
    chat_id = event_data.get("chat_id")
    handle = event_data.get("participant", {}).get("handle", "Unknown")

    logger.info(f"Participant {handle} added to chat {chat_id}")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={"participant_handle": handle, "duration_ms": duration_ms},
    )


async def handle_participant_removed(event_payload: WebhookEvent) -> None:
    """
    Handle participant removed from group chat.

    Args:
        event_data: Participant event data
    """
    start_time = time.time()
    event_data = event_payload.data
    chat_id = event_data.get("chat_id")
    handle = event_data.get("handle")

    logger.info(f"Participant {handle} removed from chat {chat_id}")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={"participant_handle": handle, "duration_ms": duration_ms},
    )


async def handle_phone_number_status_updated(event_payload: WebhookEvent) -> None:
    """
    Handle phone number status change.

    Args:
        event_data: Phone number event data
    """
    start_time = time.time()
    event_data = event_payload.data
    phone_number = event_data.get("phone_number")
    new_status = event_data.get("new_status")

    logger.warning(f"Phone number {phone_number} status changed to {new_status}")

    duration_ms = int((time.time() - start_time) * 1000)
    log_event_analytics(
        event_type=event_payload.event_type,
        event_id=event_payload.event_id,
        metadata={"new_status": new_status, "duration_ms": duration_ms},
    )


EVENT_HANDLERS = {
    "message.received": handle_message_received,
    "message.sent": handle_message_sent,
    "message.delivered": handle_message_delivered,
    "message.read": handle_message_read,
    "message.failed": handle_message_failed,
    "message.edited": handle_message_sent,  # Similar handling to sent
    "reaction.added": handle_reaction_added,
    "reaction.removed": handle_reaction_removed,
    "chat.created": handle_chat_created,
    "chat.typing_indicator.started": handle_chat_typing_started,
    "chat.typing_indicator.stopped": handle_chat_typing_stopped,
    "participant.added": handle_participant_added,
    "participant.removed": handle_participant_removed,
    "phone_number.status_updated": handle_phone_number_status_updated,
    "chat.group_name_updated": handle_chat_created,
    "chat.group_icon_updated": handle_chat_created,
}
