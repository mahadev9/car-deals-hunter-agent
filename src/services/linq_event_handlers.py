import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def handle_message_received(event_data: Dict[str, Any]) -> None:
    """
    Handle incoming message.

    Args:
        event_data: Message event data
    """
    message = event_data.get("parts", [{}])[0]
    sender = event_data.get("sender_handle", {}).get("handle", "Unknown")
    chat_id = event_data.get("chat", {}).get("id", "Unknown")

    logger.info(
        f"Message received from {sender} in chat {chat_id}: {message.get('value', '')}"
    )

    # TODO: Process message with LLM agent
    # For now, just log it


async def handle_message_sent(event_data: Dict[str, Any]) -> None:
    """
    Handle outgoing message confirmation.

    Args:
        event_data: Message event data
    """
    message = event_data.get("parts", [{}])[0]
    recipient = event_data.get("chat", {}).get("display_name", "Unknown")

    logger.info(f"Message sent to {recipient}: {message.get('value', '')}")


async def handle_message_delivered(event_data: Dict[str, Any]) -> None:
    """Handle message delivery confirmation.

    Args:
        event_data: Message event data
    """
    message_id = event_data.get("id")
    logger.info(f"Message {message_id} delivered")


async def handle_message_read(event_data: Dict[str, Any]) -> None:
    """
    Handle message read receipt.

    Args:
        event_data: Message event data
    """
    message_id = event_data.get("id")
    logger.info(f"Message {message_id} read")


async def handle_message_failed(event_data: Dict[str, Any]) -> None:
    """
    Handle message delivery failure.

    Args:
        event_data: Message failure data
    """
    message_id = event_data.get("message_id")
    code = event_data.get("code")
    reason = event_data.get("reason")

    logger.error(f"Message {message_id} failed: ({code}) {reason}")


async def handle_reaction_added(event_data: Dict[str, Any]) -> None:
    """
    Handle reaction added to message.

    Args:
        event_data: Reaction event data
    """
    message_id = event_data.get("message_id")
    reaction_type = event_data.get("reaction_type")
    from_handle = event_data.get("from")

    logger.info(
        f"Reaction {reaction_type} added to message {message_id} by {from_handle}"
    )


async def handle_reaction_removed(event_data: Dict[str, Any]) -> None:
    """
    Handle reaction removed from message.

    Args:
        event_data: Reaction event data
    """
    message_id = event_data.get("message_id")
    reaction_type = event_data.get("reaction_type")
    from_handle = event_data.get("from")

    logger.info(
        f"Reaction {reaction_type} removed from message {message_id} by {from_handle}"
    )


async def handle_chat_created(event_data: Dict[str, Any]) -> None:
    """
    Handle new chat creation.

    Args:
        event_data: Chat event data
    """
    chat_id = event_data.get("id")
    display_name = event_data.get("display_name")
    is_group = event_data.get("is_group")

    logger.info(f"Chat created: {display_name} (group: {is_group}, id: {chat_id})")


async def handle_chat_typing_started(event_data: Dict[str, Any]) -> None:
    """
    Handle typing indicator started.

    Args:
        event_data: Typing indicator event data
    """
    chat_id = event_data.get("chat_id")
    logger.info(f"User started typing in chat {chat_id}")


async def handle_chat_typing_stopped(event_data: Dict[str, Any]) -> None:
    """
    Handle typing indicator stopped.

    Args:
        event_data: Typing indicator event data
    """
    chat_id = event_data.get("chat_id")
    logger.info(f"User stopped typing in chat {chat_id}")


async def handle_participant_added(event_data: Dict[str, Any]) -> None:
    """
    Handle participant added to group chat.

    Args:
        event_data: Participant event data
    """
    chat_id = event_data.get("chat_id")
    handle = event_data.get("handle")

    logger.info(f"Participant {handle} added to chat {chat_id}")


async def handle_participant_removed(event_data: Dict[str, Any]) -> None:
    """
    Handle participant removed from group chat.

    Args:
        event_data: Participant event data
    """
    chat_id = event_data.get("chat_id")
    handle = event_data.get("handle")

    logger.info(f"Participant {handle} removed from chat {chat_id}")


async def handle_phone_number_status_updated(event_data: Dict[str, Any]) -> None:
    """
    Handle phone number status change.

    Args:
        event_data: Phone number event data
    """
    phone_number = event_data.get("phone_number")
    new_status = event_data.get("new_status")

    logger.warning(f"Phone number {phone_number} status changed to {new_status}")


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
