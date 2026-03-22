"""
Tests for messaging — conversation creation, sending, inbox, read receipts, security.
Covers the full flow: profile → start conversation → exchange messages → mark read.
"""

from database import db
from auth import create_token
from httpx import AsyncClient, ASGITransport


async def _get_client_for_user(app, user_doc):
    token = create_token(user_doc["user_id"])
    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )


class TestStartConversation:
    async def test_start_conversation(self, client_authenticated, premium_user):
        resp = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Salut! Ton streak m'impressionne!",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "conversation_id" in data
        assert "message_id" in data
        assert data["created"] is True

    async def test_start_conversation_deduplication(
        self, client_authenticated, premium_user
    ):
        """Starting a conversation with the same user returns existing one."""
        first = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "First message",
            },
        )
        second = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Second message",
            },
        )
        assert first.json()["conversation_id"] == second.json()["conversation_id"]
        assert second.json()["created"] is False

    async def test_cannot_message_self(self, client_authenticated, test_user):
        resp = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": test_user["user_id"],
                "message": "Talking to myself",
            },
        )
        assert resp.status_code == 400

    async def test_cannot_message_nonexistent_user(self, client_authenticated):
        resp = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": "fake_user_id",
                "message": "Hello?",
            },
        )
        assert resp.status_code == 404

    async def test_creates_notification(self, client_authenticated, premium_user):
        await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Hey!",
            },
        )
        notif = await db.notifications.find_one({
            "user_id": premium_user["user_id"],
            "type": "new_message",
        })
        assert notif is not None

    async def test_message_too_long(self, client_authenticated, premium_user):
        resp = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "x" * 2001,
            },
        )
        assert resp.status_code == 422

    async def test_empty_message(self, client_authenticated, premium_user):
        resp = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "",
            },
        )
        assert resp.status_code == 422


class TestSecurity:
    async def test_blocked_user_cannot_message(
        self, client_authenticated, test_user, premium_user
    ):
        """If test_user blocks premium_user, premium cannot message."""
        # Block
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/block"
        )

        # Premium tries to message test_user
        from server import app
        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.post(
                "/api/messages/conversations",
                json={
                    "recipient_id": test_user["user_id"],
                    "message": "Can you see this?",
                },
            )
            assert resp.status_code == 403

    async def test_cannot_message_private_profile(
        self, client_authenticated, premium_user
    ):
        """Cannot message a user with private profile."""
        await db.users.update_one(
            {"user_id": premium_user["user_id"]},
            {"$set": {"privacy": {"profile_visible": False}}},
        )

        resp = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Hello?",
            },
        )
        assert resp.status_code == 403

    async def test_block_prevents_message_in_existing_conversation(
        self, app, client_authenticated, test_user, premium_user
    ):
        """Blocking after conversation exists still prevents messaging."""
        # Start conversation
        create = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Hi",
            },
        )
        conv_id = create.json()["conversation_id"]

        # Block
        await client_authenticated.post(
            f"/api/users/{premium_user['user_id']}/block"
        )

        # Premium tries to send in existing conversation
        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.post(
                f"/api/messages/conversations/{conv_id}",
                json={"content": "Still here?"},
            )
            assert resp.status_code == 403


class TestInbox:
    async def test_get_empty_inbox(self, client_authenticated):
        resp = await client_authenticated.get("/api/messages/conversations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["conversations"] == []
        assert data["total"] == 0

    async def test_inbox_shows_conversations(
        self, client_authenticated, premium_user
    ):
        await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Test inbox",
            },
        )

        resp = await client_authenticated.get("/api/messages/conversations")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert "other_user" in data["conversations"][0]
        assert data["conversations"][0]["last_message"] is not None

    async def test_inbox_sorted_by_recent(
        self, app, client_authenticated, test_user, premium_user
    ):
        """Most recent conversation should be first."""
        # Create a second user for a second conversation
        import uuid
        from auth import hash_password

        second_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": second_id,
            "email": f"{second_id}@test.com",
            "name": "Second User",
            "password": hash_password("Pass123!"),
        })

        # First conversation
        await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "First conv",
            },
        )

        # Second conversation (more recent)
        await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": second_id,
                "message": "Second conv",
            },
        )

        resp = await client_authenticated.get("/api/messages/conversations")
        convs = resp.json()["conversations"]
        assert len(convs) == 2
        # Most recent first
        assert convs[0]["last_message"]["content"] == "Second conv"


