import asyncio
import logging
import time
from datetime import date

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot.config import settings
from bot.database.repositories.generation import GenerationRepository
from bot.database.repositories.user import UserRepository
from bot.handlers.states import VideoState
from bot.keyboards.generation import get_cancel_keyboard, get_video_keyboard
from bot.keyboards.main import get_main_keyboard
from bot.services.ai_providers.replicate_video import (
    VIDEO_MODELS,
    ReplicateVideoProvider,
)

logger = logging.getLogger(__name__)

router = Router(name="video")

IGNORED_BUTTONS_VIDEO = ("🎨", "💬", "🤖", "👤", "⭐", "ℹ️", "🎬")


def _video_progress_bar(pct: int) -> str:
    filled = pct // 5
    empty = 20 - filled
    return f"[{'█' * filled}{'░' * empty}] {pct}%"


def _time_estimate(elapsed: float, timeout: int) -> str:
    remaining = max(0, timeout - elapsed)
    if remaining < 60:
        return f"~{int(remaining)} сек"
    return f"~{int(remaining / 60)} мин {int(remaining % 60)} сек"


async def _update_video_timer(message: Message, start: float, provider_display: str, provider):
    while True:
        await asyncio.sleep(3)
        elapsed = time.time() - start
        pct = provider.estimate_progress(elapsed)
        time_left = _time_estimate(elapsed, provider.TIMEOUT_SECONDS)
        try:
            await message.edit_text(
                f"⏳ Генерирую видео...\n"
                f"🤖 Модель: {provider_display}\n\n"
                f"  {_video_progress_bar(pct)}\n\n"
                f"⏱ Прошло: {int(elapsed)} сек\n"
                f"⏰ Осталось: {time_left}"
            )
        except Exception:
            pass


@router.message(lambda m: m.text == "🎬 Создать видео")
async def btn_video(message: Message, state: FSMContext, session) -> None:
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(message.from_user.id)

    if user and not user.is_premium:
        today = date.today()
        if user.last_video_generation_date != today:
            user.video_generations_today = 0
            user.last_video_generation_date = today
            await session.commit()

        if user and user.video_generations_today >= user.video_daily_limit:
            await message.answer(
                "⚠️ Лимит генераций видео на сегодня исчерпан "
                f"({user.video_daily_limit}/день).\n\n"
                "⭐ Купите <b>Премиум</b> для безлимита!",
                reply_markup=get_main_keyboard(),
            )
            return

    await state.set_state(VideoState.waiting_prompt)
    await message.answer(
        "🎬 Опишите видео, которое хотите получить.\n\n"
        'Например: <i>"Закат над океаном, таймлапс, 5 секунд"</i>\n\n'
        "❌ Для отмены нажмите кнопку ниже.",
        reply_markup=get_cancel_keyboard("cancel_video"),
    )


