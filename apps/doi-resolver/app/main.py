import asyncio
import logging

from app.service import DoiResolverService

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    service = DoiResolverService()
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        pass