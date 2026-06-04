"""Tasks 1, 22, 28: Main entrypoint — modular DI, polling/webhook mode, structured logging."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config.settings import settings
from handlers import common, voice, image_handler, admin, private, mcp_handler
from services.groq_service import GroqService
from services.rate_limiter import create_rate_limiter
from services.ollama_service import OllamaService
from services.rag_service import RagService
from services.search_service import SearchService
from services.image_service import ImageService
from services.calendar_service import CalendarService
from mcp.aggregator import MCPAggregator
from utils.logging_setup import setup_logging, setup_tracing

logger = logging.getLogger(__name__)


async def build_dispatcher(
    groq_service: GroqService,
    rate_limiter,
    ollama_service: OllamaService,
    rag_service: RagService,
    search_service: SearchService,
    image_service: ImageService,
    calendar_service: CalendarService,
    mcp_aggregator: MCPAggregator,
) -> Dispatcher:
    dp = Dispatcher(
        groq_service=groq_service,
        rate_limiter=rate_limiter,
        ollama_service=ollama_service,
        rag_service=rag_service,
        search_service=search_service,
        image_service=image_service,
        calendar_service=calendar_service,
        mcp_aggregator=mcp_aggregator,
    )
    # Task 13: private mode router must be first (it filters messages)
    dp.include_router(private.router)
    dp.include_router(common.router)
    dp.include_router(voice.router)
    dp.include_router(image_handler.router)
    dp.include_router(admin.router)
    dp.include_router(mcp_handler.router)
    return dp


async def polling_mode(bot: Bot, dp: Dispatcher):
    """Task 0.1: Default long-polling mode."""
    logger.info("Запуск в режиме long polling...")
    await dp.start_polling(bot)


async def webhook_mode(bot: Bot, dp: Dispatcher):
    """Task 22: Webhook mode via aiohttp."""
    await bot.set_webhook(
        url=settings.webhook_url + settings.webhook_path,
        drop_pending_updates=True,
    )
    app = web.Application()
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=settings.webhook_port)
    await site.start()
    logger.info(f"Webhook запущен на порту {settings.webhook_port}, путь {settings.webhook_path}")

    # Task 22: graceful shutdown with webhook drain
    try:
        await asyncio.Event().wait()
    finally:
        await bot.delete_webhook()
        await runner.cleanup()
        logger.info("Webhook остановлен, очередь дренирована.")


async def main():
    # Task 28: structured logging + tracing
    setup_logging(settings.log_file, settings.log_level)
    tracer = setup_tracing("telegram-bot")

    bot = Bot(token=settings.telegram_token)

    groq_service = GroqService(settings=settings)
    rate_limiter = await create_rate_limiter(settings)
    ollama_service = OllamaService(settings=settings)
    rag_service = RagService(settings=settings, ollama_service=ollama_service)
    search_service = SearchService(settings=settings)
    image_service = ImageService(settings=settings, groq_service=groq_service)
    calendar_service = CalendarService(settings=settings)
    mcp_aggregator = MCPAggregator(settings=settings)

    await rag_service.init_pool()
    await mcp_aggregator.connect_all()

    dp = await build_dispatcher(
        groq_service, rate_limiter, ollama_service, rag_service,
        search_service, image_service, calendar_service, mcp_aggregator,
    )

    logger.info("Бот запущен.")
    try:
        if settings.webhook_url:
            await webhook_mode(bot, dp)
        else:
            await polling_mode(bot, dp)
    finally:
        await mcp_aggregator.disconnect_all()
        await image_service.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