@router.callback_query(lambda c: c.data == "cancel_video")
async def callback_cancel_video(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Генерация видео отменена.")
    await callback.message.answer(
        "Выберите действие:", reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.message(VideoState.waiting_prompt)
async def handle_video_prompt(message: Message, state: FSMContext, session) -> None:
    if not message.text:
        await message.answer("Отправьте текстовое описание видео.")
        return

    if message.text.startswith(IGNORED_BUTTONS_VIDEO):
        return

    prompt = message.text.strip()
    if not prompt:
        await message.answer("Промпт не может быть пустым. Попробуйте ещё раз.")
        return

    await state.clear()

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Отправьте /start", reply_markup=get_main_keyboard())
        return

    provider_key = user.selected_video_provider
    model_info = VIDEO_MODELS.get(provider_key, VIDEO_MODELS["wan"])
    provider_display = f"{model_info['emoji']} {model_info['name']}"

    start = time.time()
    provider_obj = ReplicateVideoProvider(api_key=settings.replicate_api_token)
    loading_msg = await message.answer(
        f"⏳ Генерирую видео...\n"
        f"🤖 Модель: {provider_display}\n\n"
        f"  {_video_progress_bar(10)}\n\n"
        f"⏱ Прошло: 0 сек\n"
        f"⏰ Осталось: ~{provider_obj.TIMEOUT_SECONDS} сек"
    )

    timer_task = asyncio.create_task(
        _update_video_timer(loading_msg, start, provider_display, provider_obj)
    )

    try:
        video_bytes = await provider_obj.generate(
            prompt,
            model=provider_key,
            width=720,
            height=1280,
            duration=5,
        )

        gen_repo = GenerationRepository(session)
        generation = await gen_repo.create(
            user_id=user.id,
            prompt=f"[VIDEO] {prompt}",
            provider=provider_key,
            image_path=None,
        )

        user.video_generations_today += 1
        user.last_video_generation_date = date.today()
        await session.commit()

        elapsed = int(time.time() - start)
        timer_task.cancel()
        try:
            await timer_task
        except asyncio.CancelledError:
            pass

        await loading_msg.delete()

        video_file = BufferedInputFile(video_bytes, filename="video.mp4")
        left = user.video_generations_left
        caption = (
            f"🎬 <b>Видео #{generation.id}</b>\n\n"
            f"📝 Промпт: <i>{prompt}</i>\n"
            f"🤖 Модель: {provider_display}\n"
            f"⏱ Время: {elapsed} сек\n"
            f"📊 Осталось: {left}/{user.video_daily_limit}"
        )

        await message.answer_video(
            video=video_file,
            caption=caption,
            reply_markup=get_video_keyboard(generation.id),
        )

    except Exception as e:
        logger.exception("Video generation failed: %s", e)
        elapsed = int(time.time() - start)
        try:
            await loading_msg.edit_text(
                f"❌ Ошибка генерации видео (заняло {elapsed} сек).\n"
                f"Попробуйте ещё раз позже.\n\n"
                f"<code>{type(e).__name__}: {str(e)[:100]}</code>"
            )
        except Exception:
            pass
        await message.answer(
            "Выберите действие:", reply_markup=get_main_keyboard()
        )
    finally:
        if not timer_task.done():
            timer_task.cancel()
            try:
                await timer_task
            except asyncio.CancelledError:
                pass


@router.callback_query(lambda c: c.data.startswith("repeat_video:"))
async def callback_repeat_video(callback: CallbackQuery, session):
    generation_id = int(callback.data.split(":")[1])
    gen_repo = GenerationRepository(session)
    generation = await gen_repo.get_by_id(generation_id)

    if not generation:
        await callback.answer("Генерация не найдена", show_alert=True)
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(callback.from_user.id)

    if user and not user.is_premium:
        today = date.today()
        if user.last_video_generation_date != today:
            user.video_generations_today = 0
            user.last_video_generation_date = today
            await session.commit()

        if user and user.video_generations_today >= user.video_daily_limit:
            await callback.answer(
                "Лимит генераций видео на сегодня исчерпан", show_alert=True
            )
            return

    await callback.answer()

    provider_key = generation.provider
    model_info = VIDEO_MODELS.get(provider_key, VIDEO_MODELS["wan"])
    provider_display = f"{model_info['emoji']} {model_info['name']}"

    start = time.time()
    provider_obj = ReplicateVideoProvider(api_key=settings.replicate_api_token)
    loading_msg = await callback.message.answer(
        f"⏳ Повторная генерация видео...\n"
        f"🤖 Модель: {provider_display}\n\n"
        f"  {_video_progress_bar(10)}\n\n"
        f"⏱ Прошло: 0 сек\n"
        f"⏰ Осталось: ~{provider_obj.TIMEOUT_SECONDS} сек"
    )

    timer_task = asyncio.create_task(
        _update_video_timer(loading_msg, start, provider_display, provider_obj)
    )

    try:
        clean_prompt = generation.prompt
        if clean_prompt.startswith("[VIDEO] "):
            clean_prompt = clean_prompt[8:]

        video_bytes = await provider_obj.generate(
            clean_prompt,
            model=provider_key,
            width=720,
            height=1280,
            duration=5,
        )

        new_gen = await gen_repo.create(
            user_id=generation.user_id,
            prompt=generation.prompt,
            provider=provider_key,
            image_path=None,
        )

        if user:
            user.video_generations_today += 1
            user.last_video_generation_date = date.today()
            await session.commit()

        elapsed = int(time.time() - start)
        timer_task.cancel()
        try:
            await timer_task
        except asyncio.CancelledError:
            pass

        await loading_msg.delete()

        left = user.video_generations_left if user else "?"
        video_file = BufferedInputFile(video_bytes, filename="video.mp4")
        await callback.message.answer_video(
            video=video_file,
            caption=(
                f"🎬 <b>Видео #{new_gen.id}</b>\n\n"
                f"📝 Промпт: <i>{clean_prompt}</i>\n"
                f"🤖 Модель: {provider_display}\n"
                f"⏱ Время: {elapsed} сек\n"
                f"📊 Осталось: {left}/{user.video_daily_limit if user else '?'}"
            ),
            reply_markup=get_video_keyboard(new_gen.id),
        )

    except Exception as e:
        logger.exception("Repeat video generation failed: %s", e)
        elapsed = int(time.time() - start)
        try:
            await loading_msg.edit_text(
                f"❌ Ошибка генерации видео (заняло {elapsed} сек).\n\n"
                f"<code>{type(e).__name__}: {str(e)[:100]}</code>"
            )
        except Exception:
            pass
        await callback.message.answer(
            "Выберите действие:", reply_markup=get_main_keyboard()
        )
    finally:
        if not timer_task.done():
            timer_task.cancel()
            try:
                await timer_task
            except asyncio.CancelledError:
                pass


@router.callback_query(lambda c: c.data.startswith("edit_video:"))
async def callback_edit_video(callback: CallbackQuery, state: FSMContext):
    await state.set_state(VideoState.waiting_prompt)
    await callback.message.edit_text(
        "✏️ Введите новый промпт для видео:",
        reply_markup=get_cancel_keyboard("cancel_video"),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("download_video:"))
async def callback_download_video(callback: CallbackQuery, session):
    generation_id = int(callback.data.split(":")[1])
    gen_repo = GenerationRepository(session)
    generation = await gen_repo.get_by_id(generation_id)

    if not generation or not generation.image_path:
        await callback.answer("Видео не найдено", show_alert=True)
        return

    from pathlib import Path

    video_path = Path(generation.image_path)
    if not video_path.exists():
        await callback.answer("Файл не найден на сервере", show_alert=True)
        return

    await callback.answer()
    from aiogram.types import FSInputFile

    clean_prompt = generation.prompt
    if clean_prompt.startswith("[VIDEO] "):
        clean_prompt = clean_prompt[8:]

    await callback.message.answer_document(
        document=FSInputFile(video_path),
        caption=f"⬇️ Видео #{generation.id} — {clean_prompt}",
    )
