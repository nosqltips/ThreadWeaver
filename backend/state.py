"""
StateGraph-native chat state manager.

Every conversation is a branch. Every message exchange is a commit
with intent metadata. Branching a conversation forks the state graph.

Falls back to simple in-memory storage if AgentStateGraph isn't available.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional

# Try to import AgentStateGraph; fall back to simple dict storage
try:
    from agentstategraph_py import StateGraph as AGS
    HAS_AGS = True
except ImportError:
    HAS_AGS = False


@dataclass
class Message:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    images: list = field(default_factory=list)


@dataclass
class Conversation:
    id: str
    title: str
    branch: str
    messages: list[Message] = field(default_factory=list)
    parent_id: Optional[str] = None
    parent_message_index: Optional[int] = None
    created_at: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)


class ChatStateManager:
    """Manages chat state backed by AgentStateGraph when available."""

    def __init__(self, db_path: str = None):
        self.conversations: dict[str, Conversation] = {}
        self._counter = 0

        # Initialize AgentStateGraph if available
        if HAS_AGS and db_path:
            self.sg = AGS(db_path)
            print(f"[StateGraph] Connected to {db_path}")
        elif HAS_AGS:
            self.sg = AGS()
            print("[StateGraph] Running in-memory")
        else:
            self.sg = None
            print("[StateGraph] Not available — using simple storage")

    def _next_id(self) -> str:
        self._counter += 1
        return f"conv-{self._counter:04d}"

    def _commit_to_sg(self, conv: Conversation, action: str, detail: str = ""):
        """Commit current conversation state to AgentStateGraph."""
        if not self.sg:
            return

        try:
            # Store conversation as JSON in StateGraph
            conv_data = {
                "title": conv.title,
                "message_count": len(conv.messages),
                "last_message": conv.messages[-1].content[:100] if conv.messages else "",
                "parent_id": conv.parent_id,
                "tags": conv.tags,
            }

            # Store messages separately for queryability
            messages_data = [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in conv.messages
            ]

            self.sg.set_json(
                f"/conversations/{conv.id}/meta",
                conv_data,
                detail or f"{action}: {conv.title}",
                ref=conv.branch,
                category=_action_to_category(action),
                agent="threadweaver",
                reasoning=f"Chat {action} in conversation '{conv.title}'",
            )

            self.sg.set_json(
                f"/conversations/{conv.id}/messages",
                messages_data,
                f"Message update: {len(conv.messages)} messages",
                ref=conv.branch,
                category="Refine",
                agent="threadweaver",
            )
        except Exception as e:
            print(f"[StateGraph] Commit error: {e}")

    def create_conversation(self, title: str = "New Chat") -> Conversation:
        conv_id = self._next_id()
        branch = f"conversations/{conv_id}"
        conv = Conversation(id=conv_id, title=title, branch=branch)
        self.conversations[conv_id] = conv

        # Create branch in StateGraph
        if self.sg:
            try:
                self.sg.branch(branch)
            except Exception:
                pass  # Branch might already exist
            self._commit_to_sg(conv, "create", f"New conversation: {title}")

        return conv

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        return self.conversations.get(conv_id)

    def add_message(self, conv_id: str, role: str, content: str, images: list = None) -> Message:
        conv = self.conversations.get(conv_id)
        if not conv:
            raise ValueError(f"Conversation {conv_id} not found")

        msg = Message(role=role, content=content, images=images or [])
        conv.messages.append(msg)

        # Auto-title from first user message
        if len(conv.messages) == 1 and role == "user":
            conv.title = content[:50] + ("..." if len(content) > 50 else "")

        # Commit to StateGraph
        category = "Explore" if role == "user" else "Refine"
        self._commit_to_sg(
            conv,
            "message",
            f"{role} message in '{conv.title}'"
        )

        return msg

    def branch_conversation(
        self, conv_id: str, at_message: int, title: str = None
    ) -> Conversation:
        source = self.conversations.get(conv_id)
        if not source:
            raise ValueError(f"Conversation {conv_id} not found")
        if at_message < 0 or at_message >= len(source.messages):
            raise ValueError(f"Message index {at_message} out of range")

        new_id = self._next_id()
        new_branch = f"conversations/{new_id}"
        new_conv = Conversation(
            id=new_id,
            title=title or f"Branch of {source.title}",
            branch=new_branch,
            messages=list(source.messages[:at_message + 1]),
            parent_id=conv_id,
            parent_message_index=at_message,
        )
        self.conversations[new_id] = new_conv

        # Create branch in StateGraph from the source branch
        if self.sg:
            try:
                self.sg.branch(new_branch, source.branch)
            except Exception:
                try:
                    self.sg.branch(new_branch)
                except Exception:
                    pass
            self._commit_to_sg(
                new_conv,
                "branch",
                f"Branched from '{source.title}' at message {at_message}"
            )

        return new_conv

    def list_conversations(self) -> list[dict]:
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
        query_lower = query.lower()
        results = []

        # Search in local state
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

        # Also search AgentStateGraph reasoning traces if available
        if self.sg:
            try:
                sg_results = self.sg.query(reasoning_contains=query)
                for r in sg_results[:5]:
                    results.append({
                        "conversation_id": "sg",
                        "conversation_title": f"[StateGraph] {r.get('intent', {}).get('description', '')}",
                        "message_index": 0,
                        "role": "system",
                        "content_preview": r.get("reasoning", "")[:100],
                        "timestamp": 0,
                    })
            except Exception:
                pass

        return results

    def create_highlight(
        self, conv_id: str, start_index: int, end_index: int, tag: str = None
    ) -> dict:
        conv = self.conversations.get(conv_id)
        if not conv:
            raise ValueError(f"Conversation {conv_id} not found")

        messages = conv.messages[start_index:end_index + 1]
        highlight = {
            "conversation_id": conv_id,
            "start_index": start_index,
            "end_index": end_index,
            "tag": tag or "highlight",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "created_at": time.time(),
        }

        if tag and tag not in conv.tags:
            conv.tags.append(tag)

        # Store highlight in StateGraph as an epoch-like bookmark
        if self.sg:
            try:
                self.sg.create_epoch(
                    f"highlight-{conv_id}-{start_index}-{end_index}",
                    f"Highlight: {tag or 'note'} from '{conv.title}'",
                    [],
                )
            except Exception:
                pass

        return highlight

    def get_conversation_tree(self, conv_id: str) -> dict:
        conv = self.conversations.get(conv_id)
        if not conv:
            return {}

        # Find root
        root_id = conv_id
        while self.conversations.get(root_id, Conversation("", "", "")).parent_id:
            parent = self.conversations[root_id].parent_id
            if parent and parent in self.conversations:
                root_id = parent
            else:
                break

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

    def get_provenance(self, conv_id: str) -> list[dict]:
        """Get AgentStateGraph provenance for a conversation."""
        if not self.sg:
            return []
        try:
            conv = self.conversations.get(conv_id)
            if not conv:
                return []
            log = self.sg.log(ref=conv.branch, limit=20)
            return log
        except Exception:
            return []


def _action_to_category(action: str) -> str:
    return {
        "create": "Checkpoint",
        "message": "Refine",
        "branch": "Explore",
        "highlight": "Checkpoint",
    }.get(action, "Refine")
