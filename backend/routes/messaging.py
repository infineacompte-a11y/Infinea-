"""
InFinea — Messaging routes (DM + Group DM).

Design:
- Direct: one conversation per pair of users (sorted participants for dedup).
- Group: type="group", N participants (max 20), admin roles, name.
- Cursor-based pagination on messages (oldest → newest).
- Denormalized last_message + unread_count on conversation doc.
- Mute: muted_by[] array — suppresses push/notifs (both direct and group).
- Read receipts: read_at timestamp (direct only, not group).
- Benchmarked: WhatsApp (groups), Discord (group DM), iMessage, Instagram DM.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request

from database import db
from auth import get_current_user
from config import limiter
from models import ConversationCreate, GroupConversationCreate, GroupUpdate, MessageSend
from services.moderation import get_blocked_ids, check_content, sanitize_text, extract_mentions
from helpers import send_push_to_user
from services.email_service import send_email_to_user, email_mention
from services.presence_service import compute_presence

router = APIRouter(tags=["messaging"])

MAX_GROUP_SIZE = 20  # WhatsApp-style cap for study groups


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
    """Return the other participant's user_id (direct conversations only)."""
    for p in conv["participants"]:
        if p != user_id:
            return p
    return user_id


def _is_group(conv: dict) -> bool:
    return conv.get("type") == "group"


async def _enrich_conversations(conversations: list, user_id: str) -> list:
    """Add enrichment to each conversation (direct → other_user, group → group_info)."""
    # Collect all participant IDs across all conversations
    all_user_ids = set()
    for conv in conversations:
        all_user_ids.update(conv["participants"])
    all_user_ids.discard(user_id)

    if not all_user_ids:
        return conversations

    users = await db.users.find(
        {"user_id": {"$in": list(all_user_ids)}},
        {"_id": 0, "user_id": 1, "name": 1, "display_name": 1, "username": 1,
         "picture": 1, "avatar_url": 1, "streak_days": 1,
         "last_active": 1, "privacy": 1},
    ).to_list(len(all_user_ids))
    user_map = {u["user_id"]: u for u in users}

    for conv in conversations:
        conv["my_unread_count"] = conv.get("unread_count", {}).get(user_id, 0)
        conv.pop("unread_count", None)
        conv["muted"] = user_id in conv.get("muted_by", [])

        if _is_group(conv):
            # ── Group enrichment ──
            members = []
            any_online = False
            for pid in conv["participants"]:
                if pid == user_id:
                    continue
                u = user_map.get(pid, {})
                # Presence: respect privacy preference
                privacy = u.get("privacy", {})
                if privacy.get("show_activity_status") is False:
                    presence = {"status": "offline", "label": None}
                else:
                    presence = compute_presence(u.get("last_active"))
                if presence["status"] == "online":
                    any_online = True
                members.append({
                    "user_id": pid,
                    "display_name": u.get("display_name") or u.get("name", "Utilisateur"),
                    "username": u.get("username"),
                    "avatar_url": u.get("avatar_url") or u.get("picture"),
                    "presence": presence,
                })
            conv["group_info"] = {
                "name": conv.get("name", "Groupe"),
                "members": members,
                "member_count": len(conv["participants"]),
                "admins": conv.get("admins", []),
                "is_admin": user_id in conv.get("admins", []),
                "created_by": conv.get("created_by"),
                "any_online": any_online,
            }
        else:
            # ── Direct enrichment ──
            other_id = _other_participant(conv, user_id)
            other = user_map.get(other_id, {})
            # Presence: respect privacy preference
            privacy = other.get("privacy", {})
            if privacy.get("show_activity_status") is False:
                presence = {"status": "offline", "label": None}
            else:
                presence = compute_presence(other.get("last_active"))
            conv["other_user"] = {
                "user_id": other_id,
                "display_name": other.get("display_name") or other.get("name", "Utilisateur"),
                "username": other.get("username"),
                "avatar_url": other.get("avatar_url") or other.get("picture"),
                "streak_days": other.get("streak_days", 0),
                "presence": presence,
            }

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


