"""Task 20: /imagine — translate any language via Groq + FLUX generation."""
import io
import logging
import urllib.parse

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message, PhotoSize, BufferedInputFile
from aiogram.exceptions import TelegramBadRequest

from services.image_service import ImageService
from services.groq_service import GroqService
from services.rate_limiter import InMemoryRateLimiter

logger = logging.getLogger(__name__)
router = Router()


FLUX_SYSTEM = (
    "You are a professional Prompt Engineer for the FLUX image generation model. "
    "Your task is to take the user's input (which can be ANY object, animal, or concept in any language) and:\n"
    "1. Translate it accurately into English.\n"
    "2. Expand it into a detailed, high-quality descriptive prompt "
    "(add keywords like 'photorealistic, 8k resolution, highly detailed, masterpiece, cinematic lighting').\n"
    "3. Output ONLY the final English prompt text. Do NOT include quotes, "
    "do NOT include intro text. Just the clean text."
)

SEARCH_SYSTEM = (
    "You are a photo search keyword extractor. "
    "The user will write a request in ANY language. "
    "Your job: output ONLY 1-2 main English NOUNS that describe what should be in the photo. "
    "No adjectives, no quality words, no sentences. "
    "Examples:\n"
    "- 'большой красный помидор' → tomato\n"
    "- 'кот' → cat\n"
    "- 'летающий корабль' → airship\n"
    "- 'красивая девушка с цветами' → woman flowers\n"
    "- 'Алматы сити' → city\n"
    "- '큰 빨간 토마토' → tomato\n"
    "- 'закат в горах' → sunset mountains\n"
    "Output ONLY the keyword(s), nothing else."
)


@router.message(Command("imagine"))
async def handle_imagine(
    message: Message,
    command: CommandObject,
    groq_service: GroqService,
    image_service: ImageService,
    rate_limiter: InMemoryRateLimiter,
):
    user_prompt = command.args

    if not user_prompt:
        await message.answer(
            "❌ Вы не ввели запрос для рисования!\n\n"
            "Пример: <code>/imagine летающий корабль</code>",
            parse_mode="HTML",
        )
        return

    user_id = message.from_user.id
    allowed, reason = await rate_limiter.check(user_id, message.chat.id)
    if not allowed:
        await message.answer(f"⏳ {reason}")
        return

    status_msg = await message.answer("🔄 Перевожу запрос и генерирую изображение...")

    try:
        # Запрос 1: полный промпт для FLUX/Pollinations
        flux_prompt_raw = await groq_service.translate_prompt(user_prompt, FLUX_SYSTEM)
        clean_prompt = flux_prompt_raw.strip().replace('"', '').replace("'", "")

        # Запрос 2: только главные существительные для поиска фото
        search_raw = await groq_service.translate_prompt(user_prompt, SEARCH_SYSTEM)
        search_keywords = search_raw.strip().replace('"', '').replace("'", "").lower()

        logger.info(
            f"user={user_id} original='{user_prompt[:30]}' "
            f"flux='{clean_prompt[:60]}' search='{search_keywords}'"
        )

        # Пробуем Pollinations (Telegram качает сам)
        encoded_prompt = urllib.parse.quote(clean_prompt)
        image_url = (
            f"https://image.pollinations.ai/p/{encoded_prompt}"
            f"?width=1024&height=1024&nologo=true&model=flux"
        )
        try:
            await message.answer_photo(
                photo=image_url,
                caption=f"🎨 {user_prompt}",
            )
            await status_msg.delete()
            logger.info(f"OK Pollinations user={user_id}")
            return
        except (TelegramBadRequest, Exception) as e:
            logger.warning(f"Pollinations недоступен: {e}")

        # Fallback: loremflickr с ТОЧНЫМИ ключевыми словами от Groq
        await status_msg.edit_text("🔄 Подбираю изображение...")
        image_bytes = await image_service.generate_photo(search_keywords)

        if not image_bytes:
            await status_msg.edit_text("⚠️ Не удалось найти изображение. Попробуйте другой запрос.")
            return

        await status_msg.delete()
        await message.answer_photo(
            BufferedInputFile(image_bytes, filename="image.jpg"),
            caption=f"🎨 {user_prompt}",
        )
        logger.info(f"OK loremflickr user={user_id} kw='{search_keywords}' size={len(image_bytes)}")

    except Exception as e:
        logger.exception(f"Ошибка /imagine user={user_id}: {e}")
        try:
            await status_msg.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


@router.message(F.photo)
async def handle_photo(
    message: Message,
    image_service: ImageService,
    rate_limiter: InMemoryRateLimiter,
):
    user_id = message.from_user.id
    allowed, reason = await rate_limiter.check(user_id, message.chat.id)
    if not allowed:
        await message.answer(f"⏳ {reason}")
        return

    sent = await message.answer("🔍 <i>Анализирую изображение...</i>", parse_mode="HTML")
    caption = message.caption or "Опиши это изображение подробно."

    try:
        photo: PhotoSize = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        buf = io.BytesIO()
        await message.bot.download_file(file.file_path, buf)
        description = await image_service.analyze_image_bytes(buf.getvalue(), question=caption)
        await sent.edit_text(
            f"🖼 <b>Анализ изображения:</b>\n\n{description}",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception(f"Ошибка анализа user={user_id}: {e}")
        await sent.edit_text("⚠️ Не удалось проанализировать изображение.")
