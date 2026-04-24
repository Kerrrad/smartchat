from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, set[WebSocket]] = defaultdict(set)
        self.connection_counts: dict[int, int] = defaultdict(int)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[user_id].add(websocket)
        self.connection_counts[user_id] += 1

    async def disconnect(self, user_id: int, websocket: WebSocket) -> bool:
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                self.active_connections.pop(user_id, None)

        if user_id not in self.connection_counts:
            return False

        self.connection_counts[user_id] = max(0, self.connection_counts[user_id] - 1)
        if self.connection_counts[user_id] == 0:
            self.connection_counts.pop(user_id, None)
            self.active_connections.pop(user_id, None)
            return True
        return False

    async def send_json_to_user(self, user_id: int, payload: dict[str, Any]) -> None:
        for connection in self.active_connections.get(user_id, set()).copy():
            await connection.send_json(payload)

    async def broadcast_to_users(self, user_ids: set[int] | list[int], payload: dict[str, Any]) -> None:
        for user_id in set(user_ids):
            await self.send_json_to_user(user_id, payload)

    async def broadcast_all(self, payload: dict[str, Any]) -> None:
        for user_id in list(self.active_connections.keys()):
            await self.send_json_to_user(user_id, payload)

    def online_user_ids(self) -> set[int]:
        return set(self.connection_counts.keys())


ws_manager = ConnectionManager()
