import asyncio
import logging

from service import PlagiarismCheckerService

logger = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

async def main():
    service = PlagiarismCheckerService()
    await service.start()

    logger.info("PlagiarismCheckerService started. Waiting for messages...")
    while True:
        await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down PlagiarismCheckerService...")