@router.post("/conversations/group")
async def create_group_conversation(
    body: GroupConversationCreate,
    user: dict = Depends(get_current_user),
):
    """Create a group conversation (WhatsApp/Discord group DM pattern).

    Creator becomes the first admin. Max 20 participants.
    Blocked users are filtered out silently.
    """
    my_id = user["user_id"]
    name = body.name.strip()

    # Deduplicate + remove self
    member_ids = list(set(mid for mid in body.member_ids if mid != my_id))
    if not member_ids:
        raise HTTPException(status_code=400, detail="Ajoutez au moins un membre")

    if len(member_ids) + 1 > MAX_GROUP_SIZE:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_GROUP_SIZE} membres par groupe")

    # Verify members exist
    existing = await db.users.find(
        {"user_id": {"$in": member_ids}},
        {"user_id": 1},
    ).to_list(len(member_ids))
    valid_ids = {u["user_id"] for u in existing}

    # Filter out blocked users
    blocked_ids = await get_blocked_ids(my_id)
    valid_ids -= blocked_ids

    if not valid_ids:
        raise HTTPException(status_code=400, detail="Aucun membre valide trouvé")

    participants = sorted(list(valid_ids) + [my_id])
    now = datetime.now(timezone.utc).isoformat()

    # Initialize unread counts for all participants
    unread = {pid: 0 for pid in participants}

    conv = {
        "conversation_id": f"conv_{uuid.uuid4().hex[:12]}",
        "type": "group",
        "name": name,
        "participants": participants,
        "admins": [my_id],
        "created_by": my_id,
        "last_message": None,
        "unread_count": unread,
        "muted_by": [],
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

    # Enrich reply_to with sender display name (batch query)
    reply_sender_ids = {
        m["reply_to"]["sender_id"]
        for m in messages
        if m.get("reply_to") and m["reply_to"].get("sender_id")
    }
    if reply_sender_ids:
        reply_users = await db.users.find(
            {"user_id": {"$in": list(reply_sender_ids)}},
            {"_id": 0, "user_id": 1, "display_name": 1, "name": 1},
        ).to_list(len(reply_sender_ids))
        rname_map = {
            u["user_id"]: u.get("display_name") or u.get("name", "Utilisateur")
            for u in reply_users
        }
        for m in messages:
            if m.get("reply_to"):
                m["reply_to"]["sender_name"] = rname_map.get(
                    m["reply_to"]["sender_id"], "Utilisateur"
                )

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
    """Send a message in a conversation (direct or group)."""
    my_id = user["user_id"]
    conv = await _get_conversation_for_user(conversation_id, my_id)

    is_grp = _is_group(conv)
    blocked_ids = await get_blocked_ids(my_id)

    if not is_grp:
        # Direct: block check against other participant
        other_id = _other_participant(conv, my_id)
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

    # Validate reply_to (WhatsApp/Discord pattern: quote a message)
    reply_to = None
    if body.reply_to:
        replied_msg = await db.messages.find_one(
            {"message_id": body.reply_to, "conversation_id": conversation_id},
            {"_id": 0, "message_id": 1, "sender_id": 1, "content": 1, "images": 1},
        )
        if replied_msg:
            reply_to = {
                "message_id": replied_msg["message_id"],
                "sender_id": replied_msg["sender_id"],
                "content": (replied_msg.get("content") or "")[:150],
                "has_images": bool(replied_msg.get("images")),
            }

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
    if reply_to:
        message["reply_to"] = reply_to
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

    # ── Determine recipients (direct: 1, group: N-1) ──
    recipient_ids = [p for p in conv["participants"] if p != my_id]

    # Update conversation denormalized fields
    inc_updates = {f"unread_count.{pid}": 1 for pid in recipient_ids}
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
            "$inc": inc_updates,
        },
    )

    # ── Notifications (non-blocking) — respect mute + blocks ──
    display = user.get("display_name") or user.get("name", "Quelqu'un")
    muted_set = set(conv.get("muted_by", []))
    notified_ids = set()

    for rid in recipient_ids:
        if rid in muted_set or rid in blocked_ids:
            continue
        notified_ids.add(rid)
        try:
            preview = (content[:80] + ("..." if len(content) > 80 else "")) if has_text else "📷 Image"
            group_prefix = f"[{conv.get('name', 'Groupe')}] " if is_grp else ""
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "user_id": rid,
                "type": "new_message",
                "title": "Nouveau message",
                "message": f"{group_prefix}{display} : {preview}",
                "icon": "message-circle",
                "data": {"conversation_id": conversation_id, "sender_id": my_id},
                "read": False,
                "created_at": now,
            })
            push_title = f"{conv.get('name', 'Groupe')}" if is_grp else f"Message de {display}"
            push_body = f"{display}: {preview}" if is_grp else preview
            await send_push_to_user(rid, push_title, push_body, url="/messages", tag="dm")
        except Exception:
            pass

    # Notify mentioned users (skip already-notified recipients)
    for m in mentions:
        if m["user_id"] in notified_ids or m["user_id"] == my_id:
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

