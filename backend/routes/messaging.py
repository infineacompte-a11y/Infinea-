"""
InFinea — Direct Messaging routes.
1:1 conversations between users.

Design:
- Conversation-based: one conversation per pair of users.
- Participants sorted for deduplication.
- Cursor-based pagination on messages (oldest → newest).
- Denormalized last_message + unread_count on conversation doc.
- Mute: muted_by[] array on conversation doc — suppresses push/notifs.
- Read receipts: read_at timestamp on messages for iMessage-style checks.
- Benchmarked: Instagram DM, WhatsApp, iMessage.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from auth import get_current_user
from config import limiter
from models import ConversationCreate, MessageSend
from services.moderation import get_blocked_ids, check_content, sanitize_text, extract_mentions
from helpers import send_push_to_user
from services.email_service import send_email_to_user, email_mention

router = APIRouter(tags=["messaging"])


# ── Helpers ──

async def _get_conversation_for_user(conversation_id: str, user_id: str):
    """Fetch conversation and verify user is a participant."""
    conv = await db.conversations.find_one(
        {"conversation_id": conversation_id, "participants": user_id},
        {"_id": 0},
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    return conv


def _other_participant(conv: dict, user_id: str) -> str:
    """Return the other participant's user_id."""
    for p in conv["participants"]:
        if p != user_id:
            return p
    return user_id


async def _enrich_conversations(conversations: list, user_id: str) -> list:
    """Add other_user info (display_name, avatar, username) to each conversation."""
    other_ids = [_other_participant(c, user_id) for c in conversations]
    if not other_ids:
        return conversations

    users = await db.users.find(
        {"user_id": {"$in": other_ids}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
         "picture": 1, "avatar_url": 1, "streak_days": 1},
    ).to_list(len(other_ids))
    user_map = {u["user_id"]: u for u in users}

    for conv in conversations:
        other_id = _other_participant(conv, user_id)
        other = user_map.get(other_id, {})
        conv["other_user"] = {
            "user_id": other_id,
            "display_name": other.get("display_name") or other.get("name", "Utilisateur"),
            "username": other.get("username"),
            "avatar_url": other.get("avatar_url") or other.get("picture"),
            "streak_days": other.get("streak_days", 0),
        }
        conv["my_unread_count"] = conv.get("unread_count", {}).get(user_id, 0)
        conv.pop("unread_count", None)
        conv["muted"] = user_id in conv.get("muted_by", [])

    return conversations


# ── Endpoints ──

