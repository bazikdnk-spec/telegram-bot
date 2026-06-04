"""Task 18: Voice message handler via Groq Whisper."""
import io
import logging
import os
import tempfile
import time

from aiogram import Router, F
from aiogram.types import Message
from services.groq_service import GroqService
from services.rate_limiter import InMemoryRateLimiter

logger = logging.getLogger(__name__)
router = Router()

MAX_VOICE_SIZE = 25 * 1024 * 1024  # 25 MB


async def _convert_ogg_to_wav(ogg_bytes: bytes) -> bytes:
    """Convert ogg/opus to wav using ffmpeg-python."""
    import ffmpeg
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f_in:
        f_in.write(ogg_bytes)
        in_path = f_in.name
    out_path = in_path.replace(".ogg", ".wav")
    try:
        ffmpeg.input(in_path).output(out_path, ar=16000, ac=1).overwrite_output().run(quiet=True)
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        for p in (in_path, out_path):
            try:
                os.unlink(p)
            except OSError:
                pass


@router.message(F.voice)
async def handle_voice(message: Message, groq_service: GroqService, rate_limiter: InMemoryRateLimiter):
    user_id = message.from_user.id
    chat_id = message.chat.id

    allowed, reason = await rate_limiter.check(user_id, chat_id)
    if not allowed:
        await message.answer(f"⏳ {reason}")
        return

    voice = message.voice
    if voice.file_size and voice.file_size > MAX_VOICE_SIZE:
        await message.answer("⚠️ Голосовое сообщение слишком большое (максимум 25 МБ).")
        return

    sent = await message.answer("🎤 <i>Распознаю речь...</i>", parse_mode="HTML")

    try:
        # Download voice
        file = await message.bot.get_file(voice.file_id)
        buf = io.BytesIO()
        await message.bot.download_file(file.file_path, buf)
        ogg_bytes = buf.getvalue()

        # Convert to wav
        try:
            wav_bytes = await _convert_ogg_to_wav(ogg_bytes)
            audio_bytes = wav_bytes
            filename = "audio.wav"
        except Exception as e:
            logger.warning(f"FFmpeg недоступен: {e}, отправляем ogg напрямую")
            audio_bytes = ogg_bytes
            filename = "audio.ogg"

        transcription = await groq_service.transcribe_audio(audio_bytes, filename)

        await sent.edit_text(
            f"🎤 <b>Распознанный текст:</b>\n<i>{transcription}</i>\n\n"
            "🤖 <i>Генерирую ответ...</i>",
            parse_mode="HTML",
        )

        # Get AI response based on transcription
        final_text = ""
        last_update = 0.0
        async for chunk in groq_service.get_ai_stream_response(user_id, transcription):
            final_text = chunk
            now = time.time()
            if now - last_update >= 1.4:
                try:
                    await sent.edit_text(
                        f"🎤 <b>Распознано:</b> <i>{transcription[:100]}…</i>\n\n{final_text}",
                        parse_mode="HTML",
                    )
                    last_update = now
                except Exception:
                    pass

        if final_text:
            try:
                await sent.edit_text(
                    f"🎤 <b>Распознано:</b> <i>{transcription[:100]}…</i>\n\n{final_text}",
                    parse_mode="HTML",
                )
            except Exception:
                pass

    except Exception as e:
        logger.exception(f"Ошибка обработки голосового: {e}")
        await sent.edit_text("⚠️ Не удалось обработать голосовое сообщение. Попробуйте ещё раз.")
