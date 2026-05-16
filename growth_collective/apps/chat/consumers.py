import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.room = await self.get_room(self.room_slug)
        if self.room is None or not self.room.is_active:
            await self.close(code=4004)
            return

        if self.room.requires_premium and not self.user.has_premium_access():
            await self.close(code=4003)
            return

        # DM rooms: only participants can connect
        if self.room.slug.startswith('dm-'):
            is_participant = await self.is_participant(self.room, self.user)
            if not is_participant:
                await self.close(code=4003)
                return

        self.group_name = f'chat_{self.room_slug}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        history = await self.get_recent_messages(self.room)
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': history,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        body = data.get('message', '').strip()
        if not body or len(body) > 2000:
            return

        message = await self.save_message(self.room, self.user, body)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message_id': message.pk,
                'body': message.body,
                'sender_name': self.user.full_name,
                'sender_initials': self.user.initials,
                'timestamp': message.created_at.isoformat(),
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'body': event['body'],
            'sender_name': event['sender_name'],
            'sender_initials': event['sender_initials'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def get_room(self, slug):
        from apps.chat.models import Room
        try:
            return Room.objects.get(slug=slug)
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def is_participant(self, room, user):
        return room.participants.filter(pk=user.pk).exists()

    @database_sync_to_async
    def get_recent_messages(self, room):
        from apps.chat.models import Message
        messages = list(
            Message.objects
            .filter(room=room, is_deleted=False)
            .select_related('sender')
            .order_by('-created_at')[:50]
        )
        return [
            {
                'message_id': m.pk,
                'body': m.body,
                'sender_name': m.sender.full_name if m.sender else 'Deleted User',
                'sender_initials': m.sender.initials if m.sender else '??',
                'timestamp': m.created_at.isoformat(),
            }
            for m in messages
        ]

    @database_sync_to_async
    def save_message(self, room, user, body):
        from apps.chat.models import Message
        return Message.objects.create(room=room, sender=user, body=body)