@router.post("/conversations")
async def create_or_get_conversation(body: ConversationCreate, user: dict = Depends(get_current_user)):
    """
    Get or create a 1:1 conversation with another user.
    Returns existing conversation if one already exists.
    """
    target_id = body.user_id
    my_id = user["user_id"]

    if target_id == my_id:
        raise HTTPException(status_code=400, detail="Impossible de vous envoyer un message")

    # Check target exists
    target = await db.users.find_one({"user_id": target_id}, {"user_id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Block check
    blocked_ids = await get_blocked_ids(my_id)
    if target_id in blocked_ids:
        raise HTTPException(status_code=403, detail="Impossible d'envoyer un message à cet utilisateur")

    # Sorted participants for dedup
    participants = sorted([my_id, target_id])

    # Get or create
    existing = await db.conversations.find_one(
        {"participants": participants},
        {"_id": 0},
    )
    if existing:
        enriched = await _enrich_conversations([existing], my_id)
        return enriched[0]

    now = datetime.now(timezone.utc).isoformat()
    conv = {
        "conversation_id": f"conv_{uuid.uuid4().hex[:12]}",
        "participants": participants,
        "last_message": None,
        "unread_count": {my_id: 0, target_id: 0},
        "created_at": now,
        "updated_at": now,
    }
    await db.conversations.insert_one({**conv, "_id": conv["conversation_id"]})
    conv.pop("_id", None)

    enriched = await _enrich_conversations([conv], my_id)
    return enriched[0]


@router.get("/conversations")
async def list_conversations(user: dict = Depends(get_current_user), limit: int = 30):
    """List user's conversations, most recent first."""
    if limit > 50:
        limit = 50

    conversations = await db.conversations.find(
        {"participants": user["user_id"]},
        {"_id": 0},
    ).sort("updated_at", -1).limit(limit).to_list(limit)

    return {"conversations": await _enrich_conversations(conversations, user["user_id"])}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    user: dict = Depends(get_current_user),
    cursor: str = None,
    limit: int = 30,
):
    """
    Get messages in a conversation (oldest → newest).
    Cursor-based: pass `next_cursor` from previous response.
    """
    if limit > 50:
        limit = 50

    conv = await _get_conversation_for_user(conversation_id, user["user_id"])

    query = {"conversation_id": conversation_id, "moderation_status": {"$ne": "hidden"}}
    if cursor:
        query["created_at"] = {"$lt": cursor}

    messages = await db.messages.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit + 1).to_list(limit + 1)

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    # Reverse to get oldest → newest order
    messages.reverse()
    next_cursor = messages[0]["created_at"] if messages and has_more else None

    return {
        "messages": messages,
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.post("/conversations/{conversation_id}/messages")
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    conversation_id: str,
    body: MessageSend,
    user: dict = Depends(get_current_user),
):
    """Send a message in a conversation."""
    my_id = user["user_id"]
    conv = await _get_conversation_for_user(conversation_id, my_id)

    other_id = _other_participant(conv, my_id)

    # Block check
    blocked_ids = await get_blocked_ids(my_id)
    if other_id in blocked_ids:
        raise HTTPException(status_code=403, detail="Impossible d'envoyer un message à cet utilisateur")

    # Sanitize + moderate text
    content = sanitize_text(body.content, max_length=1000) if body.content else ""
    has_text = bool(content.strip())

    # Validate images (max 4, same pattern as feed posts)
    images = body.images or []
    validated_images = []
    for img in images[:4]:
        if not isinstance(img, dict) or not img.get("image_url"):
            continue
        validated_images.append({
            "image_url": str(img["image_url"]),
            "thumbnail_url": str(img.get("thumbnail_url", img["image_url"])),
            "width": int(img.get("width", 0)),
            "height": int(img.get("height", 0)),
        })
    has_images = bool(validated_images)

    if not has_text and not has_images:
        raise HTTPException(status_code=400, detail="Le message ne peut pas être vide")

    if has_text:
        moderation = check_content(content)
        if not moderation["allowed"]:
            raise HTTPException(status_code=400, detail=moderation["reason"])

    # Extract @mentions
    mentions = await extract_mentions(content, my_id, blocked_ids) if has_text else []

    now = datetime.now(timezone.utc).isoformat()
    message = {
        "message_id": f"msg_{uuid.uuid4().hex[:12]}",
        "conversation_id": conversation_id,
        "sender_id": my_id,
        "content": content,
        "mentions": mentions,
        "created_at": now,
        "read_at": None,
    }
    if validated_images:
        message["images"] = validated_images

    await db.messages.insert_one({**message, "_id": message["message_id"]})
    message.pop("_id", None)

    # Layer 2: async AI moderation on message (text + images)
    try:
        from services.ai_moderation import moderate_content_async
        image_urls = [img["image_url"] for img in validated_images] if validated_images else None
        asyncio.create_task(moderate_content_async(
            content_id=message["message_id"],
            content_type="message",
            author_id=my_id,
            text=content if has_text else "",
            image_urls=image_urls,
        ))
    except Exception:
        pass

    # Update conversation denormalized fields
    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {
            "$set": {
                "last_message": {
                    "content": content[:100] if has_text else "📷 Image",
                    "sender_id": my_id,
                    "created_at": now,
                },
                "updated_at": now,
            },
            "$inc": {f"unread_count.{other_id}": 1},
        },
    )

    # Notification (non-blocking) — respect mute
    display = user.get("display_name") or user.get("name", "Quelqu'un")
    is_muted = other_id in conv.get("muted_by", [])
    if not is_muted:
        try:
            preview = (content[:80] + ("..." if len(content) > 80 else "")) if has_text else "📷 Image"
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": other_id,
                "type": "new_message",
                "title": "Nouveau message",
                "message": f"{display} : {preview}",
                "icon": "message-circle",
                "data": {"conversation_id": conversation_id, "sender_id": my_id},
                "read": False,
                "created_at": now,
            })
            await send_push_to_user(
                other_id,
                f"Message de {display}",
                preview,
                url="/messages",
                tag="dm",
            )
        except Exception:
            pass

    # Notify mentioned users (skip other participant — already notified via new_message)
    for m in mentions:
        if m["user_id"] == other_id:
            continue
        try:
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": m["user_id"],
                "type": "mention",
                "message": f"{display} vous a mentionné dans un message",
                "data": {
                    "conversation_id": conversation_id,
                    "mentioner_id": my_id,
                },
                "read": False,
                "created_at": now,
            })
            await send_push_to_user(
                m["user_id"],
                f"{display} vous a mentionné",
                content[:80],
                url="/messages",
                tag="mention",
            )
            # Email for mentions in DM
            subject, html = email_mention(display, content, "/messages")
            await send_email_to_user(m["user_id"], subject, html, email_category="social")
        except Exception:
            pass

    return message


