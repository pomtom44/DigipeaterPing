import asyncio
import logging

import uvicorn

from app import config
from app.aprs_is import AprsIsListener
from app.server import create_app
from app.store import PingStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    store = PingStore(config.DB_PATH)
    listener = AprsIsListener(store)
    app = create_app(store)

    server_config = uvicorn.Config(app, host="0.0.0.0", port=config.HTTP_PORT, log_level="warning")
    server = uvicorn.Server(server_config)

    logger.info("Starting DigipeaterPing as %s, HTTP on :%s", config.MYCALL, config.HTTP_PORT)
    await asyncio.gather(listener.run(), server.serve())


if __name__ == "__main__":
    asyncio.run(main())
