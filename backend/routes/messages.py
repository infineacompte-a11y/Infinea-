"""
InFinea — Messaging routes.
1-to-1 conversations initiated from user profiles.

Design:
- One conversation per pair of users (no duplicates).
- Initiated from profile → natural discovery through social features.
- Respects block system (Phase 1) — blocked users cannot message.
- Rate limiting: max messages per minute to prevent abuse.
- Moderation-ready: message length capped, content stored for review.
- Read receipts for inbox UX (unread badge count).

Benchmarked: Strava DMs, LinkedIn messages, Bumble BFF chat.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid

from database import db
from auth import get_current_user
from models import ConversationStart, MessageSend

router = APIRouter(prefix="/api")

# Rate limiting: max messages per user per minute
MAX_MESSAGES_PER_MINUTE = 10


# ============== HELPERS ==============


async def _get_or_create_conversation(user_a: str, user_b: str) -> dict:
    """
    Get existing conversation between two users, or return None.
    Conversations are stored with a canonical participant pair (sorted)
    to guarantee uniqueness regardless of who initiates.
    """
    participants = sorted([user_a, user_b])

    conversation = await db.conversations.find_one(
        {"participant_ids": participants},
        {"_id": 0},
    )
    return conversation


async def _check_can_message(sender_id: str, recipient_id: str):
    """Verify the sender can message the recipient (not blocked, user exists)."""
    if sender_id == recipient_id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    recipient = await db.users.find_one({"user_id": recipient_id})
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if either user has blocked the other
    block = await db.blocks.find_one({
        "$or": [
            {"blocker_id": sender_id, "blocked_id": recipient_id},
            {"blocker_id": recipient_id, "blocked_id": sender_id},
        ]
    })
    if block:
        raise HTTPException(status_code=403, detail="Unable to message this user")

    # Check recipient's profile visibility
    privacy = recipient.get("privacy", {})
    if not privacy.get("profile_visible", True):
        raise HTTPException(status_code=403, detail="This user's profile is private")

    return recipient


async def _check_rate_limit(user_id: str):
    """Basic rate limiting — prevent message spam."""
    one_minute_ago = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

    recent_count = await db.messages.count_documents({
        "sender_id": user_id,
        "created_at": {"$gte": one_minute_ago},
    })

    if recent_count >= MAX_MESSAGES_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Too many messages. Please wait a moment.",
        )


# ============== START CONVERSATION ==============


@router.post("/messages/conversations")
async def start_conversation(
    data: ConversationStart,
    user: dict = Depends(get_current_user),
):
    """
    Start a new conversation with a user (from their profile).
    If a conversation already exists, sends the message there instead.
    """
    recipient = await _check_can_message(user["user_id"], data.recipient_id)
    await _check_rate_limit(user["user_id"])

    now = datetime.now(timezone.utc).isoformat()
    participants = sorted([user["user_id"], data.recipient_id])

    # Check for existing conversation
    existing = await _get_or_create_conversation(user["user_id"], data.recipient_id)

    if existing:
        conversation_id = existing["conversation_id"]
    else:
        # Create new conversation
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        recipient_name = recipient.get("display_name") or recipient.get("name", "Utilisateur")
        sender_name = user.get("display_name") or user.get("name", "Utilisateur")

        conversation_doc = {
            "conversation_id": conversation_id,
            "participant_ids": participants,
            "participants": [
                {
                    "user_id": user["user_id"],
                    "name": sender_name,
                    "avatar_url": user.get("avatar_url", user.get("picture")),
                    "unread_count": 0,
                },
                {
                    "user_id": data.recipient_id,
                    "name": recipient_name,
                    "avatar_url": recipient.get("avatar_url", recipient.get("picture")),
                    "unread_count": 0,
                },
            ],
            "last_message": None,
            "last_message_at": now,
            "created_at": now,
        }
        await db.conversations.insert_one(conversation_doc)

    # Send the first message
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    message_doc = {
        "message_id": message_id,
        "conversation_id": conversation_id,
        "sender_id": user["user_id"],
        "content": data.message,
        "read": False,
        "created_at": now,
    }
    await db.messages.insert_one(message_doc)

    # Update conversation's last message and recipient's unread count
    sender_name = user.get("display_name") or user.get("name", "Utilisateur")
    preview = data.message[:80] + ("..." if len(data.message) > 80 else "")

    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {
            "$set": {
                "last_message": {
                    "content": preview,
                    "sender_id": user["user_id"],
                    "sender_name": sender_name,
                    "created_at": now,
                },
                "last_message_at": now,
            },
            "$inc": {
                # Increment unread for the recipient only
                "participants.$[recipient].unread_count": 1,
            },
        },
        array_filters=[{"recipient.user_id": data.recipient_id}],
    )

    # Send notification to recipient
    await db.notifications.insert_one({
        "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
        "user_id": data.recipient_id,
        "type": "new_message",
        "message": f"{sender_name} vous a envoyé un message",
        "data": {"conversation_id": conversation_id, "sender_id": user["user_id"]},
        "read": False,
        "created_at": now,
    })

    return {
        "conversation_id": conversation_id,
        "message_id": message_id,
        "created": existing is None,
    }


# ============== INBOX ==============


@router.get("/messages/conversations")
async def get_conversations(
    user: dict = Depends(get_current_user),
    limit: int = 30,
    skip: int = 0,
):
    """
    Get user's conversations (inbox).
    Sorted by last message time, most recent first.
    """
    conversations = (
        await db.conversations.find(
            {"participant_ids": user["user_id"]},
            {"_id": 0},
        )
        .sort("last_message_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    total = await db.conversations.count_documents(
        {"participant_ids": user["user_id"]}
    )

    # Enrich: add "other_user" field for easy rendering
    for conv in conversations:
        other = next(
            (p for p in conv["participants"] if p["user_id"] != user["user_id"]),
            None,
        )
        conv["other_user"] = other
        # Get my unread count
        me = next(
            (p for p in conv["participants"] if p["user_id"] == user["user_id"]),
            None,
        )
        conv["my_unread_count"] = me.get("unread_count", 0) if me else 0

    return {"conversations": conversations, "total": total}


# ============== MESSAGES IN A CONVERSATION ==============


@router.get("/messages/conversations/{conversation_id}")
async def get_messages(
    conversation_id: str,
    user: dict = Depends(get_current_user),
    limit: int = 50,
    before: Optional[str] = None,
):
    """
    Get messages in a conversation (cursor-based, newest first).
    Pass 'before' (created_at timestamp) for pagination.
    """
    conversation = await db.conversations.find_one(
        {"conversation_id": conversation_id, "participant_ids": user["user_id"]},
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    query = {"conversation_id": conversation_id}
    if before:
        query["created_at"] = {"$lt": before}

    messages = (
        await db.messages.find(query, {"_id": 0})
        .sort("created_at", -1)
        .limit(limit + 1)
        .to_list(limit + 1)
    )

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    # Reverse for chronological display (oldest first within page)
    messages.reverse()

    next_cursor = messages[0]["created_at"] if messages and has_more else None

    return {
        "messages": messages,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


# ============== SEND MESSAGE ==============


@router.post("/messages/conversations/{conversation_id}")
async def send_message(
    conversation_id: str,
    data: MessageSend,
    user: dict = Depends(get_current_user),
):
    """Send a message in an existing conversation."""
    conversation = await db.conversations.find_one(
        {"conversation_id": conversation_id, "participant_ids": user["user_id"]},
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Find recipient
    recipient_id = next(
        (p["user_id"] for p in conversation["participants"]
         if p["user_id"] != user["user_id"]),
        None,
    )

    # Check block status (may have been blocked since conversation started)
    block = await db.blocks.find_one({
        "$or": [
            {"blocker_id": user["user_id"], "blocked_id": recipient_id},
            {"blocker_id": recipient_id, "blocked_id": user["user_id"]},
        ]
    })
    if block:
        raise HTTPException(status_code=403, detail="Unable to message this user")

    await _check_rate_limit(user["user_id"])

    now = datetime.now(timezone.utc).isoformat()
    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    message_doc = {
        "message_id": message_id,
        "conversation_id": conversation_id,
        "sender_id": user["user_id"],
        "content": data.content,
        "read": False,
        "created_at": now,
    }
    await db.messages.insert_one(message_doc)

    # Update conversation
    sender_name = user.get("display_name") or user.get("name", "Utilisateur")
    preview = data.content[:80] + ("..." if len(data.content) > 80 else "")

    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {
            "$set": {
                "last_message": {
                    "content": preview,
                    "sender_id": user["user_id"],
                    "sender_name": sender_name,
                    "created_at": now,
                },
                "last_message_at": now,
            },
            "$inc": {
                "participants.$[recipient].unread_count": 1,
            },
        },
        array_filters=[{"recipient.user_id": recipient_id}],
    )

    message_doc.pop("_id", None)
    return message_doc


# ============== READ RECEIPTS ==============


@router.post("/messages/conversations/{conversation_id}/read")
async def mark_conversation_read(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    """Mark all messages in a conversation as read for the current user."""
    conversation = await db.conversations.find_one(
        {"conversation_id": conversation_id, "participant_ids": user["user_id"]},
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Mark messages as read
    await db.messages.update_many(
        {
            "conversation_id": conversation_id,
            "sender_id": {"$ne": user["user_id"]},
            "read": False,
        },
        {"$set": {"read": True}},
    )

    # Reset unread counter
    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$set": {"participants.$[me].unread_count": 0}},
        array_filters=[{"me.user_id": user["user_id"]}],
    )

    return {"message": "Conversation marked as read"}


# ============== UNREAD COUNT ==============


@router.get("/messages/unread-count")
async def get_unread_count(user: dict = Depends(get_current_user)):
    """Get total unread message count across all conversations (for badge/indicator)."""
    pipeline = [
        {"$match": {"participant_ids": user["user_id"]}},
        {"$unwind": "$participants"},
        {"$match": {"participants.user_id": user["user_id"]}},
        {"$group": {"_id": None, "total": {"$sum": "$participants.unread_count"}}},
    ]

    result = await db.conversations.aggregate(pipeline).to_list(1)
    total = result[0]["total"] if result else 0

    return {"unread_count": total}