@router.put("/conversations/{conversation_id}/read")
async def mark_conversation_read(conversation_id: str, user: dict = Depends(get_current_user)):
    """Mark all messages in conversation as read for current user."""
    my_id = user["user_id"]
    conv = await _get_conversation_for_user(conversation_id, my_id)

    # Reset unread counter
    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$set": {f"unread_count.{my_id}": 0}},
    )

    # Mark individual messages as read
    await db.messages.update_many(
        {
            "conversation_id": conversation_id,
            "sender_id": {"$ne": my_id},
            "read_at": None,
        },
        {"$set": {"read_at": datetime.now(timezone.utc).isoformat()}},
    )

    return {"message": "Conversation marquée comme lue"}


# ── Edit window constant (15 minutes — Discord/Slack benchmark) ──
EDIT_WINDOW_SECONDS = 15 * 60


@router.put("/messages/{message_id}")
async def edit_message(
    message_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Edit own message within 15-minute window.

    Benchmarked: Discord (unlimited), WhatsApp (15 min), Telegram (48h).
    InFinea uses 15-minute window — quick fix typos without altering history.
    Shows "(modifié)" badge after edit.
    """
    msg = await db.messages.find_one({"message_id": message_id})
    if not msg:
        raise HTTPException(status_code=404, detail="Message introuvable")

    if msg["sender_id"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que vos propres messages")

    # Enforce 15-minute edit window
    created = datetime.fromisoformat(msg["created_at"])
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    elapsed = (datetime.now(timezone.utc) - created).total_seconds()
    if elapsed > EDIT_WINDOW_SECONDS:
        raise HTTPException(status_code=403, detail="La fenêtre de modification de 15 minutes est expirée")

    body = await request.json()
    content = sanitize_text(str(body.get("content", "")), max_length=1000)
    if not content:
        raise HTTPException(status_code=400, detail="Le message ne peut pas être vide")

    moderation = check_content(content)
    if not moderation["allowed"]:
        raise HTTPException(status_code=400, detail=moderation["reason"])

    # Re-extract @mentions
    blocked_ids = await get_blocked_ids(user["user_id"])
    mentions = await extract_mentions(content, user["user_id"], blocked_ids)

    now = datetime.now(timezone.utc).isoformat()
    await db.messages.update_one(
        {"message_id": message_id},
        {"$set": {
            "content": content,
            "mentions": mentions,
            "edited_at": now,
        }},
    )

    # Update conversation last_message if this was the latest
    conv_id = msg["conversation_id"]
    latest = await db.messages.find_one(
        {"conversation_id": conv_id},
        {"message_id": 1},
        sort=[("created_at", -1)],
    )
    if latest and latest["message_id"] == message_id:
        await db.conversations.update_one(
            {"conversation_id": conv_id},
            {"$set": {"last_message.content": content[:100]}},
        )

    return {
        "message_id": message_id,
        "content": content,
        "mentions": mentions,
        "edited_at": now,
    }


@router.delete("/messages/{message_id}")
async def delete_message(message_id: str, user: dict = Depends(get_current_user)):
    """Delete own message."""
    msg = await db.messages.find_one(
        {"message_id": message_id, "sender_id": user["user_id"]},
        {"_id": 0},
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message introuvable")

    await db.messages.delete_one({"message_id": message_id})

    # If this was the last message, update conversation's last_message
    conv_id = msg["conversation_id"]
    latest = await db.messages.find_one(
        {"conversation_id": conv_id},
        {"_id": 0},
        sort=[("created_at", -1)],
    )
    if latest:
        await db.conversations.update_one(
            {"conversation_id": conv_id},
            {"$set": {
                "last_message": {
                    "content": latest["content"][:100],
                    "sender_id": latest["sender_id"],
                    "created_at": latest["created_at"],
                },
            }},
        )
    else:
        await db.conversations.update_one(
            {"conversation_id": conv_id},
            {"$set": {"last_message": None}},
        )

    return {"message": "Message supprimé"}


# ── Message Reactions (iMessage/Instagram DM pattern) ──
# One reaction per user per message, toggle behavior, denormalized on message doc.
# Same curated set as feed reactions: bravo, inspire, fire — InFinea identity.

MESSAGE_REACTION_TYPES = {"bravo", "inspire", "fire"}


@router.post("/messages/{message_id}/reactions")
async def toggle_message_reaction(
    message_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    Toggle a reaction on a DM message.

    Behavior (iMessage/Instagram DM pattern):
    - Same reaction type → remove (toggle off)
    - Different reaction type → switch
    - No existing reaction → add

    Reactions stored denormalized on message doc:
      reactions: {user_id: "bravo", user_id2: "fire"}

    Returns: {reacted: bool, reaction_type: str|null, reactions: dict}
    """
    body = await request.json()
    reaction_type = body.get("reaction_type", "")

    if reaction_type not in MESSAGE_REACTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Type de réaction invalide. Choix : {', '.join(sorted(MESSAGE_REACTION_TYPES))}",
        )

    msg = await db.messages.find_one({"message_id": message_id})
    if not msg:
        raise HTTPException(status_code=404, detail="Message introuvable")

    # Verify user is participant in this conversation
    conv = await _get_conversation_for_user(msg["conversation_id"], user["user_id"])

    my_id = user["user_id"]
    reactions = msg.get("reactions", {})
    existing = reactions.get(my_id)

    if existing == reaction_type:
        # Toggle off — remove reaction
        await db.messages.update_one(
            {"message_id": message_id},
            {"$unset": {f"reactions.{my_id}": ""}},
        )
        reactions.pop(my_id, None)
        return {"reacted": False, "reaction_type": None, "reactions": reactions}
    else:
        # Add or switch reaction
        await db.messages.update_one(
            {"message_id": message_id},
            {"$set": {f"reactions.{my_id}": reaction_type}},
        )
        reactions[my_id] = reaction_type

        # Notify message author (non-blocking, skip self-reaction)
        if msg["sender_id"] != my_id:
            try:
                display = user.get("display_name") or user.get("name", "Quelqu'un")
                reaction_labels = {"bravo": "bravo 👏", "inspire": "inspire ✨", "fire": "fire 🔥"}
                label = reaction_labels.get(reaction_type, reaction_type)
                await send_push_to_user(
                    msg["sender_id"],
                    f"Réaction {label}",
                    f"{display} a réagi à ton message",
                    url="/messages",
                    tag="dm_reaction",
                )
            except Exception:
                pass

        return {"reacted": True, "reaction_type": reaction_type, "reactions": reactions}


