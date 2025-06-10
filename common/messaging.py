import json
import logging
from aio_pika import connect_robust, Message, DeliveryMode, IncomingMessage
from typing import Callable, Awaitable

logger = logging.getLogger("common.messaging")

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

class RabbitConsumer:
    def __init__(self, url: str):
        self.url = url
        self._conn = None
        self._chan = None

    async def connect(self):
        if not self._conn:
            self._conn = await connect_robust(self.url)
            self._chan = await self._conn.channel()
            logger.info(f"Connected to RabbitMQ at {self.url}")

    async def consume(
        self,
        queue_name: str,
        on_message: Callable[[dict], Awaitable[None]],
        *,
        prefetch_count: int = 1
    ):
        await self.connect()
        await self._chan.set_qos(prefetch_count=prefetch_count)
        queue = await self._chan.declare_queue(queue_name, durable=True)
        await queue.consume(lambda msg: self._handle(msg, on_message))

    async def _handle(self, msg: IncomingMessage, callback: Callable[[dict], Awaitable[None]]):
        # Mesajı process() bloğu içinde ack/nack yönetimi ile ele al
        async with msg.process(ignore_processed=True):
            payload = json.loads(msg.body.decode("utf-8"))
            await callback(payload)