class TestMessages:
    async def test_send_and_retrieve_messages(
        self, app, client_authenticated, premium_user
    ):
        # Start conversation
        create = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Message 1",
            },
        )
        conv_id = create.json()["conversation_id"]

        # Send another message
        await client_authenticated.post(
            f"/api/messages/conversations/{conv_id}",
            json={"content": "Message 2"},
        )

        # Premium user replies
        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            await premium_client.post(
                f"/api/messages/conversations/{conv_id}",
                json={"content": "Reply from premium"},
            )

        # Retrieve messages
        resp = await client_authenticated.get(
            f"/api/messages/conversations/{conv_id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["messages"]) == 3
        # Chronological order (oldest first)
        assert data["messages"][0]["content"] == "Message 1"
        assert data["messages"][2]["content"] == "Reply from premium"

    async def test_message_pagination(self, client_authenticated, premium_user):
        create = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Msg 1",
            },
        )
        conv_id = create.json()["conversation_id"]

        # Send more messages
        for i in range(4):
            await client_authenticated.post(
                f"/api/messages/conversations/{conv_id}",
                json={"content": f"Msg {i + 2}"},
            )

        # Get first page (limit 3)
        resp = await client_authenticated.get(
            f"/api/messages/conversations/{conv_id}?limit=3"
        )
        data = resp.json()
        assert len(data["messages"]) == 3
        assert data["has_more"] is True

    async def test_cannot_access_others_conversation(
        self, app, client_authenticated, premium_user
    ):
        # Create conversation between test and premium
        create = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Private",
            },
        )
        conv_id = create.json()["conversation_id"]

        # Third user tries to access it
        import uuid
        from auth import hash_password

        third_id = f"user_{uuid.uuid4().hex[:12]}"
        await db.users.insert_one({
            "user_id": third_id,
            "email": f"{third_id}@test.com",
            "name": "Third",
            "password": hash_password("Pass123!"),
        })

        third_client = await _get_client_for_user(
            app, {"user_id": third_id}
        )
        async with third_client:
            resp = await third_client.get(
                f"/api/messages/conversations/{conv_id}"
            )
            assert resp.status_code == 404


class TestReadReceipts:
    async def test_mark_conversation_read(
        self, app, client_authenticated, test_user, premium_user
    ):
        # Test user sends message to premium
        create = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Read this!",
            },
        )
        conv_id = create.json()["conversation_id"]

        # Premium marks as read
        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.post(
                f"/api/messages/conversations/{conv_id}/read"
            )
            assert resp.status_code == 200

            # Verify unread count is 0
            inbox = await premium_client.get("/api/messages/conversations")
            conv = inbox.json()["conversations"][0]
            assert conv["my_unread_count"] == 0

    async def test_unread_count(
        self, app, client_authenticated, test_user, premium_user
    ):
        # Send 3 messages to premium
        create = await client_authenticated.post(
            "/api/messages/conversations",
            json={
                "recipient_id": premium_user["user_id"],
                "message": "Msg 1",
            },
        )
        conv_id = create.json()["conversation_id"]

        await client_authenticated.post(
            f"/api/messages/conversations/{conv_id}",
            json={"content": "Msg 2"},
        )
        await client_authenticated.post(
            f"/api/messages/conversations/{conv_id}",
            json={"content": "Msg 3"},
        )

        # Check premium's unread count
        premium_client = await _get_client_for_user(app, premium_user)
        async with premium_client:
            resp = await premium_client.get("/api/messages/unread-count")
            assert resp.status_code == 200
            assert resp.json()["unread_count"] == 3