@router.post("/conversations/{conversation_id}/mute")
async def toggle_mute_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    """Toggle mute on a conversation (WhatsApp/Discord pattern).

    Muted conversations still receive messages (visible in inbox),
    but suppress push notifications and in-app notification creation.
    The muted_by array on the conversation doc tracks which participants muted.
    """
    my_id = user["user_id"]
    conv = await _get_conversation_for_user(conversation_id, my_id)

    muted_by = conv.get("muted_by", [])
    if my_id in muted_by:
        # Unmute
        await db.conversations.update_one(
            {"conversation_id": conversation_id},
            {"$pull": {"muted_by": my_id}},
        )
        return {"muted": False}
    else:
        # Mute
        await db.conversations.update_one(
            {"conversation_id": conversation_id},
            {"$addToSet": {"muted_by": my_id}},
        )
        return {"muted": True}


@router.get("/messages/unread-count")
async def get_unread_messages_count(user: dict = Depends(get_current_user)):
    """Total unread messages across all conversations (for sidebar badge)."""
    pipeline = [
        {"$match": {"participants": user["user_id"]}},
        {"$project": {"count": f"$unread_count.{user['user_id']}"}},
        {"$group": {"_id": None, "total": {"$sum": "$count"}}},
    ]
    result = await db.conversations.aggregate(pipeline).to_list(1)
    total = result[0]["total"] if result else 0
    return {"unread_count": total}