MESSAGE_REACTION_TYPES = {"bravo", "inspire", "fire", "solidaire", "curieux"}


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
                reaction_labels = {"bravo": "bravo 👏", "inspire": "inspire ✨", "fire": "fire 🔥", "solidaire": "solidaire 🤝", "curieux": "curieux 🧠"}
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


# ── Group Management (WhatsApp/Discord pattern) ──


@router.post("/conversations/{conversation_id}/members")
async def add_group_members(
    conversation_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Add members to a group conversation (admin only).

    Body: {member_ids: ["user_id_1", "user_id_2"]}
    Max group size: 20 participants.
    """
    my_id = user["user_id"]
    conv = await _get_conversation_for_user(conversation_id, my_id)

    if not _is_group(conv):
        raise HTTPException(status_code=400, detail="Cette action n'est disponible que pour les groupes")

    if my_id not in conv.get("admins", []):
        raise HTTPException(status_code=403, detail="Seuls les admins peuvent ajouter des membres")

    body = await request.json()
    new_ids = body.get("member_ids", [])
    if not new_ids:
        raise HTTPException(status_code=400, detail="Aucun membre à ajouter")

    current = set(conv["participants"])
    remaining = MAX_GROUP_SIZE - len(current)
    if remaining <= 0:
        raise HTTPException(status_code=400, detail=f"Le groupe est plein ({MAX_GROUP_SIZE} max)")

    # Filter: exist, not already in, not blocked
    blocked_ids = await get_blocked_ids(my_id)
    existing_users = await db.users.find(
        {"user_id": {"$in": new_ids}}, {"user_id": 1}
    ).to_list(len(new_ids))
    valid_ids = [
        u["user_id"] for u in existing_users
        if u["user_id"] not in current and u["user_id"] not in blocked_ids
    ][:remaining]

    if not valid_ids:
        raise HTTPException(status_code=400, detail="Aucun membre valide à ajouter")

    now = datetime.now(timezone.utc).isoformat()
    # Initialize unread counts for new members
    unread_set = {f"unread_count.{uid}": 0 for uid in valid_ids}

    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {
            "$addToSet": {"participants": {"$each": valid_ids}},
            "$set": {**unread_set, "updated_at": now},
        },
    )

    return {
        "added": valid_ids,
        "member_count": len(current) + len(valid_ids),
    }


@router.delete("/conversations/{conversation_id}/members/{member_id}")
async def remove_group_member(
    conversation_id: str,
    member_id: str,
    user: dict = Depends(get_current_user),
):
    """Remove a member from a group, or leave the group yourself.

    - Admin can remove any member (except self if sole admin).
    - Any member can remove themselves (= leave group).
    - If last member leaves, group is deleted.
    """
    my_id = user["user_id"]
    conv = await _get_conversation_for_user(conversation_id, my_id)

    if not _is_group(conv):
        raise HTTPException(status_code=400, detail="Cette action n'est disponible que pour les groupes")

    admins = conv.get("admins", [])
    is_admin = my_id in admins
    is_leaving = member_id == my_id

    if not is_leaving and not is_admin:
        raise HTTPException(status_code=403, detail="Seuls les admins peuvent retirer des membres")

    if member_id not in conv["participants"]:
        raise HTTPException(status_code=404, detail="Ce membre n'est pas dans le groupe")

    # If sole admin is leaving, promote the next participant or delete group
    remaining = [p for p in conv["participants"] if p != member_id]

    if not remaining:
        # Last member leaving — delete the group and its messages
        await db.messages.delete_many({"conversation_id": conversation_id})
        await db.conversations.delete_one({"conversation_id": conversation_id})
        return {"left": True, "group_deleted": True}

    now = datetime.now(timezone.utc).isoformat()
    update = {
        "$pull": {"participants": member_id, "admins": member_id, "muted_by": member_id},
        "$unset": {f"unread_count.{member_id}": ""},
        "$set": {"updated_at": now},
    }

    # If removing the last admin, promote the earliest remaining participant
    new_admins = [a for a in admins if a != member_id]
    if not new_admins and remaining:
        update["$addToSet"] = {"admins": remaining[0]}

    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        update,
    )

    return {
        "left": is_leaving,
        "removed": member_id,
        "member_count": len(remaining),
    }


@router.put("/conversations/{conversation_id}/group")
async def update_group(
    conversation_id: str,
    body: GroupUpdate,
    user: dict = Depends(get_current_user),
):
    """Update group name (admin only)."""
    my_id = user["user_id"]
    conv = await _get_conversation_for_user(conversation_id, my_id)

    if not _is_group(conv):
        raise HTTPException(status_code=400, detail="Cette action n'est disponible que pour les groupes")

    if my_id not in conv.get("admins", []):
        raise HTTPException(status_code=403, detail="Seuls les admins peuvent modifier le groupe")

    name = body.name.strip()
    await db.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$set": {"name": name, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )

    return {"name": name}


@router.post("/conversations/{conversation_id}/admin")
async def toggle_admin(
    conversation_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Promote or demote a group member as admin.

    Body: {user_id: "target_user_id"}
    Only existing admins can toggle. Creator can always be restored.
    """
    my_id = user["user_id"]
    conv = await _get_conversation_for_user(conversation_id, my_id)

    if not _is_group(conv):
        raise HTTPException(status_code=400, detail="Cette action n'est disponible que pour les groupes")

    if my_id not in conv.get("admins", []):
        raise HTTPException(status_code=403, detail="Seuls les admins peuvent gérer les rôles")

    body_data = await request.json()
    target_id = body_data.get("user_id", "")

    if target_id not in conv["participants"]:
        raise HTTPException(status_code=404, detail="Cet utilisateur n'est pas dans le groupe")

    admins = conv.get("admins", [])
    if target_id in admins:
        # Demote — but at least 1 admin must remain
        if len(admins) <= 1:
            raise HTTPException(status_code=400, detail="Le groupe doit avoir au moins un admin")
        await db.conversations.update_one(
            {"conversation_id": conversation_id},
            {"$pull": {"admins": target_id}},
        )
        return {"user_id": target_id, "is_admin": False}
    else:
        # Promote
        await db.conversations.update_one(
            {"conversation_id": conversation_id},
            {"$addToSet": {"admins": target_id}},
        )
        return {"user_id": target_id, "is_admin": True}


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


# ── Typing indicator (iMessage / Instagram DM pattern) ──
# Uses a lightweight MongoDB collection with 6-second TTL auto-expire.
# Frontend polls every 3s alongside messages. No WebSocket needed.

TYPING_TTL_SECONDS = 6


@router.post("/conversations/{conversation_id}/typing")
@limiter.limit("20/minute")
async def signal_typing(
    request: Request,
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    """Signal that the current user is typing in a conversation."""
    my_id = user["user_id"]
    # Verify participation (lightweight check)
    conv = await db.conversations.find_one(
        {"conversation_id": conversation_id, "participants": my_id},
        {"_id": 1},
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")

    now = datetime.now(timezone.utc)
    await db.typing_indicators.update_one(
        {"conversation_id": conversation_id, "user_id": my_id},
        {"$set": {
            "conversation_id": conversation_id,
            "user_id": my_id,
            "display_name": user.get("display_name") or user.get("name", ""),
            "expires_at": now,  # TTL index will auto-delete after TYPING_TTL_SECONDS
        }},
        upsert=True,
    )
    return {"ok": True}


@router.get("/conversations/{conversation_id}/typing")
async def get_typing_users(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    """Get users currently typing in a conversation (excludes self)."""
    my_id = user["user_id"]
    # Verify participation
    conv = await db.conversations.find_one(
        {"conversation_id": conversation_id, "participants": my_id},
        {"_id": 1},
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")

    typers = await db.typing_indicators.find(
        {"conversation_id": conversation_id, "user_id": {"$ne": my_id}},
        {"_id": 0, "user_id": 1, "display_name": 1},
    ).to_list(20)

    return {"typing": typers}
