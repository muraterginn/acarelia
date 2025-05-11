import json
from aio_pika import connect_robust, Message, DeliveryMode
from app.config import settings   # her servisin kendi config’ini okuyan Settings

class RabbitPublisher:
    def __init__(self, url: str):
        self.url = url
        self._conn = None
        self._chan = None

    async def connect(self):
        if self._conn is None:
            self._conn = await connect_robust(self.url)
            self._chan = await self._conn.channel()

    async def declare_queue(self, name: str):
        await self._chan.declare_queue(name, durable=True)

    async def publish(self, queue: str, payload: dict):
        await self.connect()
        await self.declare_queue(queue)
        msg = Message(
            body=json.dumps(payload).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json"
        )
        await self._chan.default_exchange.publish(msg, routing_key=queue)