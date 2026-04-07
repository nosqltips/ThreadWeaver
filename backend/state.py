"""
StateGraph integration for chat — conversations as versioned state.

Each conversation is a branch. Each message exchange is a commit.
Branching a conversation creates a fork from any message.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional

# For now, use a simple in-memory state manager.
# When stategraph-py is pip-installable, swap this for the real thing.
# The API mirrors StateGraph exactly so the swap is seamless.


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    images: list = field(default_factory=list)  # [{data: base64, media_type: str}]


@dataclass
class Conversation:
    id: str
    title: str
    branch: str  # StateGraph branch name
    messages: list[Message] = field(default_factory=list)
    parent_id: Optional[str] = None  # if branched from another conversation
    parent_message_index: Optional[int] = None  # message index where branched
    created_at: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)


class ChatStateManager:
    """Manages chat state — conversations, branching, history."""

    def __init__(self, db_path: str = None):
        self.conversations: dict[str, Conversation] = {}
        self.db_path = db_path
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"conv-{self._counter:04d}"

    def create_conversation(self, title: str = "New Chat") -> Conversation:
        """Create a new conversation."""
        conv_id = self._next_id()
        conv = Conversation(
            id=conv_id,
            title=title,
            branch=f"conversations/{conv_id}",
        )
        self.conversations[conv_id] = conv
        return conv

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        return self.conversations.get(conv_id)

    def add_message(self, conv_id: str, role: str, content: str, images: list = None) -> Message:
        """Add a message to a conversation."""
        conv = self.conversations.get(conv_id)
        if not conv:
            raise ValueError(f"Conversation {conv_id} not found")
        msg = Message(role=role, content=content, images=images or [])
        conv.messages.append(msg)

        # Auto-title from first user message
        if len(conv.messages) == 1 and role == "user":
            conv.title = content[:50] + ("..." if len(content) > 50 else "")

        return msg

    def branch_conversation(
        self, conv_id: str, at_message: int, title: str = None
    ) -> Conversation:
        """Branch a conversation from a specific message index."""
        source = self.conversations.get(conv_id)
        if not source:
            raise ValueError(f"Conversation {conv_id} not found")
        if at_message < 0 or at_message >= len(source.messages):
            raise ValueError(f"Message index {at_message} out of range")

        new_id = self._next_id()
        new_conv = Conversation(
            id=new_id,
            title=title or f"Branch of {source.title}",
            branch=f"conversations/{new_id}",
            messages=list(source.messages[: at_message + 1]),  # copy up to branch point
            parent_id=conv_id,
            parent_message_index=at_message,
        )
        self.conversations[new_id] = new_conv
        return new_conv

    def list_conversations(self) -> list[dict]:
        """List all conversations with metadata."""
        result = []
        for conv in sorted(
            self.conversations.values(), key=lambda c: c.created_at, reverse=True
        ):
            result.append({
                "id": conv.id,
                "title": conv.title,
                "branch": conv.branch,
                "message_count": len(conv.messages),
                "parent_id": conv.parent_id,
                "parent_message_index": conv.parent_message_index,
                "tags": conv.tags,
                "created_at": conv.created_at,
            })
        return result

    def search_conversations(self, query: str) -> list[dict]:
        """Search across all conversations by content."""
        query_lower = query.lower()
        results = []
        for conv in self.conversations.values():
            for i, msg in enumerate(conv.messages):
                if query_lower in msg.content.lower():
                    results.append({
                        "conversation_id": conv.id,
                        "conversation_title": conv.title,
                        "message_index": i,
                        "role": msg.role,
                        "content_preview": msg.content[:100],
                        "timestamp": msg.timestamp,
                    })
        return results

    def create_highlight(
        self, conv_id: str, start_index: int, end_index: int, tag: str = None
    ) -> dict:
        """Highlight a range of messages — creates a tagged reference."""
        conv = self.conversations.get(conv_id)
        if not conv:
            raise ValueError(f"Conversation {conv_id} not found")

        messages = conv.messages[start_index : end_index + 1]
        highlight = {
            "conversation_id": conv_id,
            "start_index": start_index,
            "end_index": end_index,
            "tag": tag or "highlight",
            "messages": [
                {"role": m.role, "content": m.content} for m in messages
            ],
            "created_at": time.time(),
        }

        if tag and tag not in conv.tags:
            conv.tags.append(tag)

        return highlight

    def get_conversation_tree(self, conv_id: str) -> dict:
        """Get the branch tree for a conversation and all its forks."""
        conv = self.conversations.get(conv_id)
        if not conv:
            return {}

        # Find root
        root_id = conv_id
        while self.conversations.get(root_id, Conversation("", "", "")).parent_id:
            root_id = self.conversations[root_id].parent_id

        # Build tree from root
        return self._build_tree(root_id)

    def _build_tree(self, conv_id: str) -> dict:
        conv = self.conversations.get(conv_id)
        if not conv:
            return {}

        children = [
            self._build_tree(c.id)
            for c in self.conversations.values()
            if c.parent_id == conv_id
        ]

        return {
            "id": conv.id,
            "title": conv.title,
            "message_count": len(conv.messages),
            "branch_point": conv.parent_message_index,
            "children": children,
        }
