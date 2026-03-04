import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import ResearchQuery


class ResearchConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.query_id = self.scope["url_route"]["kwargs"]["query_id"]
        self.group_name = f"research_{self.query_id}"
        user = self.scope.get("user")

        if not user or user.is_anonymous:
            await self.close()
            return

        # Verify user owns the query
        owns_query = await self.check_ownership(user.id, self.query_id)
        if not owns_query:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def research_update(self, event):
        await self.send_json(event["message"])

    @database_sync_to_async
    def check_ownership(self, user_id, query_id):
        return ResearchQuery.objects.filter(id=query_id, user_id=user_id).exists()
