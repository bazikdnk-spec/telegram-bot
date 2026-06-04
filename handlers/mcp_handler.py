"""Task 7: /files command via MCP filesystem server."""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("files"))
async def cmd_files(message: Message, mcp_aggregator):
    """Task 7: List files via MCP protocol."""
    sent = await message.answer("📂 <i>Загружаю список файлов...</i>", parse_mode="HTML")
    try:
        result = await mcp_aggregator.call_tool("fs__list_directory", {"path": "."})
        if not result:
            await sent.edit_text("📂 Директория пуста или недоступна.")
            return
        lines = [f"📄 {item}" for item in (result if isinstance(result, list) else [str(result)])]
        text = "📂 <b>Файлы проекта:</b>\n\n" + "\n".join(lines[:30])
        await sent.edit_text(text, parse_mode="HTML")
    except Exception as e:
        logger.exception(f"MCP files error: {e}")
        await sent.edit_text("⚠️ MCP сервер недоступен.")


@router.message(Command("ask"))
async def cmd_ask(message: Message, rag_service, groq_service):
    """Task 14: RAG search."""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /ask <вопрос>")
        return

    question = parts[1]
    sent = await message.answer("🔎 <i>Ищу в базе знаний...</i>", parse_mode="HTML")
    try:
        answer = await rag_service.rag_answer(question, groq_service)
        if answer:
            await sent.edit_text(f"📚 {answer}")
        else:
            await sent.edit_text("📚 В базе знаний ничего не найдено по этому вопросу.")
    except Exception as e:
        logger.exception(f"RAG error: {e}")
        await sent.edit_text("⚠️ RAG сервис временно недоступен.")
